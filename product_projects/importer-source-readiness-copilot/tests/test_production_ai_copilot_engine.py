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

from importer_source_readiness.production_ai_copilot_engine import (
    AI_OUTPUT_LABELS,
    STATUS,
    build_production_ai_copilot_engine,
    write_production_ai_copilot_engine_artifacts,
)


class ProductionAiCopilotEngineTests(unittest.TestCase):
    def test_ai_copilot_manifest_registers_roles_and_keeps_gates_closed(self) -> None:
        manifest = build_production_ai_copilot_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["ai_role_count"], 8)
        self.assertEqual(manifest["ai_output_contract_count"], 8)
        self.assertEqual(manifest["allowed_output_labels"], list(AI_OUTPUT_LABELS))
        self.assertGreaterEqual(manifest["prompt_injection_test_count"], 2)
        self.assertFalse(manifest["provider_terms_review_complete"])
        self.assertFalse(manifest["qualified_ai_safety_review_complete"])
        self.assertFalse(manifest["live_model_calls_enabled"])
        self.assertFalse(manifest["can_open_customs_tariff_cfia_buyer_supplier_payment_legal_launch_gate"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])

    def test_ai_role_contracts_have_labels_redaction_fallbacks_and_blocked_gates(self) -> None:
        manifest = build_production_ai_copilot_engine(ROOT)
        contracts = {row["role"]: row for row in manifest["role_contracts"]}

        for role in (
            "intake_assistant",
            "document_extraction_assistant",
            "source_summarizer",
            "market_research_assistant",
            "packet_writer",
            "reviewer_work_order_drafter",
            "redaction_assistant",
            "qa_assistant",
        ):
            self.assertIn(role, contracts)
            self.assertIn(contracts[role]["output_label"], AI_OUTPUT_LABELS)
            self.assertEqual(contracts[role]["manual_no_ai_fallback"], "Use operator review and scoped expert-review packet when AI is disabled.")
            self.assertFalse(contracts[role]["can_open_gate"])
            self.assertIn("tariff_confirmed", contracts[role]["blocked_gates"])

        self.assertTrue(contracts["document_extraction_assistant"]["requires_redaction_preview"])
        self.assertEqual(contracts["source_summarizer"]["output_label"], "source_backed")
        self.assertEqual(contracts["reviewer_work_order_drafter"]["output_label"], "needs_expert_review")

    def test_prompt_injection_checks_block_unsafe_instructions(self) -> None:
        manifest = build_production_ai_copilot_engine(ROOT)

        self.assertTrue(manifest["prompt_injection_results"])
        for result in manifest["prompt_injection_results"]:
            self.assertEqual(result["result"], "blocked_output_no_gate_opened")
            self.assertFalse(result["can_open_gate"])
            self.assertTrue(result["human_review_required"])
            self.assertIn("tariff_confirmed", result["blocked_gates"])

    def test_output_contracts_never_open_product_gates(self) -> None:
        manifest = build_production_ai_copilot_engine(ROOT)

        for contract in manifest["output_contracts"]:
            self.assertFalse(contract["can_open_customs_tariff_cfia_buyer_supplier_payment_launch_gate"])
            self.assertFalse(contract["claims_opened"])
            self.assertFalse(contract["external_effects_created"])
            self.assertIn(contract["output_label"], AI_OUTPUT_LABELS)

    def test_writer_creates_manifest_contracts_safety_and_doc(self) -> None:
        manifest = build_production_ai_copilot_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_ai_copilot_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_contracts = json.loads(paths["output_contracts"].read_text(encoding="utf-8"))
            written_safety = json.loads(paths["safety"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_contracts["status"], "production_ai_output_contracts_ready_no_gate_opening")
            self.assertEqual(written_safety["status"], "production_ai_safety_checks_ready_fail_closed")
            self.assertIn("Production AI Copilot Engine", written_doc)
            self.assertIn("Live model calls enabled: false", written_doc)


if __name__ == "__main__":
    unittest.main()
