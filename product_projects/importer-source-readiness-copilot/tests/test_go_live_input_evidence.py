from __future__ import annotations

import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from importer_source_readiness.go_live_input_evidence import (
    EVIDENCE_RULES,
    REVIEW_AREA_ORDER,
    STATUS,
    build_go_live_returned_input_evidence_manifest,
    required_categories_for_decision,
    validate_go_live_input_record,
)


ROLE_BY_AREA = {
    "real_external_expert_reviews": "Independent security and trade expert reviewer",
    "legal_privacy_security_approval": "Privacy legal security compliance reviewer",
    "qualified_customs_trade_review": "Licensed customs broker and trade compliance reviewer",
    "hosted_staging_production_proof": "DevOps SRE deployment owner",
    "live_payment_activation": "Stripe payment billing owner",
    "real_users_private_beta_outcomes": "UX user research owner",
    "buyer_supplier_validation": "Founder commercial buyer supplier validation owner",
    "public_go_no_go_approval": "Founder accountable launch owner",
}


class GoLiveInputEvidenceTests(unittest.TestCase):
    def _complete_record(self, review_area: str, decision: str = "ready_for_my_area") -> dict[str, object]:
        categories = required_categories_for_decision(review_area, decision)
        return {
            "review_area": review_area,
            "reviewer_name": f"Reviewer for {review_area}",
            "reviewer_role": ROLE_BY_AREA[review_area],
            "qualification_basis": ROLE_BY_AREA[review_area],
            "scope_reviewed": "Public launch candidate, commit ff00abc, exact review scope only",
            "decision": decision,
            "signed_at": "2026-06-29",
            "top_issues": [],
            "evidence_missing": [],
            "claims_the_product_must_not_make": ["unscoped approval"],
            "evidence_artifacts": {
                category: f"https://evidence.example/{review_area}/{category}.pdf"
                for category in categories
            },
        }

    def test_ready_record_without_required_evidence_stays_blocked(self) -> None:
        record = {
            "review_area": "qualified_customs_trade_review",
            "reviewer_name": "Example Broker",
            "reviewer_role": "Licensed customs broker",
            "scope_reviewed": "Canada import language only",
            "decision": "ready_for_my_area",
            "signed_at": "2026-06-29",
        }

        validation = validate_go_live_input_record(record, repo_root=ROOT, generated_at="2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "received_without_required_evidence")
        self.assertFalse(validation["accepted_for_area"])
        self.assertIn("official_source_snapshot", validation["missing_evidence_categories"])
        self.assertFalse(validation["claims_opened_by_validation"])

    def test_complete_records_validate_all_areas_without_opening_claims(self) -> None:
        records = []
        for area in REVIEW_AREA_ORDER:
            decision = "go_for_public_launch" if area == "public_go_no_go_approval" else "ready_for_my_area"
            records.append(self._complete_record(area, decision))

        manifest = build_go_live_returned_input_evidence_manifest(
            records,
            generated_at="2026-06-29T00:00:00Z",
            repo_root=ROOT,
        )

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["review_area_count"], 8)
        self.assertEqual(manifest["accepted_area_count"], 8)
        self.assertTrue(manifest["public_launch_ready_by_evidence"])
        self.assertFalse(manifest["claims_opened_by_evidence_validation"])
        self.assertTrue(all(row["accepted_for_area"] for row in manifest["validation_rows"]))

    def test_not_applicable_payment_can_satisfy_scope_without_live_payment_claim(self) -> None:
        payment = self._complete_record("live_payment_activation", "not_applicable_for_this_launch")
        validation = validate_go_live_input_record(payment, repo_root=ROOT, generated_at="2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "accepted_for_area_with_attached_evidence")
        self.assertEqual(
            set(validation["required_evidence_categories"]),
            set(EVIDENCE_RULES["live_payment_activation"]["not_applicable_evidence_categories"]),
        )

        records = [payment]
        manifest = build_go_live_returned_input_evidence_manifest(
            records,
            generated_at="2026-06-29T00:00:00Z",
            repo_root=ROOT,
        )
        self.assertEqual(manifest["accepted_area_count"], 1)
        self.assertFalse(manifest["live_payment_ready_by_evidence"])
        self.assertFalse(manifest["public_launch_ready_by_evidence"])


if __name__ == "__main__":
    unittest.main()
