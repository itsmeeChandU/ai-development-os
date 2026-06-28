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

from importer_source_readiness.production_packet_engine import (
    PACKET_STATES,
    PACKET_VIEW_TYPES,
    STATUS,
    build_production_packet_engine,
    write_production_packet_engine_artifacts,
)


class ProductionPacketEngineTests(unittest.TestCase):
    def test_packet_engine_evaluates_real_fixture_with_closed_gates(self) -> None:
        manifest = build_production_packet_engine(ROOT)
        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["state_count"], 12)
        self.assertEqual(manifest["states"], list(PACKET_STATES))
        self.assertEqual(manifest["packet_count"], 1)
        self.assertEqual(manifest["packet_view_type_count"], 8)
        self.assertEqual(manifest["packet_view_count"], 8)
        self.assertGreaterEqual(manifest["claim_gate_count"], 12)
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["hosted_private_beta_ready"])
        self.assertFalse(manifest["live_payment_ready"])

        run = manifest["packet_runs"][0]
        self.assertEqual(run["packet_id"], "packet-frozen-tuna-canada-001")
        self.assertEqual(run["state"], "reviewer_ready")
        self.assertTrue(run["reviewer_ready_not_approved"])
        self.assertEqual(run["trade_direction"], "import")
        self.assertEqual(run["product_class"], "seafood")
        self.assertGreaterEqual(run["source_route_count"], 8)
        self.assertGreaterEqual(run["evidence_summary"]["stale_evidence_count"], 1)
        self.assertFalse(run["claims_opened"])
        self.assertFalse(run["external_effects_created"])

    def test_packet_engine_outputs_all_views_scores_events_and_blocked_claims(self) -> None:
        manifest = build_production_packet_engine(ROOT)
        run = manifest["packet_runs"][0]
        view_types = {row["view_type"] for row in run["packet_views"]}
        score_ids = {row["score"] for row in run["scores"]}
        blocked_claims = {row["claim"] for row in run["blocked_claims"]}
        event_states = {row["state"] for row in run["state_events"]}

        self.assertEqual(view_types, set(PACKET_VIEW_TYPES))
        self.assertEqual(score_ids, set(manifest["score_ids"]))
        self.assertEqual(event_states, set(PACKET_STATES))
        self.assertIn("buyer_supplier_evidence_score", score_ids)
        self.assertIn("tariff_confirmed", blocked_claims)
        self.assertIn("cfia_compliant", blocked_claims)
        self.assertIn("buyer_validated", blocked_claims)
        self.assertIn("supplier_recommended", blocked_claims)
        self.assertIn("ready_to_ship", blocked_claims)
        self.assertTrue(all(row["status"] == "blocked" for row in run["blocked_claims"]))
        self.assertTrue(all(row["blocked_claims_visible"] for row in run["packet_views"]))
        self.assertTrue(all(row["claims_opened"] is False for row in run["packet_views"]))
        self.assertTrue(all(row["external_effects_created"] is False for row in run["state_events"]))

    def test_writer_creates_manifest_events_doc_and_view_exports(self) -> None:
        manifest = build_production_packet_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_packet_engine_artifacts(manifest, root)

            self.assertTrue(paths["manifest"].exists())
            self.assertTrue(paths["events"].exists())
            self.assertTrue(paths["views_root"].exists())
            self.assertTrue(paths["doc"].exists())
            self.assertEqual(len(paths["view_paths"]), 8)

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_events = json.loads(paths["events"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_events["status"], "production_packet_events_ready_no_external_effects")
            self.assertEqual(written_events["event_count"], 12)
            self.assertIn("Production Packet Engine", written_doc)
            self.assertIn("Reviewer-ready is approved: false", written_doc)


if __name__ == "__main__":
    unittest.main()
