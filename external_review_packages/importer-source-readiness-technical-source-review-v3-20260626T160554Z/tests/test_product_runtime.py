from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import load_json
from importer_source_readiness.ai_review_validation import validate_ai_review_output
from importer_source_readiness.product_runtime import (
    actor_by_session,
    ai_policy_for_org,
    build_runtime_state,
    can_access_packet,
    redaction_preview_for_evidence,
    route_ai_task,
    write_runtime_artifacts,
)
from importer_source_readiness.source_packet_workflow import build_customer_workflow, load_json_list


class ProductRuntimeTests(unittest.TestCase):
    def _workflow(self) -> dict:
        return build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

    def test_runtime_state_has_auth_rbac_reviews_audit_and_deployment(self) -> None:
        workflow = self._workflow()
        runtime = build_runtime_state(workflow)

        self.assertEqual(runtime["status"], "private_beta_candidate_with_external_human_gates")
        self.assertEqual(runtime["product"], "Trade Readiness Copilot")
        self.assertEqual(runtime["internal_engine"], "Importer Source Readiness Copilot")
        self.assertEqual(runtime["public_product_surface"]["status"], "public_quick_check_ready_local_with_external_gates")
        self.assertGreaterEqual(len(runtime["users"]), 4)
        self.assertGreaterEqual(len(runtime["organizations"]), 3)
        self.assertGreaterEqual(len(runtime["claims"]), 6)
        self.assertGreaterEqual(len(runtime["review_requests"]), 1)
        self.assertGreaterEqual(len(runtime["audit_events"]), 1)
        self.assertIn("/api/auth/login", runtime["api_routes"])
        self.assertIn("/api/public/starter", runtime["api_routes"])
        self.assertIn("/api/public/quick-check", runtime["api_routes"])
        self.assertIn("/api/public/packets/:id/confirm", runtime["api_routes"])
        self.assertIn("/api/public/packets/:id/chatgpt-safe-summary", runtime["api_routes"])
        self.assertIn("/api/public/packets/:id/reports/buyer.pdf", runtime["api_routes"])
        self.assertIn("/api/public/packets/:id/reports/broker.pdf", runtime["api_routes"])
        self.assertIn("/api/opportunities", runtime["api_routes"])
        self.assertIn("/api/country-coverage", runtime["api_routes"])
        self.assertIn("/api/billing/controls", runtime["api_routes"])
        self.assertIn("/api/billing/usage", runtime["api_routes"])
        self.assertIn("/api/agent-api", runtime["api_routes"])
        self.assertIn("/api/agent-api/gateway", runtime["api_routes"])
        self.assertIn("/api/traffic-pages", runtime["api_routes"])
        self.assertIn("/api/transport-readiness", runtime["api_routes"])
        self.assertIn("/api/stages", runtime["api_routes"])
        self.assertIn("/api/research-plan", runtime["api_routes"])
        self.assertIn("/api/expert-network", runtime["api_routes"])
        self.assertIn("/api/team-workspace", runtime["api_routes"])
        self.assertIn("/api/launch-operations", runtime["api_routes"])
        self.assertIn("/api/product-operations/report", runtime["api_routes"])
        self.assertIn("/api/product-operations/run", runtime["api_routes"])
        self.assertIn("/api/agent-tools/:tool", runtime["api_routes"])
        self.assertIn("/api/orgs/current/ai-policy", runtime["api_routes"])
        self.assertIn("/api/evidence/:evidenceId/ai-permission", runtime["api_routes"])
        self.assertIn("/start", runtime["ui_routes"]["customer"])
        self.assertIn("/tools/export-readiness", runtime["ui_routes"]["customer"])
        self.assertIn("/tools/document-check", runtime["ui_routes"]["customer"])
        self.assertIn("/opportunities", runtime["ui_routes"]["customer"])
        self.assertIn("/country-coverage", runtime["ui_routes"]["customer"])
        self.assertIn("/transport-readiness", runtime["ui_routes"]["customer"])
        self.assertIn("/reports/sample", runtime["ui_routes"]["customer"])
        self.assertIn("/pricing", runtime["ui_routes"]["customer"])
        self.assertIn("/billing", runtime["ui_routes"]["customer"])
        self.assertIn("/billing/usage", runtime["ui_routes"]["customer"])
        self.assertIn("/agent-api", runtime["ui_routes"]["customer"])
        self.assertIn("/stages", runtime["ui_routes"]["customer"])
        self.assertIn("/research-plan", runtime["ui_routes"]["customer"])
        self.assertIn("/expert-network", runtime["ui_routes"]["customer"])
        self.assertIn("/team-workspace", runtime["ui_routes"]["customer"])
        self.assertIn("/launch-operations", runtime["ui_routes"]["customer"])
        self.assertIn("/ai-data-policy", runtime["ui_routes"]["customer"])
        self.assertIn("/security", runtime["ui_routes"]["customer"])
        self.assertIn("/public/packets/:packetId/result", runtime["ui_routes"]["customer"])
        self.assertIn("/public/packets/:packetId/confirm", runtime["ui_routes"]["customer"])
        self.assertIn("/workspace", runtime["ui_routes"]["customer"])
        self.assertIn("/packets/:packetId/source-monitoring", runtime["ui_routes"]["customer"])
        self.assertIn("/packets/:packetId/safe-summary", runtime["ui_routes"]["customer"])
        self.assertIn("/review/:reviewToken", runtime["ui_routes"]["expert"])
        self.assertIn("/settings/ai-data-policy", runtime["ui_routes"]["customer"])
        self.assertEqual(runtime["ai_model_router"]["status"], "ai_model_router_ready")
        self.assertEqual(runtime["redaction_pipeline"]["status"], "redaction_pipeline_ready")
        self.assertEqual(runtime["manual_no_ai_workflow"]["status"], "manual_no_ai_workflow_ready")
        self.assertGreaterEqual(len(runtime["requirements_traceability"]), 44)
        self.assertEqual(runtime["deployment"]["status"], "deployable_local_stack_ready_with_external_hosting_gates")

    def test_customer_a_cannot_access_customer_b_packet(self) -> None:
        packet = self._workflow()["packets"][0]
        customer = actor_by_session("customer-session")
        other = actor_by_session("other-customer-session")
        operator = actor_by_session("operator-session")

        self.assertTrue(can_access_packet(customer or {}, packet))
        self.assertFalse(can_access_packet(other or {}, packet))
        self.assertTrue(can_access_packet(operator or {}, packet))

    def test_runtime_artifacts_are_written(self) -> None:
        workflow = self._workflow()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = write_runtime_artifacts(root, workflow)

            self.assertEqual(state["status"], "private_beta_candidate_with_external_human_gates")
            self.assertTrue((root / "system_review_graph" / "product_runtime_state.json").exists())
            self.assertTrue((root / "system_review_graph" / "auth_rbac_matrix.json").exists())
            self.assertTrue((root / "system_review_graph" / "deployment_readiness_report.json").exists())
            self.assertTrue((root / "system_review_graph" / "ai_data_policy.json").exists())
            self.assertTrue((root / "system_review_graph" / "ai_model_router.json").exists())
            self.assertTrue((root / "system_review_graph" / "redaction_pipeline.json").exists())
            self.assertTrue((root / "system_review_graph" / "requirements_traceability_matrix.json").exists())
            self.assertTrue((root / "system_review_graph" / "public_trade_readiness_manifest.json").exists())
            self.assertTrue((root / "system_review_graph" / "exporter_mode_requirements.json").exists())
            self.assertTrue((root / "system_review_graph" / "public_report_types.json").exists())
            self.assertTrue((root / "system_review_graph" / "public_upload_policy.json").exists())

    def test_ai_policy_router_and_redaction_fail_closed(self) -> None:
        policy = ai_policy_for_org("org-importer-demo")
        self.assertEqual(policy["default_mode"], "redacted")

        denied = route_ai_task(
            organization_id="org-importer-demo",
            packet_id="packet-1",
            evidence_id="evidence-1",
            task_type="review",
            document_sensitivity="restricted",
            requested_mode="business_api",
            evidence_permission="business_api",
        )
        self.assertFalse(denied["allowed"])
        self.assertIn("requires private/no-AI mode", denied["reason_if_denied"])

        no_ai = route_ai_task(
            organization_id="org-other-demo",
            packet_id="packet-1",
            evidence_id="evidence-2",
            task_type="review",
            document_sensitivity="internal",
            requested_mode="business_api",
            evidence_permission="no_ai",
        )
        self.assertFalse(no_ai["allowed"])
        self.assertEqual(no_ai["mode"], "no_ai")

        preview = redaction_preview_for_evidence(
            {
                "evidence_id": "evidence-3",
                "packet_id": "packet-1",
                "sensitivity_level": "confidential",
                "ai_processing_mode": "redacted",
            }
        )
        self.assertTrue(preview["redaction_required"])
        self.assertIn("emails", preview["redaction_categories"])

    def test_ai_review_validation_fails_closed_on_gate_opening_and_unknown_evidence(self) -> None:
        output = {
            "review_type": "canada_compliance_simulation",
            "scope": "test",
            "summary": "unsafe",
            "findings": [
                {
                    "title": "Bad approval",
                    "severity": "P1_blocks_external_claim",
                    "issue": "tries to approve",
                    "evidence_used": ["other-org-evidence"],
                    "sources_used": ["cbsa-import-commercial-goods"],
                    "blocked_claims": ["tariff_classification_claim"],
                    "next_valid_move": "fail closed",
                    "human_review_required": True,
                }
            ],
            "can_open_gate": True,
            "human_review_required": True,
            "blocked_claims": ["tariff_classification_claim"],
        }

        result = validate_ai_review_output(
            output,
            evidence_ids={"evidence-frozen-tuna-cid-reference"},
            source_ids={"cbsa-import-commercial-goods"},
        )

        self.assertFalse(result["valid"])
        self.assertEqual(result["decision"], "rejected_fail_closed")
        self.assertIn("can_open_gate must be false", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
