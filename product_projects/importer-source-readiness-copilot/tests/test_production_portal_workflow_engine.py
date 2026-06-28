from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_portal_workflow_engine import (
    STATUS,
    build_production_portal_workflow_engine,
    write_production_portal_workflow_engine_artifacts,
)


class ProductionPortalWorkflowEngineTests(unittest.TestCase):
    def test_manifest_maps_six_portals_and_first_screen_options(self) -> None:
        manifest = build_production_portal_workflow_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["portal_count"], 6)
        self.assertEqual(manifest["workflow_count"], 6)
        self.assertEqual(manifest["first_screen_option_count"], 4)
        self.assertGreaterEqual(manifest["ui_route_count"], 60)
        self.assertGreaterEqual(manifest["api_route_count"], 50)
        self.assertTrue(manifest["all_required_routes_present"])
        self.assertTrue(manifest["first_screen_routes_present"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["live_payment_ready"])
        self.assertFalse(manifest["unrestricted_uploads_enabled"])

    def test_portal_records_cover_required_personas_and_routes(self) -> None:
        manifest = build_production_portal_workflow_engine(ROOT)
        portals = {row["portal_id"]: row for row in manifest["portal_records"]}

        for portal_id in (
            "public_portal",
            "exporter_portal",
            "importer_portal",
            "expert_reviewer_portal",
            "operator_admin_portal",
            "enterprise_portal",
        ):
            self.assertIn(portal_id, portals)
            portal = portals[portal_id]
            self.assertEqual(portal["route_coverage_status"], "covered")
            self.assertFalse(portal["missing_routes"])
            self.assertTrue(portal["business_owner_language"])
            self.assertTrue(portal["mobile_review_required"])
            self.assertTrue(portal["accessibility_review_required"])
            self.assertTrue(portal["confusion_testing_required"])
            self.assertFalse(portal["can_open_approval_payment_or_launch_gate"])

    def test_first_screen_options_use_plain_language_and_closed_gates(self) -> None:
        manifest = build_production_portal_workflow_engine(ROOT)
        labels = {row["label"] for row in manifest["first_screen_options"]}

        self.assertEqual(
            labels,
            {
                "Explore a market",
                "Prepare a buyer packet",
                "Check my documents",
                "Prepare for broker/expert review",
            },
        )
        for option in manifest["first_screen_options"]:
            self.assertTrue(option["route_exists"])
            self.assertEqual(option["copy_style"], "plain_business_owner_language")
            self.assertFalse(option["can_open_external_gate"])

    def test_ux_checks_and_gate_controls_remain_closed(self) -> None:
        manifest = build_production_portal_workflow_engine(ROOT)

        self.assertTrue(all(row["passed"] for row in manifest["ux_checks"]))
        for control in manifest["gate_controls"]:
            self.assertFalse(control["public_launch_ready"])
            self.assertFalse(control["unrestricted_uploads_enabled"])
            self.assertFalse(control["live_payment_enabled"])
            self.assertFalse(control["approval_claims_enabled"])
            self.assertFalse(control["external_effects_created"])
            self.assertFalse(control["claims_opened"])

    def test_writer_creates_manifest_routes_ux_gates_and_doc(self) -> None:
        manifest = build_production_portal_workflow_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_portal_workflow_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_routes = json.loads(paths["routes"].read_text(encoding="utf-8"))
            written_ux = json.loads(paths["ux_checks"].read_text(encoding="utf-8"))
            written_gates = json.loads(paths["gates"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_routes["status"], "production_portal_route_matrix_ready")
            self.assertEqual(written_ux["status"], "production_portal_ux_checks_ready_external_review_required")
            self.assertEqual(written_gates["status"], "production_portal_gate_controls_ready_closed")
            self.assertIn("Production Portal Workflow Engine", written_doc)
            self.assertIn("Explore a market", written_doc)


if __name__ == "__main__":
    unittest.main()
