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
    INPUT_HISTORY_STATUS,
    INPUT_LEDGER_STATUS,
    INPUT_RECORD_STATUS,
    STATUS,
    build_market_readiness_input_ledger,
    build_production_market_readiness_evidence_room,
    build_market_readiness_input_record,
    save_market_readiness_input_record,
    write_production_market_readiness_evidence_room_artifacts,
)


class ProductionMarketReadinessEvidenceRoomTests(unittest.TestCase):
    def _temp_root_with_input_templates(self, root: Path) -> None:
        graph = root / "system_review_graph"
        graph.mkdir(parents=True)
        (graph / "go_live_input_templates.json").write_text(
            (ROOT / "system_review_graph" / "go_live_input_templates.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

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
        self.assertEqual(manifest["input_ledger_status"], INPUT_LEDGER_STATUS)
        self.assertEqual(manifest["input_ledger"]["not_received_area_count"], 8)
        self.assertEqual(manifest["input_ledger_route"], "/api/market-readiness/input-ledger")
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
            self._temp_root_with_input_templates(root)
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
            self.assertTrue(result["history_relative_path"].startswith("external_inputs/history/real_users_private_beta_outcomes/"))
            self.assertTrue(result["path"].exists())
            self.assertTrue(result["history_path"].exists())
            written = json.loads(result["path"].read_text(encoding="utf-8"))
            history = json.loads(result["history_path"].read_text(encoding="utf-8"))
            self.assertEqual(written["review_area"], "real_users_private_beta_outcomes")
            self.assertEqual(history["status"], INPUT_HISTORY_STATUS)
            self.assertTrue(history["history_preserved"])
            self.assertFalse(history["claims_opened_by_history"])
            self.assertFalse(written["claims_opened_by_recording"])
            self.assertEqual(manifest["input_capture_route"], "/api/market-readiness/inputs")

    def test_input_record_writer_preserves_multiple_history_versions_for_same_area(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._temp_root_with_input_templates(root)
            first = save_market_readiness_input_record(
                {
                    "review_area": "buyer_supplier_validation",
                    "reviewer_name": "Commercial owner",
                    "reviewer_role": "Founder",
                    "scope_reviewed": "Buyer feedback v1",
                    "decision": "need_more_evidence",
                    "signed_at": "2026-06-28",
                },
                root,
            )
            second = save_market_readiness_input_record(
                {
                    "review_area": "buyer_supplier_validation",
                    "reviewer_name": "Commercial owner",
                    "reviewer_role": "Founder",
                    "scope_reviewed": "Buyer feedback v2",
                    "decision": "ready_for_my_area",
                    "signed_at": "2026-06-28",
                },
                root,
            )

            self.assertNotEqual(first["history_relative_path"], second["history_relative_path"])
            ledger = build_market_readiness_input_ledger(root)
            rows = {row["review_area"]: row for row in ledger["ledger_rows"]}
            self.assertEqual(ledger["history_record_count"], 2)
            self.assertEqual(ledger["input_history"]["status"], INPUT_HISTORY_STATUS)
            self.assertEqual(rows["buyer_supplier_validation"]["status"], "accepted_for_area")
            self.assertFalse(ledger["input_history"]["claims_opened_by_history"])

    def test_input_ledger_marks_empty_inputs_as_not_received(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._temp_root_with_input_templates(root)
            ledger = build_market_readiness_input_ledger(root)

            self.assertEqual(ledger["status"], INPUT_LEDGER_STATUS)
            self.assertEqual(ledger["review_area_count"], 8)
            self.assertEqual(ledger["input_record_count"], 0)
            self.assertEqual(ledger["history_record_count"], 0)
            self.assertEqual(ledger["accepted_area_count"], 0)
            self.assertEqual(ledger["not_received_area_count"], 8)
            self.assertFalse(ledger["public_launch_ready_by_ledger"])
            self.assertFalse(ledger["claims_opened_by_ledger"])
            self.assertTrue(all(row["status"] == "not_received" for row in ledger["ledger_rows"]))

    def test_input_ledger_separates_incomplete_needs_evidence_and_accepted_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._temp_root_with_input_templates(root)
            input_dir = root / "external_inputs"
            input_dir.mkdir()
            (input_dir / "qualified_customs_trade_review.json").write_text(
                json.dumps(
                    {
                        "review_area": "qualified_customs_trade_review",
                        "reviewer_name": "Example Broker",
                        "reviewer_role": "Licensed customs broker",
                        "scope_reviewed": "Canada import language only",
                        "decision": "need_more_evidence",
                        "signed_at": "2026-06-28",
                        "evidence_missing": ["HS classification scope"],
                    }
                ),
                encoding="utf-8",
            )
            (input_dir / "legal_privacy_security_approval.json").write_text(
                json.dumps(
                    {
                        "review_area": "legal_privacy_security_approval",
                        "reviewer_name": "Security reviewer",
                        "decision": "ready_for_my_area",
                    }
                ),
                encoding="utf-8",
            )
            (input_dir / "hosted_staging_production_proof.json").write_text(
                json.dumps(
                    {
                        "review_area": "hosted_staging_production_proof",
                        "reviewer_name": "Ops owner",
                        "reviewer_role": "Deployment owner",
                        "scope_reviewed": "Production URL and smoke proof",
                        "decision": "ready_for_my_area",
                        "signed_at": "2026-06-28",
                    }
                ),
                encoding="utf-8",
            )
            ledger = build_market_readiness_input_ledger(root)
            rows = {row["review_area"]: row for row in ledger["ledger_rows"]}

            self.assertEqual(ledger["input_record_count"], 3)
            self.assertEqual(ledger["accepted_area_count"], 1)
            self.assertEqual(ledger["needs_more_evidence_area_count"], 1)
            self.assertEqual(ledger["incomplete_area_count"], 1)
            self.assertEqual(rows["qualified_customs_trade_review"]["status"], "received_needs_more_evidence")
            self.assertEqual(rows["legal_privacy_security_approval"]["status"], "received_but_incomplete")
            self.assertIn("reviewer role or qualification", rows["legal_privacy_security_approval"]["missing_fields"])
            self.assertEqual(rows["hosted_staging_production_proof"]["status"], "accepted_for_area")
            self.assertFalse(ledger["public_launch_ready_by_ledger"])
            self.assertFalse(ledger["claims_opened_by_ledger"])

    def test_input_ledger_tracks_invalid_or_unknown_records_without_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._temp_root_with_input_templates(root)
            input_dir = root / "external_inputs"
            input_dir.mkdir()
            (input_dir / "broken.json").write_text("{not-json", encoding="utf-8")
            (input_dir / "unknown.json").write_text(
                json.dumps({"review_area": "unsupported_area", "decision": "ready_for_my_area"}),
                encoding="utf-8",
            )
            ledger = build_market_readiness_input_ledger(root)

            self.assertEqual(ledger["invalid_record_count"], 2)
            self.assertFalse(ledger["claims_opened_by_ledger"])
            self.assertTrue(all(row["claims_opened_by_ledger"] is False for row in ledger["invalid_records"]))

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
            written_input_ledger = json.loads(paths["input_ledger"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_work_orders["status"], "production_market_readiness_evidence_work_orders_ready")
            self.assertEqual(written_cards["status"], "production_market_readiness_reviewer_brief_cards_ready")
            self.assertEqual(written_matrix["status"], "production_market_readiness_gate_status_matrix_ready")
            self.assertEqual(written_input_ledger["status"], INPUT_LEDGER_STATUS)
            self.assertTrue(paths["input_history"].exists())
            written_input_history = json.loads(paths["input_history"].read_text(encoding="utf-8"))
            self.assertEqual(written_input_history["status"], INPUT_HISTORY_STATUS)
            self.assertIn("Production Market Readiness Evidence Room", written_doc)
            self.assertIn("Returned Input Ledger", written_doc)
            self.assertIn("Market-ready claim allowed: false", written_doc)


if __name__ == "__main__":
    unittest.main()
