from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from importer_source_readiness.external_validation_research import (
    GATE_IDS,
    build_external_validation_requirements,
    evaluate_go_live_input_records,
    validate_external_validation_requirements,
    write_external_validation_requirements,
)


class ExternalValidationResearchTests(unittest.TestCase):
    def test_pack_covers_all_real_world_gates_without_opening_them(self) -> None:
        report = build_external_validation_requirements("2026-06-27T00:00:00Z")

        self.assertEqual(
            report["status"],
            "external_validation_requirements_ready_all_real_world_gates_blocked",
        )
        self.assertEqual(report["gate_ids"], GATE_IDS)
        self.assertEqual(report["gate_count"], 8)
        self.assertFalse(report["public_launch_ready"])
        self.assertFalse(report["hosted_private_beta_ready"])
        self.assertFalse(report["live_payment_ready"])
        self.assertFalse(report["real_world_external_evidence_received"])
        self.assertFalse(report["simulated_ai_review_can_open_gate"])
        self.assertGreaterEqual(report["source_count"], 24)
        self.assertGreaterEqual(report["evidence_requirement_count"], 44)
        self.assertGreaterEqual(report["required_data_category_count"], 14)
        self.assertEqual(validate_external_validation_requirements(report), [])

    def test_each_gate_has_collectable_evidence_and_known_sources(self) -> None:
        report = build_external_validation_requirements("2026-06-27T00:00:00Z")
        source_ids = {row["source_id"] for row in report["source_anchors"]}
        rows_by_gate = {
            gate_id: [
                row
                for row in report["evidence_requirements"]
                if row["gate_id"] == gate_id
            ]
            for gate_id in GATE_IDS
        }

        for gate in report["gates"]:
            self.assertTrue(gate["status"].startswith("blocked_"))
            self.assertGreaterEqual(len(gate["required_evidence"]), 5)
            self.assertTrue(gate["required_reviewers_or_owners"])
            self.assertTrue(gate["cannot_claim_until"])
            self.assertTrue(gate["next_valid_move"])
            self.assertGreaterEqual(len(rows_by_gate[gate["gate_id"]]), 5)
            for source_id in gate["source_ids"]:
                self.assertIn(source_id, source_ids)

    def test_project_data_catalog_includes_full_lifecycle_records(self) -> None:
        report = build_external_validation_requirements("2026-06-27T00:00:00Z")
        categories = {row["category_id"] for row in report["required_data_catalog"]}

        for required in (
            "official_source_registry",
            "privacy_legal_records",
            "security_operational_records",
            "hosted_environment_records",
            "trade_customs_records",
            "payment_billing_records",
            "private_beta_user_outcomes",
            "buyer_supplier_validation_records",
            "public_launch_decision_records",
        ):
            self.assertIn(required, categories)

        shortcuts = set(report["unsafe_shortcuts_rejected"])
        self.assertIn("AI-assisted simulated review as approval", shortcuts)
        self.assertIn("localhost proof as hosted production proof", shortcuts)
        self.assertIn("Stripe test mode as live payment activation", shortcuts)

    def test_go_live_input_evaluator_flips_ready_when_real_inputs_are_complete(self) -> None:
        not_ready = evaluate_go_live_input_records([], "2026-06-27T00:00:00Z")
        self.assertEqual(not_ready["status"], "waiting_for_real_inputs_not_ready_yet")
        self.assertFalse(not_ready["public_launch_ready"])
        self.assertEqual(not_ready["missing_input_count"], len(GATE_IDS))

        weak_records = []
        for gate_id in GATE_IDS:
            weak_records.append(
                {
                    "review_area": gate_id,
                    "reviewer_name": f"Reviewer {gate_id}",
                    "reviewer_role": (
                        "privacy legal security customs broker trade compliance devops sre payment billing "
                        "ux user research founder commercial launch owner expert reviewer"
                    ),
                    "scope_reviewed": "public launch candidate",
                    "decision": "go_for_public_launch" if gate_id == "public_go_no_go_approval" else "ready_for_my_area",
                    "top_issues": [],
                    "evidence_missing": [],
                    "signed_at": "2026-06-27",
                }
            )
        weak = evaluate_go_live_input_records(weak_records, "2026-06-27T00:00:00Z")
        self.assertEqual(weak["status"], "waiting_for_real_inputs_not_ready_yet")
        self.assertFalse(weak["public_launch_ready"])
        self.assertEqual(weak["ready_input_count"], 0)
        self.assertEqual(weak["missing_evidence_area_count"], len(GATE_IDS))

        role_by_gate = {
            "real_external_expert_reviews": "Independent security and trade expert reviewer",
            "legal_privacy_security_approval": "Privacy legal security compliance reviewer",
            "qualified_customs_trade_review": "Licensed customs broker and trade compliance reviewer",
            "hosted_staging_production_proof": "DevOps SRE deployment owner",
            "live_payment_activation": "Stripe payment billing owner",
            "real_users_private_beta_outcomes": "UX user research owner",
            "buyer_supplier_validation": "Founder commercial buyer supplier validation owner",
            "public_go_no_go_approval": "Founder accountable launch owner",
        }
        evidence_categories = {
            "real_external_expert_reviews": [
                "review_scope",
                "qualified_reviewer_findings",
                "signed_decision",
                "package_or_commit_reference",
            ],
            "legal_privacy_security_approval": [
                "privacy_notice_or_data_map",
                "security_review_or_scan",
                "ai_data_policy",
                "signed_approval",
            ],
            "qualified_customs_trade_review": [
                "reviewer_credential",
                "country_product_scope",
                "official_source_snapshot",
                "approved_blocked_claim_language",
            ],
            "hosted_staging_production_proof": [
                "live_url_or_environment",
                "commit_or_build",
                "smoke_test_result",
                "monitoring_or_logs",
                "rollback_or_backup",
            ],
            "live_payment_activation": [
                "stripe_live_or_disabled_scope",
                "webhook_test",
                "tax_refund_support_policy",
                "billing_claim_language",
            ],
            "real_users_private_beta_outcomes": [
                "participant_records",
                "task_results",
                "claim_comprehension",
                "issues_and_changes",
            ],
            "buyer_supplier_validation": [
                "counterparty_evidence",
                "problem_validation",
                "permission_scope",
                "screening_or_risk_notes",
            ],
            "public_go_no_go_approval": [
                "all_gate_summary",
                "release_scope",
                "risk_acceptance",
                "support_and_rollback_owner",
                "signed_go_no_go",
            ],
        }
        records = []
        for gate_id in GATE_IDS:
            records.append(
                {
                    "review_area": gate_id,
                    "reviewer_name": f"Reviewer {gate_id}",
                    "reviewer_role": role_by_gate[gate_id],
                    "scope_reviewed": "public launch candidate",
                    "decision": "go_for_public_launch" if gate_id == "public_go_no_go_approval" else "ready_for_my_area",
                    "top_issues": [],
                    "evidence_missing": [],
                    "evidence_artifacts": {
                        category: f"https://evidence.example/{gate_id}/{category}.pdf"
                        for category in evidence_categories[gate_id]
                    },
                    "signed_at": "2026-06-27",
                }
            )
        ready = evaluate_go_live_input_records(records, "2026-06-27T00:00:00Z", repo_root=ROOT)
        self.assertEqual(ready["status"], "go_live_ready_after_real_inputs")
        self.assertTrue(ready["public_launch_ready"])
        self.assertEqual(ready["missing_input_count"], 0)
        self.assertEqual(ready["accepted_with_attached_evidence_count"], len(GATE_IDS))
        self.assertFalse(ready["claims_opened_by_evidence_validation"])

    def test_writer_creates_machine_and_human_readable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_external_validation_requirements(root, "2026-06-27T00:00:00Z")

            self.assertEqual(
                result["status"],
                "external_validation_requirements_ready_all_real_world_gates_blocked",
            )
            report_path = root / "system_review_graph" / "external_validation_requirements_report.json"
            evidence_path = root / "system_review_graph" / "external_validation_evidence_requirements.json"
            input_templates_path = root / "system_review_graph" / "go_live_input_templates.json"
            input_readiness_path = root / "system_review_graph" / "go_live_input_readiness_report.json"
            input_evidence_path = root / "system_review_graph" / "go_live_returned_input_evidence_manifest.json"
            input_matrix_path = root / "system_review_graph" / "go_live_returned_input_validation_matrix.json"
            docs_path = root / "docs" / "EXTERNAL_VALIDATION_REQUIREMENTS.md"
            brief_docs_path = root / "docs" / "EXTERNAL_VALIDATION_REVIEWER_BRIEF.md"
            input_docs_path = root / "docs" / "GO_LIVE_INPUT_REQUESTS.md"
            input_evidence_docs_path = root / "docs" / "GO_LIVE_RETURNED_INPUT_EVIDENCE.md"
            pdf_path = root / "output" / "pdf" / "external_validation_requirements.pdf"
            brief_pdf_path = root / "output" / "pdf" / "external_validation_reviewer_brief.pdf"
            input_pdf_path = root / "output" / "pdf" / "go_live_input_requests.pdf"
            self.assertTrue(report_path.exists())
            self.assertTrue(evidence_path.exists())
            self.assertTrue(input_templates_path.exists())
            self.assertTrue(input_readiness_path.exists())
            self.assertTrue(input_evidence_path.exists())
            self.assertTrue(input_matrix_path.exists())
            self.assertTrue(docs_path.exists())
            self.assertTrue(brief_docs_path.exists())
            self.assertTrue(input_docs_path.exists())
            self.assertTrue(input_evidence_docs_path.exists())
            self.assertTrue(pdf_path.exists())
            self.assertTrue(brief_pdf_path.exists())
            self.assertTrue(input_pdf_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            input_readiness = json.loads(input_readiness_path.read_text(encoding="utf-8"))
            input_evidence = json.loads(input_evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "external_validation_evidence_requirements_ready")
            self.assertEqual(evidence["evidence_requirement_count"], report["evidence_requirement_count"])
            self.assertEqual(input_readiness["status"], "waiting_for_real_inputs_not_ready_yet")
            self.assertEqual(input_evidence["status"], "go_live_returned_input_evidence_ready_claims_closed")
            self.assertEqual(input_evidence["not_received_area_count"], len(GATE_IDS))
            self.assertIn("External Validation Requirements", docs_path.read_text(encoding="utf-8"))
            brief = brief_docs_path.read_text(encoding="utf-8")
            self.assertIn("What I need from you", brief)
            self.assertIn("What is not approved yet", brief)
            self.assertNotIn("blocker", brief.lower())
            self.assertNotIn("gate", brief.lower())
            input_doc = input_docs_path.read_text(encoding="utf-8")
            self.assertIn("Once Inputs Are Received", input_doc)
            self.assertIn("external_inputs/", input_doc)
            self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF"))
            self.assertTrue(brief_pdf_path.read_bytes().startswith(b"%PDF"))
            self.assertTrue(input_pdf_path.read_bytes().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
