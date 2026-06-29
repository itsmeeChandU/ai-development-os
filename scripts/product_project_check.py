#!/usr/bin/env python3
"""Validate the bundled importer source readiness product project."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "product_projects" / "importer-source-readiness-copilot"
EXPECTED_WAVE_1_REVIEW_ROLES = {
    "UX/Product Usability Review",
    "Security/Public Upload Review",
    "Privacy/Legal Review",
    "AI Safety/Prompt Injection Review",
    "DevOps/Production Readiness Review",
}
REQUIRED_AI_ASSISTED_FINDING_FIELDS = {
    "finding_id",
    "reviewer_role",
    "severity",
    "affected_stage",
    "affected_file_or_artifact",
    "issue",
    "owner",
    "required_fix",
    "retest_command",
    "blocks_private_beta",
    "blocks_public_launch",
    "review_origin",
    "model_or_agent_used",
    "web_sources_checked",
    "confidence",
    "human_followup_required",
}


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def main() -> int:
    required = [
        PROJECT / "README.md",
        PROJECT / "AGENTS.md",
        PROJECT / "PRODUCT_DOCTRINE.md",
        PROJECT / "CUSTOMER_SOURCE_PACKET_SPEC.md",
        PROJECT / "SOURCE_OF_TRUTH.md",
        PROJECT / "SOURCE_OF_TRUTH_CURRENT.md",
        PROJECT / "RUN_RESULTS.md",
        PROJECT / "EXTERNAL_REVIEW_SUMMARY.md",
        PROJECT / "REDACTION_REPORT.md",
        PROJECT / "REVIEW_USE_TERMS.md",
        PROJECT / "OFFLINE_REPRODUCTION.md",
        PROJECT / "PACKAGE_AUDIT.md",
        PROJECT / "data" / "sample_source_cards.json",
        PROJECT / "data" / "country_requirements_matrix.json",
        PROJECT / "data" / "evidence_packets.json",
        PROJECT / "data" / "official_source_registry.json",
        PROJECT / "data" / "investor_evidence.json",
        PROJECT / "data" / "canada_tool_registry.json",
        PROJECT / "data" / "expert_review_simulations.json",
        PROJECT / "data" / "launch_controls.json",
        PROJECT / "data" / "customer_source_packets.json",
        PROJECT / "data" / "evidence_ledger.json",
        PROJECT / "src" / "importer_source_readiness" / "readiness.py",
        PROJECT / "src" / "importer_source_readiness" / "external_gates.py",
        PROJECT / "src" / "importer_source_readiness" / "continuation.py",
        PROJECT / "src" / "importer_source_readiness" / "investor_readiness.py",
        PROJECT / "src" / "importer_source_readiness" / "board_readiness.py",
        PROJECT / "src" / "importer_source_readiness" / "operator_app.py",
        PROJECT / "src" / "importer_source_readiness" / "operator_workflow.py",
        PROJECT / "src" / "importer_source_readiness" / "operator_report.py",
        PROJECT / "src" / "importer_source_readiness" / "operator_screenshots.py",
        PROJECT / "src" / "importer_source_readiness" / "source_packet_workflow.py",
        PROJECT / "src" / "importer_source_readiness" / "customer_store.py",
        PROJECT / "src" / "importer_source_readiness" / "product_runtime.py",
        PROJECT / "src" / "importer_source_readiness" / "document_processing.py",
        PROJECT / "src" / "importer_source_readiness" / "policy_intelligence.py",
        PROJECT / "src" / "importer_source_readiness" / "completion_platform.py",
        PROJECT / "src" / "importer_source_readiness" / "product_operations.py",
        PROJECT / "src" / "importer_source_readiness" / "ai_review_validation.py",
        PROJECT / "src" / "importer_source_readiness" / "external_review.py",
        PROJECT / "src" / "importer_source_readiness" / "final_go_live.py",
        PROJECT / "src" / "importer_source_readiness" / "external_validation_research.py",
        PROJECT / "src" / "importer_source_readiness" / "production_ai_copilot_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_country_source_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_data_model.py",
        PROJECT / "src" / "importer_source_readiness" / "production_decision_scoring_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_document_intelligence_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_evidence_claim_gate_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_enterprise_api_platform.py",
        PROJECT / "src" / "importer_source_readiness" / "production_expert_review_network.py",
        PROJECT / "src" / "importer_source_readiness" / "production_launch_control_plane.py",
        PROJECT / "src" / "importer_source_readiness" / "production_market_intelligence_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_market_readiness_evidence_room.py",
        PROJECT / "src" / "importer_source_readiness" / "production_trade_discovery_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_trade_data_catalog_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_packet_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_persistence.py",
        PROJECT / "src" / "importer_source_readiness" / "production_payment_monetization_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_portal_workflow_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_redevelopment.py",
        PROJECT / "src" / "importer_source_readiness" / "production_reports_engine.py",
        PROJECT / "src" / "importer_source_readiness" / "production_security_privacy_reliability_engine.py",
        PROJECT / "tests" / "test_readiness.py",
        PROJECT / "tests" / "test_external_gates.py",
        PROJECT / "tests" / "test_continuation.py",
        PROJECT / "tests" / "test_investor_readiness.py",
        PROJECT / "tests" / "test_board_go_live.py",
        PROJECT / "tests" / "test_operator_app.py",
        PROJECT / "tests" / "test_operator_workflow.py",
        PROJECT / "tests" / "test_operator_screenshots.py",
        PROJECT / "tests" / "test_source_packet_workflow.py",
        PROJECT / "tests" / "test_customer_store.py",
        PROJECT / "tests" / "test_product_runtime.py",
        PROJECT / "tests" / "test_policy_intelligence.py",
        PROJECT / "tests" / "test_completion_platform.py",
        PROJECT / "tests" / "test_external_package_audit.py",
        PROJECT / "tests" / "test_external_review_workflow.py",
        PROJECT / "tests" / "test_final_go_live.py",
        PROJECT / "tests" / "test_external_validation_research.py",
        PROJECT / "tests" / "test_production_ai_copilot_engine.py",
        PROJECT / "tests" / "test_production_country_source_engine.py",
        PROJECT / "tests" / "test_production_data_model.py",
        PROJECT / "tests" / "test_production_decision_scoring_engine.py",
        PROJECT / "tests" / "test_production_document_intelligence_engine.py",
        PROJECT / "tests" / "test_production_evidence_claim_gate_engine.py",
        PROJECT / "tests" / "test_production_enterprise_api_platform.py",
        PROJECT / "tests" / "test_production_expert_review_network.py",
        PROJECT / "tests" / "test_production_launch_control_plane.py",
        PROJECT / "tests" / "test_production_market_intelligence_engine.py",
        PROJECT / "tests" / "test_production_market_readiness_evidence_room.py",
        PROJECT / "tests" / "test_production_trade_discovery_engine.py",
        PROJECT / "tests" / "test_production_trade_data_catalog_engine.py",
        PROJECT / "tests" / "test_production_packet_engine.py",
        PROJECT / "tests" / "test_production_persistence.py",
        PROJECT / "tests" / "test_proof_loop.py",
        PROJECT / "tests" / "test_production_payment_monetization_engine.py",
        PROJECT / "tests" / "test_production_portal_workflow_engine.py",
        PROJECT / "tests" / "test_production_redevelopment.py",
        PROJECT / "tests" / "test_production_reports_engine.py",
        PROJECT / "tests" / "test_production_security_privacy_reliability_engine.py",
        PROJECT / "scripts" / "run_readiness.py",
        PROJECT / "scripts" / "run_external_gates.py",
        PROJECT / "scripts" / "export_operator_dashboard.py",
        PROJECT / "scripts" / "plan_continuation.py",
        PROJECT / "scripts" / "build_vc_pitch_packet.py",
        PROJECT / "scripts" / "build_board_go_live_packet.py",
        PROJECT / "scripts" / "serve_operator_app.py",
        PROJECT / "scripts" / "run_operator_workflow.py",
        PROJECT / "scripts" / "run_customer_workflow.py",
        PROJECT / "scripts" / "run_policy_intelligence.py",
        PROJECT / "scripts" / "run_completion_platform.py",
        PROJECT / "scripts" / "run_product_operations.py",
        PROJECT / "scripts" / "build_external_review_packet.py",
        PROJECT / "scripts" / "audit_external_package.py",
        PROJECT / "scripts" / "run_final_go_live_review.py",
        PROJECT / "scripts" / "run_external_validation_requirements.py",
        PROJECT / "scripts" / "run_production_ai_copilot_engine.py",
        PROJECT / "scripts" / "run_production_country_source_engine.py",
        PROJECT / "scripts" / "run_production_data_model.py",
        PROJECT / "scripts" / "run_production_decision_scoring_engine.py",
        PROJECT / "scripts" / "run_production_document_intelligence_engine.py",
        PROJECT / "scripts" / "run_production_evidence_claim_gate_engine.py",
        PROJECT / "scripts" / "run_production_enterprise_api_platform.py",
        PROJECT / "scripts" / "run_production_expert_review_network.py",
        PROJECT / "scripts" / "run_production_launch_control_plane.py",
        PROJECT / "scripts" / "run_production_market_intelligence_engine.py",
        PROJECT / "scripts" / "run_production_market_readiness_evidence_room.py",
        PROJECT / "scripts" / "run_production_trade_discovery_engine.py",
        PROJECT / "scripts" / "run_production_trade_data_catalog_engine.py",
        PROJECT / "scripts" / "run_production_packet_engine.py",
        PROJECT / "scripts" / "run_production_persistence.py",
        PROJECT / "scripts" / "run_all_artifacts.py",
        PROJECT / "scripts" / "run_production_payment_monetization_engine.py",
        PROJECT / "scripts" / "run_production_portal_workflow_engine.py",
        PROJECT / "scripts" / "run_production_redevelopment.py",
        PROJECT / "scripts" / "run_production_reports_engine.py",
        PROJECT / "scripts" / "run_production_security_privacy_reliability_engine.py",
        PROJECT / "scripts" / "package_external_review.py",
        PROJECT / "scripts" / "check_product.py",
        PROJECT / "docs" / "PRODUCT_AUTOMATION_RUNBOOK.md",
        PROJECT / "docs" / "PRODUCT_STATUS.md",
        PROJECT / "docs" / "REQUIREMENTS_ANALYSIS.md",
        PROJECT / "docs" / "PUBLIC_TRADE_READINESS.md",
        PROJECT / "docs" / "ALL_STAGES_COMPLETION.md",
        PROJECT / "docs" / "AI_DATA_POLICY.md",
        PROJECT / "docs" / "DOCUMENT_PROCESSING.md",
        PROJECT / "docs" / "OPPORTUNITY_SCANNER.md",
        PROJECT / "docs" / "POLICY_MONITORING.md",
        PROJECT / "docs" / "AGENT_API.md",
        PROJECT / "docs" / "STARTUP_LIFECYCLE.md",
        PROJECT / "docs" / "OPERATOR_GUIDE.md",
        PROJECT / "docs" / "UI_UX_COMPONENT_SYSTEM.md",
        PROJECT / "docs" / "EXTERNAL_REVIEW_PROCESS.md",
        PROJECT / "docs" / "EXTERNAL_VALIDATION_REQUIREMENTS.md",
        PROJECT / "docs" / "EXTERNAL_VALIDATION_REVIEWER_BRIEF.md",
        PROJECT / "docs" / "GO_LIVE_INPUT_REQUESTS.md",
        PROJECT / "docs" / "PRODUCTION_AI_COPILOT_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_COUNTRY_SOURCE_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_DATA_MODEL.md",
        PROJECT / "docs" / "PRODUCTION_PERSISTENCE.md",
        PROJECT / "docs" / "PRODUCTION_DECISION_SCORING_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_DOCUMENT_INTELLIGENCE_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_EVIDENCE_CLAIM_GATE_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_ENTERPRISE_API_PLATFORM.md",
        PROJECT / "docs" / "PRODUCTION_EXPERT_REVIEW_NETWORK.md",
        PROJECT / "docs" / "PRODUCTION_LAUNCH_CONTROL_PLANE.md",
        PROJECT / "docs" / "PRODUCTION_MARKET_INTELLIGENCE_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_MARKET_READINESS_EVIDENCE_ROOM.md",
        PROJECT / "docs" / "PRODUCTION_TRADE_DISCOVERY_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_TRADE_DATA_CATALOG_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_PACKET_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_PAYMENT_MONETIZATION_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_PORTAL_WORKFLOWS.md",
        PROJECT / "docs" / "PRODUCTION_REDEVELOPMENT.md",
        PROJECT / "docs" / "PRODUCTION_REPORTS_ENGINE.md",
        PROJECT / "docs" / "PRODUCTION_SECURITY_PRIVACY_RELIABILITY_ENGINE.md",
        PROJECT / "docs" / "BUSINESS_CORE_LOGIC_CURRENT_STATE.md",
        PROJECT / "docs" / "FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md",
        PROJECT / "docs" / "NON_FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md",
        PROJECT / "system_review_graph" / "external_gate_report.json",
        PROJECT / "system_review_graph" / "continuation_plan.json",
        PROJECT / "system_review_graph" / "vc_pitch_readiness_report.json",
        PROJECT / "system_review_graph" / "board_go_live_readiness_report.json",
        PROJECT / "system_review_graph" / "operator_workflow_report.json",
        PROJECT / "system_review_graph" / "operator_dashboard.html",
        PROJECT / "system_review_graph" / "operator_screenshot_manifest.json",
        PROJECT / "system_review_graph" / "operator_screenshots" / "operator-dashboard.png",
        PROJECT / "system_review_graph" / "customer_readiness_report.json",
        PROJECT / "system_review_graph" / "customer_readiness_report.md",
        PROJECT / "system_review_graph" / "customer_source_packets.json",
        PROJECT / "system_review_graph" / "evidence_ledger.json",
        PROJECT / "system_review_graph" / "customer_ai_review_runs.json",
        PROJECT / "system_review_graph" / "customer_workflow.sqlite",
        PROJECT / "system_review_graph" / "product_runtime_state.json",
        PROJECT / "system_review_graph" / "auth_rbac_matrix.json",
        PROJECT / "system_review_graph" / "claims_gate_matrix.json",
        PROJECT / "system_review_graph" / "review_requests.json",
        PROJECT / "system_review_graph" / "human_review_findings.json",
        PROJECT / "system_review_graph" / "report_exports.json",
        PROJECT / "system_review_graph" / "audit_events.json",
        PROJECT / "system_review_graph" / "deletion_requests.json",
        PROJECT / "system_review_graph" / "deployment_readiness_report.json",
        PROJECT / "system_review_graph" / "private_beta_readiness_checklist.json",
        PROJECT / "system_review_graph" / "ai_data_policy.json",
        PROJECT / "system_review_graph" / "model_endpoints.json",
        PROJECT / "system_review_graph" / "ai_model_router.json",
        PROJECT / "system_review_graph" / "redaction_pipeline.json",
        PROJECT / "system_review_graph" / "manual_no_ai_workflow.json",
        PROJECT / "system_review_graph" / "requirements_traceability_matrix.json",
        PROJECT / "system_review_graph" / "public_trade_readiness_manifest.json",
        PROJECT / "system_review_graph" / "exporter_mode_requirements.json",
        PROJECT / "system_review_graph" / "public_report_types.json",
        PROJECT / "system_review_graph" / "public_upload_policy.json",
        PROJECT / "system_review_graph" / "intelligence_hub_policy_monitor.json",
        PROJECT / "system_review_graph" / "policy_source_snapshots.json",
        PROJECT / "system_review_graph" / "policy_change_impact_report.json",
        PROJECT / "system_review_graph" / "policy_intelligence.sqlite",
        PROJECT / "system_review_graph" / "completion_platform_manifest.json",
        PROJECT / "system_review_graph" / "country_coverage_report.json",
        PROJECT / "system_review_graph" / "opportunity_scanner_report.json",
        PROJECT / "system_review_graph" / "business_logic_phase_report.json",
        PROJECT / "system_review_graph" / "business_phase_completion_report.json",
        PROJECT / "system_review_graph" / "transport_readiness_report.json",
        PROJECT / "system_review_graph" / "billing_credit_controls.json",
        PROJECT / "system_review_graph" / "agent_api_manifest.json",
        PROJECT / "system_review_graph" / "traffic_pages_manifest.json",
        PROJECT / "system_review_graph" / "research_execution_plan.json",
        PROJECT / "system_review_graph" / "team_workspace_report.json",
        PROJECT / "system_review_graph" / "expert_network_report.json",
        PROJECT / "system_review_graph" / "billing_usage_ledger.json",
        PROJECT / "system_review_graph" / "agent_api_gateway_contract.json",
        PROJECT / "system_review_graph" / "launch_operations_report.json",
        PROJECT / "system_review_graph" / "all_stage_readiness_report.json",
        PROJECT / "system_review_graph" / "product_operations_report.json",
        PROJECT / "system_review_graph" / "product_operations_log.json",
        PROJECT / "system_review_graph" / "final_go_live_decision_report.json",
        PROJECT / "system_review_graph" / "current_external_gate_research.json",
        PROJECT / "system_review_graph" / "external_validation_requirements_report.json",
        PROJECT / "system_review_graph" / "external_validation_evidence_requirements.json",
        PROJECT / "system_review_graph" / "go_live_input_templates.json",
        PROJECT / "system_review_graph" / "go_live_input_readiness_report.json",
        PROJECT / "system_review_graph" / "production_ai_copilot_manifest.json",
        PROJECT / "system_review_graph" / "production_ai_output_contracts.json",
        PROJECT / "system_review_graph" / "production_ai_safety_checks.json",
        PROJECT / "system_review_graph" / "production_country_source_engine_manifest.json",
        PROJECT / "system_review_graph" / "production_country_packs.json",
        PROJECT / "system_review_graph" / "production_source_lifecycle.json",
        PROJECT / "system_review_graph" / "production_source_snapshot_history.json",
        PROJECT / "system_review_graph" / "production_source_refresh_audit_events.json",
        PROJECT / "system_review_graph" / "production_data_model_manifest.json",
        PROJECT / "system_review_graph" / "production_data_model_seed.json",
        PROJECT / "system_review_graph" / "production_persistence_snapshot.json",
        PROJECT / "system_review_graph" / "production_persistence_row_counts.json",
        PROJECT / "system_review_graph" / "production_domain.sqlite",
        PROJECT / "system_review_graph" / "production_decision_scoring_manifest.json",
        PROJECT / "system_review_graph" / "production_decision_score_records.json",
        PROJECT / "system_review_graph" / "production_score_cap_policy.json",
        PROJECT / "system_review_graph" / "production_market_intelligence_manifest.json",
        PROJECT / "system_review_graph" / "production_market_signals.json",
        PROJECT / "system_review_graph" / "production_market_dataset_connectors.json",
        PROJECT / "system_review_graph" / "production_market_readiness_evidence_room_manifest.json",
        PROJECT / "system_review_graph" / "production_market_readiness_evidence_work_orders.json",
        PROJECT / "system_review_graph" / "production_market_readiness_reviewer_brief_cards.json",
        PROJECT / "system_review_graph" / "production_market_readiness_gate_status_matrix.json",
        PROJECT / "system_review_graph" / "production_market_readiness_input_ledger.json",
        PROJECT / "system_review_graph" / "production_market_readiness_input_history.json",
        PROJECT / "system_review_graph" / "production_trade_discovery_manifest.json",
        PROJECT / "system_review_graph" / "production_trade_discovery_category_map.json",
        PROJECT / "system_review_graph" / "production_trade_discovery_country_lanes.json",
        PROJECT / "system_review_graph" / "production_trade_discovery_beginner_flows.json",
        PROJECT / "system_review_graph" / "production_trade_discovery_source_registry.json",
        PROJECT / "system_review_graph" / "production_trade_discovery_requirement_audit.json",
        PROJECT / "system_review_graph" / "production_trade_data_catalog_manifest.json",
        PROJECT / "system_review_graph" / "production_trade_data_query_templates.json",
        PROJECT / "system_review_graph" / "production_trade_data_query_work_orders.json",
        PROJECT / "system_review_graph" / "production_trade_data_browse_cards.json",
        PROJECT / "system_review_graph" / "production_trade_data_ingestion_policy.json",
        PROJECT / "system_review_graph" / "production_document_intelligence_manifest.json",
        PROJECT / "system_review_graph" / "production_document_pipeline.json",
        PROJECT / "system_review_graph" / "production_document_extracted_fields.json",
        PROJECT / "system_review_graph" / "production_evidence_claim_gate_manifest.json",
        PROJECT / "system_review_graph" / "production_expert_review_network_manifest.json",
        PROJECT / "system_review_graph" / "production_reviewer_profiles.json",
        PROJECT / "system_review_graph" / "production_review_requests.json",
        PROJECT / "system_review_graph" / "production_review_finding_contracts.json",
        PROJECT / "system_review_graph" / "production_claim_gate_decisions.json",
        PROJECT / "system_review_graph" / "production_evidence_claim_mappers.json",
        PROJECT / "data" / "official_sample_documents" / "canada" / "cbsa-ci1-canada-customs-invoice.pdf",
        PROJECT / "data" / "official_sample_documents" / "canada" / "cbsa-a8a-b-cargo-control-document.pdf",
        PROJECT / "data" / "official_sample_documents" / "canada" / "cfia-5272-documentation-review-request.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-commercial-invoice-canada.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-packing-list-india-export.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-certificate-of-origin-india.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-bill-of-lading-vietnam.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-airway-bill-generic.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-product-specification-vietnam-seafood.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-lab-certificate-food.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-health-certificate-vietnam.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-purchase-order-canada-buyer.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-contract-incoterms.pdf",
        PROJECT / "data" / "parser_qa_documents" / "synthetic-inspection-report-supplier.pdf",
        PROJECT / "system_review_graph" / "production_packet_engine_manifest.json",
        PROJECT / "system_review_graph" / "production_packet_events.json",
        PROJECT / "system_review_graph" / "production_persistence_snapshot.json",
        PROJECT / "system_review_graph" / "production_persistence_row_counts.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "starter_packet.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "market_research_packet.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "buyer_ready_packet.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "supplier_request_packet.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "broker_review_packet.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "operator_packet.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "executive_decision_packet.json",
        PROJECT / "system_review_graph" / "production_packet_views" / "packet-frozen-tuna-canada-001" / "blocked_claims_packet.json",
        PROJECT / "system_review_graph" / "production_redevelopment_plan.json",
        PROJECT / "system_review_graph" / "production_research_anchors.json",
        PROJECT / "system_review_graph" / "production_reports_engine_manifest.json",
        PROJECT / "system_review_graph" / "production_report_catalog.json",
        PROJECT / "system_review_graph" / "production_report_exports.json",
        PROJECT / "system_review_graph" / "production_report_citations.json",
        PROJECT / "system_review_graph" / "production_portal_workflow_manifest.json",
        PROJECT / "system_review_graph" / "production_portal_route_matrix.json",
        PROJECT / "system_review_graph" / "production_portal_ux_checks.json",
        PROJECT / "system_review_graph" / "production_portal_gate_controls.json",
        PROJECT / "system_review_graph" / "production_enterprise_api_manifest.json",
        PROJECT / "system_review_graph" / "production_enterprise_api_contracts.json",
        PROJECT / "system_review_graph" / "production_enterprise_rbac_policy.json",
        PROJECT / "system_review_graph" / "production_enterprise_workspace_controls.json",
        PROJECT / "system_review_graph" / "production_enterprise_webhook_policy.json",
        PROJECT / "system_review_graph" / "production_enterprise_audit_export_policy.json",
        PROJECT / "system_review_graph" / "production_enterprise_research_references.json",
        PROJECT / "system_review_graph" / "production_payment_monetization_manifest.json",
        PROJECT / "system_review_graph" / "production_pricing_tiers.json",
        PROJECT / "system_review_graph" / "production_paid_scope_policy.json",
        PROJECT / "system_review_graph" / "production_checkout_gate_controls.json",
        PROJECT / "system_review_graph" / "production_payment_webhook_controls.json",
        PROJECT / "system_review_graph" / "production_payment_research_references.json",
        PROJECT / "system_review_graph" / "production_security_privacy_reliability_manifest.json",
        PROJECT / "system_review_graph" / "production_trust_control_matrix.json",
        PROJECT / "system_review_graph" / "production_vendor_register.json",
        PROJECT / "system_review_graph" / "production_backup_restore_drill.json",
        PROJECT / "system_review_graph" / "production_incident_runbooks.json",
        PROJECT / "system_review_graph" / "production_trust_research_references.json",
        PROJECT / "system_review_graph" / "production_launch_control_plane_manifest.json",
        PROJECT / "system_review_graph" / "production_launch_gate_states.json",
        PROJECT / "system_review_graph" / "production_launch_scope_matrix.json",
        PROJECT / "system_review_graph" / "production_public_launch_decision.json",
        PROJECT / "system_review_graph" / "reviewer_wave_execution_plan.json",
        PROJECT / "system_review_graph" / "private_beta_smoke_test_plan.json",
        PROJECT / "system_review_graph" / "external_review_findings_report.json",
        PROJECT / "system_review_graph" / "external_review_blocker_ledger.jsonl",
        PROJECT / "system_review_graph" / "ai_assisted_external_review_plan.json",
        PROJECT / "system_review_graph" / "ai_assisted_external_review_findings_report.json",
        PROJECT / "system_review_graph" / "research_execution_runs.json",
        PROJECT / "system_review_graph" / "expert_review_work_orders.json",
        PROJECT / "system_review_graph" / "team_workspace_activity.json",
        PROJECT / "system_review_graph" / "launch_operations_events.json",
        PROJECT / "START_HERE.md",
        PROJECT / "WHAT_WE_ARE_BUILDING.md",
        PROJECT / "CURRENT_SLICE_VS_TARGET_PRODUCT.md",
        PROJECT / "FINAL_GO_LIVE_HANDOFF.md",
        PROJECT / "system_review_graph" / "generated_reports" / "data_intake_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "generated_reports" / "missing_evidence_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "generated_reports" / "starter_checklist_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "generated_reports" / "chatgpt_safe_summary_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "generated_reports" / "broker_packet_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "generated_reports" / "business_decision_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "source_refresh_runs.json",
        PROJECT / "system_review_graph" / "source_refresh_report_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "expert_review_packet_packet-frozen-tuna-canada-001.md",
        PROJECT / "output" / "pdf" / "external_validation_requirements.pdf",
        PROJECT / "output" / "pdf" / "external_validation_reviewer_brief.pdf",
        PROJECT / "output" / "pdf" / "go_live_input_requests.pdf",
        PROJECT / "investor" / "vc_pitch_deck.md",
        PROJECT / "investor" / "one_pager.md",
        PROJECT / "investor" / "demo_script.md",
        PROJECT / "investor" / "diligence_room_index.md",
        PROJECT / "board" / "board_go_live_brief.md",
        PROJECT / "board" / "expert_review_packet.md",
        PROJECT / "board" / "launch_control_checklist.md",
        PROJECT / "board" / "financial_operating_model.md",
        PROJECT / "migrations" / "0001_product_runtime.sql",
        PROJECT / "migrations" / "0002_production_domain_model.sql",
        PROJECT / "Dockerfile",
        PROJECT / "compose.yaml",
        PROJECT / ".env.example",
        PROJECT / "docs" / "SECURITY_PRIVACY.md",
        PROJECT / "docs" / "DEPLOYMENT.md",
        PROJECT / "handoffs" / "product_completion_handoff.md",
        PROJECT / "external_review_findings" / "README.md",
        PROJECT / "external_review_findings" / "UX_PRODUCT_REVIEW.md",
        PROJECT / "external_review_findings" / "SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        PROJECT / "external_review_findings" / "PRIVACY_LEGAL_REVIEW.md",
        PROJECT / "external_review_findings" / "AI_SAFETY_REVIEW.md",
        PROJECT / "external_review_findings" / "TRADE_BOUNDARY_REVIEW.md",
        PROJECT / "external_review_findings" / "FREIGHT_LOGISTICS_REVIEW.md",
        PROJECT / "external_review_findings" / "REPORT_LANGUAGE_REVIEW.md",
        PROJECT / "external_review_findings" / "DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        PROJECT / "external_review_findings" / "BILLING_PAYMENT_REVIEW.md",
        PROJECT / "external_review_findings" / "EXTERNAL_REVIEW_SUMMARY.json",
        PROJECT / "reviewer_packets" / "README.md",
        PROJECT / "reviewer_packets" / "WAVE_1_UX_PRODUCT_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_1_PRIVACY_LEGAL_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_1_AI_SAFETY_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_2_TRADE_BOUNDARY_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_2_FREIGHT_LOGISTICS_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_2_REPORT_LANGUAGE_REVIEW.md",
        PROJECT / "reviewer_packets" / "WAVE_3_BILLING_PAYMENT_REVIEW.md",
        PROJECT / "ai_assisted_review" / "README.md",
        PROJECT / "ai_assisted_review" / "AI_ASSISTED_REVIEW_SUMMARY.md",
        PROJECT / "ai_assisted_review" / "WEB_RESEARCH_SOURCE_LOG.md",
        PROJECT / "ai_assisted_review" / "simulated_findings" / ".gitkeep",
        PROJECT / "ai_assisted_review" / "simulated_findings" / "WAVE_1_UX_PRODUCT_REVIEW.json",
        PROJECT / "ai_assisted_review" / "simulated_findings" / "WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.json",
        PROJECT / "ai_assisted_review" / "simulated_findings" / "WAVE_1_PRIVACY_LEGAL_REVIEW.json",
        PROJECT / "ai_assisted_review" / "simulated_findings" / "WAVE_1_AI_SAFETY_REVIEW.json",
        PROJECT / "ai_assisted_review" / "simulated_findings" / "WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.json",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_1_UX_PRODUCT_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_1_PRIVACY_LEGAL_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_1_AI_SAFETY_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_2_TRADE_BOUNDARY_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_2_FREIGHT_LOGISTICS_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_2_REPORT_LANGUAGE_REVIEW.md",
        PROJECT / "ai_assisted_review" / "role_prompts" / "WAVE_3_BILLING_PAYMENT_REVIEW.md",
    ]
    missing = [path.relative_to(ROOT) for path in required if not path.exists()]
    if missing:
        print("Product project check: FAIL")
        for path in missing:
            print(f"missing: {path}")
        return 1

    commands = [
        ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        ["python3", "scripts/run_readiness.py"],
        ["python3", "scripts/run_external_gates.py"],
        ["python3", "scripts/plan_continuation.py"],
        ["python3", "scripts/build_vc_pitch_packet.py"],
        ["python3", "scripts/build_board_go_live_packet.py"],
        ["python3", "scripts/run_operator_workflow.py"],
        ["python3", "scripts/run_customer_workflow.py"],
        ["python3", "scripts/run_policy_intelligence.py"],
        ["python3", "scripts/run_completion_platform.py"],
        ["python3", "scripts/run_product_operations.py"],
        ["python3", "scripts/run_final_go_live_review.py"],
        ["python3", "scripts/run_external_validation_requirements.py"],
        ["python3", "scripts/run_production_redevelopment.py"],
        ["python3", "scripts/run_production_data_model.py"],
        ["python3", "scripts/run_production_packet_engine.py"],
        ["python3", "scripts/run_production_country_source_engine.py"],
        ["python3", "scripts/run_production_trade_discovery_engine.py"],
        ["python3", "scripts/run_production_trade_data_catalog_engine.py"],
        ["python3", "scripts/run_production_market_intelligence_engine.py"],
        ["python3", "scripts/run_production_document_intelligence_engine.py"],
        ["python3", "scripts/run_production_evidence_claim_gate_engine.py"],
        ["python3", "scripts/run_production_decision_scoring_engine.py"],
        ["python3", "scripts/run_production_ai_copilot_engine.py"],
        ["python3", "scripts/run_production_expert_review_network.py"],
        ["python3", "scripts/run_production_reports_engine.py"],
        ["python3", "scripts/run_production_persistence.py"],
        ["python3", "scripts/run_production_portal_workflow_engine.py"],
        ["python3", "scripts/run_production_enterprise_api_platform.py"],
        ["python3", "scripts/run_production_payment_monetization_engine.py"],
        ["python3", "scripts/run_production_security_privacy_reliability_engine.py"],
        ["python3", "scripts/run_production_launch_control_plane.py"],
        ["python3", "scripts/run_production_market_readiness_evidence_room.py"],
        ["python3", "scripts/build_external_review_packet.py"],
        ["python3", "scripts/export_operator_dashboard.py"],
        ["python3", "scripts/audit_external_package.py", "--root", "."],
        ["python3", "scripts/check_product.py"],
    ]
    for command in commands:
        result = _run(command, PROJECT)
        if result.returncode != 0:
            print("Product project check: FAIL")
            print(f"command: {' '.join(command)}")
            print(result.stdout)
            print(result.stderr)
            return result.returncode

    blocker_result = _run(
        [
            "python3",
            "scripts/blocker_ledger.py",
            "validate",
            "--input",
            "product_projects/importer-source-readiness-copilot/system_review_graph/blockers.jsonl",
            "--out",
            str(Path(tempfile.gettempdir()) / "ados-product-project-blockers.json"),
        ],
        ROOT,
    )
    if blocker_result.returncode != 0:
        print("Product project check: FAIL")
        print(blocker_result.stdout)
        print(blocker_result.stderr)
        return blocker_result.returncode
    external_review_blocker_result = _run(
        [
            "python3",
            "scripts/blocker_ledger.py",
            "validate",
            "--input",
            "product_projects/importer-source-readiness-copilot/system_review_graph/external_review_blocker_ledger.jsonl",
            "--out",
            str(Path(tempfile.gettempdir()) / "ados-product-project-external-review-blockers.json"),
        ],
        ROOT,
    )
    if external_review_blocker_result.returncode != 0:
        print("Product project check: FAIL")
        print(external_review_blocker_result.stdout)
        print(external_review_blocker_result.stderr)
        return external_review_blocker_result.returncode

    report = json.loads(
        (PROJECT / "system_review_graph" / "readiness_report.json").read_text(encoding="utf-8")
    )
    external = json.loads(
        (PROJECT / "system_review_graph" / "external_gate_report.json").read_text(encoding="utf-8")
    )
    continuation = json.loads(
        (PROJECT / "system_review_graph" / "continuation_plan.json").read_text(encoding="utf-8")
    )
    vc_pitch = json.loads(
        (PROJECT / "system_review_graph" / "vc_pitch_readiness_report.json").read_text(encoding="utf-8")
    )
    board = json.loads(
        (PROJECT / "system_review_graph" / "board_go_live_readiness_report.json").read_text(encoding="utf-8")
    )
    workflow = json.loads(
        (PROJECT / "system_review_graph" / "operator_workflow_report.json").read_text(encoding="utf-8")
    )
    customer = json.loads(
        (PROJECT / "system_review_graph" / "customer_readiness_report.json").read_text(encoding="utf-8")
    )
    evidence_ledger = json.loads(
        (PROJECT / "system_review_graph" / "evidence_ledger.json").read_text(encoding="utf-8")
    )
    runtime = json.loads(
        (PROJECT / "system_review_graph" / "product_runtime_state.json").read_text(encoding="utf-8")
    )
    auth_rbac = json.loads(
        (PROJECT / "system_review_graph" / "auth_rbac_matrix.json").read_text(encoding="utf-8")
    )
    claims_gate = json.loads(
        (PROJECT / "system_review_graph" / "claims_gate_matrix.json").read_text(encoding="utf-8")
    )
    review_requests = json.loads(
        (PROJECT / "system_review_graph" / "review_requests.json").read_text(encoding="utf-8")
    )
    audit_events = json.loads(
        (PROJECT / "system_review_graph" / "audit_events.json").read_text(encoding="utf-8")
    )
    deployment = json.loads(
        (PROJECT / "system_review_graph" / "deployment_readiness_report.json").read_text(encoding="utf-8")
    )
    ai_data_policy = json.loads(
        (PROJECT / "system_review_graph" / "ai_data_policy.json").read_text(encoding="utf-8")
    )
    ai_model_router = json.loads(
        (PROJECT / "system_review_graph" / "ai_model_router.json").read_text(encoding="utf-8")
    )
    redaction_pipeline = json.loads(
        (PROJECT / "system_review_graph" / "redaction_pipeline.json").read_text(encoding="utf-8")
    )
    manual_no_ai_workflow = json.loads(
        (PROJECT / "system_review_graph" / "manual_no_ai_workflow.json").read_text(encoding="utf-8")
    )
    requirements_traceability = json.loads(
        (PROJECT / "system_review_graph" / "requirements_traceability_matrix.json").read_text(encoding="utf-8")
    )
    public_trade = json.loads(
        (PROJECT / "system_review_graph" / "public_trade_readiness_manifest.json").read_text(encoding="utf-8")
    )
    exporter_mode = json.loads(
        (PROJECT / "system_review_graph" / "exporter_mode_requirements.json").read_text(encoding="utf-8")
    )
    public_reports = json.loads(
        (PROJECT / "system_review_graph" / "public_report_types.json").read_text(encoding="utf-8")
    )
    public_upload_policy = json.loads(
        (PROJECT / "system_review_graph" / "public_upload_policy.json").read_text(encoding="utf-8")
    )
    policy_monitor = json.loads(
        (PROJECT / "system_review_graph" / "intelligence_hub_policy_monitor.json").read_text(encoding="utf-8")
    )
    policy_snapshots = json.loads(
        (PROJECT / "system_review_graph" / "policy_source_snapshots.json").read_text(encoding="utf-8")
    )
    policy_impact = json.loads(
        (PROJECT / "system_review_graph" / "policy_change_impact_report.json").read_text(encoding="utf-8")
    )
    completion = json.loads(
        (PROJECT / "system_review_graph" / "completion_platform_manifest.json").read_text(encoding="utf-8")
    )
    country_coverage = json.loads(
        (PROJECT / "system_review_graph" / "country_coverage_report.json").read_text(encoding="utf-8")
    )
    opportunity_scanner = json.loads(
        (PROJECT / "system_review_graph" / "opportunity_scanner_report.json").read_text(encoding="utf-8")
    )
    business_logic = json.loads(
        (PROJECT / "system_review_graph" / "business_logic_phase_report.json").read_text(encoding="utf-8")
    )
    business_phase_completion = json.loads(
        (PROJECT / "system_review_graph" / "business_phase_completion_report.json").read_text(encoding="utf-8")
    )
    business_core_doc = (PROJECT / "docs" / "BUSINESS_CORE_LOGIC_CURRENT_STATE.md").read_text(encoding="utf-8")
    functional_doc = (PROJECT / "docs" / "FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md").read_text(encoding="utf-8")
    non_functional_doc = (PROJECT / "docs" / "NON_FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md").read_text(encoding="utf-8")
    transport_readiness = json.loads(
        (PROJECT / "system_review_graph" / "transport_readiness_report.json").read_text(encoding="utf-8")
    )
    billing_controls = json.loads(
        (PROJECT / "system_review_graph" / "billing_credit_controls.json").read_text(encoding="utf-8")
    )
    agent_api = json.loads(
        (PROJECT / "system_review_graph" / "agent_api_manifest.json").read_text(encoding="utf-8")
    )
    traffic_pages = json.loads(
        (PROJECT / "system_review_graph" / "traffic_pages_manifest.json").read_text(encoding="utf-8")
    )
    research_execution = json.loads(
        (PROJECT / "system_review_graph" / "research_execution_plan.json").read_text(encoding="utf-8")
    )
    team_workspace = json.loads(
        (PROJECT / "system_review_graph" / "team_workspace_report.json").read_text(encoding="utf-8")
    )
    expert_network = json.loads(
        (PROJECT / "system_review_graph" / "expert_network_report.json").read_text(encoding="utf-8")
    )
    billing_usage = json.loads(
        (PROJECT / "system_review_graph" / "billing_usage_ledger.json").read_text(encoding="utf-8")
    )
    agent_gateway = json.loads(
        (PROJECT / "system_review_graph" / "agent_api_gateway_contract.json").read_text(encoding="utf-8")
    )
    launch_operations = json.loads(
        (PROJECT / "system_review_graph" / "launch_operations_report.json").read_text(encoding="utf-8")
    )
    all_stages = json.loads(
        (PROJECT / "system_review_graph" / "all_stage_readiness_report.json").read_text(encoding="utf-8")
    )
    product_operations = json.loads(
        (PROJECT / "system_review_graph" / "product_operations_report.json").read_text(encoding="utf-8")
    )
    final_go_live = json.loads(
        (PROJECT / "system_review_graph" / "final_go_live_decision_report.json").read_text(encoding="utf-8")
    )
    current_sources = json.loads(
        (PROJECT / "system_review_graph" / "current_external_gate_research.json").read_text(encoding="utf-8")
    )
    external_validation = json.loads(
        (PROJECT / "system_review_graph" / "external_validation_requirements_report.json").read_text(encoding="utf-8")
    )
    external_validation_evidence = json.loads(
        (PROJECT / "system_review_graph" / "external_validation_evidence_requirements.json").read_text(encoding="utf-8")
    )
    go_live_input_templates = json.loads(
        (PROJECT / "system_review_graph" / "go_live_input_templates.json").read_text(encoding="utf-8")
    )
    production_redevelopment = json.loads(
        (PROJECT / "system_review_graph" / "production_redevelopment_plan.json").read_text(encoding="utf-8")
    )
    production_research = json.loads(
        (PROJECT / "system_review_graph" / "production_research_anchors.json").read_text(encoding="utf-8")
    )
    production_data_model = json.loads(
        (PROJECT / "system_review_graph" / "production_data_model_manifest.json").read_text(encoding="utf-8")
    )
    production_packet_engine = json.loads(
        (PROJECT / "system_review_graph" / "production_packet_engine_manifest.json").read_text(encoding="utf-8")
    )
    production_persistence = json.loads(
        (PROJECT / "system_review_graph" / "production_persistence_snapshot.json").read_text(encoding="utf-8")
    )
    production_country_source_engine = json.loads(
        (PROJECT / "system_review_graph" / "production_country_source_engine_manifest.json").read_text(encoding="utf-8")
    )
    production_trade_discovery = json.loads(
        (PROJECT / "system_review_graph" / "production_trade_discovery_manifest.json").read_text(encoding="utf-8")
    )
    production_trade_data_catalog = json.loads(
        (PROJECT / "system_review_graph" / "production_trade_data_catalog_manifest.json").read_text(encoding="utf-8")
    )
    production_market_intelligence = json.loads(
        (PROJECT / "system_review_graph" / "production_market_intelligence_manifest.json").read_text(encoding="utf-8")
    )
    production_market_readiness = json.loads(
        (PROJECT / "system_review_graph" / "production_market_readiness_evidence_room_manifest.json").read_text(encoding="utf-8")
    )
    production_market_readiness_input_ledger = json.loads(
        (PROJECT / "system_review_graph" / "production_market_readiness_input_ledger.json").read_text(encoding="utf-8")
    )
    production_market_readiness_input_history = json.loads(
        (PROJECT / "system_review_graph" / "production_market_readiness_input_history.json").read_text(encoding="utf-8")
    )
    production_document_intelligence = json.loads(
        (PROJECT / "system_review_graph" / "production_document_intelligence_manifest.json").read_text(encoding="utf-8")
    )
    production_evidence_claim_gate = json.loads(
        (PROJECT / "system_review_graph" / "production_evidence_claim_gate_manifest.json").read_text(encoding="utf-8")
    )
    production_decision_scoring = json.loads(
        (PROJECT / "system_review_graph" / "production_decision_scoring_manifest.json").read_text(encoding="utf-8")
    )
    production_ai_copilot = json.loads(
        (PROJECT / "system_review_graph" / "production_ai_copilot_manifest.json").read_text(encoding="utf-8")
    )
    production_expert_review = json.loads(
        (PROJECT / "system_review_graph" / "production_expert_review_network_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    production_reports = json.loads(
        (PROJECT / "system_review_graph" / "production_reports_engine_manifest.json").read_text(encoding="utf-8")
    )
    production_portals = json.loads(
        (PROJECT / "system_review_graph" / "production_portal_workflow_manifest.json").read_text(encoding="utf-8")
    )
    production_enterprise = json.loads(
        (PROJECT / "system_review_graph" / "production_enterprise_api_manifest.json").read_text(encoding="utf-8")
    )
    production_payments = json.loads(
        (PROJECT / "system_review_graph" / "production_payment_monetization_manifest.json").read_text(encoding="utf-8")
    )
    production_trust = json.loads(
        (PROJECT / "system_review_graph" / "production_security_privacy_reliability_manifest.json").read_text(encoding="utf-8")
    )
    production_launch = json.loads(
        (PROJECT / "system_review_graph" / "production_launch_control_plane_manifest.json").read_text(encoding="utf-8")
    )
    official_source_registry = json.loads(
        (PROJECT / "data" / "official_source_registry.json").read_text(encoding="utf-8")
    )
    go_live_input_readiness = json.loads(
        (PROJECT / "system_review_graph" / "go_live_input_readiness_report.json").read_text(encoding="utf-8")
    )
    reviewer_wave_plan = json.loads(
        (PROJECT / "system_review_graph" / "reviewer_wave_execution_plan.json").read_text(encoding="utf-8")
    )
    private_beta_smoke = json.loads(
        (PROJECT / "system_review_graph" / "private_beta_smoke_test_plan.json").read_text(encoding="utf-8")
    )
    external_review = json.loads(
        (PROJECT / "system_review_graph" / "external_review_findings_report.json").read_text(encoding="utf-8")
    )
    ai_assisted_review = json.loads(
        (PROJECT / "system_review_graph" / "ai_assisted_external_review_plan.json").read_text(encoding="utf-8")
    )
    ai_assisted_findings = json.loads(
        (PROJECT / "system_review_graph" / "ai_assisted_external_review_findings_report.json").read_text(
            encoding="utf-8"
        )
    )
    external_review_summary = json.loads(
        (PROJECT / "external_review_findings" / "EXTERNAL_REVIEW_SUMMARY.json").read_text(encoding="utf-8")
    )
    external_review_blockers = [
        json.loads(line)
        for line in (PROJECT / "system_review_graph" / "external_review_blocker_ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    research_runs = json.loads(
        (PROJECT / "system_review_graph" / "research_execution_runs.json").read_text(encoding="utf-8")
    )
    expert_work_orders = json.loads(
        (PROJECT / "system_review_graph" / "expert_review_work_orders.json").read_text(encoding="utf-8")
    )
    team_activity = json.loads(
        (PROJECT / "system_review_graph" / "team_workspace_activity.json").read_text(encoding="utf-8")
    )
    launch_events = json.loads(
        (PROJECT / "system_review_graph" / "launch_operations_events.json").read_text(encoding="utf-8")
    )
    screenshot_manifest = json.loads(
        (PROJECT / "system_review_graph" / "operator_screenshot_manifest.json").read_text(encoding="utf-8")
    )
    if report.get("status") != "ready_with_external_gates" or report.get("blocker_count") != 9:
        print("Product project check: FAIL")
        print("unexpected product readiness report")
        return 1
    if external.get("status") != "ready_with_external_gates" or external.get("blocker_count", 0) < 10:
        print("Product project check: FAIL")
        print("unexpected external gate report")
        return 1
    if (
        continuation.get("status") != "startup_in_progress"
        or continuation.get("must_continue") is not True
        or continuation.get("lane_count", 0) < 5
    ):
        print("Product project check: FAIL")
        print("unexpected continuation plan")
        return 1
    closed_claims = set(continuation.get("closed_claims", []))
    required_closed_claims = {"fully_operational", "launch_ready", "commercially_ready"}
    if not required_closed_claims.issubset(closed_claims):
        print("Product project check: FAIL")
        print("continuation plan does not close premature completion claims")
        return 1
    if vc_pitch.get("status") != "vc_pitch_ready_with_diligence_gates":
        print("Product project check: FAIL")
        print("unexpected VC pitch readiness report")
        return 1
    if len(vc_pitch.get("diligence_lanes", [])) < 6 or vc_pitch.get("evidence_ready") is not True:
        print("Product project check: FAIL")
        print("VC pitch report missing diligence lanes or investor evidence")
        return 1
    if board.get("status") != "board_go_live_candidate_with_human_approval_gates":
        print("Product project check: FAIL")
        print("unexpected board go-live readiness report")
        return 1
    if board.get("primary_market") != "Canada" or board.get("human_approval_gate_count", 0) < 10:
        print("Product project check: FAIL")
        print("board go-live report missing Canada focus or approval gates")
        return 1
    for key in ("canadian_tools_ready", "simulated_expert_reviews_ready", "launch_controls_ready"):
        if board.get(key) is not True:
            print("Product project check: FAIL")
            print(f"board go-live report missing {key}")
            return 1
    if (
        workflow.get("status") != "operator_workflow_ready_internal"
        or workflow.get("operator_can_use_now") is not True
        or workflow.get("work_queue_count", 0) < 20
    ):
        print("Product project check: FAIL")
        print("operator workflow report missing internal-ready work queue")
        return 1
    workflow_types = set(workflow.get("work_queue_counts_by_type", {}))
    expected_workflow_types = {
        "source_card_review",
        "external_evidence_gate",
        "continuation_lane",
        "human_approval_gate",
    }
    if not expected_workflow_types.issubset(workflow_types):
        print("Product project check: FAIL")
        print("operator workflow report missing required queue row types")
        return 1
    if screenshot_manifest.get("status") != "screenshots_ready":
        print("Product project check: FAIL")
        print("operator screenshot manifest should have screenshots_ready status")
        return 1
    if screenshot_manifest.get("screenshot_count", 0) < 1:
        print("Product project check: FAIL")
        print("operator screenshot manifest should include at least one generated screenshot")
        return 1
    dashboard_html = (PROJECT / "system_review_graph" / "operator_dashboard.html").read_text(encoding="utf-8")
    if "Operator Screenshots" not in dashboard_html or "operator_screenshots/operator-dashboard.png" not in dashboard_html:
        print("Product project check: FAIL")
        print("operator dashboard missing screenshot gallery")
        return 1
    if "Operator Work Queue" not in dashboard_html or "Canada Tools" not in dashboard_html:
        print("Product project check: FAIL")
        print("operator dashboard missing work queue")
        return 1
    if "Customer Source Packet Workflow" not in dashboard_html:
        print("Product project check: FAIL")
        print("operator dashboard missing customer source-packet workflow")
        return 1
    if "Path To Private Beta" not in dashboard_html or "Internal logic ready - external claims blocked" not in dashboard_html:
        print("Product project check: FAIL")
        print("operator dashboard missing guided customer workflow status")
        return 1
    if customer.get("status") != "customer_workflow_ready_internal":
        print("Product project check: FAIL")
        print("customer source-packet workflow is not internal ready")
        return 1
    if customer.get("display_status") != "Internal logic ready - external claims blocked":
        print("Product project check: FAIL")
        print("customer source-packet workflow missing safe display status")
        return 1
    if customer.get("operator_display_status") != "Operator workbench usable for internal review":
        print("Product project check: FAIL")
        print("customer source-packet workflow missing operator display status")
        return 1
    if customer.get("customer_stage_status") != "Customer packet prototype active - real customer use not enabled":
        print("Product project check: FAIL")
        print("customer source-packet workflow missing prototype stage status")
        return 1
    if customer.get("private_beta_status") != "blocked":
        print("Product project check: FAIL")
        print("customer source-packet workflow should keep private beta blocked")
        return 1
    if customer.get("packet_count", 0) < 1 or customer.get("blocker_count", 0) < 1:
        print("Product project check: FAIL")
        print("customer source-packet workflow missing packets or blockers")
        return 1
    if len(customer.get("blocker_groups", [])) < 3 or not customer.get("ai_review_runs"):
        print("Product project check: FAIL")
        print("customer source-packet workflow missing grouped blockers or AI review runs")
        return 1
    packet = customer.get("packets", [{}])[0]
    if not str(packet.get("customer_visible_status_label") or "").startswith("Blocked -"):
        print("Product project check: FAIL")
        print("customer source-packet workflow missing customer-readable packet status")
        return 1
    evidence_summary = packet.get("evidence_summary", {})
    if evidence_summary.get("attached", 0) < 3 or evidence_summary.get("missing", 0) < 4:
        print("Product project check: FAIL")
        print("customer source-packet workflow missing evidence quality summary")
        return 1
    if evidence_summary.get("ai_allowed", 0) < 1:
        print("Product project check: FAIL")
        print("customer source-packet workflow missing AI permission summary")
        return 1
    group_titles = {row.get("title") for row in packet.get("blocker_groups", [])}
    required_groups = {"Compliance Review", "Source Rights / Contract", "Buyer Validation"}
    if not required_groups.issubset(group_titles):
        print("Product project check: FAIL")
        print("customer source-packet workflow missing required grouped blockers")
        return 1
    blocked_claims = set(customer.get("blocked_claims", []))
    required_customer_blocked_claims = {
        "tariff_confirmed",
        "cfia_compliant",
        "supplier_recommended",
        "buyer_validated",
        "ready_to_import",
    }
    if not required_customer_blocked_claims.issubset(blocked_claims):
        print("Product project check: FAIL")
        print("customer source-packet workflow opened unsafe claims")
        return 1
    if evidence_ledger.get("status") != "evidence_ledger_ready_internal" or evidence_ledger.get("evidence_count", 0) < 3:
        print("Product project check: FAIL")
        print("evidence ledger missing internal-ready evidence rows")
        return 1
    if "stale" not in evidence_ledger.get("counts_by_quality", {}):
        print("Product project check: FAIL")
        print("evidence ledger missing quality counts")
        return 1
    if not all("sensitivity_level" in row and "ai_processing_mode" in row for row in evidence_ledger.get("rows", [])):
        print("Product project check: FAIL")
        print("evidence ledger missing sensitivity or AI permission fields")
        return 1
    if runtime.get("status") != "private_beta_candidate_with_external_human_gates":
        print("Product project check: FAIL")
        print("runtime state missing private-beta candidate status")
        return 1
    if runtime.get("product") != "Trade Readiness Copilot":
        print("Product project check: FAIL")
        print("runtime state missing public Trade Readiness Copilot product name")
        return 1
    if runtime.get("internal_engine") != "Importer Source Readiness Copilot":
        print("Product project check: FAIL")
        print("runtime state missing internal engine boundary")
        return 1
    if runtime.get("public_product_surface", {}).get("status") != "public_quick_check_ready_local_with_external_gates":
        print("Product project check: FAIL")
        print("runtime state missing public quick-check surface status")
        return 1
    if len(runtime.get("users", [])) < 4 or len(runtime.get("organizations", [])) < 3:
        print("Product project check: FAIL")
        print("runtime state missing users or organizations")
        return 1
    if "/api/auth/login" not in runtime.get("api_routes", []):
        print("Product project check: FAIL")
        print("runtime state missing auth routes")
        return 1
    for route in (
        "/start",
        "/tools/export-readiness",
        "/tools/document-check",
        "/opportunities",
        "/reports/sample",
        "/pricing",
        "/billing",
        "/ai-data-policy",
        "/security",
        "/public/packets/:packetId/result",
        "/public/packets/:packetId/confirm",
        "/workspace",
        "/packets/:packetId/source-monitoring",
        "/packets/:packetId/safe-summary",
    ):
        if route not in runtime.get("ui_routes", {}).get("customer", []):
            print("Product project check: FAIL")
            print(f"runtime state missing public UI route {route}")
            return 1
    for route in (
        "/api/public/starter",
        "/api/public/quick-check",
        "/api/public/packets/:id/confirm",
        "/api/public/packets/:id/chatgpt-safe-summary",
        "/api/public/packets/:id/reports/starter.pdf",
        "/api/public/packets/:id/reports/buyer.pdf",
        "/api/public/packets/:id/reports/broker.pdf",
        "/api/public/packets/:id/reports/missing.pdf",
        "/api/public/packets/:id/delete-files",
        "/api/opportunities",
        "/api/country-coverage",
        "/api/billing/controls",
        "/api/agent-api",
        "/api/traffic-pages",
        "/api/transport-readiness",
        "/api/product-operations/report",
        "/api/product-operations/run",
        "/api/agent-tools/:tool",
    ):
        if route not in runtime.get("api_routes", []):
            print("Product project check: FAIL")
            print(f"runtime state missing public API route {route}")
            return 1
    if "/api/orgs/current/ai-policy" not in runtime.get("api_routes", []):
        print("Product project check: FAIL")
        print("runtime state missing AI policy routes")
        return 1
    if "/api/evidence/:evidenceId/ai-permission" not in runtime.get("api_routes", []):
        print("Product project check: FAIL")
        print("runtime state missing evidence AI permission route")
        return 1
    if "/settings/ai-data-policy" not in runtime.get("ui_routes", {}).get("customer", []):
        print("Product project check: FAIL")
        print("runtime state missing AI policy settings route")
        return 1
    if "/review/:reviewToken" not in runtime.get("ui_routes", {}).get("expert", []):
        print("Product project check: FAIL")
        print("runtime state missing expert review routes")
        return 1
    if auth_rbac.get("security_controls", {}).get("rbac") is None:
        print("Product project check: FAIL")
        print("auth/RBAC matrix missing RBAC control")
        return 1
    if claims_gate.get("blocked_by_default") is not True or len(claims_gate.get("claims", [])) < 6:
        print("Product project check: FAIL")
        print("claims gate matrix should keep claims blocked by default")
        return 1
    if not review_requests or review_requests[0].get("token") != "review-token-packet-frozen-tuna-canada-001":
        print("Product project check: FAIL")
        print("review requests missing scoped frozen tuna token")
        return 1
    if len(audit_events.get("events", [])) < 3:
        print("Product project check: FAIL")
        print("audit events missing packet, AI, or report export events")
        return 1
    if deployment.get("status") != "deployable_local_stack_ready_with_external_hosting_gates":
        print("Product project check: FAIL")
        print("deployment readiness missing hostable local stack status")
        return 1
    if ai_data_policy.get("status") != "ai_data_policy_ready" or len(ai_data_policy.get("policies", [])) < 2:
        print("Product project check: FAIL")
        print("AI data policy missing organization policies")
        return 1
    if ai_model_router.get("status") != "ai_model_router_ready" or not ai_model_router.get("route_decisions"):
        print("Product project check: FAIL")
        print("AI model router missing route decisions")
        return 1
    if redaction_pipeline.get("status") != "redaction_pipeline_ready" or "emails" not in redaction_pipeline.get("categories", []):
        print("Product project check: FAIL")
        print("redaction pipeline missing categories")
        return 1
    if manual_no_ai_workflow.get("status") != "manual_no_ai_workflow_ready":
        print("Product project check: FAIL")
        print("manual no-AI workflow is not ready")
        return 1
    requirement_ids = {row.get("id") for row in requirements_traceability.get("requirements", [])}
    if len(requirements_traceability.get("requirements", [])) < 44:
        print("Product project check: FAIL")
        print("requirements traceability matrix is incomplete")
        return 1
    for requirement_id in (
        "REQ-PUBLIC-01",
        "REQ-EXPORT-01",
        "REQ-EXPORT-09",
        "REQ-STARTER-01",
        "REQ-PDF-01",
        "REQ-CONFIRM-01",
        "REQ-IH-01",
        "REQ-OPPORTUNITY-01",
        "REQ-COVERAGE-01",
        "REQ-TRANSPORT-01",
        "REQ-BILLING-01",
        "REQ-AGENT-01",
        "REQ-TRAFFIC-01",
        "REQ-STAGE-01",
        "REQ-RESEARCH-01",
        "REQ-EXPERT-01",
        "REQ-TEAM-01",
        "REQ-API-GATEWAY-01",
        "REQ-LAUNCH-OPS-01",
        "REQ-OPERATIONS-01",
    ):
        if requirement_id not in requirement_ids:
            print("Product project check: FAIL")
            print(f"requirements traceability matrix missing {requirement_id}")
            return 1
    if public_trade.get("status") != "public_trade_readiness_ready_local":
        print("Product project check: FAIL")
        print("public trade readiness manifest is missing or stale")
        return 1
    if public_trade.get("public_product") != "Trade Readiness Copilot":
        print("Product project check: FAIL")
        print("public trade readiness manifest has wrong product name")
        return 1
    if "/api/public/starter" not in public_trade.get("routes", {}).get("api", []):
        print("Product project check: FAIL")
        print("public trade readiness manifest missing starter API")
        return 1
    for route in (
        "/opportunities",
        "/country-coverage",
        "/transport-readiness",
        "/reports/sample",
        "/pricing",
        "/billing/usage",
        "/agent-api",
        "/stages",
        "/research-plan",
        "/expert-network",
        "/team-workspace",
        "/launch-operations",
        "/security",
        "/tools/document-check",
    ):
        if route not in public_trade.get("routes", {}).get("ui", []):
            print("Product project check: FAIL")
            print(f"public trade readiness manifest missing {route}")
            return 1
    for route in (
        "/api/opportunities",
        "/api/country-coverage",
        "/api/billing/controls",
        "/api/billing/usage",
        "/api/agent-api",
        "/api/agent-api/gateway",
        "/api/traffic-pages",
        "/api/transport-readiness",
        "/api/stages",
        "/api/research-plan",
        "/api/expert-network",
        "/api/team-workspace",
        "/api/launch-operations",
    ):
        if route not in public_trade.get("routes", {}).get("api", []):
            print("Product project check: FAIL")
            print(f"public trade readiness manifest missing {route}")
            return 1
    if "beginner_no_documents" not in public_trade.get("modes", {}):
        print("Product project check: FAIL")
        print("public trade readiness manifest missing beginner mode")
        return 1
    if public_trade.get("intelligence_hub_policy_monitor", {}).get("status") != "database_style_contract_ready":
        print("Product project check: FAIL")
        print("public trade readiness manifest missing policy monitor contract")
        return 1
    if "completion_stage_contracts" not in public_trade:
        print("Product project check: FAIL")
        print("public trade readiness manifest missing completion-stage contracts")
        return 1
    if exporter_mode.get("status") != "exporter_mode_requirements_ready":
        print("Product project check: FAIL")
        print("exporter mode requirements manifest is missing or stale")
        return 1
    if "exporter_side_readiness" not in exporter_mode.get("readiness_lanes", []):
        print("Product project check: FAIL")
        print("exporter mode manifest missing exporter-side readiness lane")
        return 1
    if "Broker Review Packet.pdf" not in public_reports.get("reports", []):
        print("Product project check: FAIL")
        print("public report types missing broker review PDF")
        return 1
    if "Starter Checklist.pdf" not in public_reports.get("reports", []):
        print("Product project check: FAIL")
        print("public report types missing starter checklist PDF")
        return 1
    for report_name in ("Opportunity Research Report.pdf", "Policy Change Impact Report.pdf", "Broker/Freight-Forwarder Packet.pdf"):
        if report_name not in public_reports.get("reports", []):
            print("Product project check: FAIL")
            print(f"public report types missing {report_name}")
            return 1
    if public_upload_policy.get("notice_required") is not True:
        print("Product project check: FAIL")
        print("public upload policy should require notice acceptance")
        return 1
    if public_upload_policy.get("quarantine") != "enabled" or public_upload_policy.get("direct_file_serving") is not False:
        print("Product project check: FAIL")
        print("public upload policy should quarantine uploads and disable direct file serving")
        return 1
    if public_upload_policy.get("user_confirmation_required") is not True:
        print("Product project check: FAIL")
        print("public upload policy should require user confirmation")
        return 1
    if policy_monitor.get("status") != "intelligence_hub_policy_monitor_ready_with_external_refresh_gates":
        print("Product project check: FAIL")
        print("policy monitor is missing or stale")
        return 1
    if policy_monitor.get("monitored_source_count", 0) < 8 or policy_monitor.get("stale_source_blocker_count", 0) < 1:
        print("Product project check: FAIL")
        print("policy monitor missing sources or stale-source blockers")
        return 1
    if policy_snapshots.get("status") != "policy_source_snapshots_ready" or policy_impact.get("status") != "policy_change_impact_report_ready":
        print("Product project check: FAIL")
        print("policy snapshot or impact artifact is missing")
        return 1
    if completion.get("status") != "all_local_stages_implemented_with_external_gates":
        print("Product project check: FAIL")
        print("completion platform artifact is missing or stale")
        return 1
    if country_coverage.get("status") != "country_coverage_ready_with_claim_gates":
        print("Product project check: FAIL")
        print("country coverage artifact is missing or stale")
        return 1
    if opportunity_scanner.get("status") != "opportunity_scanner_ready_with_research_gates" or opportunity_scanner.get("signal_count", 0) < 1:
        print("Product project check: FAIL")
        print("opportunity scanner artifact is missing signal rows")
        return 1
    if business_logic.get("status") != "business_logic_implemented_with_external_evidence_gates":
        print("Product project check: FAIL")
        print("business logic phase report is missing or stale")
        return 1
    if business_logic.get("phase_count") != 13:
        print("Product project check: FAIL")
        print("business logic report must include the thirteen business phase surfaces")
        return 1
    if set(business_logic.get("phase_ids", [])) != {f"phase-{index}" for index in range(1, 14)}:
        print("Product project check: FAIL")
        print("business logic report must expose phases 1-13")
        return 1
    if not business_logic.get("packet_rows"):
        print("Product project check: FAIL")
        print("business logic report missing packet rows")
        return 1
    first_business_row = business_logic["packet_rows"][0]
    if first_business_row.get("decision_tree", {}).get("question_count") != 12:
        print("Product project check: FAIL")
        print("business logic decision tree must include twelve decision questions")
        return 1
    if first_business_row.get("business_scores", {}).get("score_count") != 6:
        print("Product project check: FAIL")
        print("business logic report must expose six separate business scores")
        return 1
    if first_business_row.get("canonical_packet_contract", {}).get("status") != "canonical_trade_packet_contract_ready":
        print("Product project check: FAIL")
        print("business logic report missing canonical trade packet contract")
        return 1
    if first_business_row.get("business_gate_decision", {}).get("status") != "business_logic_executable_external_gates_blocked":
        print("Product project check: FAIL")
        print("business logic report missing executable allowed/blocked action matrix")
        return 1
    if first_business_row.get("buyer_supplier_evidence", {}).get("status") != "buyer_supplier_evidence_evaluated_claims_blocked":
        print("Product project check: FAIL")
        print("business logic report missing buyer/supplier evidence evaluation")
        return 1
    if first_business_row.get("source_freshness", {}).get("status") != "source_freshness_blocked_until_refresh_and_review":
        print("Product project check: FAIL")
        print("business logic report missing source freshness evaluation")
        return 1
    if business_logic.get("operation_status") != "business_logic_operational_local_with_evidence_gates":
        print("Product project check: FAIL")
        print("business logic report missing local operation proof")
        return 1
    if business_phase_completion.get("status") != "local_business_logic_implemented_external_gates_preserved":
        print("Product project check: FAIL")
        print("business phase completion report missing implemented-local-logic status")
        return 1
    if business_phase_completion.get("completion_phase_contracts", {}).get("phase_count") != 14:
        print("Product project check: FAIL")
        print("business phase completion report must include phases 0-13")
        return 1
    if business_phase_completion.get("completion_phase_contracts", {}).get("local_contract_ready_phase_count") != 14:
        print("Product project check: FAIL")
        print("business phase completion report must mark phases 0-13 locally contract-ready")
        return 1
    if business_phase_completion.get("completion_phase_contracts", {}).get("public_launch_ready") is not False:
        print("Product project check: FAIL")
        print("business phase completion report must keep public launch blocked")
        return 1
    if business_phase_completion.get("operation_status") != "business_phase_completion_operational_local_business_logic_external_gates_preserved":
        print("Product project check: FAIL")
        print("business phase completion report missing local operation proof")
        return 1
    for term in (
        "business_logic_implemented_with_external_evidence_gates",
        "business_logic_operational_local_with_evidence_gates",
        "local_business_logic_implemented_external_gates_preserved",
        "market_signal_score",
        "evidence_completeness_score",
        "source_freshness_score",
        "buyer_supplier_evidence_score",
        "responsibility_clarity_score",
        "decision_safety_score",
        "No Open Local Business-Logic Questions",
    ):
        if term not in business_core_doc:
            print("Product project check: FAIL")
            print(f"business core logic document missing {term}")
            return 1
    for term in ("FR-10", "Business Decision Preparation", "external_effects_created: false", "claims_opened: false"):
        if term not in functional_doc:
            print("Product project check: FAIL")
            print(f"functional requirements document missing {term}")
            return 1
    for term in ("NFR-01", "Keep external effects closed by default", "live payment ready remains false", "delivery policy audit passes"):
        if term not in non_functional_doc:
            print("Product project check: FAIL")
            print(f"non-functional requirements document missing {term}")
            return 1
    if transport_readiness.get("status") != "transport_readiness_ready_with_forwarder_gates" or not transport_readiness.get("rows"):
        print("Product project check: FAIL")
        print("transport readiness artifact is missing packet rows")
        return 1
    if billing_controls.get("status") != "billing_credit_controls_ready_local_no_live_checkout" or billing_controls.get("live_checkout_enabled") is not False:
        print("Product project check: FAIL")
        print("billing controls should be local with live checkout disabled")
        return 1
    if agent_api.get("status") != "agent_api_manifest_ready_scoped_and_metered":
        print("Product project check: FAIL")
        print("agent API manifest is missing or stale")
        return 1
    forbidden_tools = set(agent_api.get("forbidden_tools", []))
    for tool in ("approve_import", "confirm_tariff", "validate_buyer", "ship_goods"):
        if tool not in forbidden_tools:
            print("Product project check: FAIL")
            print(f"agent API manifest should forbid {tool}")
            return 1
    if traffic_pages.get("status") != "traffic_pages_manifest_ready" or len(traffic_pages.get("pages", [])) < 10:
        print("Product project check: FAIL")
        print("traffic pages artifact is missing checklist pages")
        return 1
    if research_execution.get("status") != "research_execution_ready_with_evidence_gates":
        print("Product project check: FAIL")
        print("research execution plan is missing or stale")
        return 1
    if research_execution.get("operation_status") != "research_execution_operational_local_with_evidence_gates":
        print("Product project check: FAIL")
        print("research execution plan missing local operation proof")
        return 1
    if team_workspace.get("status") != "team_workspace_ready_local_with_approval_gates":
        print("Product project check: FAIL")
        print("team workspace report is missing or stale")
        return 1
    if team_workspace.get("operation_status") != "team_workspace_operational_local_with_approval_gates":
        print("Product project check: FAIL")
        print("team workspace report missing local operation proof")
        return 1
    if expert_network.get("status") != "expert_network_ready_local_with_human_review_gates":
        print("Product project check: FAIL")
        print("expert network report is missing or stale")
        return 1
    if expert_network.get("operation_status") != "expert_network_operational_local_with_human_review_gates":
        print("Product project check: FAIL")
        print("expert network report missing local operation proof")
        return 1
    if billing_usage.get("status") != "billing_usage_ledger_ready_local_no_charges":
        print("Product project check: FAIL")
        print("billing usage ledger should be local with no charges")
        return 1
    if billing_usage.get("executed_usage_event_count", 0) < 1 or billing_usage.get("external_charge_created") is not False:
        print("Product project check: FAIL")
        print("billing usage ledger missing executed local usage or created an external charge")
        return 1
    if agent_gateway.get("status") != "agent_api_gateway_ready_local_executor_no_external_effects":
        print("Product project check: FAIL")
        print("agent API gateway should be local executor with no external effects")
        return 1
    if agent_gateway.get("operation_status") != "agent_api_gateway_executed_local_no_external_effects":
        print("Product project check: FAIL")
        print("agent API gateway missing local execution proof")
        return 1
    if launch_operations.get("status") != "launch_operations_ready_for_private_beta_review":
        print("Product project check: FAIL")
        print("launch operations report is missing or stale")
        return 1
    if launch_operations.get("operation_status") != "launch_operations_operational_local_with_human_approval_gates":
        print("Product project check: FAIL")
        print("launch operations report missing local operation proof")
        return 1
    if (
        all_stages.get("status") != "all_local_stages_implemented_with_external_gates"
        or all_stages.get("stage_count") != 19
        or all_stages.get("implemented_stage_count") != 19
        or all_stages.get("go_live_state_count") != 18
        or all_stages.get("runbook_stage_range") != "0-18"
    ):
        print("Product project check: FAIL")
        print("all-stage readiness report is missing exact Stage 0-18 local coverage")
        return 1
    public_go_live = next(
        (row for row in all_stages.get("stages", []) if row.get("stage_id") == "stage-18"),
        {},
    )
    if public_go_live.get("status") != "public_go_live_subset_defined_blocked_until_approval":
        print("Product project check: FAIL")
        print("stage-18 must keep public go-live blocked until owner approval")
        return 1
    if all_stages.get("operation_status") != "local_product_operations_executed":
        print("Product project check: FAIL")
        print("all-stage readiness report missing product operation proof")
        return 1
    if all_stages.get("local_execution_proof_count", 0) < 8:
        print("Product project check: FAIL")
        print("all-stage readiness report missing enough local execution proofs")
        return 1
    if product_operations.get("status") != "local_product_operations_executed":
        print("Product project check: FAIL")
        print("product operations report is not executed")
        return 1
    if product_operations.get("operation_count", 0) < 8:
        print("Product project check: FAIL")
        print("product operations report missing operation events")
        return 1
    if product_operations.get("external_effects_created") is not False or product_operations.get("claims_opened") is not False:
        print("Product project check: FAIL")
        print("product operations opened an external effect or claim")
        return 1
    if (
        final_go_live.get("status") != "local_go_live_contract_complete_public_launch_blocked"
        or final_go_live.get("local_contract_complete") is not True
        or final_go_live.get("public_launch_ready") is not False
        or final_go_live.get("hosted_private_beta_ready") is not False
        or final_go_live.get("unsafe_gates_closed") is not True
        or len(final_go_live.get("public_launch_blockers", [])) < 6
    ):
        print("Product project check: FAIL")
        print("final go-live decision must keep launch/private-beta blocked with concrete blockers")
        return 1
    if current_sources.get("status") != "current_external_gate_research_ready" or current_sources.get("source_count", 0) < 8:
        print("Product project check: FAIL")
        print("current external gate research must include dated source anchors")
        return 1
    if (
        external_validation.get("status") != "external_validation_requirements_ready_all_real_world_gates_blocked"
        or external_validation.get("gate_count") != 8
        or external_validation.get("source_count", 0) < 24
        or external_validation.get("evidence_requirement_count", 0) < 44
        or external_validation.get("required_data_category_count", 0) < 14
        or external_validation.get("public_launch_ready") is not False
        or external_validation.get("hosted_private_beta_ready") is not False
        or external_validation.get("live_payment_ready") is not False
        or external_validation.get("simulated_ai_review_can_open_gate") is not False
    ):
        print("Product project check: FAIL")
        print("external validation requirements must cover all real-world gates while keeping them blocked")
        return 1
    expected_external_validation_gates = {
        "real_external_expert_reviews",
        "legal_privacy_security_approval",
        "qualified_customs_trade_review",
        "hosted_staging_production_proof",
        "live_payment_activation",
        "real_users_private_beta_outcomes",
        "buyer_supplier_validation",
        "public_go_no_go_approval",
    }
    if {row.get("gate_id") for row in external_validation.get("gates", [])} != expected_external_validation_gates:
        print("Product project check: FAIL")
        print("external validation requirements missing expected real-world gate IDs")
        return 1
    if any(not str(row.get("status", "")).startswith("blocked_") for row in external_validation.get("gates", [])):
        print("Product project check: FAIL")
        print("external validation requirements opened a gate without real evidence")
        return 1
    if (
        external_validation_evidence.get("status") != "external_validation_evidence_requirements_ready"
        or external_validation_evidence.get("evidence_requirement_count") != external_validation.get("evidence_requirement_count")
    ):
        print("Product project check: FAIL")
        print("external validation evidence requirements are missing or inconsistent")
        return 1
    if (
        production_redevelopment.get("status") != "production_redevelopment_contract_ready_with_external_build_gates"
        or production_redevelopment.get("production_layer_count") != 14
        or production_redevelopment.get("phase_count") != 21
        or production_redevelopment.get("research_anchor_count") != 18
        or production_redevelopment.get("domain_entity_count", 0) < 39
        or production_redevelopment.get("external_claims_opened") is not False
        or production_redevelopment.get("public_launch_ready") is not False
        or production_redevelopment.get("hosted_production_ready") is not False
        or production_redevelopment.get("live_payment_ready") is not False
    ):
        print("Product project check: FAIL")
        print("production redevelopment contract must cover 14 layers, phases 0-20, research anchors, and closed launch gates")
        return 1
    if production_research.get("source_count") != production_redevelopment.get("research_anchor_count"):
        print("Product project check: FAIL")
        print("production research anchors must match the redevelopment source count")
        return 1
    official_source_ids = {row.get("id") for row in official_source_registry}
    research_source_ids = {row.get("id") for row in production_redevelopment.get("research_anchors", [])}
    required_production_source_ids = {
        "cbsa-import-commercial-goods",
        "cbsa-customs-tariff-2026",
        "cbsa-licensed-customs-brokers",
        "cfia-airs",
        "gac-sanctions",
        "ised-trade-data-online",
        "canada-cid",
        "india-dgft-foreign-trade-policy",
        "world-bank-wits",
        "itc-trade-map",
        "itc-market-access-map",
        "wco-harmonized-system",
        "icc-incoterms-2020",
        "opc-pipeda-principles",
        "owasp-file-upload",
        "owasp-llm01-prompt-injection",
        "nist-ai-rmf",
        "stripe-go-live",
    }
    if not required_production_source_ids.issubset(official_source_ids | research_source_ids):
        print("Product project check: FAIL")
        print("production source registry is missing required source IDs")
        return 1
    allowed_non_registry_source_ids = {
        "official_source_registry",
        "user_research_required",
        "enterprise_user_validation_required",
        "reviewer_findings",
        "user_validation_records",
    }
    allowed_source_ids = official_source_ids | research_source_ids | allowed_non_registry_source_ids
    for phase in production_redevelopment.get("redevelopment_phases", []):
        for track in ("build_track", "research_track", "source_track", "evidence_track", "gate_track"):
            if not phase.get(track):
                print("Product project check: FAIL")
                print(f"production phase {phase.get('phase')} missing {track}")
                return 1
        if any(layer_id < 1 or layer_id > 14 for layer_id in phase.get("layers", [])):
            print("Product project check: FAIL")
            print(f"production phase {phase.get('phase')} references a non-existent production layer")
            return 1
        if any(source_id not in allowed_source_ids for source_id in phase.get("source_track", [])):
            print("Product project check: FAIL")
            print(f"production phase {phase.get('phase')} references an unknown source ID")
            return 1
    if (
        production_data_model.get("status") != "production_data_model_ready_local_schema_proof_external_db_gates_closed"
        or production_data_model.get("table_count", 0) < 40
        or production_data_model.get("foreign_key_count", 0) < 70
        or production_data_model.get("index_count", 0) < 35
        or production_data_model.get("row_level_security_table_count", 0) < 25
        or production_data_model.get("domain_event_count", 0) < 14
        or production_data_model.get("hosted_database_ready") is not False
        or production_data_model.get("external_claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production data model must include schema, relationships, RLS, domain events, and closed external gates")
        return 1
    production_schema_sql = (PROJECT / "migrations" / "0002_production_domain_model.sql").read_text(encoding="utf-8")
    for expected_sql in (
        "enable row level security",
        "current_setting('app.current_organization_id', true)",
        "constraint decision_scores_name_check",
        "buyer_supplier_evidence_score",
        "external_charge_created boolean not null default false",
    ):
        if expected_sql not in production_schema_sql:
            print("Product project check: FAIL")
            print(f"production data model migration missing SQL invariant: {expected_sql}")
            return 1
    production_table_names = {row.get("table") for row in production_data_model.get("tables", [])}
    for required_table in (
        "trade_readiness_packets",
        "packet_events",
        "source_records",
        "source_snapshots",
        "evidence_items",
        "market_signals",
        "blocked_claims",
        "decision_scores",
        "review_requests",
        "reports",
        "audit_events",
    ):
        if required_table not in production_table_names:
            print("Product project check: FAIL")
            print(f"production data model missing table {required_table}")
            return 1
    if (
        production_packet_engine.get("status") != "production_packet_engine_ready_local_state_machine_claim_gates_closed"
        or production_packet_engine.get("packet_count", 0) < 1
        or production_packet_engine.get("state_count") != 12
        or production_packet_engine.get("packet_view_type_count") != 8
        or production_packet_engine.get("packet_view_count", 0) < 8
        or production_packet_engine.get("packet_event_count", 0) < 12
        or production_packet_engine.get("external_effects_created") is not False
        or production_packet_engine.get("claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production packet engine manifest should prove local state/view engine with closed gates")
        return 1
    packet_runs = production_packet_engine.get("packet_runs", [])
    if not packet_runs:
        print("Product project check: FAIL")
        print("production packet engine missing packet run evidence")
        return 1
    packet_run = packet_runs[0]
    view_types = {row.get("view_type") for row in packet_run.get("packet_views", [])}
    score_ids = {row.get("score") for row in packet_run.get("scores", [])}
    event_states = {row.get("state") for row in packet_run.get("state_events", [])}
    if view_types != {
        "starter_packet",
        "market_research_packet",
        "buyer_ready_packet",
        "supplier_request_packet",
        "broker_review_packet",
        "operator_packet",
        "executive_decision_packet",
        "blocked_claims_packet",
    }:
        print("Product project check: FAIL")
        print("production packet engine should generate all eight packet views")
        return 1
    if score_ids != {
        "market_signal_score",
        "evidence_completeness_score",
        "source_freshness_score",
        "buyer_supplier_evidence_score",
        "responsibility_clarity_score",
        "decision_safety_score",
    }:
        print("Product project check: FAIL")
        print("production packet engine should output the six canonical scores")
        return 1
    if event_states != set(production_packet_engine.get("states", [])):
        print("Product project check: FAIL")
        print("production packet engine should write an event row for every production state")
        return 1
    if packet_run.get("state") != "reviewer_ready":
        print("Product project check: FAIL")
        print(f"fixture packet should be reviewer_ready, got {packet_run.get('state')!r}")
        return 1
    if packet_run.get("reviewer_ready_not_approved") is not True:
        print("Product project check: FAIL")
        print("reviewer-ready packet must explicitly remain not approved")
        return 1
    if (
        production_persistence.get("status") != "production_persistence_ready_local_domain_rows_external_db_gate_closed"
        or production_persistence.get("total_row_count", 0) < 150
        or production_persistence.get("validation_error_count") != 0
        or production_persistence.get("hosted_postgres_ready") is not False
        or production_persistence.get("production_migration_applied") is not False
        or production_persistence.get("external_claims_opened") is not False
        or production_persistence.get("public_launch_ready") is not False
    ):
        print("Product project check: FAIL")
        print("production persistence should load local domain rows while keeping hosted/external gates closed")
        return 1
    required_persistence_tables = {
        "organizations",
        "users",
        "workspaces",
        "trade_lanes",
        "trade_readiness_packets",
        "product_profiles",
        "country_packs",
        "source_records",
        "source_snapshots",
        "evidence_items",
        "blocked_claims",
        "claim_gate_mappers",
        "decision_scores",
        "review_requests",
        "reports",
        "audit_events",
    }
    if set(production_persistence.get("table_order", [])) != required_persistence_tables:
        print("Product project check: FAIL")
        print("production persistence table order missing required domain tables")
        return 1
    for table, minimum in {
        "trade_readiness_packets": 1,
        "evidence_items": 3,
        "source_records": 20,
        "source_snapshots": 20,
        "decision_scores": 6,
        "reports": 12,
        "audit_events": 3,
    }.items():
        if production_persistence.get("row_counts", {}).get(table, 0) < minimum:
            print("Product project check: FAIL")
            print(f"production persistence table {table} below minimum row proof")
            return 1
    production_store = PROJECT / "system_review_graph" / "production_domain.sqlite"
    with sqlite3.connect(production_store) as conn:
        production_store_tables = {
            row[0]
            for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
        }
        for table in required_persistence_tables:
            if table not in production_store_tables:
                print("Product project check: FAIL")
                print(f"production domain sqlite missing table {table}")
                return 1
            count = conn.execute(f"select count(*) from {table}").fetchone()[0]
            if count != production_persistence.get("row_counts", {}).get(table):
                print("Product project check: FAIL")
                print(
                    f"production domain sqlite table {table} count mismatch "
                    f"{count} != {production_persistence.get('row_counts', {}).get(table)}"
                )
                return 1
        opened_claim_boundary_count = conn.execute(
            "select count(*) from trade_readiness_packets where claim_boundary_status != 'external_claims_closed'"
        ).fetchone()[0]
    if opened_claim_boundary_count:
        print("Product project check: FAIL")
        print("production domain sqlite opened a packet claim boundary")
        return 1
    if (
        production_country_source_engine.get("status") != "production_country_source_engine_ready_reference_packs_claim_gates_closed"
        or production_country_source_engine.get("country_pack_count") != 4
        or production_country_source_engine.get("source_lifecycle_count", 0) < 20
        or production_country_source_engine.get("researched_source_fact_count", 0) < 18
        or production_country_source_engine.get("external_effects_created") is not False
        or production_country_source_engine.get("claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production country/source engine should build reference packs, lifecycle rows, and closed gates")
        return 1
    country_packs = {row.get("country_pack_id"): row for row in production_country_source_engine.get("country_packs", [])}
    for pack_id in ("CA-import", "IN-export", "VN-demo-origin", "GENERIC-fallback"):
        if pack_id not in country_packs:
            print("Product project check: FAIL")
            print(f"production country/source engine missing country pack {pack_id}")
            return 1
    canada_required_source_areas = {
        "customs_import_process",
        "tariff_orientation",
        "regulated_goods",
        "sanctions_restricted_party",
        "trade_data",
        "buyer_importer_discovery",
        "broker_directory",
        "import_controls",
    }
    if not canada_required_source_areas.issubset(set(country_packs["CA-import"].get("source_types_present", []))):
        print("Product project check: FAIL")
        print("Canada import pack missing required source areas")
        return 1
    if country_packs["CA-import"].get("coverage_level") != "reference_only":
        print("Product project check: FAIL")
        print("Canada import pack should remain reference_only until qualified review")
        return 1
    if country_packs["GENERIC-fallback"].get("coverage_level") != "generic":
        print("Product project check: FAIL")
        print("generic fallback country pack should stay generic")
        return 1
    source_lifecycle = {row.get("source_id"): row for row in production_country_source_engine.get("source_lifecycle", [])}
    for source_id in ("cbsa-import-commercial-goods", "cfia-airs", "canada-cid"):
        if source_lifecycle.get(source_id, {}).get("source_state") != "checked_current_reference_only":
            print("Product project check: FAIL")
            print(f"{source_id} should be checked_current_reference_only from dated refresh records")
            return 1
    if source_lifecycle.get("cbsa-customs-tariff-2026", {}).get("source_state") != "not_checked":
        print("Product project check: FAIL")
        print("tariff source should remain not_checked until a dated refresh exists")
        return 1
    impacts = production_country_source_engine.get("packet_source_impacts", [])
    if not impacts or "tariff_confirmed" not in impacts[0].get("blocked_claims", []) or "cfia_approved" not in impacts[0].get("blocked_claims", []):
        print("Product project check: FAIL")
        print("packet source impact should preserve tariff and CFIA claim blocks")
        return 1
    if (
        production_trade_discovery.get("status")
        != "production_trade_discovery_engine_ready_beginner_research_routed_no_opportunity_claims"
        or production_trade_discovery.get("category_count", 0) < 12
        or production_trade_discovery.get("country_lane_count", 0) < 12
        or production_trade_discovery.get("beginner_flow_count", 0) < 8
        or production_trade_discovery.get("dataset_route_count", 0) < 6
        or production_trade_discovery.get("external_effects_created") is not False
        or production_trade_discovery.get("claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production trade discovery should build source-routed beginner discovery with closed claims")
        return 1
    if production_trade_discovery.get("missing_registry_sources"):
        print("Product project check: FAIL")
        print("production trade discovery references missing source registry ids")
        return 1
    for key in (
        "recommendation_claimed",
        "market_opportunity_claimed",
        "demand_claimed",
        "profitability_claimed",
        "buyer_validation_claimed",
        "supplier_verification_claimed",
        "customs_approval_claimed",
        "cfia_approval_claimed",
        "public_launch_ready",
    ):
        if production_trade_discovery.get(key) is not False:
            print("Product project check: FAIL")
            print(f"production trade discovery expected {key}=false")
            return 1
    for blocked_claim in ("best_product_to_import", "guaranteed_demand", "buyer_validated", "supplier_verified", "cfia_approved"):
        if blocked_claim not in production_trade_discovery.get("blocked_claims", []):
            print("Product project check: FAIL")
            print(f"production trade discovery should block {blocked_claim}")
            return 1
    discovery_source_ids = {row.get("source_id") for row in production_trade_discovery.get("source_records", [])}
    for source_id in (
        "ised-trade-data-online",
        "canada-cid",
        "statcan-wds",
        "cbsa-import-commercial-goods",
        "cfia-airs",
        "gac-sanctions",
        "canada-trade-commissioner-export-guide",
        "gac-export-controls",
        "world-bank-wits",
        "itc-trade-map",
        "itc-market-access-map",
        "wco-harmonized-system",
    ):
        if source_id not in discovery_source_ids:
            print("Product project check: FAIL")
            print(f"production trade discovery missing source route {source_id}")
            return 1
    discovery_flow_ids = {row.get("flow_id") for row in production_trade_discovery.get("beginner_flows", [])}
    for flow_id in ("browse_canada_imports", "browse_canada_exports", "compare_origin_lanes_to_canada", "check_regulated_goods_early"):
        if flow_id not in discovery_flow_ids:
            print("Product project check: FAIL")
            print(f"production trade discovery missing beginner flow {flow_id}")
            return 1
    discovery_lane_ids = {row.get("lane_id") for row in production_trade_discovery.get("country_lanes", [])}
    for lane_id in ("IN-to-CA", "VN-to-CA", "US-to-CA", "MX-to-CA", "CN-to-CA", "EU-to-CA", "CA-to-US", "GENERIC-to-CA"):
        if lane_id not in discovery_lane_ids:
            print("Product project check: FAIL")
            print(f"production trade discovery missing country lane {lane_id}")
            return 1
    if any(row.get("trade_values_loaded") is not False for row in production_trade_discovery.get("country_lanes", [])):
        print("Product project check: FAIL")
        print("production trade discovery country lanes must not contain invented trade values")
        return 1
    if any(row.get("recommendation_claimed") is not False for row in production_trade_discovery.get("country_lanes", [])):
        print("Product project check: FAIL")
        print("production trade discovery country lanes must not claim recommendations")
        return 1
    if any(row.get("recommendation_claimed") is not False for row in production_trade_discovery.get("category_families", [])):
        print("Product project check: FAIL")
        print("production trade discovery categories must not claim recommendations")
        return 1
    if (
        production_trade_data_catalog.get("status")
        != "production_trade_data_catalog_engine_ready_query_plans_no_values_loaded"
        or production_trade_data_catalog.get("template_count", 0) < 7
        or production_trade_data_catalog.get("browse_card_count", 0) < 5
        or production_trade_data_catalog.get("query_work_order_count", 0) < 120
        or production_trade_data_catalog.get("values_loaded") is not False
        or production_trade_data_catalog.get("numeric_values_shown") is not False
        or production_trade_data_catalog.get("recommendations_created") is not False
        or production_trade_data_catalog.get("demand_claimed") is not False
        or production_trade_data_catalog.get("profitability_claimed") is not False
        or production_trade_data_catalog.get("buyer_validation_claimed") is not False
        or production_trade_data_catalog.get("supplier_verification_claimed") is not False
        or production_trade_data_catalog.get("external_effects_created") is not False
        or production_trade_data_catalog.get("claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production trade data catalog should build query plans and work orders with values and claims closed")
        return 1
    if production_trade_data_catalog.get("missing_registry_sources"):
        print("Product project check: FAIL")
        print("production trade data catalog references missing source registry ids")
        return 1
    catalog_template_ids = {row.get("template_id") for row in production_trade_data_catalog.get("query_templates", [])}
    for template_id in (
        "canada_imports_by_product_origin",
        "canada_exports_by_product_destination",
        "origin_country_comparison_for_canada",
        "canadian_importer_lead_lookup",
        "regulated_goods_source_overlay",
        "market_access_comparison",
        "global_context_fallback",
    ):
        if template_id not in catalog_template_ids:
            print("Product project check: FAIL")
            print(f"production trade data catalog missing query template {template_id}")
            return 1
    if any(row.get("values_loaded") is not False for row in production_trade_data_catalog.get("query_templates", [])):
        print("Product project check: FAIL")
        print("production trade data catalog templates must not pretend values are loaded")
        return 1
    if any(row.get("allowed_to_show_numeric_values") is not False for row in production_trade_data_catalog.get("query_templates", [])):
        print("Product project check: FAIL")
        print("production trade data catalog templates must block numeric display before ingestion")
        return 1
    if any(row.get("values_loaded") is not False for row in production_trade_data_catalog.get("query_work_orders", [])):
        print("Product project check: FAIL")
        print("production trade data catalog work orders must not contain values before ingestion")
        return 1
    if any(row.get("dated_dataset_row_attached") is not False for row in production_trade_data_catalog.get("query_work_orders", [])):
        print("Product project check: FAIL")
        print("production trade data catalog work orders must require dated rows")
        return 1
    if (
        production_market_intelligence.get("status") != "production_market_intelligence_engine_ready_source_routed_no_demand_claims"
        or production_market_intelligence.get("metric_count") != 9
        or production_market_intelligence.get("market_signal_count", 0) < 9
        or production_market_intelligence.get("dataset_connector_count", 0) < 7
        or production_market_intelligence.get("external_effects_created") is not False
        or production_market_intelligence.get("claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production market intelligence should produce source-routed signals with closed claims")
        return 1
    for blocked_claim in ("profitable_market", "guaranteed_demand", "buyer_validated"):
        if blocked_claim not in production_market_intelligence.get("blocked_claims", []):
            print("Product project check: FAIL")
            print(f"production market intelligence should block {blocked_claim}")
            return 1
    metric_names = {row.get("metric") for row in production_market_intelligence.get("signals", [])}
    for metric in (
        "destination_import_value",
        "three_to_five_year_trend",
        "top_origin_countries",
        "unit_value_range",
        "market_access_barriers",
        "buyer_importer_lead_routes",
    ):
        if metric not in metric_names:
            print("Product project check: FAIL")
            print(f"production market intelligence missing metric {metric}")
            return 1
    if any(row.get("value_status") != "not_ingested_dataset_required" for row in production_market_intelligence.get("signals", [])):
        print("Product project check: FAIL")
        print("market signals should not contain invented values before dataset ingestion")
        return 1
    market_packet_runs = production_market_intelligence.get("packet_runs", [])
    if not market_packet_runs:
        print("Product project check: FAIL")
        print("production market intelligence missing packet run evidence")
        return 1
    market_packet = market_packet_runs[0].get("market_packet", {})
    if (
        market_packet.get("can_claim_market_demand") is not False
        or market_packet.get("can_claim_profitability") is not False
        or market_packet.get("can_claim_buyer_validation") is not False
    ):
        print("Product project check: FAIL")
        print("market packet must not claim demand, profitability, or buyer validation")
        return 1
    if (
        production_document_intelligence.get("status") != "production_document_intelligence_engine_ready_local_pipeline_security_gates_closed"
        or production_document_intelligence.get("pipeline_stage_count", 0) < 16
        or production_document_intelligence.get("document_class_count") != 11
        or production_document_intelligence.get("official_sample_document_count", 0) < 3
        or production_document_intelligence.get("source_route_only_sample_count", 0) < 3
        or production_document_intelligence.get("synthetic_parser_fixture_count") != 11
        or production_document_intelligence.get("extracted_field_count", 0) < 20
        or production_document_intelligence.get("real_uploads_enabled") is not False
        or production_document_intelligence.get("malware_scan_proven") is not False
        or production_document_intelligence.get("object_storage_ready") is not False
        or production_document_intelligence.get("external_effects_created") is not False
        or production_document_intelligence.get("claims_opened") is not False
        or production_document_intelligence.get("public_launch_ready") is not False
        or production_document_intelligence.get("parser_outputs_are_draft") is not True
    ):
        print("Product project check: FAIL")
        print("production document intelligence should produce sample-backed draft records with closed security and claim gates")
        return 1
    for blocked_claim in ("document_authenticity_verified", "customs_ready", "tariff_confirmed", "cfia_approved", "supplier_verified"):
        if blocked_claim not in production_document_intelligence.get("blocked_claims", []):
            print("Product project check: FAIL")
            print(f"production document intelligence should block {blocked_claim}")
            return 1
    document_stages = {row.get("stage") for row in production_document_intelligence.get("pipeline_stages", [])}
    for stage in ("malware_scan", "document_classification", "field_extraction", "evidence_ledger_mapping", "redaction_preview", "ai_optional_analysis"):
        if stage not in document_stages:
            print("Product project check: FAIL")
            print(f"production document intelligence missing pipeline stage {stage}")
            return 1
    source_ids_for_documents = {row.get("source_id") for row in production_document_intelligence.get("source_records", [])}
    for source_id in ("cbsa-ci1-canada-customs-invoice", "india-dgft-appendices-anf", "vietnam-customs-portal", "owasp-file-upload"):
        if source_id not in source_ids_for_documents:
            print("Product project check: FAIL")
            print(f"production document intelligence missing source record {source_id}")
            return 1
    document_sample_levels = {row.get("sample_level") for row in production_document_intelligence.get("document_records", [])}
    for sample_level in ("official_pdf_downloaded", "synthetic_parser_fixture"):
        if sample_level not in document_sample_levels:
            print("Product project check: FAIL")
            print(f"production document intelligence missing document sample level {sample_level}")
            return 1
    expected_document_classes = {
        "commercial_invoice",
        "packing_list",
        "certificate_of_origin",
        "bill_of_lading",
        "airway_bill",
        "product_specification",
        "lab_certificate",
        "phytosanitary_or_health_certificate",
        "purchase_order",
        "contract",
        "inspection_report",
    }
    document_classes = {row.get("classification", {}).get("type") for row in production_document_intelligence.get("document_records", [])}
    if not expected_document_classes.issubset(document_classes):
        print("Product project check: FAIL")
        print("production document intelligence does not cover every expected document class")
        return 1
    for field in production_document_intelligence.get("extracted_fields", []):
        if field.get("supports_claims") != []:
            print("Product project check: FAIL")
            print("production document extracted fields must not support claims directly")
            return 1
        for key in ("document_id", "page_or_section", "extracted_value", "confidence", "provenance", "user_confirmation_status", "claim_boundary"):
            if key not in field:
                print("Product project check: FAIL")
                print(f"production document extracted field missing {key}")
                return 1
    if (
        production_evidence_claim_gate.get("status") != "production_evidence_claim_gate_engine_ready_claims_fail_closed"
        or production_evidence_claim_gate.get("claim_type_count", 0) < 17
        or production_evidence_claim_gate.get("claim_gate_decision_count", 0) < production_evidence_claim_gate.get("claim_type_count", 0)
        or production_evidence_claim_gate.get("safe_research_claim_count", 0) < 1
        or production_evidence_claim_gate.get("forbidden_external_claim_count", 0) < 6
        or production_evidence_claim_gate.get("evidence_mapper_count", 0) < 1
        or production_evidence_claim_gate.get("claim_gate_mapper_count") != production_evidence_claim_gate.get("claim_type_count")
        or production_evidence_claim_gate.get("external_effects_created") is not False
        or production_evidence_claim_gate.get("claims_opened") is not False
        or production_evidence_claim_gate.get("public_launch_ready") is not False
        or production_evidence_claim_gate.get("live_payment_ready") is not False
    ):
        print("Product project check: FAIL")
        print("production evidence claim-gate should make can_show_claim decisions while keeping external gates closed")
        return 1
    claim_decisions = {
        row.get("claim_type"): row for row in production_evidence_claim_gate.get("claim_gate_decisions", [])
    }
    safe_decision = claim_decisions.get("hs_candidate_research_route", {})
    if safe_decision.get("can_show_claim") is not True:
        print("Product project check: FAIL")
        print("HS candidate research route should be showable as preparation only")
        return 1
    if "source:wco-harmonized-system" not in {row.get("evidence_id") for row in safe_decision.get("evidence_trail", [])}:
        print("Product project check: FAIL")
        print("HS candidate research route should cite WCO source evidence")
        return 1
    if claim_decisions.get("document_field_extraction_draft", {}).get("can_show_claim") is not False:
        print("Product project check: FAIL")
        print("document field extraction claim must stay blocked until real customer extraction exists")
        return 1
    if "missing customer document field extraction" not in claim_decisions.get("document_field_extraction_draft", {}).get("missing_evidence", []):
        print("Product project check: FAIL")
        print("document field extraction should explain the missing customer extraction")
        return 1
    for claim_type in ("tariff_confirmed", "cfia_approved", "buyer_validated", "supplier_verified", "customs_ready", "shipment_approved"):
        decision = claim_decisions.get(claim_type, {})
        if decision.get("can_show_claim") is not False or decision.get("allowed_wording"):
            print("Product project check: FAIL")
            print(f"production evidence claim-gate must keep {claim_type} blocked")
            return 1
    tariff_source_mapper = next(
        (
            row
            for row in production_evidence_claim_gate.get("evidence_mappers", [])
            if row.get("evidence_id") == "source:cbsa-customs-tariff-2026"
        ),
        {},
    )
    if "hs_candidate_research_route" not in tariff_source_mapper.get("supports_claims", []):
        print("Product project check: FAIL")
        print("tariff source evidence should support source-routed HS preparation")
        return 1
    if "tariff_confirmed" not in tariff_source_mapper.get("blocks_claims", []):
        print("Product project check: FAIL")
        print("tariff source evidence should block tariff-confirmed wording without qualified review")
        return 1
    if (
        production_decision_scoring.get("status") != "production_decision_scoring_engine_ready_no_global_readiness_score"
        or production_decision_scoring.get("score_count") != 6
        or production_decision_scoring.get("decision_score_record_count", 0) < 6
        or production_decision_scoring.get("single_global_readiness_score_created") is not False
        or production_decision_scoring.get("combined_readiness_label_created") is not False
        or production_decision_scoring.get("approval_language_allowed") is not False
        or production_decision_scoring.get("external_effects_created") is not False
        or production_decision_scoring.get("claims_opened") is not False
        or production_decision_scoring.get("public_launch_ready") is not False
        or production_decision_scoring.get("live_payment_ready") is not False
    ):
        print("Product project check: FAIL")
        print("production decision scoring should keep six capped scores separate with closed gates")
        return 1
    expected_score_ids = {
        "market_signal_score",
        "evidence_completeness_score",
        "source_freshness_score",
        "buyer_supplier_evidence_score",
        "responsibility_clarity_score",
        "decision_safety_score",
    }
    if set(production_decision_scoring.get("score_ids", [])) != expected_score_ids:
        print("Product project check: FAIL")
        print("production decision scoring must expose the six canonical score IDs")
        return 1
    score_records = {
        row.get("score"): row
        for row in production_decision_scoring.get("decision_score_records", [])
        if row.get("packet_id") == "packet-frozen-tuna-canada-001"
    }
    if set(score_records) != expected_score_ids:
        print("Product project check: FAIL")
        print("production decision scoring missing current packet score records")
        return 1
    for score_id, record in score_records.items():
        for field in ("score_value", "score_cap", "label", "reason", "cap_reason", "blocking_fields", "next_action"):
            if field not in record:
                print("Product project check: FAIL")
                print(f"production decision score {score_id} missing {field}")
                return 1
        if record.get("single_global_readiness_score_used") is not False:
            print("Product project check: FAIL")
            print(f"production decision score {score_id} must not use a global readiness score")
            return 1
        if record.get("approval_language_blocked") is not True:
            print("Product project check: FAIL")
            print(f"production decision score {score_id} must block approval language")
            return 1
        if record.get("score_value", 0) > record.get("score_cap", 100):
            print("Product project check: FAIL")
            print(f"production decision score {score_id} exceeds its cap")
            return 1
    for score_id in ("source_freshness_score", "responsibility_clarity_score", "decision_safety_score"):
        if score_records.get(score_id, {}).get("label") != "red":
            print("Product project check: FAIL")
            print(f"production decision score {score_id} should stay red for the current packet")
            return 1
    if "tariff_confirmed" not in score_records.get("decision_safety_score", {}).get("blocked_claim_dependencies", []):
        print("Product project check: FAIL")
        print("decision safety score should depend on blocked tariff confirmation")
        return 1
    summaries = production_decision_scoring.get("packet_score_summaries", [])
    if not summaries or summaries[0].get("single_global_readiness_score_created") is not False:
        print("Product project check: FAIL")
        print("packet score summary must refuse a single global readiness score")
        return 1
    if (
        production_ai_copilot.get("status") != "production_ai_copilot_engine_ready_no_gate_opening"
        or production_ai_copilot.get("ai_role_count") != 8
        or production_ai_copilot.get("ai_output_contract_count") != 8
        or production_ai_copilot.get("prompt_injection_test_count", 0) < 2
        or production_ai_copilot.get("provider_terms_review_complete") is not False
        or production_ai_copilot.get("qualified_ai_safety_review_complete") is not False
        or production_ai_copilot.get("live_model_calls_enabled") is not False
        or production_ai_copilot.get("can_open_customs_tariff_cfia_buyer_supplier_payment_legal_launch_gate") is not False
        or production_ai_copilot.get("external_effects_created") is not False
        or production_ai_copilot.get("claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production AI copilot should register AI roles while keeping live calls and gates closed")
        return 1
    expected_ai_roles = {
        "intake_assistant",
        "document_extraction_assistant",
        "source_summarizer",
        "market_research_assistant",
        "packet_writer",
        "reviewer_work_order_drafter",
        "redaction_assistant",
        "qa_assistant",
    }
    ai_roles = {row.get("role") for row in production_ai_copilot.get("role_contracts", [])}
    if ai_roles != expected_ai_roles:
        print("Product project check: FAIL")
        print("production AI copilot role contracts are incomplete")
        return 1
    allowed_labels = {"draft", "source_backed", "needs_user_confirmation", "needs_expert_review", "blocked"}
    for contract in production_ai_copilot.get("role_contracts", []):
        if contract.get("output_label") not in allowed_labels:
            print("Product project check: FAIL")
            print(f"production AI role {contract.get('role')} has invalid output label")
            return 1
        if contract.get("can_open_gate") is not False:
            print("Product project check: FAIL")
            print(f"production AI role {contract.get('role')} must not open gates")
            return 1
        if "tariff_confirmed" not in contract.get("blocked_gates", []):
            print("Product project check: FAIL")
            print(f"production AI role {contract.get('role')} should block tariff_confirmed")
            return 1
    for contract in production_ai_copilot.get("output_contracts", []):
        if (
            contract.get("can_open_customs_tariff_cfia_buyer_supplier_payment_launch_gate") is not False
            or contract.get("claims_opened") is not False
        ):
            print("Product project check: FAIL")
            print(f"production AI output {contract.get('role')} must keep gates closed")
            return 1
    for result in production_ai_copilot.get("prompt_injection_results", []):
        if result.get("result") != "blocked_output_no_gate_opened" or result.get("can_open_gate") is not False:
            print("Product project check: FAIL")
            print(f"prompt injection check {result.get('test_id')} should fail closed")
            return 1
    if (
        production_expert_review.get("status") != "production_expert_review_network_ready_scope_limited_no_external_claims"
        or production_expert_review.get("reviewer_lane_count") != 10
        or production_expert_review.get("profile_requirement_count") != 10
        or production_expert_review.get("finding_template_count") != 10
        or production_expert_review.get("review_request_count", 0) < 10
        or production_expert_review.get("gate_impact_count", 0) < 10
        or production_expert_review.get("source_registry_coverage_count", 0) < 9
        or production_expert_review.get("real_reviewer_signoff_recorded") is not False
        or production_expert_review.get("qualified_credentials_verified") is not False
        or production_expert_review.get("scope_limited_approval_recorded") is not False
        or production_expert_review.get("can_open_customs_tariff_cfia_buyer_supplier_security_privacy_payment_launch_gate") is not False
        or production_expert_review.get("external_effects_created") is not False
        or production_expert_review.get("claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production expert review network should create scoped review lanes while keeping real signoff and gates closed")
        return 1
    expected_reviewer_lanes = {
        "customs_trade_reviewer",
        "regulated_food_product_reviewer",
        "freight_logistics_reviewer",
        "market_trade_consultant_reviewer",
        "supplier_evidence_reviewer",
        "privacy_legal_reviewer",
        "security_upload_reviewer",
        "ai_safety_reviewer",
        "report_language_reviewer",
        "payment_billing_reviewer",
    }
    reviewer_lanes = {row.get("reviewer_lane_id") for row in production_expert_review.get("reviewer_profiles", [])}
    if reviewer_lanes != expected_reviewer_lanes:
        print("Product project check: FAIL")
        print("production expert review profile lanes are incomplete")
        return 1
    for profile in production_expert_review.get("reviewer_profiles", []):
        if (
            profile.get("profile_status") != "missing_real_reviewer"
            or profile.get("credential_status") != "missing"
            or not profile.get("required_credential_evidence")
            or not profile.get("source_requirements")
            or profile.get("can_open_external_claim_gate") is not False
        ):
            print("Product project check: FAIL")
            print(f"reviewer profile {profile.get('reviewer_lane_id')} should require credentials and keep gates closed")
            return 1
    for request in production_expert_review.get("review_requests", []):
        if (
            request.get("status") != "draft_ready_to_send_no_external_effect"
            or request.get("scoped_review_link_status") != "token_required_not_sent"
            or request.get("external_effects_created") is not False
            or request.get("claims_opened") is not False
            or "tariff_confirmed" not in request.get("out_of_scope_claims", [])
        ):
            print("Product project check: FAIL")
            print(f"review request {request.get('review_request_id')} should be draft-only and scoped")
            return 1
    for template in production_expert_review.get("finding_templates", []):
        if template.get("can_open_external_claim_gate") is not False or not template.get("evidence_attachments_required"):
            print("Product project check: FAIL")
            print(f"finding template {template.get('finding_template_id')} should require evidence and keep gates closed")
            return 1
    for finding in production_expert_review.get("pending_findings", []):
        if (
            finding.get("status") != "awaiting_real_reviewer_finding"
            or finding.get("decision") != "not_submitted"
            or finding.get("claims_opened") is not False
            or finding.get("external_effects_created") is not False
        ):
            print("Product project check: FAIL")
            print(f"pending finding {finding.get('finding_id')} should not record a reviewer decision")
            return 1
    for impact in production_expert_review.get("gate_impacts", []):
        if impact.get("can_show_after_local_request_only") is not False or impact.get("can_open_external_claim_gate") is not False:
            print("Product project check: FAIL")
            print(f"gate impact {impact.get('gate_impact_id')} should not open claims")
            return 1
    if (
        production_reports.get("status") != "production_reports_engine_ready_cited_exports_blocked_claims_visible"
        or production_reports.get("report_type_count") != 12
        or production_reports.get("report_record_count", 0) < 12
        or production_reports.get("export_record_count", 0) < 36
        or production_reports.get("citation_record_count", 0) < 24
        or production_reports.get("blocked_claim_sections_required") is not True
        or production_reports.get("html_preview_supported") is not True
        or production_reports.get("pdf_export_supported") is not True
        or production_reports.get("json_export_supported") is not True
        or production_reports.get("version_history_supported") is not True
        or production_reports.get("can_hide_blocked_claims") is not False
        or production_reports.get("claims_opened") is not False
        or production_reports.get("external_effects_created") is not False
        or production_reports.get("public_launch_ready") is not False
        or production_reports.get("live_payment_ready") is not False
    ):
        print("Product project check: FAIL")
        print("production reports should export cited report views while keeping blocked claims and gates closed")
        return 1
    expected_report_types = {
        "starter_trade_readiness_packet",
        "market_opportunity_brief",
        "buyer_ready_packet",
        "supplier_document_request",
        "broker_review_packet",
        "missing_evidence_report",
        "blocked_claims_report",
        "country_source_map",
        "source_freshness_report",
        "expert_review_summary",
        "executive_decision_report",
        "audit_export",
    }
    report_types = {row.get("report_type") for row in production_reports.get("report_records", [])}
    if report_types != expected_report_types:
        print("Product project check: FAIL")
        print("production reports are missing required report types")
        return 1
    citation_types = {row.get("citation_type") for row in production_reports.get("citation_records", [])}
    if not {"source", "evidence"}.issubset(citation_types):
        print("Product project check: FAIL")
        print("production reports should include source and evidence citations")
        return 1
    for record in production_reports.get("report_records", []):
        if (
            record.get("watermark") != "DRAFT - NOT APPROVAL"
            or record.get("review_status") != "not_reviewed"
            or record.get("blocked_claim_section_included") is not True
            or record.get("can_hide_blocked_claims") is not False
            or record.get("blocked_claim_count", 0) < 1
            or record.get("citation_count", 0) < 1
            or record.get("claims_opened") is not False
            or record.get("external_effects_created") is not False
        ):
            print("Product project check: FAIL")
            print(f"production report {record.get('report_id')} should keep citations, watermark, and blocked claims")
            return 1
    for export in production_reports.get("export_records", []):
        export_path = PROJECT / str(export.get("path", ""))
        if not export_path.exists():
            print("Product project check: FAIL")
            print(f"production report export missing: {export.get('path')}")
            return 1
        if export.get("format") == "pdf" and not export_path.read_bytes().startswith(b"%PDF"):
            print("Product project check: FAIL")
            print(f"production report PDF is invalid: {export.get('path')}")
            return 1
        if (
            export.get("blocked_claim_section_included") is not True
            or export.get("claims_opened") is not False
            or export.get("external_effects_created") is not False
        ):
            print("Product project check: FAIL")
            print(f"production report export {export.get('path')} should keep blocked claims and gates closed")
            return 1
    if (
        production_portals.get("status") != "production_portal_workflow_engine_ready_routes_gated_business_owner_ux"
        or production_portals.get("portal_count") != 6
        or production_portals.get("workflow_count") != 6
        or production_portals.get("first_screen_option_count") != 4
        or production_portals.get("all_required_routes_present") is not True
        or production_portals.get("first_screen_routes_present") is not True
        or production_portals.get("plain_language_required") is not True
        or production_portals.get("accessibility_review_required") is not True
        or production_portals.get("mobile_review_required") is not True
        or production_portals.get("confusion_testing_required") is not True
        or production_portals.get("claims_opened") is not False
        or production_portals.get("external_effects_created") is not False
        or production_portals.get("public_launch_ready") is not False
        or production_portals.get("live_payment_ready") is not False
        or production_portals.get("unrestricted_uploads_enabled") is not False
    ):
        print("Product project check: FAIL")
        print("production portal workflows should cover routes and keep public/payment/approval gates closed")
        return 1
    expected_portals = {
        "public_portal",
        "exporter_portal",
        "importer_portal",
        "expert_reviewer_portal",
        "operator_admin_portal",
        "enterprise_portal",
    }
    if {row.get("portal_id") for row in production_portals.get("portal_records", [])} != expected_portals:
        print("Product project check: FAIL")
        print("production portal personas are incomplete")
        return 1
    first_labels = {row.get("label") for row in production_portals.get("first_screen_options", [])}
    if first_labels != {"Explore a market", "Prepare a buyer packet", "Check my documents", "Prepare for broker/expert review"}:
        print("Product project check: FAIL")
        print("production portal first screen options are incorrect")
        return 1
    for portal in production_portals.get("portal_records", []):
        if portal.get("route_coverage_status") != "covered" or portal.get("can_open_approval_payment_or_launch_gate") is not False:
            print("Product project check: FAIL")
            print(f"portal {portal.get('portal_id')} should be route-covered and gate-closed")
            return 1
    for check in production_portals.get("ux_checks", []):
        if check.get("passed") is not True:
            print("Product project check: FAIL")
            print(f"portal UX check failed: {check.get('check_id')}")
            return 1
    for control in production_portals.get("gate_controls", []):
        if (
            control.get("public_launch_ready") is not False
            or control.get("unrestricted_uploads_enabled") is not False
            or control.get("live_payment_enabled") is not False
            or control.get("approval_claims_enabled") is not False
            or control.get("claims_opened") is not False
            or control.get("external_effects_created") is not False
        ):
            print("Product project check: FAIL")
            print(f"portal gate control {control.get('gate_control_id')} should stay closed")
            return 1
    if (
        production_enterprise.get("status") != "production_enterprise_api_platform_ready_local_contracts_external_gates_closed"
        or production_enterprise.get("api_contract_count", 0) < 17
        or production_enterprise.get("all_required_api_routes_present") is not True
        or production_enterprise.get("research_reference_count") != 5
        or production_enterprise.get("workspace_control_count", 0) < 3
        or production_enterprise.get("api_key_record_count", 0) < 2
        or production_enterprise.get("webhook_record_count", 0) < 2
        or production_enterprise.get("hosted_enterprise_ready") is not False
        or production_enterprise.get("live_api_keys_issued") is not False
        or production_enterprise.get("webhook_delivery_enabled") is not False
        or production_enterprise.get("unrestricted_uploads_enabled") is not False
        or production_enterprise.get("white_label_claims_approved") is not False
        or production_enterprise.get("claims_opened") is not False
        or production_enterprise.get("external_effects_created") is not False
    ):
        print("Product project check: FAIL")
        print("production enterprise API platform should be route-covered, researched, and gate-closed")
        return 1
    for contract in production_enterprise.get("api_contracts", []):
        if (
            contract.get("route_present") is not True
            or contract.get("auth_required") is not True
            or contract.get("tenant_filter_required") is not True
            or contract.get("object_level_authorization_required") is not True
            or contract.get("claim_gate_required") is not True
            or contract.get("external_effects_created") is not False
            or contract.get("claims_opened") is not False
            or contract.get("live_mode_enabled") is not False
        ):
            print("Product project check: FAIL")
            print(f"enterprise API contract {contract.get('path')} should be auth/tenant/claim gated and effect-closed")
            return 1
    for row in production_enterprise.get("api_key_records", []):
        if row.get("raw_secret_returned") is not False or row.get("live_key_issued") is not False:
            print("Product project check: FAIL")
            print(f"enterprise API key {row.get('api_key_id')} should not issue a live secret")
            return 1
    for row in production_enterprise.get("webhook_records", []):
        if row.get("delivery_enabled") is not False or row.get("external_effects_created") is not False:
            print("Product project check: FAIL")
            print(f"enterprise webhook {row.get('webhook_id')} should keep delivery closed")
            return 1
    if "remove blocked claims" not in production_enterprise.get("white_label_policy", {}).get("forbidden_customization", []):
        print("Product project check: FAIL")
        print("enterprise white-label policy should forbid removing blocked claims")
        return 1
    if (
        production_payments.get("status") != "production_payment_monetization_engine_ready_live_checkout_closed"
        or production_payments.get("pricing_tier_count") != 7
        or production_payments.get("research_reference_count") != 5
        or production_payments.get("blocked_payment_gate_count") != production_payments.get("payment_gate_count")
        or production_payments.get("external_charge_created") is not False
        or production_payments.get("live_checkout_enabled") is not False
        or production_payments.get("live_payment_ready") is not False
        or production_payments.get("checkout_url_created") is not False
        or production_payments.get("webhook_delivery_enabled") is not False
        or production_payments.get("claims_opened") is not False
        or production_payments.get("public_launch_ready") is not False
        or "prepared trade readiness packet" not in production_payments.get("allowed_paid_scope", [])
        or "customs approval" not in production_payments.get("forbidden_paid_scope", [])
    ):
        print("Product project check: FAIL")
        print("production payment monetization should charge only for preparation and keep live checkout closed")
        return 1
    for tier in production_payments.get("pricing_tiers", []):
        if tier.get("paid") and (
            tier.get("can_charge_for_approval") is not False
            or tier.get("live_checkout_enabled") is not False
            or "tariff confirmation" not in tier.get("forbidden_scope", [])
        ):
            print("Product project check: FAIL")
            print(f"paid tier {tier.get('tier_id')} should not charge for approval")
            return 1
    for webhook in production_payments.get("webhook_controls", []):
        if (
            webhook.get("delivery_enabled") is not False
            or webhook.get("external_effects_created") is not False
            or webhook.get("signature_verification_required") is not True
            or webhook.get("idempotency_required") is not True
            or webhook.get("duplicate_event_handling_required") is not True
            or webhook.get("out_of_order_event_handling_required") is not True
        ):
            print("Product project check: FAIL")
            print(f"payment webhook {webhook.get('event_type')} should stay closed and robust")
            return 1
    if (
        production_trust.get("status") != "production_security_privacy_reliability_engine_ready_local_controls_external_trust_gates_closed"
        or production_trust.get("trust_control_count", 0) < 15
        or production_trust.get("research_reference_count", 0) < 9
        or production_trust.get("blocked_trust_gate_count") != production_trust.get("trust_gate_count")
        or production_trust.get("unapproved_vendor_count") != production_trust.get("vendor_record_count")
        or production_trust.get("real_file_uploads_allowed") is not False
        or production_trust.get("unrestricted_uploads_enabled") is not False
        or production_trust.get("hosted_private_beta_ready") is not False
        or production_trust.get("production_trust_approved") is not False
        or production_trust.get("public_launch_ready") is not False
    ):
        print("Product project check: FAIL")
        print("production trust should map controls while keeping real-file, hosted, and public gates closed")
        return 1
    for key in (
        "managed_auth_ready",
        "admin_mfa_enforced",
        "hosted_secure_sessions_ready",
        "hosted_rate_limits_enforced",
        "private_object_storage_ready",
        "malware_scanning_ready",
        "production_audit_log_ready",
        "retention_policy_approved",
        "vendor_register_approved",
        "production_backup_restore_passed",
        "production_monitoring_ready",
        "incident_runbook_rehearsed",
        "secrets_manager_ready",
        "data_residency_approved",
    ):
        if production_trust.get(key) is not False:
            print("Product project check: FAIL")
            print(f"production trust expected {key}=false")
            return 1
    backup_drill = production_trust.get("backup_restore_drill", {})
    if (
        backup_drill.get("status") != "local_backup_restore_hash_drill_passed"
        or backup_drill.get("production_backup_restore_test_passed") is not False
        or backup_drill.get("hash_match_count") != backup_drill.get("existing_artifact_count")
    ):
        print("Product project check: FAIL")
        print("production trust local restore drill should pass without claiming production restore proof")
        return 1
    for vendor in production_trust.get("vendor_register", []):
        if vendor.get("production_approved") is not False or vendor.get("customer_data_allowed") is not False:
            print("Product project check: FAIL")
            print(f"vendor {vendor.get('vendor_id')} should not be production-approved")
            return 1
    for gate in production_trust.get("trust_gates", []):
        if gate.get("state") != "blocked" or gate.get("opened_by_local_artifact") is not False:
            print("Product project check: FAIL")
            print(f"trust gate {gate.get('gate_id')} should stay blocked")
            return 1
    if (
        production_launch.get("status") != "production_launch_control_plane_ready_exact_scope_public_launch_blocked"
        or production_launch.get("launch_gate_count") != 13
        or production_launch.get("blocked_launch_gate_count", 0) < 8
        or production_launch.get("public_scope_candidate_count") != 6
        or production_launch.get("blocked_public_scope_count") != 8
        or production_launch.get("exact_public_scope_approved") is not False
        or production_launch.get("public_launch_approved") is not False
        or production_launch.get("activation_allowed") is not False
        or production_launch.get("external_claims_opened") is not False
    ):
        print("Product project check: FAIL")
        print("production launch control plane should keep exact public scope and activation blocked")
        return 1
    for key in (
        "hosted_private_beta_ready",
        "production_infrastructure_ready",
        "real_user_evidence_ready",
        "payment_activation_ready",
        "final_owner_approval_recorded",
    ):
        if production_launch.get(key) is not False:
            print("Product project check: FAIL")
            print(f"production launch expected {key}=false")
            return 1
    blocked_scope_ids = {row.get("scope_id") for row in production_launch.get("blocked_public_scope", [])}
    for required in ("unrestricted_real_uploads", "live_payments", "automated_outreach", "buyer_validated_language", "supplier_verified_language"):
        if required not in blocked_scope_ids:
            print("Product project check: FAIL")
            print(f"production launch blocked scope missing {required}")
            return 1
    for row in production_launch.get("public_scope_candidates", []):
        if row.get("activation_allowed") is not False:
            print("Product project check: FAIL")
            print(f"public scope candidate {row.get('scope_id')} should remain activation-blocked")
            return 1
    final_owner = next((row for row in production_launch.get("launch_gates", []) if row.get("gate_id") == "final_owner_gate"), {})
    if final_owner.get("state") != "blocked":
        print("Product project check: FAIL")
        print("final owner gate should remain blocked")
        return 1
    external_validation_pdf = PROJECT / "output" / "pdf" / "external_validation_requirements.pdf"
    if not external_validation_pdf.exists() or not external_validation_pdf.read_bytes().startswith(b"%PDF"):
        print("Product project check: FAIL")
        print("external validation PDF is missing or invalid")
        return 1
    external_validation_reviewer_brief_pdf = PROJECT / "output" / "pdf" / "external_validation_reviewer_brief.pdf"
    if not external_validation_reviewer_brief_pdf.exists() or not external_validation_reviewer_brief_pdf.read_bytes().startswith(b"%PDF"):
        print("Product project check: FAIL")
        print("external validation reviewer brief PDF is missing or invalid")
        return 1
    go_live_input_pdf = PROJECT / "output" / "pdf" / "go_live_input_requests.pdf"
    if not go_live_input_pdf.exists() or not go_live_input_pdf.read_bytes().startswith(b"%PDF"):
        print("Product project check: FAIL")
        print("go-live input request PDF is missing or invalid")
        return 1
    reviewer_brief_md = (PROJECT / "docs" / "EXTERNAL_VALIDATION_REVIEWER_BRIEF.md").read_text(encoding="utf-8")
    for jargon in ("blocker", "gate"):
        if jargon in reviewer_brief_md.lower():
            print("Product project check: FAIL")
            print(f"external validation reviewer brief should avoid reviewer-facing jargon: {jargon}")
            return 1
    if go_live_input_templates.get("status") != "go_live_input_templates_ready":
        print("Product project check: FAIL")
        print("go-live input templates must be ready")
        return 1
    if go_live_input_templates.get("template_count") != 8:
        print("Product project check: FAIL")
        print("go-live input templates must cover the eight review areas")
        return 1
    if (
        go_live_input_readiness.get("status") != "waiting_for_real_inputs_not_ready_yet"
        or go_live_input_readiness.get("public_launch_ready") is not False
        or go_live_input_readiness.get("missing_input_count") != 8
    ):
        print("Product project check: FAIL")
        print("go-live input readiness must wait for eight real returned inputs before public launch")
        return 1
    go_live_input_md = (PROJECT / "docs" / "GO_LIVE_INPUT_REQUESTS.md").read_text(encoding="utf-8")
    if "Once Inputs Are Received" not in go_live_input_md or "external_inputs/" not in go_live_input_md:
        print("Product project check: FAIL")
        print("go-live input request doc must explain how returned inputs are used")
        return 1
    if (
        production_market_readiness.get("status") != "production_market_readiness_evidence_room_ready_inputs_mapped_gates_closed"
        or production_market_readiness.get("gate_count") != 8
        or production_market_readiness.get("work_order_count") != 8
        or production_market_readiness.get("reviewer_brief_card_count") != 8
        or production_market_readiness.get("missing_input_count") != go_live_input_readiness.get("missing_input_count")
        or production_market_readiness.get("source_anchor_count", 0) < 24
        or production_market_readiness.get("input_capture_enabled_local") is not True
        or production_market_readiness.get("input_capture_route") != "/api/market-readiness/inputs"
        or production_market_readiness.get("input_form_contract", {}).get("status") != "market_readiness_input_form_contract_ready"
        or production_market_readiness.get("input_ledger_status") != "production_market_readiness_input_ledger_ready_claims_closed"
        or production_market_readiness.get("input_ledger_route") != "/api/market-readiness/input-ledger"
        or production_market_readiness.get("input_history_status") != "production_market_readiness_input_history_ready_local_audit_trail"
        or production_market_readiness.get("input_history_route") != "/api/market-readiness/input-history"
    ):
        print("Product project check: FAIL")
        print("market readiness evidence room must map all real-world inputs, work orders, source anchors, local input capture, and input ledger")
        return 1
    unaccepted_input_areas = (
        production_market_readiness_input_ledger.get("review_area_count", 0)
        - production_market_readiness_input_ledger.get("accepted_area_count", 0)
    )
    if (
        production_market_readiness_input_ledger.get("status") != "production_market_readiness_input_ledger_ready_claims_closed"
        or production_market_readiness_input_ledger.get("review_area_count") != 8
        or production_market_readiness_input_ledger.get("accepted_area_count") != production_market_readiness.get("ready_input_count")
        or unaccepted_input_areas != production_market_readiness.get("missing_input_count")
        or production_market_readiness_input_ledger.get("claims_opened_by_ledger") is not False
        or production_market_readiness_input_ledger.get("public_launch_ready_by_ledger") is not False
        or production_market_readiness_input_ledger.get("invalid_record_count") != 0
    ):
        print("Product project check: FAIL")
        print("market readiness input ledger must track returned-input quality without opening claims")
        return 1
    if (
        production_market_readiness_input_history.get("status") != "production_market_readiness_input_history_ready_local_audit_trail"
        or production_market_readiness_input_history.get("claims_opened_by_history") is not False
        or production_market_readiness_input_history.get("invalid_history_record_count") != 0
    ):
        print("Product project check: FAIL")
        print("market readiness input history must preserve returned-input iterations without opening claims")
        return 1
    for key in (
        "public_launch_ready",
        "hosted_private_beta_ready",
        "live_payment_ready",
        "launch_control_activation_allowed",
        "exact_public_scope_approved",
        "external_effects_created",
        "claims_opened_by_room",
        "market_ready_claim_allowed",
    ):
        if production_market_readiness.get(key) is not False:
            print("Product project check: FAIL")
            print(f"market readiness evidence room expected {key}=false")
            return 1
    market_work_orders = production_market_readiness.get("work_orders", [])
    if {row.get("gate_id") for row in market_work_orders} != expected_external_validation_gates:
        print("Product project check: FAIL")
        print("market readiness evidence room missing expected work-order gate IDs")
        return 1
    allowed_market_input_states = {"missing_real_input", "real_input_received_for_scope_review"}
    if any(row.get("input_state") not in allowed_market_input_states for row in market_work_orders):
        print("Product project check: FAIL")
        print("market readiness evidence room should show missing or scoped-received input states only")
        return 1
    if any(row.get("claims_opened_by_this_work_order") is not False for row in market_work_orders):
        print("Product project check: FAIL")
        print("market readiness work orders must not open claims")
        return 1
    if "market_ready" not in production_market_readiness.get("blocked_claims", []):
        print("Product project check: FAIL")
        print("market readiness evidence room must keep market_ready blocked")
        return 1
    if reviewer_wave_plan.get("status") != "reviewer_wave_execution_plan_ready" or reviewer_wave_plan.get("wave_count") != 3:
        print("Product project check: FAIL")
        print("reviewer wave execution plan must include three gated waves")
        return 1
    if private_beta_smoke.get("status") != "private_beta_smoke_test_plan_ready_blocked_until_wave_1_and_staging":
        print("Product project check: FAIL")
        print("private beta smoke plan must remain blocked until Wave 1 and staging proof")
        return 1
    if (
        external_review.get("status") != "external_review_ready_findings_pending"
        or external_review.get("actual_external_review_completed") is not False
        or external_review.get("required_review_count") != 9
        or external_review.get("completed_review_count") != 0
        or external_review.get("pending_review_count") != 9
        or external_review.get("private_beta_blocked_until_wave_1_complete") is not True
        or external_review.get("public_launch_ready") is not False
        or external_review.get("unsafe_gates_closed") is not True
    ):
        print("Product project check: FAIL")
        print("external review report must stay pending with private-beta/public-launch gates closed")
        return 1
    if (
        external_review_summary.get("actual_external_review_completed") is not False
        or external_review_summary.get("completed_review_count") != 0
        or len(external_review_blockers) != 9
    ):
        print("Product project check: FAIL")
        print("external review summary/blocker ledger does not match pending review truth")
        return 1
    if any(row.get("gate") != "closed" or row.get("unsafe_to_bypass") is not True for row in external_review_blockers):
        print("Product project check: FAIL")
        print("external review blocker ledger must keep all reviewer gates closed")
        return 1
    if (
        ai_assisted_review.get("status") != "ai_assisted_external_review_ready"
        or ai_assisted_review.get("solo_developer_mode") is not True
        or ai_assisted_review.get("human_equivalent_approval") is not False
        or ai_assisted_review.get("can_open_private_beta_gate") is not False
        or ai_assisted_review.get("can_open_public_launch_gate") is not False
        or ai_assisted_review.get("can_reduce_findings_before_real_review") is not True
        or ai_assisted_review.get("required_role_count") != 9
    ):
        print("Product project check: FAIL")
        print("AI-assisted review plan must support solo review without opening approval gates")
        return 1
    if (
        ai_assisted_review.get("wave_1_simulated_review_status") != "ai_assisted_wave_1_reviewed_with_blockers"
        or ai_assisted_review.get("simulated_review_count") != 5
        or ai_assisted_review.get("simulated_finding_count") != 5
    ):
        print("Product project check: FAIL")
        print("AI-assisted review plan must record five Wave 1 simulated blocker findings")
        return 1
    if (
        ai_assisted_findings.get("status") != "ai_assisted_wave_1_reviewed_with_blockers"
        or ai_assisted_findings.get("review_origin") != "ai_assisted_simulated_review"
        or ai_assisted_findings.get("real_external_review_count") != 0
        or ai_assisted_findings.get("human_equivalent_approval") is not False
        or ai_assisted_findings.get("can_open_private_beta_gate") is not False
        or ai_assisted_findings.get("can_open_public_launch_gate") is not False
        or ai_assisted_findings.get("simulated_review_count") != 5
        or ai_assisted_findings.get("simulated_finding_count") != 5
        or ai_assisted_findings.get("private_beta_blocking_findings") != 5
    ):
        print("Product project check: FAIL")
        print("AI-assisted findings must be five simulated Wave 1 blockers with real approval gates closed")
        return 1
    simulated_reviews = ai_assisted_findings.get("simulated_reviews", [])
    if {row.get("reviewer_role") for row in simulated_reviews} != EXPECTED_WAVE_1_REVIEW_ROLES:
        print("Product project check: FAIL")
        print("AI-assisted findings missing one or more Wave 1 reviewer roles")
        return 1
    for review in simulated_reviews:
        if review.get("review_origin") != "ai_assisted_simulated_review" or review.get("verdict") != "blocked":
            print("Product project check: FAIL")
            print("AI-assisted review rows must stay simulated and blocked")
            return 1
        for finding in review.get("findings", []):
            missing = REQUIRED_AI_ASSISTED_FINDING_FIELDS - set(finding)
            if (
                missing
                or finding.get("review_origin") != "ai_assisted_simulated_review"
                or finding.get("human_followup_required") is not True
                or finding.get("blocks_private_beta") is not True
                or finding.get("blocks_public_launch") is not True
            ):
                print("Product project check: FAIL")
                print("AI-assisted simulated findings must be complete blockers requiring human follow-up")
                return 1
    operation_coverage = product_operations.get("execution_coverage", {})
    for key in (
        "data_intake",
        "research_execution",
        "evidence_reporting",
        "expert_review_routing",
        "team_workspace_activity",
        "billing_metering",
        "agent_tool_execution",
        "launch_control_event",
        "persistence_refresh",
    ):
        if operation_coverage.get(key) is not True:
            print("Product project check: FAIL")
            print(f"product operations missing coverage for {key}")
            return 1
    if not isinstance(research_runs, list) or not research_runs:
        print("Product project check: FAIL")
        print("research execution run log is empty")
        return 1
    if not isinstance(expert_work_orders, list) or not expert_work_orders:
        print("Product project check: FAIL")
        print("expert review work orders are missing")
        return 1
    if not isinstance(team_activity, list) or not team_activity:
        print("Product project check: FAIL")
        print("team workspace activity is missing")
        return 1
    if not isinstance(launch_events, list) or not launch_events:
        print("Product project check: FAIL")
        print("launch operation events are missing")
        return 1
    if any(row.get("public_launch_allowed") is not False for row in launch_events):
        print("Product project check: FAIL")
        print("launch operation events opened public launch")
        return 1
    store_path = PROJECT / "system_review_graph" / "customer_workflow.sqlite"
    with sqlite3.connect(store_path) as conn:
        tables = {
            row[0]
            for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
        }
    required_tables = {
        "source_packets",
        "evidence_items",
        "official_sources",
        "claims",
        "blockers",
        "review_runs",
        "review_requests",
        "report_exports",
        "users",
        "organizations",
        "memberships",
        "gate_decisions",
        "audit_events",
    }
    if not required_tables.issubset(tables):
        print("Product project check: FAIL")
        print("customer workflow sqlite store missing required tables")
        return 1
    policy_store_path = PROJECT / "system_review_graph" / "policy_intelligence.sqlite"
    with sqlite3.connect(policy_store_path) as conn:
        policy_tables = {
            row[0]
            for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
        }
    required_policy_tables = {
        "monitored_sources",
        "source_snapshots",
        "source_change_classifications",
        "packet_source_impacts",
        "stale_source_blockers",
    }
    if not required_policy_tables.issubset(policy_tables):
        print("Product project check: FAIL")
        print("policy intelligence sqlite store missing required tables")
        return 1

    print("Product project check: PASS")
    print(f"project={PROJECT.relative_to(ROOT)}")
    print(f"status={report['status']}")
    print(f"blocker_count={report['blocker_count']}")
    print(f"external_blocker_count={external['blocker_count']}")
    print(f"continuation_lanes={continuation['lane_count']}")
    print(f"startup_status={continuation['status']}")
    print(f"vc_pitch_status={vc_pitch['status']}")
    print(f"board_go_live_status={board['status']}")
    print(f"operator_workflow_status={workflow['status']}")
    print(f"operator_work_queue_count={workflow['work_queue_count']}")
    print(f"operator_screenshots={screenshot_manifest['screenshot_count']}")
    print(f"customer_workflow_status={customer['status']}")
    print(f"customer_packet_count={customer['packet_count']}")
    print(f"customer_blocker_count={customer['blocker_count']}")
    print(f"customer_blocker_groups={len(customer['blocker_groups'])}")
    print(f"evidence_ledger_status={evidence_ledger['status']}")
    print(f"runtime_status={runtime['status']}")
    print(f"public_surface_status={runtime['public_product_surface']['status']}")
    print(f"runtime_users={len(runtime['users'])}")
    print(f"ai_policy_status={ai_data_policy['status']}")
    print(f"ai_router_status={ai_model_router['status']}")
    print(f"requirements_traceability={len(requirements_traceability['requirements'])}")
    print(f"public_trade_manifest={public_trade['status']}")
    print(f"exporter_mode_manifest={exporter_mode['status']}")
    print(f"policy_monitor={policy_monitor['status']}")
    print(f"completion_platform={completion['status']}")
    print(f"opportunity_scanner={opportunity_scanner['status']}")
    print(f"business_logic={business_logic['status']}")
    print("requirements_docs=current_state_set_ready")
    print(f"country_coverage={country_coverage['status']}")
    print(f"transport_readiness={transport_readiness['status']}")
    print(f"billing_controls={billing_controls['status']}")
    print(f"agent_api={agent_api['status']}")
    print(f"traffic_pages={len(traffic_pages['pages'])}")
    print(f"all_stages={all_stages['status']}")
    print(f"research_execution={research_execution['status']}")
    print(f"team_workspace={team_workspace['status']}")
    print(f"expert_network={expert_network['status']}")
    print(f"billing_usage={billing_usage['status']}")
    print(f"agent_gateway={agent_gateway['status']}")
    print(f"launch_operations={launch_operations['status']}")
    print(f"product_operations={product_operations['status']}")
    print(f"product_operation_count={product_operations['operation_count']}")
    print(f"final_go_live_status={final_go_live['status']}")
    print(f"final_public_launch_ready={final_go_live['public_launch_ready']}")
    print(f"current_external_source_anchors={current_sources['source_count']}")
    print(f"external_validation_status={external_validation['status']}")
    print(f"external_validation_gates={external_validation['gate_count']}")
    print(f"external_validation_evidence_requirements={external_validation['evidence_requirement_count']}")
    print(f"production_redevelopment_status={production_redevelopment['status']}")
    print(f"production_redevelopment_layers={production_redevelopment['production_layer_count']}")
    print(f"production_redevelopment_phases={production_redevelopment['phase_count']}")
    print(f"production_redevelopment_sources={production_redevelopment['research_anchor_count']}")
    print(f"production_data_model_status={production_data_model['status']}")
    print(f"production_data_model_tables={production_data_model['table_count']}")
    print(f"production_data_model_foreign_keys={production_data_model['foreign_key_count']}")
    print(f"production_data_model_rls_tables={production_data_model['row_level_security_table_count']}")
    print(f"production_packet_engine_status={production_packet_engine['status']}")
    print(f"production_packet_engine_packets={production_packet_engine['packet_count']}")
    print(f"production_packet_engine_views={production_packet_engine['packet_view_count']}")
    print(f"production_packet_engine_events={production_packet_engine['packet_event_count']}")
    print(f"production_persistence_status={production_persistence['status']}")
    print(f"production_persistence_rows={production_persistence['total_row_count']}")
    print(f"production_persistence_validation_errors={production_persistence['validation_error_count']}")
    print(f"production_persistence_hosted_postgres_ready={production_persistence['hosted_postgres_ready']}")
    print(f"production_country_source_engine_status={production_country_source_engine['status']}")
    print(f"production_country_packs={production_country_source_engine['country_pack_count']}")
    print(f"production_source_lifecycle_rows={production_country_source_engine['source_lifecycle_count']}")
    print(f"production_trade_discovery_status={production_trade_discovery['status']}")
    print(f"production_trade_discovery_categories={production_trade_discovery['category_count']}")
    print(f"production_trade_discovery_country_lanes={production_trade_discovery['country_lane_count']}")
    print(f"production_trade_discovery_beginner_flows={production_trade_discovery['beginner_flow_count']}")
    print(f"production_trade_data_catalog_status={production_trade_data_catalog['status']}")
    print(f"production_trade_data_catalog_templates={production_trade_data_catalog['template_count']}")
    print(f"production_trade_data_catalog_work_orders={production_trade_data_catalog['query_work_order_count']}")
    print(f"production_market_intelligence_status={production_market_intelligence['status']}")
    print(f"production_market_signals={production_market_intelligence['market_signal_count']}")
    print(f"production_market_dataset_connectors={production_market_intelligence['dataset_connector_count']}")
    print(f"production_market_readiness_status={production_market_readiness['status']}")
    print(f"production_market_readiness_work_orders={production_market_readiness['work_order_count']}")
    print(f"production_market_readiness_missing_inputs={production_market_readiness['missing_input_count']}")
    print(f"production_market_readiness_input_ledger={production_market_readiness_input_ledger['status']}")
    print(f"production_market_readiness_input_history={production_market_readiness_input_history['status']}")
    print(f"production_evidence_claim_gate_status={production_evidence_claim_gate['status']}")
    print(f"production_evidence_claim_gate_decisions={production_evidence_claim_gate['claim_gate_decision_count']}")
    print(f"production_evidence_claim_gate_safe_claims={production_evidence_claim_gate['safe_research_claim_count']}")
    print(f"production_decision_scoring_status={production_decision_scoring['status']}")
    print(f"production_decision_score_records={production_decision_scoring['decision_score_record_count']}")
    print(f"production_decision_single_global_score={production_decision_scoring['single_global_readiness_score_created']}")
    print(f"production_ai_copilot_status={production_ai_copilot['status']}")
    print(f"production_ai_roles={production_ai_copilot['ai_role_count']}")
    print(f"production_ai_live_model_calls={production_ai_copilot['live_model_calls_enabled']}")
    print(f"production_expert_review_status={production_expert_review['status']}")
    print(f"production_expert_reviewer_lanes={production_expert_review['reviewer_lane_count']}")
    print(f"production_expert_real_signoff_recorded={production_expert_review['real_reviewer_signoff_recorded']}")
    print(f"production_reports_status={production_reports['status']}")
    print(f"production_report_types={production_reports['report_type_count']}")
    print(f"production_report_exports={production_reports['export_record_count']}")
    print(f"production_portals_status={production_portals['status']}")
    print(f"production_portal_count={production_portals['portal_count']}")
    print(f"production_portal_routes_present={production_portals['all_required_routes_present']}")
    print(f"production_enterprise_status={production_enterprise['status']}")
    print(f"production_enterprise_api_contracts={production_enterprise['api_contract_count']}")
    print(f"production_enterprise_routes_present={production_enterprise['all_required_api_routes_present']}")
    print(f"production_payments_status={production_payments['status']}")
    print(f"production_payment_tiers={production_payments['pricing_tier_count']}")
    print(f"production_live_checkout_enabled={production_payments['live_checkout_enabled']}")
    print(f"production_trust_status={production_trust['status']}")
    print(f"production_trust_controls={production_trust['trust_control_count']}")
    print(f"production_real_file_uploads_allowed={production_trust['real_file_uploads_allowed']}")
    print(f"production_launch_status={production_launch['status']}")
    print(f"production_launch_gates={production_launch['launch_gate_count']}")
    print(f"production_public_launch_approved={production_launch['public_launch_approved']}")
    print(f"external_validation_pdf={external_validation_pdf.relative_to(PROJECT)}")
    print(f"external_validation_reviewer_brief_pdf={external_validation_reviewer_brief_pdf.relative_to(PROJECT)}")
    print(f"go_live_input_status={go_live_input_readiness['status']}")
    print(f"go_live_missing_inputs={go_live_input_readiness['missing_input_count']}")
    print(f"go_live_input_pdf={go_live_input_pdf.relative_to(PROJECT)}")
    print(f"external_review_status={external_review['status']}")
    print(f"external_review_required={external_review['required_review_count']}")
    print(f"external_review_completed={external_review['completed_review_count']}")
    print(f"external_review_blockers={len(external_review_blockers)}")
    print(f"ai_assisted_review_status={ai_assisted_review['status']}")
    print(f"ai_assisted_wave_1_status={ai_assisted_findings['status']}")
    print(f"ai_assisted_simulated_reviews={ai_assisted_findings['simulated_review_count']}")
    print(f"ai_assisted_simulated_findings={ai_assisted_findings['simulated_finding_count']}")
    print(f"review_requests={len(review_requests)}")
    print(f"audit_events={len(audit_events['events'])}")
    print(f"deployment_status={deployment['status']}")
    print("customer_store=ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
