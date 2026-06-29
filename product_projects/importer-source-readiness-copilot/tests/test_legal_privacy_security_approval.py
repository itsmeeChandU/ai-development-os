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

from importer_source_readiness.legal_privacy_security_approval import (
    REQUIRED_PROOF_CATEGORIES,
    build_legal_privacy_security_approval_contract,
    build_legal_privacy_security_approval_intake,
    validate_legal_privacy_security_approval_record,
    write_legal_privacy_security_approval_artifacts,
)


def _complete_evidence() -> dict[str, str]:
    return {item["category"]: f"evidence/{item['category']}.pdf" for item in REQUIRED_PROOF_CATEGORIES}


class LegalPrivacySecurityApprovalTests(unittest.TestCase):
    def test_contract_has_sources_categories_and_claims_closed(self) -> None:
        contract = build_legal_privacy_security_approval_contract("2026-06-29T00:00:00Z")

        self.assertEqual(contract["status"], "legal_privacy_security_approval_contract_ready_claims_closed")
        self.assertEqual(contract["required_evidence_category_count"], 14)
        self.assertGreaterEqual(contract["source_anchor_count"], 9)
        self.assertIn("external_inputs/legal_privacy_security_approval.json", contract["drop_paths"])
        self.assertFalse(contract["claims_opened"])
        self.assertFalse(contract["external_effects_created"])

        source_ids = {row["source_id"] for row in contract["source_anchors"]}
        self.assertIn("opc-pipeda-principles", source_ids)
        self.assertIn("owasp-asvs", source_ids)
        self.assertIn("nist-csf-2", source_ids)

    def test_complete_private_beta_record_is_accepted_without_opening_effects(self) -> None:
        record = {
            "approval_scope_id": "private-beta-ca-real-docs-v1",
            "review_scope_type": "private_beta_real_data",
            "jurisdiction": "Canada",
            "reviewer_name": "Example Privacy Security Reviewer",
            "reviewer_roles": ["privacy_legal_reviewer", "application_security_reviewer"],
            "reviewer_qualification": "Qualified privacy and application security reviewer for scoped private beta.",
            "reviewed_at": "2026-06-29",
            "build_or_commit_ref": "abc123",
            "decision": "approve_for_private_beta_scope",
            "evidence_artifacts": _complete_evidence(),
        }

        result = validate_legal_privacy_security_approval_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(result["status"], "accepted_private_beta_legal_privacy_security_scope_evidence")
        self.assertTrue(result["accepted_for_legal_privacy_security_evidence"])
        self.assertTrue(result["legal_privacy_security_approved_by_evidence"])
        self.assertFalse(result["real_file_uploads_allowed_by_intake"])
        self.assertFalse(result["hosted_private_beta_ready_by_approval_evidence"])
        self.assertFalse(result["public_launch_ready_by_approval_evidence"])
        self.assertFalse(result["claims_opened_by_validation"])
        self.assertFalse(result["external_effects_created"])

    def test_missing_required_roles_blocks_private_beta_approval(self) -> None:
        record = {
            "approval_scope_id": "private-beta-ca-real-docs-v1",
            "review_scope_type": "private_beta_real_data",
            "jurisdiction": "Canada",
            "reviewer_name": "Example Privacy Reviewer",
            "reviewer_roles": ["privacy_legal_reviewer"],
            "reviewer_qualification": "Privacy reviewer only.",
            "reviewed_at": "2026-06-29",
            "build_or_commit_ref": "abc123",
            "decision": "approve_for_private_beta_scope",
            "evidence_artifacts": _complete_evidence(),
        }

        result = validate_legal_privacy_security_approval_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(result["status"], "received_missing_required_reviewer_roles")
        self.assertIn("application_security_reviewer", result["missing_reviewer_roles"])
        self.assertFalse(result["legal_privacy_security_approved_by_evidence"])

    def test_demo_no_real_data_scope_is_accepted_but_does_not_approve_real_data(self) -> None:
        record = {
            "approval_scope_id": "demo-no-real-data-v1",
            "review_scope_type": "demo_no_real_data",
            "jurisdiction": "Canada",
            "reviewer_name": "Example Reviewer",
            "reviewer_roles": ["qualified_privacy_security_reviewer"],
            "reviewer_qualification": "Scoped demo/no-real-data reviewer.",
            "reviewed_at": "2026-06-29",
            "build_or_commit_ref": "abc123",
            "decision": "approve_demo_no_real_data_only",
            "evidence_artifacts": {
                "review_scope_excludes_real_user_data": "evidence/scope.md",
                "reviewer_scope_acknowledgement": "evidence/reviewer.md",
                "no_real_uploads_or_ai_processing": "evidence/no-real-data.md",
                "future_approval_condition": "evidence/future-approval.md",
            },
        }

        result = validate_legal_privacy_security_approval_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(result["status"], "accepted_demo_no_real_data_approval_scope_evidence")
        self.assertTrue(result["accepted_for_legal_privacy_security_evidence"])
        self.assertFalse(result["legal_privacy_security_approved_by_evidence"])
        self.assertFalse(result["real_file_uploads_allowed_by_intake"])

    def test_current_repo_has_zero_records_and_all_gates_blocked(self) -> None:
        manifest = build_legal_privacy_security_approval_intake(ROOT, "2026-06-29T00:00:00Z")

        self.assertEqual(
            manifest["status"],
            "legal_privacy_security_approval_intake_ready_real_approval_evidence_required_claims_closed",
        )
        self.assertEqual(manifest["approval_record_count"], 0)
        self.assertEqual(manifest["accepted_approval_record_count"], 0)
        self.assertEqual(manifest["required_evidence_category_count"], 14)
        self.assertEqual(manifest["missing_evidence_category_count"], 14)
        self.assertEqual(manifest["blocked_gate_count"], 14)
        self.assertEqual(manifest["blocker_export_count"], 14)
        self.assertFalse(manifest["legal_privacy_security_approved_by_evidence"])
        self.assertFalse(manifest["real_file_uploads_allowed_by_intake"])
        self.assertFalse(manifest["claims_opened_by_intake"])

    def test_writer_creates_all_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_legal_privacy_security_approval_artifacts(root, "2026-06-29T00:00:00Z")

            self.assertEqual(result["approval_record_count"], 0)
            for relative in (
                "system_review_graph/legal_privacy_security_approval_contract.json",
                "system_review_graph/legal_privacy_security_approval_manifest.json",
                "system_review_graph/legal_privacy_security_approval_gate_matrix.json",
                "system_review_graph/legal_privacy_security_approval_blocker_export.jsonl",
                "docs/LEGAL_PRIVACY_SECURITY_APPROVAL_PROOF.md",
            ):
                self.assertTrue((root / relative).exists(), relative)

            manifest = json.loads(
                (root / "system_review_graph" / "legal_privacy_security_approval_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            doc = (root / "docs" / "LEGAL_PRIVACY_SECURITY_APPROVAL_PROOF.md").read_text(encoding="utf-8")
            self.assertEqual(manifest["blocked_gate_count"], 14)
            self.assertIn("Real file uploads allowed by intake: false", doc)

    def test_external_input_record_counts_in_temp_root_without_opening_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "external_inputs"
            input_dir.mkdir()
            (input_dir / "legal_privacy_security_approval.json").write_text(
                json.dumps(
                    {
                        "approval_scope_id": "private-beta-ca-real-docs-v1",
                        "review_scope_type": "private_beta_real_data",
                        "jurisdiction": "Canada",
                        "reviewer_name": "Example Privacy Security Reviewer",
                        "reviewer_roles": ["qualified_privacy_security_reviewer"],
                        "reviewer_qualification": "Qualified privacy/security reviewer.",
                        "reviewed_at": "2026-06-29",
                        "build_or_commit_ref": "abc123",
                        "decision": "approve_for_private_beta_scope",
                        "evidence_artifacts": _complete_evidence(),
                    }
                ),
                encoding="utf-8",
            )

            manifest = build_legal_privacy_security_approval_intake(root, "2026-06-29T00:00:00Z")

            self.assertEqual(manifest["approval_record_count"], 1)
            self.assertEqual(manifest["accepted_approval_record_count"], 1)
            self.assertEqual(manifest["blocked_gate_count"], 0)
            self.assertTrue(manifest["legal_privacy_security_approved_by_evidence"])
            self.assertFalse(manifest["real_file_uploads_allowed_by_intake"])
            self.assertFalse(manifest["hosted_private_beta_ready_by_approval_evidence"])
            self.assertFalse(manifest["public_launch_ready_by_approval_evidence"])
            self.assertFalse(manifest["claims_opened_by_intake"])


if __name__ == "__main__":
    unittest.main()
