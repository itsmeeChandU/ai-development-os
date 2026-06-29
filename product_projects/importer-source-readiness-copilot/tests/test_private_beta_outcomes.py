from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from importer_source_readiness.private_beta_outcomes import (
    STATUS,
    TASKS,
    build_private_beta_outcome_contract,
    build_private_beta_session_schema,
    validate_private_beta_session_record,
    write_private_beta_outcome_artifacts,
)


def _passing_task_results(segment: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for task in TASKS:
        task_id = task["task_id"]
        if segment in task.get("required_for_segments", []):
            status = "completed_without_help"
        elif segment in task.get("allowed_not_applicable_segments", []):
            status = "not_applicable_with_reason"
        else:
            status = "not_observed"
        rows.append({"task_id": task_id, "status": status, "evidence_ref": f"https://evidence.example/{task_id}"})
    return rows


def _complete_session(segment: str = "beginner_user_no_documents") -> dict[str, object]:
    return {
        "session_id": "beta-session-001",
        "participant_segment": segment,
        "participant_role": "Owner of a small export business",
        "participant_is_real_target_user": True,
        "participant_is_internal_team": False,
        "session_date": "2026-06-29",
        "consent_record_ref": "https://evidence.example/consent.pdf",
        "environment_url_or_ref": "https://staging.example/trade-check",
        "build_or_commit_ref": "commit:d808830",
        "task_results": _passing_task_results(segment),
        "claim_comprehension": {
            "participant_understood_no_customs_approval": True,
            "participant_understood_no_buyer_validation": True,
            "participant_understood_no_supplier_verification": True,
            "participant_understood_next_valid_move": True,
            "unsafe_approval_misunderstanding": False,
        },
        "privacy_or_deletion_result": {
            "deletion_or_retention_choice_recorded": True,
            "critical_upload_or_privacy_incident": False,
            "real_upload_used": False,
            "upload_was_synthetic_or_permitted": True,
        },
        "issues": [{"severity": "P2", "status": "open", "summary": "Label could be clearer"}],
        "artifact_references": ["https://evidence.example/session-notes.pdf"],
        "outcome_decision": "counts_for_beta_evidence",
    }


class PrivateBetaOutcomeTests(unittest.TestCase):
    def test_session_schema_sets_real_user_evidence_requirements(self) -> None:
        schema = build_private_beta_session_schema("2026-06-29T00:00:00Z")

        self.assertEqual(schema["status"], "private_beta_session_evidence_schema_ready_claims_closed")
        self.assertEqual(schema["required_session_count"], 5)
        self.assertEqual(schema["task_count"], 9)
        self.assertIn("claim_comprehension", schema["required_evidence_categories"])
        self.assertFalse(schema["claims_opened"])

    def test_complete_real_session_accepts_without_opening_claims(self) -> None:
        validation = validate_private_beta_session_record(
            _complete_session("document_holding_import_or_export_user"),
            "2026-06-29T00:00:00Z",
        )

        self.assertEqual(validation["status"], "accepted_real_user_session")
        self.assertTrue(validation["accepted_for_private_beta_evidence"])
        self.assertEqual(validation["failed_required_tasks"], [])
        self.assertFalse(validation["claims_opened_by_session_validation"])

    def test_internal_or_simulated_session_cannot_count_as_real_beta_evidence(self) -> None:
        record = _complete_session()
        record["participant_is_internal_team"] = True
        record["simulated"] = True

        validation = validate_private_beta_session_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "blocked_simulated_or_internal_session")
        self.assertFalse(validation["accepted_for_private_beta_evidence"])
        self.assertTrue(validation["simulated_or_internal"])
        self.assertIn("cannot count as real private-beta user evidence", validation["next_valid_move"])

    def test_empty_current_repo_keeps_real_user_outcome_gate_closed(self) -> None:
        contract = build_private_beta_outcome_contract(ROOT, "2026-06-29T00:00:00Z")

        self.assertEqual(contract["status"], STATUS)
        self.assertEqual(contract["required_session_count"], 5)
        self.assertEqual(contract["current_real_session_count"], 0)
        self.assertEqual(contract["accepted_required_session_count"], 0)
        self.assertFalse(contract["required_segments_met"])
        self.assertFalse(contract["real_user_evidence_ready"])
        self.assertFalse(contract["public_launch_ready"])
        self.assertFalse(contract["claims_opened"])
        self.assertGreaterEqual(contract["gate_matrix"]["blocked_gate_count"], 7)

    def test_writer_creates_private_beta_outcome_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "system_review_graph").mkdir()
            (root / "system_review_graph" / "private_beta_smoke_test_plan.json").write_text(
                json.dumps({"status": "private_beta_smoke_test_plan_ready_blocked_until_wave_1_and_staging"}),
                encoding="utf-8",
            )
            (root / "system_review_graph" / "go_live_returned_input_evidence_manifest.json").write_text(
                json.dumps({"validation_rows": []}),
                encoding="utf-8",
            )

            result = write_private_beta_outcome_artifacts(root, "2026-06-29T00:00:00Z")

            self.assertEqual(result["status"], STATUS)
            self.assertTrue((root / "system_review_graph" / "private_beta_outcome_contract.json").exists())
            self.assertTrue((root / "system_review_graph" / "private_beta_session_evidence_schema.json").exists())
            self.assertTrue((root / "system_review_graph" / "private_beta_outcome_gate_matrix.json").exists())
            self.assertTrue((root / "docs" / "PRIVATE_BETA_OUTCOME_CONTRACT.md").exists())


if __name__ == "__main__":
    unittest.main()
