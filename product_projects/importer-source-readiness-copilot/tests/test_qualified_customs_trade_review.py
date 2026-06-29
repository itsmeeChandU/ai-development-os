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

from importer_source_readiness.qualified_customs_trade_review import (
    REQUIRED_PROOF_CATEGORIES,
    build_qualified_customs_trade_review_contract,
    build_qualified_customs_trade_review_intake,
    validate_qualified_customs_trade_review_record,
    write_qualified_customs_trade_review_artifacts,
)


def _complete_evidence() -> dict[str, str]:
    return {item["category"]: f"evidence/{item['category']}.pdf" for item in REQUIRED_PROOF_CATEGORIES}


class QualifiedCustomsTradeReviewTests(unittest.TestCase):
    def test_contract_has_sources_categories_and_claims_closed(self) -> None:
        contract = build_qualified_customs_trade_review_contract("2026-06-29T00:00:00Z")

        self.assertEqual(contract["status"], "qualified_customs_trade_review_contract_ready_claims_closed")
        self.assertEqual(contract["required_evidence_category_count"], 14)
        self.assertGreaterEqual(contract["source_anchor_count"], 9)
        self.assertIn("external_inputs/qualified_customs_trade_review.json", contract["drop_paths"])
        self.assertFalse(contract["claims_opened"])
        self.assertFalse(contract["external_effects_created"])

        source_ids = {row["source_id"] for row in contract["source_anchors"]}
        self.assertIn("cbsa-import-commercial-goods", source_ids)
        self.assertIn("cbsa-licensed-customs-brokers", source_ids)
        self.assertIn("cfia-airs", source_ids)
        self.assertIn("wco-harmonized-system", source_ids)

    def test_complete_canada_food_record_is_accepted_without_approval_claims(self) -> None:
        record = {
            "review_scope_id": "frozen-tuna-canada-review-v1",
            "review_scope_type": "canada_import_food_or_regulated_goods_preparation",
            "origin_country": "Vietnam",
            "destination_country": "Canada",
            "product_or_hs_description": "Frozen tuna fillets, HS candidate 0304.87, CFIA food route suspected.",
            "reviewer_name": "Example Licensed Customs Broker",
            "reviewer_roles": ["licensed_customs_broker", "cfia_food_import_reviewer"],
            "reviewer_qualification": "Licensed customs broker with food import review scope.",
            "reviewed_at": "2026-06-29",
            "build_or_commit_ref": "abc123",
            "decision": "approve_preparation_language_for_scope",
            "evidence_artifacts": _complete_evidence(),
        }

        result = validate_qualified_customs_trade_review_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(result["status"], "accepted_qualified_customs_trade_preparation_scope_evidence")
        self.assertTrue(result["accepted_for_customs_trade_review_evidence"])
        self.assertTrue(result["customs_trade_reviewed_by_evidence"])
        self.assertFalse(result["tariff_confirmed_by_review_evidence"])
        self.assertFalse(result["cfia_approved_by_review_evidence"])
        self.assertFalse(result["customs_ready_by_review_evidence"])
        self.assertFalse(result["shipment_ready_by_review_evidence"])
        self.assertFalse(result["public_launch_ready_by_review_evidence"])
        self.assertFalse(result["claims_opened_by_validation"])
        self.assertFalse(result["external_effects_created"])

    def test_regulated_goods_scope_requires_regulated_goods_reviewer(self) -> None:
        record = {
            "review_scope_id": "frozen-tuna-canada-review-v1",
            "review_scope_type": "canada_import_food_or_regulated_goods_preparation",
            "origin_country": "Vietnam",
            "destination_country": "Canada",
            "product_or_hs_description": "Frozen tuna fillets",
            "reviewer_name": "Example Customs Reviewer",
            "reviewer_roles": ["customs_trade_reviewer"],
            "reviewer_qualification": "Customs reviewer only.",
            "reviewed_at": "2026-06-29",
            "build_or_commit_ref": "abc123",
            "decision": "approve_preparation_language_for_scope",
            "evidence_artifacts": _complete_evidence(),
        }

        result = validate_qualified_customs_trade_review_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(result["status"], "received_missing_required_customs_trade_reviewer_roles")
        self.assertIn("regulated_goods_reviewer", result["missing_reviewer_roles"])
        self.assertFalse(result["customs_trade_reviewed_by_evidence"])

    def test_demo_reference_scope_is_accepted_but_not_trade_reviewed(self) -> None:
        record = {
            "review_scope_id": "demo-no-trade-claims-v1",
            "review_scope_type": "demo_reference_only",
            "origin_country": "India",
            "destination_country": "Canada",
            "product_or_hs_description": "Generic demo product",
            "reviewer_name": "Example Reviewer",
            "reviewer_roles": ["customs_trade_reviewer"],
            "reviewer_qualification": "Scoped reviewer for no-trade-claims demo.",
            "reviewed_at": "2026-06-29",
            "build_or_commit_ref": "abc123",
            "decision": "approve_demo_reference_only",
            "evidence_artifacts": {
                "launch_scope_excludes_trade_claims": "evidence/scope.md",
                "owner_decision": "evidence/owner.md",
                "future_review_trigger": "evidence/future.md",
            },
        }

        result = validate_qualified_customs_trade_review_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(result["status"], "accepted_customs_trade_demo_or_no_claim_scope_evidence")
        self.assertTrue(result["accepted_for_customs_trade_review_evidence"])
        self.assertFalse(result["customs_trade_reviewed_by_evidence"])
        self.assertFalse(result["tariff_confirmed_by_review_evidence"])

    def test_current_repo_has_zero_records_and_all_gates_blocked(self) -> None:
        manifest = build_qualified_customs_trade_review_intake(ROOT, "2026-06-29T00:00:00Z")

        self.assertEqual(
            manifest["status"],
            "qualified_customs_trade_review_intake_ready_real_review_evidence_required_claims_closed",
        )
        self.assertEqual(manifest["review_record_count"], 0)
        self.assertEqual(manifest["accepted_review_record_count"], 0)
        self.assertEqual(manifest["required_evidence_category_count"], 14)
        self.assertEqual(manifest["missing_evidence_category_count"], 14)
        self.assertEqual(manifest["blocked_gate_count"], 14)
        self.assertEqual(manifest["blocker_export_count"], 14)
        self.assertFalse(manifest["customs_trade_reviewed_by_evidence"])
        self.assertFalse(manifest["tariff_confirmed_by_review_evidence"])
        self.assertFalse(manifest["cfia_approved_by_review_evidence"])
        self.assertFalse(manifest["claims_opened_by_intake"])

    def test_writer_creates_all_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_qualified_customs_trade_review_artifacts(root, "2026-06-29T00:00:00Z")

            self.assertEqual(result["review_record_count"], 0)
            for relative in (
                "system_review_graph/qualified_customs_trade_review_contract.json",
                "system_review_graph/qualified_customs_trade_review_manifest.json",
                "system_review_graph/qualified_customs_trade_review_gate_matrix.json",
                "system_review_graph/qualified_customs_trade_review_blocker_export.jsonl",
                "docs/QUALIFIED_CUSTOMS_TRADE_REVIEW_PROOF.md",
            ):
                self.assertTrue((root / relative).exists(), relative)

            manifest = json.loads(
                (root / "system_review_graph" / "qualified_customs_trade_review_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            doc = (root / "docs" / "QUALIFIED_CUSTOMS_TRADE_REVIEW_PROOF.md").read_text(encoding="utf-8")
            self.assertEqual(manifest["blocked_gate_count"], 14)
            self.assertIn("Tariff confirmed by review evidence: false", doc)

    def test_external_input_record_counts_without_opening_tariff_or_cfia_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "external_inputs"
            input_dir.mkdir()
            (input_dir / "qualified_customs_trade_review.json").write_text(
                json.dumps(
                    {
                        "review_scope_id": "frozen-tuna-canada-review-v1",
                        "review_scope_type": "canada_import_food_or_regulated_goods_preparation",
                        "origin_country": "Vietnam",
                        "destination_country": "Canada",
                        "product_or_hs_description": "Frozen tuna fillets, HS candidate 0304.87",
                        "reviewer_name": "Example Licensed Customs Broker",
                        "reviewer_roles": ["customs_broker_or_trade_compliance_specialist", "food_import_compliance_reviewer"],
                        "reviewer_qualification": "Qualified customs and regulated food import reviewer.",
                        "reviewed_at": "2026-06-29",
                        "build_or_commit_ref": "abc123",
                        "decision": "approve_preparation_language_for_scope",
                        "evidence_artifacts": _complete_evidence(),
                    }
                ),
                encoding="utf-8",
            )

            manifest = build_qualified_customs_trade_review_intake(root, "2026-06-29T00:00:00Z")

            self.assertEqual(manifest["review_record_count"], 1)
            self.assertEqual(manifest["accepted_review_record_count"], 1)
            self.assertEqual(manifest["blocked_gate_count"], 0)
            self.assertTrue(manifest["customs_trade_reviewed_by_evidence"])
            self.assertFalse(manifest["tariff_confirmed_by_review_evidence"])
            self.assertFalse(manifest["cfia_approved_by_review_evidence"])
            self.assertFalse(manifest["customs_ready_by_review_evidence"])
            self.assertFalse(manifest["shipment_ready_by_review_evidence"])
            self.assertFalse(manifest["claims_opened_by_intake"])


if __name__ == "__main__":
    unittest.main()
