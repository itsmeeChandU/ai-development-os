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
    build_runtime_state,
    can_access_packet,
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
        self.assertGreaterEqual(len(runtime["users"]), 4)
        self.assertGreaterEqual(len(runtime["organizations"]), 3)
        self.assertGreaterEqual(len(runtime["claims"]), 6)
        self.assertGreaterEqual(len(runtime["review_requests"]), 1)
        self.assertGreaterEqual(len(runtime["audit_events"]), 1)
        self.assertIn("/api/auth/login", runtime["api_routes"])
        self.assertIn("/review/:reviewToken", runtime["ui_routes"]["expert"])
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
