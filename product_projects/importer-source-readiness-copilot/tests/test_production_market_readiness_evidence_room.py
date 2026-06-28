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

from importer_source_readiness.production_market_readiness_evidence_room import (
    INPUT_RECORD_STATUS,
    STATUS,
    build_production_market_readiness_evidence_room,
    build_market_readiness_input_record,
    save_market_readiness_input_record,
    write_production_market_readiness_evidence_room_artifacts,
)


class ProductionMarketReadinessEvidenceRoomTests(unittest.TestCase):
    def test_evidence_room_maps_all_real_world_go_live_inputs_without_opening_claims(self) -> None:
        manifest = build_production_market_readiness_evidence_room(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["gate_count"], 8)
        self.assertEqual(manifest["required_input_count"], 8)
        self.assertEqual(manifest["missing_input_count"], 8)
        self.assertEqual(manifest["ready_input_count"], 0)
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["hosted_private_beta_ready"])
        self.assertFalse(manifest["live_payment_ready"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened_by_room"])
        self.assertFalse(manifest["market_ready_claim_allowed"])
        self.assertIn("market_ready", manifest["blocked_claims"])
        self.assertIn("buyer_validated", manifest["blocked_claims"])

    def test_work_orders_have_templates_sources_drop_paths_and_next_moves(self) -> None:
        manifest = build_production_market_readiness_evidence_room(ROOT)
        work_orders = {row["gate_id"]: row for row in manifest["work_orders"]}

        for gate_id in {
            "real_external_expert_reviews",
            "legal_privacy_security_approval",
            "qualified_customs_trade_review",
            "hosted_staging_production_proof",
            "live_payment_activation",
            "real_users_private_beta_outcomes",
            "buyer_supplier_validation",
            "public_go_no_go_approval",
        }:
            self.assertIn(gate_id, work_orders)
            row = work_orders[gate_id]
            self.assertEqual(row["input_state"], "missing_real_input")
            self.assertEqual(row["drop_path"], f"external_inputs/{gate_id}.json")
            self.assertGreaterEqual(len(row["minimum_input"]), 4)
            self.assertGreaterEqual(len(row["required_evidence"]), 3)
            self.assertGreaterEqual(row["source_anchor_count"], 1)
            self.assertFalse(row["external_effects_created"])
            self.assertFalse(row["claims_opened_by_this_work_order"])
            self.assertIn("python3 scripts/run_external_validation_requirements.py", row["rerun_command"])

        self.assertTrue(work_orders["qualified_customs_trade_review"]["blocks_trade_claims"])
        self.assertTrue(work_orders["live_payment_activation"]["blocks_live_payment"])
        self.assertTrue(work_orders["hosted_staging_production_proof"]["blocks_private_beta"])

    def test_reviewer_brief_cards_are_plain_work_requests(self) -> None:
        manifest = build_production_market_readiness_evidence_room(ROOT)
        cards = {row["review_area"]: row for row in manifest["reviewer_brief_cards"]}

        self.assertEqual(len(cards), 8)
        customs = cards["qualified_customs_trade_review"]
        self.assertIn("where_to_save_response", customs)
        self.assertIn("external_validation_reviewer_brief.pdf", customs["what_to_send"])
        self.assertIn("This is ready to ship unless you object.", customs["what_not_to_say"])
        self.assertIn("customs_trade_approved", customs["claims_still_closed"])

    def test_input_record_builder_saves_returned_input_without_opening_claims(self) -> None:
        fields = {
            "review_area": "qualified_customs_trade_review",
            "reviewer_name": "Example Trade Reviewer",
            "reviewer_role": "Customs and trade language reviewer",
            "scope_reviewed": "Commit abc123, Canada import language only",
            "decision": "need_more_evidence",
            "signed_at": "2026-06-28",
            "top_issues": "HS language needs qualification\nCFIA wording must stay blocked",
            "evidence_missing": "broker scope\nsource snapshot",
            "evidence_links_or_files": "review-notes.pdf",
            "claims_the_product_must_not_make": "customs approved",
            "what_would_make_this_ready": "Attach scoped broker language review.",
        }
        record = build_market_readiness_input_record(fields, ROOT, "2026-06-28T00:00:00Z")

        self.assertEqual(record["status"], INPUT_RECORD_STATUS)
        self.assertEqual(record["review_area"], "qualified_customs_trade_review")
        self.assertEqual(record["decision"], "need_more_evidence")
        self.assertTrue(record["minimum_input_present"])
        self.assertFalse(record["ready_decision_candidate"])
        self.assertFalse(record["external_effects_created"])
        self.assertFalse(record["claims_opened_by_recording"])
        self.assertEqual(len(record["top_issues"]), 2)

    def test_input_record_writer_uses_external_inputs_folder_in_temp_root(self) -> None:
        manifest = build_production_market_readiness_evidence_room(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph = root / "system_review_graph"
            graph.mkdir(parents=True)
            (graph / "go_live_input_templates.json").write_text(
                (ROOT / "system_review_graph" / "go_live_input_templates.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            result = save_market_readiness_input_record(
                {
                    "review_area": "real_users_private_beta_outcomes",
                    "reviewer_name": "Example UX Owner",
                    "reviewer_role": "User research owner",
                    "scope_reviewed": "Private beta smoke results",
                    "decision": "need_more_evidence",
                    "signed_at": "2026-06-28",
                },
                root,
            )

            self.assertEqual(result["status"], INPUT_RECORD_STATUS)
            self.assertEqual(result["relative_path"], "external_inputs/real_users_private_beta_outcomes.json")
            self.assertTrue(result["path"].exists())
            written = json.loads(result["path"].read_text(encoding="utf-8"))
            self.assertEqual(written["review_area"], "real_users_private_beta_outcomes")
            self.assertFalse(written["claims_opened_by_recording"])
            self.assertEqual(manifest["input_capture_route"], "/api/market-readiness/inputs")

    def test_writer_creates_evidence_room_artifacts(self) -> None:
        manifest = build_production_market_readiness_evidence_room(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_market_readiness_evidence_room_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_work_orders = json.loads(paths["work_orders"].read_text(encoding="utf-8"))
            written_cards = json.loads(paths["reviewer_cards"].read_text(encoding="utf-8"))
            written_matrix = json.loads(paths["matrix"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_work_orders["status"], "production_market_readiness_evidence_work_orders_ready")
            self.assertEqual(written_cards["status"], "production_market_readiness_reviewer_brief_cards_ready")
            self.assertEqual(written_matrix["status"], "production_market_readiness_gate_status_matrix_ready")
            self.assertIn("Production Market Readiness Evidence Room", written_doc)
            self.assertIn("Market-ready claim allowed: false", written_doc)


if __name__ == "__main__":
    unittest.main()
