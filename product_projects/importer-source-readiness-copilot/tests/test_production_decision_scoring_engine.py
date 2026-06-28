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

from importer_source_readiness.production_decision_scoring_engine import (
    SCORE_IDS,
    STATUS,
    build_production_decision_scoring_engine,
    write_production_decision_scoring_engine_artifacts,
)


PACKET_ID = "packet-frozen-tuna-canada-001"


class ProductionDecisionScoringEngineTests(unittest.TestCase):
    def test_scoring_manifest_outputs_six_separate_scores_and_closed_gates(self) -> None:
        manifest = build_production_decision_scoring_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["score_count"], 6)
        self.assertEqual(manifest["score_ids"], list(SCORE_IDS))
        self.assertGreaterEqual(manifest["packet_count"], 1)
        self.assertEqual(manifest["decision_score_record_count"], manifest["packet_count"] * 6)
        self.assertFalse(manifest["single_global_readiness_score_created"])
        self.assertFalse(manifest["combined_readiness_label_created"])
        self.assertFalse(manifest["approval_language_allowed"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["live_payment_ready"])

    def test_current_packet_scores_have_reasons_caps_blockers_and_next_actions(self) -> None:
        manifest = build_production_decision_scoring_engine(ROOT)
        records = {
            row["score"]: row
            for row in manifest["decision_score_records"]
            if row["packet_id"] == PACKET_ID
        }

        self.assertEqual(set(records), set(SCORE_IDS))
        for score_id, record in records.items():
            self.assertIn("reason", record)
            self.assertIn("cap_reason", record)
            self.assertIn("next_action", record)
            self.assertIsInstance(record["blocking_fields"], list)
            self.assertFalse(record["single_global_readiness_score_used"], score_id)
            self.assertTrue(record["approval_language_blocked"], score_id)
            self.assertFalse(record["claims_opened"], score_id)
            self.assertLessEqual(record["score_value"], record["score_cap"])

    def test_claim_gate_inputs_cap_external_decision_scores(self) -> None:
        manifest = build_production_decision_scoring_engine(ROOT)
        records = {
            row["score"]: row
            for row in manifest["decision_score_records"]
            if row["packet_id"] == PACKET_ID
        }

        self.assertEqual(records["source_freshness_score"]["label"], "red")
        self.assertEqual(records["source_freshness_score"]["score_cap"], 39)
        self.assertIn("tariff_confirmed", records["source_freshness_score"]["blocked_claim_dependencies"])
        self.assertIn("source:cbsa-customs-tariff-2026", records["source_freshness_score"]["supporting_evidence_refs"])

        self.assertEqual(records["responsibility_clarity_score"]["label"], "red")
        self.assertIn("incoterms_responsibility_path", records["responsibility_clarity_score"]["blocked_claim_dependencies"])

        self.assertEqual(records["decision_safety_score"]["label"], "red")
        for claim_type in ("tariff_confirmed", "cfia_approved", "buyer_validated", "supplier_verified", "customs_ready", "shipment_approved"):
            self.assertIn(claim_type, records["decision_safety_score"]["blocked_claim_dependencies"])

    def test_packet_summary_refuses_single_readiness_score(self) -> None:
        manifest = build_production_decision_scoring_engine(ROOT)
        summary = next(row for row in manifest["packet_score_summaries"] if row["packet_id"] == PACKET_ID)

        self.assertEqual(summary["score_count"], 6)
        self.assertEqual(summary["lowest_label"], "red")
        self.assertFalse(summary["single_global_readiness_score_created"])
        self.assertIn("do not collapse", summary["customer_facing_summary"])
        self.assertIn("hs_candidate_research_route", summary["safe_claims_showable"])

    def test_writer_creates_manifest_records_policy_and_doc(self) -> None:
        manifest = build_production_decision_scoring_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_decision_scoring_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_records = json.loads(paths["records"].read_text(encoding="utf-8"))
            written_policy = json.loads(paths["policy"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_records["status"], "production_decision_score_records_ready")
            self.assertEqual(written_policy["status"], "production_score_cap_policy_ready")
            self.assertIn("Production Decision Scoring Engine", written_doc)
            self.assertIn("Single global readiness score created: false", written_doc)


if __name__ == "__main__":
    unittest.main()
