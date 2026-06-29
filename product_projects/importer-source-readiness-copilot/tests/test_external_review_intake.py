from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from importer_source_readiness.external_review_intake import (
    STATUS,
    build_returned_external_review_contract,
    build_returned_external_review_intake,
    validate_returned_external_review_record,
    write_returned_external_review_intake_artifacts,
)


def _evidence_artifacts(role_id: str) -> dict[str, str]:
    return {
        "reviewer_identity": f"https://evidence.example/{role_id}/identity.pdf",
        "credential_or_qualification": f"https://evidence.example/{role_id}/credential.pdf",
        "scope_reviewed": f"https://evidence.example/{role_id}/scope.pdf",
        "package_or_commit_reference": f"https://evidence.example/{role_id}/package.txt",
        "signed_decision": f"https://evidence.example/{role_id}/decision.pdf",
        "findings_or_no_findings_rationale": f"https://evidence.example/{role_id}/rationale.pdf",
    }


def _complete_review(role_id: str = "security-public-upload", decision: str = "approve_within_scope") -> dict[str, object]:
    return {
        "review_id": f"review-{role_id}-001",
        "role_id": role_id,
        "reviewer_name": "Security Reviewer",
        "reviewer_role": "Independent application security reviewer",
        "qualification_basis": "Application security and file upload review",
        "scope_reviewed": "External review package 20260629T114559Z, exact scoped security review",
        "package_or_commit_ref": "commit:adadd50",
        "signed_at": "2026-06-29",
        "decision": decision,
        "findings": [],
        "evidence_artifacts": _evidence_artifacts(role_id),
    }


class ExternalReviewIntakeTests(unittest.TestCase):
    def test_contract_covers_all_review_roles_without_opening_claims(self) -> None:
        contract = build_returned_external_review_contract("2026-06-29T00:00:00Z")

        self.assertEqual(contract["status"], "external_review_returned_finding_contract_ready_claims_closed")
        self.assertEqual(contract["review_role_count"], 9)
        self.assertIn("approve_within_scope", contract["allowed_decisions"])
        self.assertIn("signed_decision", contract["required_evidence_categories"])
        self.assertFalse(contract["claims_opened"])

    def test_complete_scoped_review_accepts_but_does_not_open_claims(self) -> None:
        validation = validate_returned_external_review_record(
            _complete_review(),
            "2026-06-29T00:00:00Z",
        )

        self.assertEqual(validation["status"], "accepted_qualified_review_no_blocking_findings")
        self.assertTrue(validation["accepted_for_review_evidence"])
        self.assertTrue(validation["scope_approval_recorded"])
        self.assertFalse(validation["claims_opened_by_validation"])

    def test_blocking_review_exports_unresolved_findings(self) -> None:
        record = _complete_review("security-public-upload", "block")
        record["findings"] = [
            {
                "finding_id": "SEC-001",
                "reviewer_role": "Security/Public Upload Review",
                "severity": "P0",
                "affected_stage": "hosted_private_beta",
                "affected_file_or_artifact": "system_review_graph/public_upload_policy.json",
                "issue": "Hosted upload malware scanning is not proven.",
                "owner": "security reviewer",
                "required_fix": "Attach hosted malware scanning and quarantine proof.",
                "retest_command": "python3 scripts/check_product.py",
                "blocks_private_beta": True,
                "blocks_public_launch": True,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            returned = root / "external_review_findings" / "returned"
            returned.mkdir(parents=True)
            (returned / "security-public-upload.json").write_text(json.dumps(record), encoding="utf-8")

            manifest = build_returned_external_review_intake(root, "2026-06-29T00:00:00Z")

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["returned_record_count"], 1)
        self.assertEqual(manifest["accepted_review_evidence_count"], 1)
        self.assertEqual(manifest["scope_approval_count"], 0)
        self.assertEqual(manifest["unresolved_blocking_finding_count"], 1)
        self.assertTrue(any(row["finding_id"] == "SEC-001" for row in manifest["blocker_export"]["rows"]))
        self.assertFalse(manifest["claims_opened_by_intake"])

    def test_current_repo_has_no_returned_reviews_and_stays_blocked(self) -> None:
        manifest = build_returned_external_review_intake(ROOT, "2026-06-29T00:00:00Z")

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["returned_record_count"], 0)
        self.assertEqual(manifest["accepted_review_evidence_count"], 0)
        self.assertEqual(manifest["pending_review_count"], 9)
        self.assertFalse(manifest["wave_1_scope_ready_by_evidence"])
        self.assertFalse(manifest["public_launch_ready_by_review_evidence"])
        self.assertFalse(manifest["claims_opened_by_intake"])

    def test_writer_creates_returned_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_returned_external_review_intake_artifacts(root, "2026-06-29T00:00:00Z")

            self.assertEqual(result["status"], STATUS)
            self.assertTrue((root / "system_review_graph" / "external_review_returned_finding_contract.json").exists())
            self.assertTrue((root / "system_review_graph" / "external_review_returned_findings_manifest.json").exists())
            self.assertTrue((root / "system_review_graph" / "external_review_returned_review_matrix.json").exists())
            self.assertTrue((root / "system_review_graph" / "external_review_returned_blocker_export.jsonl").exists())
            self.assertTrue((root / "docs" / "EXTERNAL_REVIEW_RETURNED_FINDINGS.md").exists())


if __name__ == "__main__":
    unittest.main()
