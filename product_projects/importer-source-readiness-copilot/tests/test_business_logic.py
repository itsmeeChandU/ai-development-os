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
from importer_source_readiness.business_logic import (
    BUSINESS_COMPLETION_PHASE_IDS,
    BUSINESS_PHASE_IDS,
    BUSINESS_SCORE_IDS,
    build_business_logic_phases,
)
from importer_source_readiness.product_operations import (
    execute_agent_tool,
    generate_business_decision_report,
    persist_product_state,
)
from importer_source_readiness.source_packet_workflow import build_customer_workflow, load_json_list


class BusinessLogicTests(unittest.TestCase):
    def _workflow(self) -> tuple[dict, list[dict]]:
        official_sources = load_json(ROOT / "data" / "official_source_registry.json")
        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=official_sources,
            generated_at="2026-06-25T00:00:00+00:00",
        )
        return workflow, official_sources

    def test_business_logic_phases_are_real_packet_logic(self) -> None:
        workflow, official_sources = self._workflow()
        report = build_business_logic_phases(workflow, official_sources)

        self.assertEqual(report["status"], "business_logic_phases_ready_with_evidence_gates")
        self.assertEqual(report["phase_count"], 5)
        self.assertEqual(report["phase_ids"], BUSINESS_PHASE_IDS)
        self.assertEqual(report["score_ids"], BUSINESS_SCORE_IDS)
        self.assertEqual(report["business_identity_lock"]["first_wedge"], "foreign_exporters_preparing_to_sell_into_canada")
        self.assertEqual(
            report["completion_phase_contracts"]["status"],
            "all_14_phase_contracts_ready_external_gates_preserved",
        )
        self.assertEqual(report["completion_phase_contracts"]["phase_ids"], BUSINESS_COMPLETION_PHASE_IDS)
        self.assertEqual(report["completion_phase_contracts"]["phase_count"], 14)
        self.assertFalse(report["completion_phase_contracts"]["public_launch_ready"])
        self.assertEqual(report["packet_count"], 1)
        row = report["packet_rows"][0]
        self.assertEqual(row["business_positioning"], "trade_decision_preparation_not_compliance_approval")
        self.assertEqual(row["recommended_first_wedge"], "foreign_exporters_selling_into_canada")
        self.assertIn("market_demand_proven", row["blocked_claims"])

        decision = row["decision_tree"]
        self.assertEqual(decision["status"], "decision_tree_ready_claims_blocked")
        self.assertEqual(decision["question_count"], 12)
        self.assertIn("blocked", decision["answer_state_policy"])
        self.assertTrue(all("answer_state" in step for step in decision["questions"]))
        self.assertTrue(any(step["status"] == "blocked_until_confirmed" for step in decision["questions"]))

        canonical = row["canonical_packet_contract"]
        self.assertEqual(canonical["status"], "canonical_trade_packet_contract_ready")
        self.assertIn(canonical["stage"], {"starter", "document", "decision", "reviewer_ready", "beta_ready"})
        self.assertIn("reviewer_ready", canonical["stage_required_answers"])
        self.assertIn("beta_ready", canonical["stage_required_answers"])
        self.assertIn("provenance", canonical["schema_required_fields"])
        self.assertEqual(canonical["field_provenance"]["responsibility_path"]["mode"], "system_derived")
        self.assertEqual(canonical["field_provenance"]["source_url"]["mode"], "official_source_reference")

        scores = row["business_scores"]
        self.assertEqual(scores["status"], "five_business_scores_ready_no_approval_claims")
        self.assertEqual(scores["score_count"], 5)
        self.assertEqual(set(scores["scores"]), set(BUSINESS_SCORE_IDS))
        self.assertEqual(scores["scores"]["decision_safety_score"]["color"], "red")
        self.assertIn("cap_reason", scores["scores"]["decision_safety_score"])
        self.assertIn("cap at 39", scores["formula_contract"]["decision_safety_score"])
        self.assertIn("buyer_validated", scores["score_policy"]["forbidden_labels"])

    def test_market_country_source_and_signoff_contracts_stay_blocked_safe(self) -> None:
        workflow, official_sources = self._workflow()
        row = build_business_logic_phases(workflow, official_sources)["packet_rows"][0]

        market = row["market_intelligence"]
        self.assertEqual(market["status"], "market_intelligence_ready_as_research_plan")
        self.assertEqual(market["buyer_importer_discovery"]["status"], "lead_discovery_only")
        self.assertEqual(market["import_dependency_signal"]["status"], "unknown_until_trade_and_production_data_attached")
        self.assertIn("tariff_advantage_confirmed", market["tariff_and_market_access_comparison"]["blocked_claims"])
        self.assertTrue(market["tariff_and_market_access_comparison"]["source_routes"])

        country_packs = row["country_packs"]
        self.assertEqual(country_packs["status"], "country_packs_ready_with_reference_boundaries")
        countries = {pack["country"]: pack for pack in country_packs["packs"]}
        self.assertIn("Canada", countries)
        self.assertIn("Vietnam", countries)
        self.assertIn("India", countries)
        self.assertEqual(countries["India"]["role"], "strategic_next_origin_pack")
        self.assertTrue(countries["Canada"]["import_sources"])
        self.assertTrue(countries["Canada"]["trade_data_sources"])

        source_monitor = row["source_monitoring_contract"]
        self.assertEqual(source_monitor["status"], "source_monitoring_contract_ready_no_live_fetch_claim")
        self.assertIn("robots_status", source_monitor["registry_required_fields"])
        self.assertIn("register first, fetch later", source_monitor["fetch_policy"])
        self.assertIn("current_law_confirmed", source_monitor["blocked_claims"])
        first_source = source_monitor["sources"][0]
        self.assertIn("canonical_url", first_source)
        self.assertIn("fetch_mode", first_source)
        self.assertIn("diff_strategy", first_source)
        self.assertIn("freshness_status", first_source)
        self.assertIn("diff_classifier", first_source)
        self.assertIn("packet_impact_logic", first_source)
        self.assertIn("packet-frozen-tuna-canada-001", first_source["packet_tags"])

        outputs = row["packet_outputs"]
        self.assertEqual(outputs["status"], "commercial_packet_outputs_ready_claims_blocked")
        self.assertTrue(outputs["supplier_document_request"]["requested_items"])
        self.assertIn("broker_or_expert", outputs["question_sets"])

    def test_report_level_reviewer_and_beta_contracts_do_not_open_approvals(self) -> None:
        workflow, official_sources = self._workflow()
        report = build_business_logic_phases(workflow, official_sources)

        signoff = report["reviewer_signoff_framework"]
        self.assertEqual(signoff["status"], "reviewer_signoff_framework_ready_no_approval_substitution")
        self.assertEqual(signoff["final_rule"], "no reviewer lane, no claim lane")
        self.assertTrue(any(row["reviewer_lane"] == "Trade-Boundary/Customs Language" for row in signoff["lanes"]))
        self.assertFalse(any(row["ai_can_approve"] for row in signoff["lanes"]))
        self.assertEqual(signoff["customs_trade_template"]["decision"], "reference_only_ok|not_ready|needs_more_evidence")

        beta = report["hosted_beta_control_contract"]
        self.assertEqual(beta["status"], "hosted_beta_controls_blocked_until_real_platform_proof")
        self.assertEqual(beta["storage_recommendation"], "managed Postgres plus object storage for hosted beta; local SQLite and filesystem remain dev/local only")
        self.assertIn("live checkout stays disabled", beta["payment_policy"])
        self.assertEqual(
            report["metadata_only_beta_contract"]["status"],
            "metadata_only_beta_contract_ready_real_users_required",
        )
        self.assertEqual(
            report["buyer_supplier_validation_contract"]["status"],
            "buyer_supplier_validation_ladders_ready_claims_blocked",
        )
        self.assertEqual(
            report["payment_pricing_contract"]["status"],
            "payment_pricing_contract_ready_live_checkout_disabled",
        )
        self.assertFalse(report["payment_pricing_contract"]["live_checkout_enabled"])
        self.assertFalse(report["public_launch_contract"]["public_launch_ready"])

    def test_business_decision_operation_and_agent_tool_generate_artifacts(self) -> None:
        packets = load_json_list(ROOT / "data" / "customer_source_packets.json")
        evidence = load_json_list(ROOT / "data" / "evidence_ledger.json")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir(parents=True)
            (root / "data" / "official_source_registry.json").write_text(
                (ROOT / "data" / "official_source_registry.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            persist_product_state(root, packets, evidence)
            generated = generate_business_decision_report(root, "packet-frozen-tuna-canada-001")
            self.assertEqual(generated["business_decision"]["status"], "business_decision_report_generated")
            self.assertFalse(generated["business_decision"]["external_claims_opened"])
            self.assertTrue(
                (root / "system_review_graph" / "generated_reports" / "business_decision_packet-frozen-tuna-canada-001.json").exists()
            )

            tool = execute_agent_tool(
                root,
                "get_business_logic_phase_report",
                {"packet_id": "packet-frozen-tuna-canada-001"},
            )
            self.assertEqual(tool["status"], "agent_tool_executed_local")
            self.assertFalse(tool["can_open_claim_gate"])
            self.assertEqual(tool["result"]["business_logic"][0]["packet_id"], "packet-frozen-tuna-canada-001")


if __name__ == "__main__":
    unittest.main()
