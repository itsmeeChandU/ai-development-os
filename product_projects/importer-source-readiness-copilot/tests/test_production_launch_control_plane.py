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

from importer_source_readiness.production_launch_control_plane import (
    STATUS,
    build_production_launch_control_plane,
    write_production_launch_control_plane_artifacts,
)


class ProductionLaunchControlPlaneTests(unittest.TestCase):
    def test_launch_control_plane_keeps_public_launch_blocked(self) -> None:
        manifest = build_production_launch_control_plane(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["launch_gate_count"], 13)
        self.assertGreaterEqual(manifest["blocked_launch_gate_count"], 8)
        self.assertFalse(manifest["public_launch_approved"])
        self.assertFalse(manifest["activation_allowed"])
        self.assertFalse(manifest["exact_public_scope_approved"])
        self.assertFalse(manifest["external_claims_opened"])
        self.assertFalse(manifest["hosted_private_beta_ready"])
        self.assertFalse(manifest["payment_activation_ready"])
        self.assertFalse(manifest["security_real_file_uploads_allowed"])
        self.assertFalse(manifest["payment_live_checkout_enabled"])

    def test_exact_scope_matrix_is_candidate_only(self) -> None:
        manifest = build_production_launch_control_plane(ROOT)

        self.assertEqual(manifest["public_scope_candidate_count"], 6)
        self.assertEqual(manifest["blocked_public_scope_count"], 8)
        candidate_ids = {row["scope_id"] for row in manifest["public_scope_candidates"]}
        blocked_ids = {row["scope_id"] for row in manifest["blocked_public_scope"]}
        self.assertIn("no_document_starter_packet", candidate_ids)
        self.assertIn("source_routing", candidate_ids)
        self.assertIn("live_payments", blocked_ids)
        self.assertIn("unrestricted_real_uploads", blocked_ids)
        for row in manifest["public_scope_candidates"]:
            self.assertFalse(row["activation_allowed"])
        for row in manifest["blocked_public_scope"]:
            self.assertFalse(row["activation_allowed"])

    def test_launch_gates_point_to_real_artifacts_without_opening_public_scope(self) -> None:
        manifest = build_production_launch_control_plane(ROOT)
        gates = {row["gate_id"]: row for row in manifest["launch_gates"]}

        self.assertTrue(gates["business_logic_gate"]["local_evidence_present"])
        self.assertTrue(gates["security_gate"]["local_evidence_present"])
        self.assertEqual(gates["security_gate"]["state"], "blocked")
        self.assertEqual(gates["payment_gate"]["state"], "blocked")
        self.assertEqual(gates["final_owner_gate"]["state"], "blocked")
        self.assertEqual(gates["business_logic_gate"]["approved_scope"], "local_review_only")
        for gate in manifest["launch_gates"]:
            self.assertFalse(gate["public_launch_contribution"])

    def test_writer_creates_launch_control_artifacts(self) -> None:
        manifest = build_production_launch_control_plane(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_launch_control_plane_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            gates = json.loads(paths["gates"].read_text(encoding="utf-8"))
            scope = json.loads(paths["scope"].read_text(encoding="utf-8"))
            decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
            doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(gates["status"], "production_launch_gate_states_ready_public_launch_blocked")
            self.assertEqual(scope["status"], "production_launch_scope_matrix_ready_activation_blocked")
            self.assertFalse(decision["public_launch_approved"])
            self.assertIn("Production Launch Control Plane", doc)


if __name__ == "__main__":
    unittest.main()
