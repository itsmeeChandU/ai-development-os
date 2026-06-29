from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from importer_source_readiness.hosted_deployment_proof import (
    REQUIRED_PROOF_CATEGORIES,
    STATUS,
    build_hosted_deployment_contract,
    build_hosted_deployment_proof_intake,
    validate_hosted_deployment_record,
    write_hosted_deployment_proof_artifacts,
)


def _evidence_artifacts() -> dict[str, str]:
    return {
        row["category"]: f"https://evidence.example/hosted/{row['category']}.pdf"
        for row in REQUIRED_PROOF_CATEGORIES
    }


def _complete_record() -> dict[str, object]:
    return {
        "environment_id": "staging-private-beta-001",
        "environment_type": "staging_private_beta",
        "environment_url": "https://staging.example.com/trade-check",
        "operator_name": "DevOps Owner",
        "deployed_at": "2026-06-29",
        "build_or_commit_ref": "commit:314aa0c",
        "decision": "ready_for_private_beta_scope",
        "evidence_artifacts": _evidence_artifacts(),
    }


class HostedDeploymentProofTests(unittest.TestCase):
    def test_contract_defines_hosted_evidence_without_opening_claims(self) -> None:
        contract = build_hosted_deployment_contract("2026-06-29T00:00:00Z")

        self.assertEqual(contract["status"], "hosted_deployment_proof_contract_ready_claims_closed")
        self.assertEqual(contract["required_evidence_category_count"], len(REQUIRED_PROOF_CATEGORIES))
        self.assertGreaterEqual(contract["source_anchor_count"], 5)
        self.assertFalse(contract["claims_opened"])

    def test_complete_https_staging_record_accepts_environment_evidence_only(self) -> None:
        validation = validate_hosted_deployment_record(_complete_record(), "2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "accepted_hosted_private_beta_scope_evidence")
        self.assertTrue(validation["accepted_for_hosted_deployment_evidence"])
        self.assertTrue(validation["hosted_private_beta_ready_by_environment_evidence"])
        self.assertFalse(validation["public_launch_ready_by_environment_evidence"])
        self.assertFalse(validation["real_file_uploads_allowed_by_environment_evidence"])
        self.assertFalse(validation["claims_opened_by_validation"])

    def test_localhost_never_counts_as_hosted_proof(self) -> None:
        record = _complete_record()
        record["environment_url"] = "http://127.0.0.1:8877/trade-check"

        validation = validate_hosted_deployment_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "received_localhost_not_hosted_proof")
        self.assertFalse(validation["accepted_for_hosted_deployment_evidence"])
        self.assertTrue(validation["local_url_used"])

    def test_current_repo_has_no_hosted_proof_and_stays_blocked(self) -> None:
        manifest = build_hosted_deployment_proof_intake(ROOT, "2026-06-29T00:00:00Z")

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["hosted_record_count"], 0)
        self.assertEqual(manifest["accepted_hosted_record_count"], 0)
        self.assertEqual(manifest["missing_evidence_category_count"], len(REQUIRED_PROOF_CATEGORIES))
        self.assertEqual(manifest["blocker_export_count"], len(REQUIRED_PROOF_CATEGORIES))
        self.assertFalse(manifest["hosted_private_beta_ready_by_environment_evidence"])
        self.assertFalse(manifest["public_launch_ready_by_environment_evidence"])
        self.assertFalse(manifest["claims_opened_by_intake"])

    def test_writer_creates_hosted_deployment_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_hosted_deployment_proof_artifacts(root, "2026-06-29T00:00:00Z")

            self.assertEqual(result["status"], STATUS)
            self.assertTrue((root / "system_review_graph" / "hosted_deployment_proof_contract.json").exists())
            self.assertTrue((root / "system_review_graph" / "hosted_deployment_proof_manifest.json").exists())
            self.assertTrue((root / "system_review_graph" / "hosted_deployment_gate_matrix.json").exists())
            self.assertTrue((root / "system_review_graph" / "hosted_deployment_blocker_export.jsonl").exists())
            self.assertTrue((root / "docs" / "HOSTED_DEPLOYMENT_PROOF.md").exists())

    def test_complete_record_loaded_from_external_input_counts_as_environment_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "external_inputs"
            input_dir.mkdir()
            (input_dir / "hosted_staging_production_proof.json").write_text(
                json.dumps(_complete_record()),
                encoding="utf-8",
            )

            manifest = build_hosted_deployment_proof_intake(root, "2026-06-29T00:00:00Z")

        self.assertEqual(manifest["hosted_record_count"], 1)
        self.assertEqual(manifest["accepted_hosted_record_count"], 1)
        self.assertEqual(manifest["missing_evidence_category_count"], 0)
        self.assertEqual(manifest["blocked_gate_count"], 0)
        self.assertTrue(manifest["hosted_private_beta_ready_by_environment_evidence"])
        self.assertFalse(manifest["public_launch_ready_by_environment_evidence"])


if __name__ == "__main__":
    unittest.main()
