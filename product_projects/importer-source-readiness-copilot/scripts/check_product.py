#!/usr/bin/env python3
"""Run the standalone product proof gate."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_BLOCKER_FIELDS = {
    "id",
    "module",
    "issue",
    "owner",
    "evidence",
    "gate",
    "next_valid_move",
    "unsafe_to_bypass",
}
VALID_GATES = {"closed", "open", "not_applicable"}
REQUIRED_EXTERNAL_REVIEW_FIELDS = {
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
}
EXPECTED_REVIEW_ROLES = {
    "UX/Product Usability Review",
    "Security/Public Upload Review",
    "Privacy/Legal Review",
    "AI Safety/Prompt Injection Review",
    "Trade-Boundary/Customs-Language Review",
    "Freight/Logistics Review",
    "Report-Language Review",
    "DevOps/Production Readiness Review",
    "Billing/Payment Review",
}
EXPECTED_WAVE_1_REVIEW_ROLES = {
    "UX/Product Usability Review",
    "Security/Public Upload Review",
    "Privacy/Legal Review",
    "AI Safety/Prompt Injection Review",
    "DevOps/Production Readiness Review",
}
REQUIRED_AI_ASSISTED_FINDING_FIELDS = REQUIRED_EXTERNAL_REVIEW_FIELDS | {
    "review_origin",
    "model_or_agent_used",
    "web_sources_checked",
    "confidence",
    "human_followup_required",
}


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _validate_blockers(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing blocker ledger: {path.relative_to(ROOT)}"]

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"blockers.jsonl:{line_number}: invalid JSON: {exc}")
            continue
        missing = sorted(REQUIRED_BLOCKER_FIELDS - set(row))
        if missing:
            errors.append(f"blockers.jsonl:{line_number}: missing {', '.join(missing)}")
        if row.get("gate") not in VALID_GATES:
            errors.append(f"blockers.jsonl:{line_number}: invalid gate {row.get('gate')!r}")
    return errors


def _validate_blocker_rows(rows: list[dict[str, Any]], label: str) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        missing = sorted(REQUIRED_BLOCKER_FIELDS - set(row))
        if missing:
            errors.append(f"{label}:{index}: missing {', '.join(missing)}")
        if row.get("gate") not in VALID_GATES:
            errors.append(f"{label}:{index}: invalid gate {row.get('gate')!r}")
    return errors


def main() -> int:
    commands = [
        [sys.executable, "-m", "compileall", "-q", "src", "scripts"],
        [sys.executable, "scripts/run_all_artifacts.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "scripts/audit_external_package.py", "--root", "."],
    ]
    for command in commands:
        result = _run(command)
        if result.returncode != 0:
            print("Product check: FAIL")
            print(f"command: {' '.join(command)}")
            print(result.stdout)
            print(result.stderr)
            return result.returncode

    report_path = ROOT / "system_review_graph" / "readiness_report.json"
    report = _load_json(report_path)
    external = _load_json(ROOT / "system_review_graph" / "external_gate_report.json")
    continuation = _load_json(ROOT / "system_review_graph" / "continuation_plan.json")
    vc_pitch = _load_json(ROOT / "system_review_graph" / "vc_pitch_readiness_report.json")
    board = _load_json(ROOT / "system_review_graph" / "board_go_live_readiness_report.json")
    workflow = _load_json(ROOT / "system_review_graph" / "operator_workflow_report.json")
    customer = _load_json(ROOT / "system_review_graph" / "customer_readiness_report.json")
    evidence_ledger = _load_json(ROOT / "system_review_graph" / "evidence_ledger.json")
    runtime = _load_json(ROOT / "system_review_graph" / "product_runtime_state.json")
    auth_rbac = _load_json(ROOT / "system_review_graph" / "auth_rbac_matrix.json")
    claims_gate = _load_json(ROOT / "system_review_graph" / "claims_gate_matrix.json")
    review_requests = _load_json(ROOT / "system_review_graph" / "review_requests.json")
    audit_events = _load_json(ROOT / "system_review_graph" / "audit_events.json")
    deployment = _load_json(ROOT / "system_review_graph" / "deployment_readiness_report.json")
    ai_data_policy = _load_json(ROOT / "system_review_graph" / "ai_data_policy.json")
    ai_model_router = _load_json(ROOT / "system_review_graph" / "ai_model_router.json")
    redaction_pipeline = _load_json(ROOT / "system_review_graph" / "redaction_pipeline.json")
    manual_no_ai_workflow = _load_json(ROOT / "system_review_graph" / "manual_no_ai_workflow.json")
    requirements_traceability = _load_json(ROOT / "system_review_graph" / "requirements_traceability_matrix.json")
    public_trade = _load_json(ROOT / "system_review_graph" / "public_trade_readiness_manifest.json")
    exporter_mode = _load_json(ROOT / "system_review_graph" / "exporter_mode_requirements.json")
    public_reports = _load_json(ROOT / "system_review_graph" / "public_report_types.json")
    public_upload_policy = _load_json(ROOT / "system_review_graph" / "public_upload_policy.json")
    policy_monitor = _load_json(ROOT / "system_review_graph" / "intelligence_hub_policy_monitor.json")
    policy_snapshots = _load_json(ROOT / "system_review_graph" / "policy_source_snapshots.json")
    policy_impact = _load_json(ROOT / "system_review_graph" / "policy_change_impact_report.json")
    completion = _load_json(ROOT / "system_review_graph" / "completion_platform_manifest.json")
    country_coverage = _load_json(ROOT / "system_review_graph" / "country_coverage_report.json")
    opportunity_scanner = _load_json(ROOT / "system_review_graph" / "opportunity_scanner_report.json")
    business_logic = _load_json(ROOT / "system_review_graph" / "business_logic_phase_report.json")
    business_phase_completion = _load_json(ROOT / "system_review_graph" / "business_phase_completion_report.json")
    transport_readiness = _load_json(ROOT / "system_review_graph" / "transport_readiness_report.json")
    billing_controls = _load_json(ROOT / "system_review_graph" / "billing_credit_controls.json")
    agent_api = _load_json(ROOT / "system_review_graph" / "agent_api_manifest.json")
    traffic_pages = _load_json(ROOT / "system_review_graph" / "traffic_pages_manifest.json")
    research_execution = _load_json(ROOT / "system_review_graph" / "research_execution_plan.json")
    team_workspace = _load_json(ROOT / "system_review_graph" / "team_workspace_report.json")
    expert_network = _load_json(ROOT / "system_review_graph" / "expert_network_report.json")
    billing_usage = _load_json(ROOT / "system_review_graph" / "billing_usage_ledger.json")
    agent_gateway = _load_json(ROOT / "system_review_graph" / "agent_api_gateway_contract.json")
    launch_operations = _load_json(ROOT / "system_review_graph" / "launch_operations_report.json")
    all_stages = _load_json(ROOT / "system_review_graph" / "all_stage_readiness_report.json")
    product_operations = _load_json(ROOT / "system_review_graph" / "product_operations_report.json")
    final_go_live = _load_json(ROOT / "system_review_graph" / "final_go_live_decision_report.json")
    current_sources = _load_json(ROOT / "system_review_graph" / "current_external_gate_research.json")
    external_validation = _load_json(ROOT / "system_review_graph" / "external_validation_requirements_report.json")
    external_validation_evidence = _load_json(ROOT / "system_review_graph" / "external_validation_evidence_requirements.json")
    go_live_input_templates = _load_json(ROOT / "system_review_graph" / "go_live_input_templates.json")
    go_live_returned_input_evidence = _load_json(ROOT / "system_review_graph" / "go_live_returned_input_evidence_manifest.json")
    go_live_returned_input_matrix = _load_json(ROOT / "system_review_graph" / "go_live_returned_input_validation_matrix.json")
    hosted_deployment_proof = _load_json(ROOT / "system_review_graph" / "hosted_deployment_proof_manifest.json")
    hosted_deployment_contract = _load_json(ROOT / "system_review_graph" / "hosted_deployment_proof_contract.json")
    hosted_deployment_gate_matrix = _load_json(ROOT / "system_review_graph" / "hosted_deployment_gate_matrix.json")
    hosted_deployment_blockers = _load_jsonl(ROOT / "system_review_graph" / "hosted_deployment_blocker_export.jsonl")
    payment_activation_proof = _load_json(ROOT / "system_review_graph" / "payment_activation_proof_manifest.json")
    payment_activation_contract = _load_json(ROOT / "system_review_graph" / "payment_activation_proof_contract.json")
    payment_activation_gate_matrix = _load_json(ROOT / "system_review_graph" / "payment_activation_gate_matrix.json")
    payment_activation_blockers = _load_jsonl(ROOT / "system_review_graph" / "payment_activation_blocker_export.jsonl")
    legal_privacy_security_approval = _load_json(
        ROOT / "system_review_graph" / "legal_privacy_security_approval_manifest.json"
    )
    legal_privacy_security_approval_contract = _load_json(
        ROOT / "system_review_graph" / "legal_privacy_security_approval_contract.json"
    )
    legal_privacy_security_approval_gate_matrix = _load_json(
        ROOT / "system_review_graph" / "legal_privacy_security_approval_gate_matrix.json"
    )
    legal_privacy_security_approval_blockers = _load_jsonl(
        ROOT / "system_review_graph" / "legal_privacy_security_approval_blocker_export.jsonl"
    )
    qualified_customs_trade_review = _load_json(
        ROOT / "system_review_graph" / "qualified_customs_trade_review_manifest.json"
    )
    qualified_customs_trade_review_contract = _load_json(
        ROOT / "system_review_graph" / "qualified_customs_trade_review_contract.json"
    )
    qualified_customs_trade_review_gate_matrix = _load_json(
        ROOT / "system_review_graph" / "qualified_customs_trade_review_gate_matrix.json"
    )
    qualified_customs_trade_review_blockers = _load_jsonl(
        ROOT / "system_review_graph" / "qualified_customs_trade_review_blocker_export.jsonl"
    )
    production_redevelopment = _load_json(ROOT / "system_review_graph" / "production_redevelopment_plan.json")
    production_research = _load_json(ROOT / "system_review_graph" / "production_research_anchors.json")
    production_data_model = _load_json(ROOT / "system_review_graph" / "production_data_model_manifest.json")
    production_packet_engine = _load_json(ROOT / "system_review_graph" / "production_packet_engine_manifest.json")
    production_persistence = _load_json(ROOT / "system_review_graph" / "production_persistence_snapshot.json")
    production_repository = _load_json(ROOT / "system_review_graph" / "production_repository_service_manifest.json")
    production_country_source_engine = _load_json(ROOT / "system_review_graph" / "production_country_source_engine_manifest.json")
    production_trade_discovery = _load_json(ROOT / "system_review_graph" / "production_trade_discovery_manifest.json")
    production_trade_data_catalog = _load_json(ROOT / "system_review_graph" / "production_trade_data_catalog_manifest.json")
    production_market_intelligence = _load_json(ROOT / "system_review_graph" / "production_market_intelligence_manifest.json")
    production_market_readiness = _load_json(ROOT / "system_review_graph" / "production_market_readiness_evidence_room_manifest.json")
    production_market_readiness_input_ledger = _load_json(ROOT / "system_review_graph" / "production_market_readiness_input_ledger.json")
    production_market_readiness_input_history = _load_json(ROOT / "system_review_graph" / "production_market_readiness_input_history.json")
    production_document_intelligence = _load_json(ROOT / "system_review_graph" / "production_document_intelligence_manifest.json")
    production_document_parser_qa = _load_json(ROOT / "system_review_graph" / "production_document_parser_qa_matrix.json")
    production_document_sample_library = _load_json(ROOT / "system_review_graph" / "production_document_sample_library.json")
    production_evidence_claim_gate = _load_json(ROOT / "system_review_graph" / "production_evidence_claim_gate_manifest.json")
    production_decision_scoring = _load_json(ROOT / "system_review_graph" / "production_decision_scoring_manifest.json")
    production_ai_copilot = _load_json(ROOT / "system_review_graph" / "production_ai_copilot_manifest.json")
    production_expert_review = _load_json(ROOT / "system_review_graph" / "production_expert_review_network_manifest.json")
    production_reports = _load_json(ROOT / "system_review_graph" / "production_reports_engine_manifest.json")
    production_portals = _load_json(ROOT / "system_review_graph" / "production_portal_workflow_manifest.json")
    production_enterprise = _load_json(ROOT / "system_review_graph" / "production_enterprise_api_manifest.json")
    production_api_service = _load_json(ROOT / "system_review_graph" / "production_api_service_manifest.json")
    production_payments = _load_json(ROOT / "system_review_graph" / "production_payment_monetization_manifest.json")
    production_trust = _load_json(ROOT / "system_review_graph" / "production_security_privacy_reliability_manifest.json")
    production_launch = _load_json(ROOT / "system_review_graph" / "production_launch_control_plane_manifest.json")
    official_source_registry = _load_json(ROOT / "data" / "official_source_registry.json")
    business_core_doc = (ROOT / "docs" / "BUSINESS_CORE_LOGIC_CURRENT_STATE.md").read_text(encoding="utf-8")
    functional_doc = (ROOT / "docs" / "FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md").read_text(encoding="utf-8")
    non_functional_doc = (ROOT / "docs" / "NON_FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md").read_text(encoding="utf-8")
    operator_app_source = (ROOT / "src" / "importer_source_readiness" / "operator_app.py").read_text(encoding="utf-8")
    go_live_input_readiness = _load_json(ROOT / "system_review_graph" / "go_live_input_readiness_report.json")
    reviewer_wave_plan = _load_json(ROOT / "system_review_graph" / "reviewer_wave_execution_plan.json")
    private_beta_smoke = _load_json(ROOT / "system_review_graph" / "private_beta_smoke_test_plan.json")
    private_beta_outcome = _load_json(ROOT / "system_review_graph" / "private_beta_outcome_contract.json")
    private_beta_session_schema = _load_json(ROOT / "system_review_graph" / "private_beta_session_evidence_schema.json")
    private_beta_outcome_gate_matrix = _load_json(ROOT / "system_review_graph" / "private_beta_outcome_gate_matrix.json")
    external_review = _load_json(ROOT / "system_review_graph" / "external_review_findings_report.json")
    external_review_intake = _load_json(ROOT / "system_review_graph" / "external_review_returned_findings_manifest.json")
    external_review_intake_contract = _load_json(ROOT / "system_review_graph" / "external_review_returned_finding_contract.json")
    external_review_intake_matrix = _load_json(ROOT / "system_review_graph" / "external_review_returned_review_matrix.json")
    external_review_intake_blockers = _load_jsonl(ROOT / "system_review_graph" / "external_review_returned_blocker_export.jsonl")
    ai_assisted_review = _load_json(ROOT / "system_review_graph" / "ai_assisted_external_review_plan.json")
    ai_assisted_findings = _load_json(ROOT / "system_review_graph" / "ai_assisted_external_review_findings_report.json")
    external_review_summary = _load_json(ROOT / "external_review_findings" / "EXTERNAL_REVIEW_SUMMARY.json")
    external_review_blockers = _load_jsonl(ROOT / "system_review_graph" / "external_review_blocker_ledger.jsonl")
    research_runs = _load_json(ROOT / "system_review_graph" / "research_execution_runs.json")
    expert_work_orders = _load_json(ROOT / "system_review_graph" / "expert_review_work_orders.json")
    team_activity = _load_json(ROOT / "system_review_graph" / "team_workspace_activity.json")
    launch_events = _load_json(ROOT / "system_review_graph" / "launch_operations_events.json")
    screenshot_manifest_path = ROOT / "system_review_graph" / "operator_screenshot_manifest.json"
    screenshot_manifest = _load_json(screenshot_manifest_path) if screenshot_manifest_path.exists() else {}
    expected = {
        "status": "ready_with_external_gates",
        "row_count": 2,
        "blocker_count": 9,
        "blocked_unsafe_rows": 0,
    }
    failures = [
        f"{key} expected {value!r}, got {report.get(key)!r}"
        for key, value in expected.items()
        if report.get(key) != value
    ]
    if external.get("status") != "ready_with_external_gates":
        failures.append(f"external gate status expected ready_with_external_gates, got {external.get('status')!r}")
    if external.get("blocker_count", 0) < 10:
        failures.append("external gate report should include country, buyer, expert, contract, data, and launch blockers")
    if not (ROOT / "system_review_graph" / "operator_dashboard.html").exists():
        failures.append("operator dashboard was not generated")
    else:
        dashboard_html = (ROOT / "system_review_graph" / "operator_dashboard.html").read_text(encoding="utf-8")
        if "Operator Screenshots" not in dashboard_html:
            failures.append("operator dashboard should include the screenshot gallery")
        if "Operator Work Queue" not in dashboard_html:
            failures.append("operator dashboard should include the operator work queue")
        if "Canada Tools" not in dashboard_html:
            failures.append("operator dashboard should link Canadian tool references")
        if "Customer Source Packet Workflow" not in dashboard_html:
            failures.append("operator dashboard should include the customer source-packet workflow")
        if "/packets/packet-frozen-tuna-canada-001" not in dashboard_html:
            failures.append("operator dashboard should link the customer source-packet route")
        if "Path To Private Beta" not in dashboard_html:
            failures.append("operator dashboard should include the private beta path")
        if "Internal logic ready - external claims blocked" not in dashboard_html:
            failures.append("operator dashboard should use safe customer-facing status language")
    for path in (
        "scripts/serve_operator_app.py",
        "src/importer_source_readiness/operator_app.py",
        "src/importer_source_readiness/source_packet_workflow.py",
        "src/importer_source_readiness/customer_store.py",
        "src/importer_source_readiness/product_runtime.py",
        "src/importer_source_readiness/document_processing.py",
        "src/importer_source_readiness/policy_intelligence.py",
        "src/importer_source_readiness/completion_platform.py",
        "src/importer_source_readiness/product_operations.py",
        "src/importer_source_readiness/ai_review_validation.py",
        "src/importer_source_readiness/external_review.py",
        "src/importer_source_readiness/external_review_intake.py",
        "src/importer_source_readiness/external_validation_research.py",
        "src/importer_source_readiness/go_live_input_evidence.py",
        "src/importer_source_readiness/hosted_deployment_proof.py",
        "src/importer_source_readiness/payment_activation_proof.py",
        "src/importer_source_readiness/legal_privacy_security_approval.py",
        "src/importer_source_readiness/qualified_customs_trade_review.py",
        "src/importer_source_readiness/private_beta_outcomes.py",
        "src/importer_source_readiness/production_ai_copilot_engine.py",
        "src/importer_source_readiness/production_country_source_engine.py",
        "src/importer_source_readiness/production_data_model.py",
        "src/importer_source_readiness/production_decision_scoring_engine.py",
        "src/importer_source_readiness/production_document_intelligence_engine.py",
        "src/importer_source_readiness/production_evidence_claim_gate_engine.py",
        "src/importer_source_readiness/production_enterprise_api_platform.py",
        "src/importer_source_readiness/production_api_service.py",
        "src/importer_source_readiness/production_expert_review_network.py",
        "src/importer_source_readiness/production_market_intelligence_engine.py",
        "src/importer_source_readiness/production_market_readiness_evidence_room.py",
        "src/importer_source_readiness/production_trade_discovery_engine.py",
        "src/importer_source_readiness/production_trade_data_catalog_engine.py",
        "src/importer_source_readiness/production_launch_control_plane.py",
        "src/importer_source_readiness/production_packet_engine.py",
        "src/importer_source_readiness/production_payment_monetization_engine.py",
        "src/importer_source_readiness/production_portal_workflow_engine.py",
        "src/importer_source_readiness/production_reports_engine.py",
        "src/importer_source_readiness/production_security_privacy_reliability_engine.py",
        "src/importer_source_readiness/production_redevelopment.py",
        "tests/test_operator_app.py",
        "tests/test_source_packet_workflow.py",
        "tests/test_customer_store.py",
        "tests/test_product_runtime.py",
        "tests/test_completion_platform.py",
        "tests/test_external_package_audit.py",
        "tests/test_external_review_workflow.py",
        "tests/test_external_review_intake.py",
        "tests/test_external_validation_research.py",
        "tests/test_go_live_input_evidence.py",
        "tests/test_hosted_deployment_proof.py",
        "tests/test_payment_activation_proof.py",
        "tests/test_legal_privacy_security_approval.py",
        "tests/test_qualified_customs_trade_review.py",
        "tests/test_private_beta_outcomes.py",
        "tests/test_production_ai_copilot_engine.py",
        "tests/test_production_country_source_engine.py",
        "tests/test_production_data_model.py",
        "tests/test_production_decision_scoring_engine.py",
        "tests/test_production_document_intelligence_engine.py",
        "tests/test_production_evidence_claim_gate_engine.py",
        "tests/test_production_enterprise_api_platform.py",
        "tests/test_production_api_service.py",
        "tests/test_production_expert_review_network.py",
        "tests/test_production_market_intelligence_engine.py",
        "tests/test_production_market_readiness_evidence_room.py",
        "tests/test_production_trade_discovery_engine.py",
        "tests/test_production_trade_data_catalog_engine.py",
        "tests/test_production_launch_control_plane.py",
        "tests/test_production_packet_engine.py",
        "tests/test_production_payment_monetization_engine.py",
        "tests/test_production_portal_workflow_engine.py",
        "tests/test_production_reports_engine.py",
        "tests/test_production_security_privacy_reliability_engine.py",
        "tests/test_production_redevelopment.py",
        "scripts/run_customer_workflow.py",
        "scripts/run_policy_intelligence.py",
        "scripts/run_completion_platform.py",
        "scripts/run_product_operations.py",
        "scripts/run_all_artifacts.py",
        "scripts/audit_external_package.py",
        "scripts/build_external_review_packet.py",
        "scripts/run_external_review_intake.py",
        "scripts/run_final_go_live_review.py",
        "scripts/run_external_validation_requirements.py",
        "scripts/run_hosted_deployment_proof.py",
        "scripts/run_payment_activation_proof.py",
        "scripts/run_legal_privacy_security_approval.py",
        "scripts/run_qualified_customs_trade_review.py",
        "scripts/run_private_beta_outcomes.py",
        "scripts/run_production_ai_copilot_engine.py",
        "scripts/run_production_country_source_engine.py",
        "scripts/run_production_data_model.py",
        "scripts/run_production_decision_scoring_engine.py",
        "scripts/run_production_document_intelligence_engine.py",
        "scripts/run_production_evidence_claim_gate_engine.py",
        "scripts/run_production_enterprise_api_platform.py",
        "scripts/run_production_api_service.py",
        "scripts/run_production_expert_review_network.py",
        "scripts/run_production_market_intelligence_engine.py",
        "scripts/run_production_market_readiness_evidence_room.py",
        "scripts/run_production_trade_discovery_engine.py",
        "scripts/run_production_trade_data_catalog_engine.py",
        "scripts/run_production_launch_control_plane.py",
        "scripts/run_production_packet_engine.py",
        "scripts/run_production_persistence.py",
        "scripts/run_production_repository.py",
        "scripts/run_production_payment_monetization_engine.py",
        "scripts/run_production_portal_workflow_engine.py",
        "scripts/run_production_reports_engine.py",
        "scripts/run_production_security_privacy_reliability_engine.py",
        "scripts/run_production_redevelopment.py",
        "scripts/package_external_review.py",
        "data/customer_source_packets.json",
        "data/evidence_ledger.json",
        "START_HERE.md",
        "WHAT_WE_ARE_BUILDING.md",
        "CURRENT_SLICE_VS_TARGET_PRODUCT.md",
        "FINAL_GO_LIVE_HANDOFF.md",
        "CUSTOMER_SOURCE_PACKET_SPEC.md",
        "SOURCE_OF_TRUTH.md",
        "SOURCE_OF_TRUTH_CURRENT.md",
        "RUN_RESULTS.md",
        "EXTERNAL_REVIEW_SUMMARY.md",
        "REDACTION_REPORT.md",
        "REVIEW_USE_TERMS.md",
        "OFFLINE_REPRODUCTION.md",
        "PACKAGE_AUDIT.md",
        "docs/EXTERNAL_REVIEW_PROCESS.md",
        "docs/EXTERNAL_REVIEW_RETURNED_FINDINGS.md",
        "docs/EXTERNAL_VALIDATION_REQUIREMENTS.md",
        "docs/EXTERNAL_VALIDATION_REVIEWER_BRIEF.md",
        "docs/GO_LIVE_INPUT_REQUESTS.md",
        "docs/HOSTED_DEPLOYMENT_PROOF.md",
        "docs/PAYMENT_ACTIVATION_PROOF.md",
        "docs/LEGAL_PRIVACY_SECURITY_APPROVAL_PROOF.md",
        "docs/QUALIFIED_CUSTOMS_TRADE_REVIEW_PROOF.md",
        "docs/PRIVATE_BETA_OUTCOME_CONTRACT.md",
        "docs/PRODUCTION_AI_COPILOT_ENGINE.md",
        "docs/PRODUCTION_COUNTRY_SOURCE_ENGINE.md",
        "docs/PRODUCTION_DATA_MODEL.md",
        "docs/PRODUCTION_DECISION_SCORING_ENGINE.md",
        "docs/PRODUCTION_DOCUMENT_INTELLIGENCE_ENGINE.md",
        "docs/PRODUCTION_EVIDENCE_CLAIM_GATE_ENGINE.md",
        "docs/PRODUCTION_ENTERPRISE_API_PLATFORM.md",
        "docs/PRODUCTION_API_SERVICE.md",
        "docs/PRODUCTION_EXPERT_REVIEW_NETWORK.md",
        "docs/PRODUCTION_MARKET_INTELLIGENCE_ENGINE.md",
        "docs/PRODUCTION_MARKET_READINESS_EVIDENCE_ROOM.md",
        "docs/PRODUCTION_TRADE_DISCOVERY_ENGINE.md",
        "docs/PRODUCTION_TRADE_DATA_CATALOG_ENGINE.md",
        "docs/PRODUCTION_LAUNCH_CONTROL_PLANE.md",
        "docs/PRODUCTION_PACKET_ENGINE.md",
        "docs/PRODUCTION_PERSISTENCE.md",
        "docs/PRODUCTION_REPOSITORY_SERVICE.md",
        "docs/PRODUCTION_PAYMENT_MONETIZATION_ENGINE.md",
        "docs/PRODUCTION_PORTAL_WORKFLOWS.md",
        "docs/PRODUCTION_REPORTS_ENGINE.md",
        "docs/PRODUCTION_SECURITY_PRIVACY_RELIABILITY_ENGINE.md",
        "docs/PRODUCTION_REDEVELOPMENT.md",
        "docs/BUSINESS_CORE_LOGIC_CURRENT_STATE.md",
        "docs/FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md",
        "docs/NON_FUNCTIONAL_REQUIREMENTS_CURRENT_STATE.md",
        "system_review_graph/customer_readiness_report.json",
        "system_review_graph/customer_readiness_report.md",
        "system_review_graph/customer_source_packets.json",
        "system_review_graph/evidence_ledger.json",
        "system_review_graph/customer_ai_review_runs.json",
        "system_review_graph/customer_workflow.sqlite",
        "system_review_graph/product_runtime_state.json",
        "system_review_graph/auth_rbac_matrix.json",
        "system_review_graph/claims_gate_matrix.json",
        "system_review_graph/review_requests.json",
        "system_review_graph/human_review_findings.json",
        "system_review_graph/report_exports.json",
        "system_review_graph/audit_events.json",
        "system_review_graph/deletion_requests.json",
        "system_review_graph/deployment_readiness_report.json",
        "system_review_graph/private_beta_readiness_checklist.json",
        "system_review_graph/ai_data_policy.json",
        "system_review_graph/model_endpoints.json",
        "system_review_graph/ai_model_router.json",
        "system_review_graph/redaction_pipeline.json",
        "system_review_graph/manual_no_ai_workflow.json",
        "system_review_graph/requirements_traceability_matrix.json",
        "system_review_graph/public_trade_readiness_manifest.json",
        "system_review_graph/exporter_mode_requirements.json",
        "system_review_graph/public_report_types.json",
        "system_review_graph/public_upload_policy.json",
        "system_review_graph/intelligence_hub_policy_monitor.json",
        "system_review_graph/policy_source_snapshots.json",
        "system_review_graph/policy_change_impact_report.json",
        "system_review_graph/policy_intelligence.sqlite",
        "system_review_graph/completion_platform_manifest.json",
        "system_review_graph/country_coverage_report.json",
        "system_review_graph/opportunity_scanner_report.json",
        "system_review_graph/business_logic_phase_report.json",
        "system_review_graph/business_phase_completion_report.json",
        "system_review_graph/transport_readiness_report.json",
        "system_review_graph/billing_credit_controls.json",
        "system_review_graph/agent_api_manifest.json",
        "system_review_graph/traffic_pages_manifest.json",
        "system_review_graph/research_execution_plan.json",
        "system_review_graph/team_workspace_report.json",
        "system_review_graph/expert_network_report.json",
        "system_review_graph/billing_usage_ledger.json",
        "system_review_graph/agent_api_gateway_contract.json",
        "system_review_graph/launch_operations_report.json",
        "system_review_graph/all_stage_readiness_report.json",
        "system_review_graph/product_operations_report.json",
        "system_review_graph/product_operations_log.json",
        "system_review_graph/final_go_live_decision_report.json",
        "system_review_graph/current_external_gate_research.json",
        "system_review_graph/external_validation_requirements_report.json",
        "system_review_graph/external_validation_evidence_requirements.json",
        "system_review_graph/go_live_input_templates.json",
        "system_review_graph/go_live_input_readiness_report.json",
        "system_review_graph/go_live_returned_input_evidence_manifest.json",
        "system_review_graph/go_live_returned_input_validation_matrix.json",
        "system_review_graph/hosted_deployment_proof_contract.json",
        "system_review_graph/hosted_deployment_proof_manifest.json",
        "system_review_graph/hosted_deployment_gate_matrix.json",
        "system_review_graph/hosted_deployment_blocker_export.jsonl",
        "system_review_graph/payment_activation_proof_contract.json",
        "system_review_graph/payment_activation_proof_manifest.json",
        "system_review_graph/payment_activation_gate_matrix.json",
        "system_review_graph/payment_activation_blocker_export.jsonl",
        "system_review_graph/legal_privacy_security_approval_contract.json",
        "system_review_graph/legal_privacy_security_approval_manifest.json",
        "system_review_graph/legal_privacy_security_approval_gate_matrix.json",
        "system_review_graph/legal_privacy_security_approval_blocker_export.jsonl",
        "system_review_graph/qualified_customs_trade_review_contract.json",
        "system_review_graph/qualified_customs_trade_review_manifest.json",
        "system_review_graph/qualified_customs_trade_review_gate_matrix.json",
        "system_review_graph/qualified_customs_trade_review_blocker_export.jsonl",
        "system_review_graph/private_beta_outcome_contract.json",
        "system_review_graph/private_beta_session_evidence_schema.json",
        "system_review_graph/private_beta_outcome_gate_matrix.json",
        "system_review_graph/production_country_source_engine_manifest.json",
        "system_review_graph/production_country_packs.json",
        "system_review_graph/production_source_lifecycle.json",
        "system_review_graph/production_source_snapshot_history.json",
        "system_review_graph/production_source_refresh_audit_events.json",
        "system_review_graph/production_ai_copilot_manifest.json",
        "system_review_graph/production_ai_output_contracts.json",
        "system_review_graph/production_ai_safety_checks.json",
        "system_review_graph/production_data_model_manifest.json",
        "system_review_graph/production_data_model_seed.json",
        "system_review_graph/production_decision_scoring_manifest.json",
        "system_review_graph/production_decision_score_records.json",
        "system_review_graph/production_score_cap_policy.json",
        "system_review_graph/production_market_intelligence_manifest.json",
        "system_review_graph/production_market_signals.json",
        "system_review_graph/production_market_dataset_connectors.json",
        "system_review_graph/production_market_readiness_evidence_room_manifest.json",
        "system_review_graph/production_market_readiness_evidence_work_orders.json",
        "system_review_graph/production_market_readiness_reviewer_brief_cards.json",
        "system_review_graph/production_market_readiness_gate_status_matrix.json",
        "system_review_graph/production_market_readiness_input_ledger.json",
        "system_review_graph/production_market_readiness_input_history.json",
        "system_review_graph/production_trade_discovery_manifest.json",
        "system_review_graph/production_trade_discovery_category_map.json",
        "system_review_graph/production_trade_discovery_country_lanes.json",
        "system_review_graph/production_trade_discovery_beginner_flows.json",
        "system_review_graph/production_trade_discovery_source_registry.json",
        "system_review_graph/production_trade_discovery_requirement_audit.json",
        "system_review_graph/production_trade_data_catalog_manifest.json",
        "system_review_graph/production_trade_data_query_templates.json",
        "system_review_graph/production_trade_data_query_work_orders.json",
        "system_review_graph/production_trade_data_browse_cards.json",
        "system_review_graph/production_trade_data_ingestion_policy.json",
        "system_review_graph/production_document_intelligence_manifest.json",
        "system_review_graph/production_document_pipeline.json",
        "system_review_graph/production_document_extracted_fields.json",
        "system_review_graph/production_document_parser_qa_matrix.json",
        "system_review_graph/production_document_sample_library.json",
        "system_review_graph/production_evidence_claim_gate_manifest.json",
        "system_review_graph/production_expert_review_network_manifest.json",
        "system_review_graph/production_reviewer_profiles.json",
        "system_review_graph/production_review_requests.json",
        "system_review_graph/production_review_finding_contracts.json",
        "system_review_graph/production_reports_engine_manifest.json",
        "system_review_graph/production_report_catalog.json",
        "system_review_graph/production_report_exports.json",
        "system_review_graph/production_report_citations.json",
        "system_review_graph/production_portal_workflow_manifest.json",
        "system_review_graph/production_portal_route_matrix.json",
        "system_review_graph/production_portal_ux_checks.json",
        "system_review_graph/production_portal_gate_controls.json",
        "system_review_graph/production_enterprise_api_manifest.json",
        "system_review_graph/production_enterprise_api_contracts.json",
        "system_review_graph/production_enterprise_rbac_policy.json",
        "system_review_graph/production_enterprise_workspace_controls.json",
        "system_review_graph/production_enterprise_webhook_policy.json",
        "system_review_graph/production_enterprise_audit_export_policy.json",
        "system_review_graph/production_enterprise_research_references.json",
        "system_review_graph/production_api_service_manifest.json",
        "system_review_graph/production_api_service_sample_responses.json",
        "system_review_graph/production_payment_monetization_manifest.json",
        "system_review_graph/production_pricing_tiers.json",
        "system_review_graph/production_paid_scope_policy.json",
        "system_review_graph/production_checkout_gate_controls.json",
        "system_review_graph/production_payment_webhook_controls.json",
        "system_review_graph/production_payment_research_references.json",
        "system_review_graph/production_security_privacy_reliability_manifest.json",
        "system_review_graph/production_trust_control_matrix.json",
        "system_review_graph/production_vendor_register.json",
        "system_review_graph/production_backup_restore_drill.json",
        "system_review_graph/production_incident_runbooks.json",
        "system_review_graph/production_trust_research_references.json",
        "system_review_graph/production_launch_control_plane_manifest.json",
        "system_review_graph/production_launch_gate_states.json",
        "system_review_graph/production_launch_scope_matrix.json",
        "system_review_graph/production_public_launch_decision.json",
        "system_review_graph/production_claim_gate_decisions.json",
        "system_review_graph/production_evidence_claim_mappers.json",
        "data/official_sample_documents/canada/cbsa-ci1-canada-customs-invoice.pdf",
        "data/official_sample_documents/canada/cbsa-a8a-b-cargo-control-document.pdf",
        "data/official_sample_documents/canada/cfia-5272-documentation-review-request.pdf",
        "data/parser_qa_documents/synthetic-commercial-invoice-canada.pdf",
        "data/parser_qa_documents/synthetic-packing-list-india-export.pdf",
        "data/parser_qa_documents/synthetic-certificate-of-origin-india.pdf",
        "data/parser_qa_documents/synthetic-bill-of-lading-vietnam.pdf",
        "data/parser_qa_documents/synthetic-airway-bill-generic.pdf",
        "data/parser_qa_documents/synthetic-product-specification-vietnam-seafood.pdf",
        "data/parser_qa_documents/synthetic-lab-certificate-food.pdf",
        "data/parser_qa_documents/synthetic-health-certificate-vietnam.pdf",
        "data/parser_qa_documents/synthetic-purchase-order-canada-buyer.pdf",
        "data/parser_qa_documents/synthetic-contract-incoterms.pdf",
        "data/parser_qa_documents/synthetic-inspection-report-supplier.pdf",
        "system_review_graph/production_packet_engine_manifest.json",
        "system_review_graph/production_packet_events.json",
        "system_review_graph/production_persistence_snapshot.json",
        "system_review_graph/production_persistence_row_counts.json",
        "system_review_graph/production_domain.sqlite",
        "system_review_graph/production_repository_service_manifest.json",
        "system_review_graph/production_repository_packet_context_packet-frozen-tuna-canada-001.json",
        "system_review_graph/production_repository_report_context_packet-frozen-tuna-canada-001.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/starter_packet.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/market_research_packet.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/buyer_ready_packet.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/supplier_request_packet.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/broker_review_packet.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/operator_packet.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/executive_decision_packet.json",
        "system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/blocked_claims_packet.json",
        "system_review_graph/production_redevelopment_plan.json",
        "system_review_graph/production_research_anchors.json",
        "system_review_graph/reviewer_wave_execution_plan.json",
        "system_review_graph/private_beta_smoke_test_plan.json",
        "system_review_graph/external_review_findings_report.json",
        "system_review_graph/external_review_blocker_ledger.jsonl",
        "system_review_graph/external_review_returned_finding_contract.json",
        "system_review_graph/external_review_returned_findings_manifest.json",
        "system_review_graph/external_review_returned_review_matrix.json",
        "system_review_graph/external_review_returned_blocker_export.jsonl",
        "system_review_graph/ai_assisted_external_review_plan.json",
        "system_review_graph/ai_assisted_external_review_findings_report.json",
        "system_review_graph/research_execution_runs.json",
        "system_review_graph/expert_review_work_orders.json",
        "system_review_graph/team_workspace_activity.json",
        "system_review_graph/launch_operations_events.json",
        "system_review_graph/generated_reports/data_intake_packet-frozen-tuna-canada-001.json",
        "system_review_graph/generated_reports/missing_evidence_packet-frozen-tuna-canada-001.json",
        "system_review_graph/generated_reports/starter_checklist_packet-frozen-tuna-canada-001.json",
        "system_review_graph/generated_reports/chatgpt_safe_summary_packet-frozen-tuna-canada-001.json",
        "system_review_graph/generated_reports/broker_packet_packet-frozen-tuna-canada-001.json",
        "system_review_graph/generated_reports/business_decision_packet-frozen-tuna-canada-001.json",
        "system_review_graph/source_refresh_runs.json",
        "system_review_graph/source_refresh_report_packet-frozen-tuna-canada-001.json",
        "system_review_graph/expert_review_packet_packet-frozen-tuna-canada-001.md",
        "output/pdf/external_validation_requirements.pdf",
        "output/pdf/external_validation_reviewer_brief.pdf",
        "output/pdf/go_live_input_requests.pdf",
        "migrations/0001_product_runtime.sql",
        "migrations/0002_production_domain_model.sql",
        "Dockerfile",
        "compose.yaml",
        ".env.example",
        "docs/PUBLIC_TRADE_READINESS.md",
        "docs/ALL_STAGES_COMPLETION.md",
        "docs/GO_LIVE_READINESS.md",
        "docs/AI_DATA_POLICY.md",
        "docs/DOCUMENT_PROCESSING.md",
        "docs/OPPORTUNITY_SCANNER.md",
        "docs/POLICY_MONITORING.md",
        "docs/AGENT_API.md",
        "docs/SECURITY_PRIVACY.md",
        "docs/DEPLOYMENT.md",
        "external_review_findings/README.md",
        "external_review_findings/UX_PRODUCT_REVIEW.md",
        "external_review_findings/SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        "external_review_findings/PRIVACY_LEGAL_REVIEW.md",
        "external_review_findings/AI_SAFETY_REVIEW.md",
        "external_review_findings/TRADE_BOUNDARY_REVIEW.md",
        "external_review_findings/FREIGHT_LOGISTICS_REVIEW.md",
        "external_review_findings/REPORT_LANGUAGE_REVIEW.md",
        "external_review_findings/DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        "external_review_findings/BILLING_PAYMENT_REVIEW.md",
        "external_review_findings/EXTERNAL_REVIEW_SUMMARY.json",
        "reviewer_packets/README.md",
        "reviewer_packets/WAVE_1_UX_PRODUCT_REVIEW.md",
        "reviewer_packets/WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        "reviewer_packets/WAVE_1_PRIVACY_LEGAL_REVIEW.md",
        "reviewer_packets/WAVE_1_AI_SAFETY_REVIEW.md",
        "reviewer_packets/WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        "reviewer_packets/WAVE_2_TRADE_BOUNDARY_REVIEW.md",
        "reviewer_packets/WAVE_2_FREIGHT_LOGISTICS_REVIEW.md",
        "reviewer_packets/WAVE_2_REPORT_LANGUAGE_REVIEW.md",
        "reviewer_packets/WAVE_3_BILLING_PAYMENT_REVIEW.md",
        "ai_assisted_review/README.md",
        "ai_assisted_review/AI_ASSISTED_REVIEW_SUMMARY.md",
        "ai_assisted_review/WEB_RESEARCH_SOURCE_LOG.md",
        "ai_assisted_review/simulated_findings/.gitkeep",
        "ai_assisted_review/simulated_findings/WAVE_1_UX_PRODUCT_REVIEW.json",
        "ai_assisted_review/simulated_findings/WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.json",
        "ai_assisted_review/simulated_findings/WAVE_1_PRIVACY_LEGAL_REVIEW.json",
        "ai_assisted_review/simulated_findings/WAVE_1_AI_SAFETY_REVIEW.json",
        "ai_assisted_review/simulated_findings/WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.json",
        "ai_assisted_review/role_prompts/WAVE_1_UX_PRODUCT_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_1_PRIVACY_LEGAL_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_1_AI_SAFETY_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_2_TRADE_BOUNDARY_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_2_FREIGHT_LOGISTICS_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_2_REPORT_LANGUAGE_REVIEW.md",
        "ai_assisted_review/role_prompts/WAVE_3_BILLING_PAYMENT_REVIEW.md",
    ):
        if not (ROOT / path).exists():
            failures.append(f"missing required product file: {path}")
    if production_redevelopment.get("status") != "production_redevelopment_contract_ready_with_external_build_gates":
        failures.append(
            "production redevelopment status expected production_redevelopment_contract_ready_with_external_build_gates, "
            f"got {production_redevelopment.get('status')!r}"
        )
    if production_redevelopment.get("production_layer_count") != 14:
        failures.append("production redevelopment should keep the fourteen-layer production model")
    if production_redevelopment.get("phase_count") != 21:
        failures.append("production redevelopment should cover phases 0 through 20")
    if production_redevelopment.get("research_anchor_count") != 18:
        failures.append("production redevelopment should include the dated 18-source research map")
    if production_redevelopment.get("domain_entity_count", 0) < 39:
        failures.append("production redevelopment should include the permanent research-intelligence entities")
    if production_research.get("source_count") != production_redevelopment.get("research_anchor_count"):
        failures.append("production research anchor artifact should match the redevelopment source count")
    if production_redevelopment.get("external_claims_opened") is not False:
        failures.append("production redevelopment must not open external claims")
    for key in ("public_launch_ready", "hosted_production_ready", "live_payment_ready"):
        if production_redevelopment.get(key) is not False:
            failures.append(f"production redevelopment expected {key}=false")
    official_source_ids = {row.get("id") for row in official_source_registry}
    research_source_ids = {row.get("id") for row in production_redevelopment.get("research_anchors", [])}
    allowed_non_registry_source_ids = {
        "official_source_registry",
        "user_research_required",
        "enterprise_user_validation_required",
        "reviewer_findings",
        "user_validation_records",
    }
    required_source_ids = {
        "cbsa-import-commercial-goods",
        "cbsa-customs-tariff-2026",
        "cbsa-licensed-customs-brokers",
        "cfia-airs",
        "gac-sanctions",
        "ised-trade-data-online",
        "canada-cid",
        "statcan-wds",
        "canada-trade-commissioner-export-guide",
        "gac-export-controls",
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
    missing_sources = sorted(required_source_ids - (official_source_ids | research_source_ids))
    if missing_sources:
        failures.append(f"production source registry is missing required source ids: {', '.join(missing_sources)}")
    for phase in production_redevelopment.get("redevelopment_phases", []):
        for track in ("build_track", "research_track", "source_track", "evidence_track", "gate_track"):
            if not phase.get(track):
                failures.append(f"production phase {phase.get('phase')} missing {track}")
        if any(layer_id < 1 or layer_id > 14 for layer_id in phase.get("layers", [])):
            failures.append(f"production phase {phase.get('phase')} references a non-existent production layer")
        for source_id in phase.get("source_track", []):
            if source_id not in (official_source_ids | research_source_ids | allowed_non_registry_source_ids):
                failures.append(f"production phase {phase.get('phase')} references unknown source {source_id}")
    if production_data_model.get("status") != "production_data_model_ready_local_schema_proof_external_db_gates_closed":
        failures.append(
            "production data model status expected production_data_model_ready_local_schema_proof_external_db_gates_closed, "
            f"got {production_data_model.get('status')!r}"
        )
    if production_data_model.get("table_count", 0) < 40:
        failures.append("production data model should include the first package production tables")
    if production_data_model.get("foreign_key_count", 0) < 70:
        failures.append("production data model should include explicit foreign-key relationships")
    if production_data_model.get("index_count", 0) < 35:
        failures.append("production data model should include query-path indexes")
    if production_data_model.get("row_level_security_table_count", 0) < 25:
        failures.append("production data model should include tenant-scoped RLS tables")
    if production_data_model.get("domain_event_count", 0) < 14:
        failures.append("production data model should include the domain event list")
    if production_data_model.get("hosted_database_ready") is not False:
        failures.append("production data model must not claim hosted database readiness")
    if production_data_model.get("external_claims_opened") is not False:
        failures.append("production data model must not open external claims")
    production_table_names = {row.get("table") for row in production_data_model.get("tables", [])}
    for required_table in (
        "trade_readiness_packets",
        "packet_events",
        "source_records",
        "source_snapshots",
        "evidence_items",
        "market_signals",
        "buyer_profiles",
        "supplier_profiles",
        "blocked_claims",
        "decision_scores",
        "review_requests",
        "review_findings",
        "reports",
        "audit_events",
        "billing_accounts",
    ):
        if required_table not in production_table_names:
            failures.append(f"production data model missing table {required_table}")
    production_schema_sql = (ROOT / "migrations" / "0002_production_domain_model.sql").read_text(encoding="utf-8")
    for expected_sql in (
        "enable row level security",
        "current_setting('app.current_organization_id', true)",
        "constraint decision_scores_name_check",
        "buyer_supplier_evidence_score",
        "external_charge_created boolean not null default false",
    ):
        if expected_sql not in production_schema_sql:
            failures.append(f"production data model migration missing SQL invariant: {expected_sql}")
    if production_packet_engine.get("status") != "production_packet_engine_ready_local_state_machine_claim_gates_closed":
        failures.append(
            "production packet engine status expected production_packet_engine_ready_local_state_machine_claim_gates_closed, "
            f"got {production_packet_engine.get('status')!r}"
        )
    if production_packet_engine.get("packet_count", 0) < 1:
        failures.append("production packet engine should evaluate at least one packet")
    if production_packet_engine.get("state_count") != 12:
        failures.append("production packet engine should expose 12 production states")
    if production_packet_engine.get("packet_view_type_count") != 8:
        failures.append("production packet engine should expose 8 packet view types")
    if production_packet_engine.get("packet_view_count", 0) < 8:
        failures.append("production packet engine should generate all packet views")
    if production_packet_engine.get("packet_event_count", 0) < 12:
        failures.append("production packet engine should generate state event proof")
    if production_packet_engine.get("external_effects_created") is not False:
        failures.append("production packet engine must not create external effects")
    if production_packet_engine.get("claims_opened") is not False:
        failures.append("production packet engine must not open external claims")
    packet_runs = production_packet_engine.get("packet_runs", [])
    if not packet_runs:
        failures.append("production packet engine missing packet run evidence")
    else:
        packet_run = packet_runs[0]
        view_types = {row.get("view_type") for row in packet_run.get("packet_views", [])}
        score_ids = {row.get("score") for row in packet_run.get("scores", [])}
        event_states = {row.get("state") for row in packet_run.get("state_events", [])}
        required_views = {
            "starter_packet",
            "market_research_packet",
            "buyer_ready_packet",
            "supplier_request_packet",
            "broker_review_packet",
            "operator_packet",
            "executive_decision_packet",
            "blocked_claims_packet",
        }
        if view_types != required_views:
            failures.append("production packet engine packet views are incomplete")
        if score_ids != {
            "market_signal_score",
            "evidence_completeness_score",
            "source_freshness_score",
            "buyer_supplier_evidence_score",
            "responsibility_clarity_score",
            "decision_safety_score",
        }:
            failures.append("production packet engine should output the six canonical scores")
        if event_states != set(production_packet_engine.get("states", [])):
            failures.append("production packet engine should write an event row for every production state")
        if packet_run.get("state") != "reviewer_ready":
            failures.append(f"fixture packet should be reviewer_ready, got {packet_run.get('state')!r}")
        if packet_run.get("reviewer_ready_not_approved") is not True:
            failures.append("reviewer-ready packet must explicitly remain not approved")
        if packet_run.get("claims_opened") is not False:
            failures.append("packet run must keep claims closed")
    if production_country_source_engine.get("status") != "production_country_source_engine_ready_reference_packs_claim_gates_closed":
        failures.append(
            "production country/source engine status expected production_country_source_engine_ready_reference_packs_claim_gates_closed, "
            f"got {production_country_source_engine.get('status')!r}"
        )
    if production_country_source_engine.get("country_pack_count") != 4:
        failures.append("production country/source engine should produce four country packs")
    if production_country_source_engine.get("source_lifecycle_count", 0) < 20:
        failures.append("production country/source engine should include official source lifecycle rows")
    if production_country_source_engine.get("researched_source_fact_count", 0) < 18:
        failures.append("production country/source engine should include researched source facts")
    if production_country_source_engine.get("external_effects_created") is not False:
        failures.append("production country/source engine must not create external effects")
    if production_country_source_engine.get("claims_opened") is not False:
        failures.append("production country/source engine must not open claims")
    country_packs = {row.get("country_pack_id"): row for row in production_country_source_engine.get("country_packs", [])}
    for pack_id in ("CA-import", "IN-export", "VN-demo-origin", "GENERIC-fallback"):
        if pack_id not in country_packs:
            failures.append(f"production country/source engine missing country pack {pack_id}")
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
    if country_packs.get("CA-import"):
        present = set(country_packs["CA-import"].get("source_types_present", []))
        if not canada_required_source_areas.issubset(present):
            failures.append("Canada import pack missing required source areas")
        if country_packs["CA-import"].get("coverage_level") != "reference_only":
            failures.append("Canada import pack should remain reference_only until qualified review")
    if country_packs.get("GENERIC-fallback", {}).get("coverage_level") != "generic":
        failures.append("generic fallback country pack should stay generic")
    source_lifecycle = {row.get("source_id"): row for row in production_country_source_engine.get("source_lifecycle", [])}
    for source_id in ("cbsa-import-commercial-goods", "cfia-airs", "canada-cid"):
        state = source_lifecycle.get(source_id, {}).get("source_state")
        if state not in {"checked_current_reference_only", "refresh_attempted_not_verified", "source_unavailable"}:
            failures.append(f"{source_id} should have a dated source refresh outcome, got {state!r}")
        if state != "checked_current_reference_only" and source_lifecycle.get(source_id, {}).get("claims_opened") is not False:
            failures.append(f"{source_id} unverified refresh state must keep claims closed")
    if source_lifecycle.get("cbsa-customs-tariff-2026", {}).get("source_state") != "not_checked":
        failures.append("tariff source should remain not_checked until a dated refresh exists")
    impacts = production_country_source_engine.get("packet_source_impacts", [])
    if not impacts:
        failures.append("production country/source engine should generate packet source impacts")
    else:
        impact = impacts[0]
        if "tariff_confirmed" not in impact.get("blocked_claims", []):
            failures.append("packet source impact should block tariff confirmation")
        if "cfia_approved" not in impact.get("blocked_claims", []):
            failures.append("packet source impact should block CFIA approval")
        if impact.get("external_claims_opened") is not False:
            failures.append("packet source impact must keep external claims closed")
    if production_trade_discovery.get("status") != "production_trade_discovery_engine_ready_beginner_research_routed_no_opportunity_claims":
        failures.append(
            "production trade discovery status expected production_trade_discovery_engine_ready_beginner_research_routed_no_opportunity_claims, "
            f"got {production_trade_discovery.get('status')!r}"
        )
    if production_trade_discovery.get("category_count", 0) < 12:
        failures.append("production trade discovery should expose at least 12 beginner category families")
    if production_trade_discovery.get("country_lane_count", 0) < 12:
        failures.append("production trade discovery should expose diverse Canada import/export country lanes")
    if production_trade_discovery.get("beginner_flow_count", 0) < 8:
        failures.append("production trade discovery should expose beginner flows before packet creation")
    if production_trade_discovery.get("dataset_route_count", 0) < 6:
        failures.append("production trade discovery should register dataset routes for source-backed research")
    if production_trade_discovery.get("missing_registry_sources"):
        failures.append(
            "production trade discovery references missing source registry ids: "
            + ", ".join(production_trade_discovery.get("missing_registry_sources", []))
        )
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
        "external_effects_created",
        "claims_opened",
    ):
        if production_trade_discovery.get(key) is not False:
            failures.append(f"production trade discovery expected {key}=false")
    for blocked_claim in ("best_product_to_import", "guaranteed_demand", "buyer_validated", "supplier_verified", "cfia_approved"):
        if blocked_claim not in production_trade_discovery.get("blocked_claims", []):
            failures.append(f"production trade discovery should block {blocked_claim}")
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
            failures.append(f"production trade discovery missing source route {source_id}")
    discovery_flow_ids = {row.get("flow_id") for row in production_trade_discovery.get("beginner_flows", [])}
    for flow_id in ("browse_canada_imports", "browse_canada_exports", "compare_origin_lanes_to_canada", "check_regulated_goods_early"):
        if flow_id not in discovery_flow_ids:
            failures.append(f"production trade discovery missing beginner flow {flow_id}")
    discovery_lane_ids = {row.get("lane_id") for row in production_trade_discovery.get("country_lanes", [])}
    for lane_id in ("IN-to-CA", "VN-to-CA", "US-to-CA", "MX-to-CA", "CN-to-CA", "EU-to-CA", "CA-to-US", "GENERIC-to-CA"):
        if lane_id not in discovery_lane_ids:
            failures.append(f"production trade discovery missing country lane {lane_id}")
    if any(row.get("trade_values_loaded") is not False for row in production_trade_discovery.get("country_lanes", [])):
        failures.append("production trade discovery country lanes must not contain invented trade values")
    if any(row.get("recommendation_claimed") is not False for row in production_trade_discovery.get("country_lanes", [])):
        failures.append("production trade discovery country lanes must not claim recommendations")
    if any(row.get("recommendation_claimed") is not False for row in production_trade_discovery.get("category_families", [])):
        failures.append("production trade discovery categories must not claim recommendations")
    if any(row.get("values_loaded") is not False for row in production_trade_discovery.get("dataset_routes", [])):
        failures.append("production trade discovery dataset routes must not pretend values are loaded")
    if production_trade_data_catalog.get("status") != "production_trade_data_catalog_engine_ready_query_plans_no_values_loaded":
        failures.append(
            "production trade data catalog status expected production_trade_data_catalog_engine_ready_query_plans_no_values_loaded, "
            f"got {production_trade_data_catalog.get('status')!r}"
        )
    if production_trade_data_catalog.get("template_count", 0) < 7:
        failures.append("production trade data catalog should expose reusable query templates")
    if production_trade_data_catalog.get("browse_card_count", 0) < 5:
        failures.append("production trade data catalog should expose beginner browse cards")
    if production_trade_data_catalog.get("query_work_order_count", 0) < 120:
        failures.append("production trade data catalog should generate lane/category query work orders")
    if production_trade_data_catalog.get("missing_registry_sources"):
        failures.append(
            "production trade data catalog references missing source registry ids: "
            + ", ".join(production_trade_data_catalog.get("missing_registry_sources", []))
        )
    for key in (
        "values_loaded",
        "numeric_values_shown",
        "recommendations_created",
        "demand_claimed",
        "profitability_claimed",
        "buyer_validation_claimed",
        "supplier_verification_claimed",
        "external_effects_created",
        "claims_opened",
    ):
        if production_trade_data_catalog.get(key) is not False:
            failures.append(f"production trade data catalog expected {key}=false")
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
            failures.append(f"production trade data catalog missing query template {template_id}")
    if any(row.get("values_loaded") is not False for row in production_trade_data_catalog.get("query_templates", [])):
        failures.append("production trade data catalog templates must not pretend values are loaded")
    if any(row.get("allowed_to_show_numeric_values") is not False for row in production_trade_data_catalog.get("query_templates", [])):
        failures.append("production trade data catalog templates must block numeric display before ingestion")
    if any(row.get("values_loaded") is not False for row in production_trade_data_catalog.get("query_work_orders", [])):
        failures.append("production trade data catalog work orders must not contain values before ingestion")
    if any(row.get("dated_dataset_row_attached") is not False for row in production_trade_data_catalog.get("query_work_orders", [])):
        failures.append("production trade data catalog work orders must require dated rows")
    if production_market_intelligence.get("status") != "production_market_intelligence_engine_ready_source_routed_no_demand_claims":
        failures.append(
            "production market intelligence status expected production_market_intelligence_engine_ready_source_routed_no_demand_claims, "
            f"got {production_market_intelligence.get('status')!r}"
        )
    if production_market_intelligence.get("metric_count") != 9:
        failures.append("production market intelligence should expose 9 metric records")
    if production_market_intelligence.get("market_signal_count", 0) < 9:
        failures.append("production market intelligence should generate market signal rows")
    if production_market_intelligence.get("dataset_connector_count", 0) < 7:
        failures.append("production market intelligence should register dataset connectors")
    if production_market_intelligence.get("external_effects_created") is not False:
        failures.append("production market intelligence must not create external effects")
    if production_market_intelligence.get("claims_opened") is not False:
        failures.append("production market intelligence must not open claims")
    for blocked_claim in ("profitable_market", "guaranteed_demand", "buyer_validated"):
        if blocked_claim not in production_market_intelligence.get("blocked_claims", []):
            failures.append(f"production market intelligence should block {blocked_claim}")
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
            failures.append(f"production market intelligence missing metric {metric}")
    if any(row.get("value_status") != "not_ingested_dataset_required" for row in production_market_intelligence.get("signals", [])):
        failures.append("market signals should not contain invented values before dataset ingestion")
    if any(row.get("claims_opened") is not False for row in production_market_intelligence.get("signals", [])):
        failures.append("market signals must keep claims closed")
    market_packet_runs = production_market_intelligence.get("packet_runs", [])
    if not market_packet_runs:
        failures.append("production market intelligence missing packet run evidence")
    else:
        market_packet = market_packet_runs[0].get("market_packet", {})
        if market_packet.get("can_claim_market_demand") is not False:
            failures.append("market packet must not claim market demand")
        if market_packet.get("can_claim_profitability") is not False:
            failures.append("market packet must not claim profitability")
        if market_packet.get("can_claim_buyer_validation") is not False:
            failures.append("market packet must not claim buyer validation")
    if production_document_intelligence.get("status") != "production_document_intelligence_engine_ready_local_pipeline_security_gates_closed":
        failures.append(
            "production document intelligence status expected production_document_intelligence_engine_ready_local_pipeline_security_gates_closed, "
            f"got {production_document_intelligence.get('status')!r}"
        )
    if production_document_intelligence.get("pipeline_stage_count", 0) < 16:
        failures.append("production document intelligence should expose the full upload/document pipeline")
    if production_document_intelligence.get("document_class_count") != 11:
        failures.append("production document intelligence should cover the eleven expected trade-document classes")
    if production_document_intelligence.get("official_sample_document_count", 0) < 3:
        failures.append("production document intelligence should include downloaded official CBSA/CFIA samples")
    if production_document_intelligence.get("source_route_only_sample_count", 0) < 3:
        failures.append("production document intelligence should include source-route-only India/Vietnam sample rows")
    if production_document_intelligence.get("synthetic_parser_fixture_count") != 11:
        failures.append("production document intelligence should include one synthetic parser fixture per expected document class")
    if production_document_intelligence.get("extracted_field_count", 0) < 20:
        failures.append("production document intelligence should extract parser QA field rows")
    if production_document_intelligence.get("parser_qa_status") != "production_document_parser_qa_ready_fixture_expectations_checked":
        failures.append("production document intelligence should include parser QA status")
    if production_document_intelligence.get("parser_qa_fixture_count") != 11:
        failures.append("production document parser QA should cover all eleven synthetic fixtures")
    if production_document_intelligence.get("parser_qa_passed_count") != 11:
        failures.append("production document parser QA should pass all eleven synthetic fixtures")
    if production_document_intelligence.get("parser_qa_needs_rule_count") != 0:
        failures.append("production document parser QA should have no missing parser rules for synthetic fixtures")
    if production_document_parser_qa.get("status") != "production_document_parser_qa_ready_fixture_expectations_checked":
        failures.append("production document parser QA matrix should be generated")
    if production_document_parser_qa.get("fixture_count") != 11:
        failures.append("production document parser QA matrix should cover eleven fixtures")
    if production_document_parser_qa.get("passed_count") != 11 or production_document_parser_qa.get("needs_rule_count") != 0:
        failures.append("production document parser QA matrix should pass all fixtures")
    if any(row.get("claims_opened") is not False for row in production_document_parser_qa.get("rows", [])):
        failures.append("production document parser QA rows must not open claims")
    if production_document_intelligence.get("sample_library_status") != "production_document_sample_library_ready_source_boundaries_closed":
        failures.append("production document intelligence should expose sample-library status")
    if production_document_intelligence.get("sample_library_count", 0) < 18:
        failures.append("production document intelligence sample library should cover official, route-only, and synthetic samples")
    if production_document_intelligence.get("sample_library_official_pdf_count") != 3:
        failures.append("production document intelligence sample library should include three official PDF samples")
    if production_document_intelligence.get("sample_library_source_route_only_count", 0) < 4:
        failures.append("production document intelligence sample library should include Canada/India/Vietnam route-only rows")
    if production_document_intelligence.get("sample_library_synthetic_fixture_count") != 11:
        failures.append("production document intelligence sample library should include eleven synthetic parser fixtures")
    if production_document_intelligence.get("sample_library_claims_opened") is not False:
        failures.append("production document intelligence sample library must not open claims")
    if production_document_sample_library.get("status") != "production_document_sample_library_ready_source_boundaries_closed":
        failures.append("production document sample library artifact should be generated")
    if production_document_sample_library.get("official_pdf_count") != 3:
        failures.append("production document sample library artifact should include three official PDFs")
    if production_document_sample_library.get("source_route_only_count", 0) < 4:
        failures.append("production document sample library artifact should include source-route-only rows")
    if production_document_sample_library.get("synthetic_fixture_count") != 11:
        failures.append("production document sample library artifact should include all synthetic fixtures")
    if production_document_sample_library.get("customer_evidence_allowed_count") != 0:
        failures.append("production document sample library must not allow samples as customer evidence")
    if production_document_sample_library.get("claims_opened") is not False:
        failures.append("production document sample library must keep claims closed")
    if production_document_sample_library.get("missing_file_count") != 0:
        failures.append("production document sample library should have all file-backed samples present")
    library_countries = set(production_document_sample_library.get("country_coverage", []))
    for country_code in ("CA", "IN", "VN", "GENERIC"):
        if country_code not in library_countries:
            failures.append(f"production document sample library missing country coverage {country_code}")
    library_rows = production_document_sample_library.get("rows", [])
    if any(row.get("customer_evidence_allowed") is not False for row in library_rows):
        failures.append("production document sample library rows must not allow customer evidence")
    if any(row.get("claims_opened") is not False for row in library_rows):
        failures.append("production document sample library rows must not open claims")
    official_library_rows = [row for row in library_rows if row.get("sample_level") == "official_pdf_downloaded"]
    if any(not row.get("file_metadata", {}).get("sha256") for row in official_library_rows):
        failures.append("official document sample rows must include local file hashes")
    route_only_source_ids = {row.get("source_id") for row in library_rows if row.get("sample_level") == "official_source_route_only"}
    for source_id in ("india-dgft-appendices-anf", "india-cbic-customs-forms", "vietnam-customs-portal", "cbsa-b3b-commented-menu-route"):
        if source_id not in route_only_source_ids:
            failures.append(f"production document sample library missing route-only source {source_id}")
    for key in ("real_uploads_enabled", "malware_scan_proven", "object_storage_ready", "external_effects_created", "claims_opened", "public_launch_ready"):
        if production_document_intelligence.get(key) is not False:
            failures.append(f"production document intelligence expected {key}=false")
    if production_document_intelligence.get("parser_outputs_are_draft") is not True:
        failures.append("production document intelligence parser outputs must remain draft")
    for blocked_claim in ("document_authenticity_verified", "customs_ready", "tariff_confirmed", "cfia_approved", "supplier_verified"):
        if blocked_claim not in production_document_intelligence.get("blocked_claims", []):
            failures.append(f"production document intelligence should block {blocked_claim}")
    document_stages = {row.get("stage") for row in production_document_intelligence.get("pipeline_stages", [])}
    for stage in ("malware_scan", "document_classification", "field_extraction", "evidence_ledger_mapping", "redaction_preview", "ai_optional_analysis"):
        if stage not in document_stages:
            failures.append(f"production document intelligence missing pipeline stage {stage}")
    source_ids_for_documents = {row.get("source_id") for row in production_document_intelligence.get("source_records", [])}
    for source_id in ("cbsa-ci1-canada-customs-invoice", "india-dgft-appendices-anf", "vietnam-customs-portal", "owasp-file-upload"):
        if source_id not in source_ids_for_documents:
            failures.append(f"production document intelligence missing source record {source_id}")
    document_sample_levels = {row.get("sample_level") for row in production_document_intelligence.get("document_records", [])}
    for sample_level in ("official_pdf_downloaded", "synthetic_parser_fixture"):
        if sample_level not in document_sample_levels:
            failures.append(f"production document intelligence missing document sample level {sample_level}")
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
        failures.append("production document intelligence does not cover every expected document class")
    for field in production_document_intelligence.get("extracted_fields", []):
        for key in ("document_id", "page_or_section", "extracted_value", "confidence", "provenance", "user_confirmation_status", "claim_boundary"):
            if key not in field:
                failures.append(f"production document extracted field missing {key}")
                break
        if field.get("supports_claims") != []:
            failures.append("production document extracted fields must not support claims directly")
            break
    if production_evidence_claim_gate.get("status") != "production_evidence_claim_gate_engine_ready_claims_fail_closed":
        failures.append(
            "production evidence claim-gate status expected production_evidence_claim_gate_engine_ready_claims_fail_closed, "
            f"got {production_evidence_claim_gate.get('status')!r}"
        )
    if production_evidence_claim_gate.get("claim_type_count", 0) < 17:
        failures.append("production evidence claim-gate should include the Phase 11 claim types")
    if production_evidence_claim_gate.get("claim_gate_decision_count", 0) < production_evidence_claim_gate.get("claim_type_count", 0):
        failures.append("production evidence claim-gate should emit a decision for every claim type")
    if production_evidence_claim_gate.get("safe_research_claim_count", 0) < 1:
        failures.append("production evidence claim-gate should allow safe preparation/source-routing statements")
    if production_evidence_claim_gate.get("forbidden_external_claim_count", 0) < 6:
        failures.append("production evidence claim-gate should register the forbidden external claim set")
    if production_evidence_claim_gate.get("evidence_mapper_count", 0) < 1:
        failures.append("production evidence claim-gate should emit evidence mappers")
    if production_evidence_claim_gate.get("claim_gate_mapper_count") != production_evidence_claim_gate.get("claim_type_count"):
        failures.append("production evidence claim-gate should emit one mapper per claim type")
    if (
        production_evidence_claim_gate.get("qualified_customs_trade_review_evidence_status")
        != "qualified_customs_trade_review_intake_ready_real_review_evidence_required_claims_closed"
    ):
        failures.append("production evidence claim-gate should consume the qualified customs/trade review proof manifest")
    if production_evidence_claim_gate.get("qualified_customs_trade_review_record_count") != 0:
        failures.append("production evidence claim-gate should show zero returned qualified customs/trade records")
    if production_evidence_claim_gate.get("qualified_customs_trade_accepted_review_record_count") != 0:
        failures.append("production evidence claim-gate should not accept qualified customs/trade proof in committed state")
    if production_evidence_claim_gate.get("qualified_customs_trade_review_blocked_gate_count") != 14:
        failures.append("production evidence claim-gate should keep fourteen qualified customs/trade gates blocked")
    for key in (
        "qualified_customs_trade_reviewed_by_evidence",
        "tariff_confirmed_by_review_evidence",
        "cfia_approved_by_review_evidence",
        "customs_ready_by_review_evidence",
        "qualified_customs_trade_claims_opened_by_intake",
    ):
        if production_evidence_claim_gate.get(key) is not False:
            failures.append(f"production evidence claim-gate expected {key}=false")
    for key in ("external_effects_created", "claims_opened", "public_launch_ready", "live_payment_ready"):
        if production_evidence_claim_gate.get(key) is not False:
            failures.append(f"production evidence claim-gate expected {key}=false")
    claim_decisions = {
        row.get("claim_type"): row for row in production_evidence_claim_gate.get("claim_gate_decisions", [])
    }
    safe_decision = claim_decisions.get("hs_candidate_research_route", {})
    if safe_decision.get("can_show_claim") is not True:
        failures.append("production evidence claim-gate should allow HS candidate research route as preparation only")
    if "source:wco-harmonized-system" not in {row.get("evidence_id") for row in safe_decision.get("evidence_trail", [])}:
        failures.append("HS candidate research route should include WCO source evidence")
    if claim_decisions.get("document_field_extraction_draft", {}).get("can_show_claim") is not False:
        failures.append("document field extraction claim must stay blocked until a real customer extraction exists")
    if "missing customer document field extraction" not in claim_decisions.get("document_field_extraction_draft", {}).get("missing_evidence", []):
        failures.append("document field extraction should explain the missing customer extraction")
    for claim_type in ("tariff_confirmed", "cfia_approved", "buyer_validated", "supplier_verified", "customs_ready", "shipment_approved"):
        decision = claim_decisions.get(claim_type, {})
        if decision.get("can_show_claim") is not False:
            failures.append(f"production evidence claim-gate must keep {claim_type} blocked")
        if decision.get("allowed_wording"):
            failures.append(f"production evidence claim-gate must not provide allowed wording for {claim_type}")
    tariff_source_mapper = next(
        (
            row
            for row in production_evidence_claim_gate.get("evidence_mappers", [])
            if row.get("evidence_id") == "source:cbsa-customs-tariff-2026"
        ),
        {},
    )
    if "hs_candidate_research_route" not in tariff_source_mapper.get("supports_claims", []):
        failures.append("tariff source evidence should support only source-routed HS preparation")
    if "tariff_confirmed" not in tariff_source_mapper.get("blocks_claims", []):
        failures.append("tariff source evidence should block tariff-confirmed wording without qualified review")
    if production_decision_scoring.get("status") != "production_decision_scoring_engine_ready_no_global_readiness_score":
        failures.append(
            "production decision scoring status expected production_decision_scoring_engine_ready_no_global_readiness_score, "
            f"got {production_decision_scoring.get('status')!r}"
        )
    if production_decision_scoring.get("score_count") != 6:
        failures.append("production decision scoring should keep the six canonical scores separate")
    if production_decision_scoring.get("decision_score_record_count", 0) < 6:
        failures.append("production decision scoring should emit score records")
    for key in ("single_global_readiness_score_created", "combined_readiness_label_created", "approval_language_allowed", "external_effects_created", "claims_opened", "public_launch_ready", "live_payment_ready"):
        if production_decision_scoring.get(key) is not False:
            failures.append(f"production decision scoring expected {key}=false")
    expected_score_ids = {
        "market_signal_score",
        "evidence_completeness_score",
        "source_freshness_score",
        "buyer_supplier_evidence_score",
        "responsibility_clarity_score",
        "decision_safety_score",
    }
    if set(production_decision_scoring.get("score_ids", [])) != expected_score_ids:
        failures.append("production decision scoring must expose the six canonical score IDs")
    score_records = {
        row.get("score"): row
        for row in production_decision_scoring.get("decision_score_records", [])
        if row.get("packet_id") == "packet-frozen-tuna-canada-001"
    }
    if set(score_records) != expected_score_ids:
        failures.append("production decision scoring missing current packet score records")
    for score_id, record in score_records.items():
        for field in ("score_value", "score_cap", "label", "reason", "cap_reason", "blocking_fields", "next_action"):
            if field not in record:
                failures.append(f"production decision score {score_id} missing {field}")
                break
        if record.get("single_global_readiness_score_used") is not False:
            failures.append(f"production decision score {score_id} must not use a global readiness score")
        if record.get("approval_language_blocked") is not True:
            failures.append(f"production decision score {score_id} must block approval language")
        if record.get("score_value", 0) > record.get("score_cap", 100):
            failures.append(f"production decision score {score_id} exceeds its cap")
    for score_id in ("source_freshness_score", "responsibility_clarity_score", "decision_safety_score"):
        if score_records.get(score_id, {}).get("label") != "red":
            failures.append(f"production decision score {score_id} should stay red for the current packet")
    if "tariff_confirmed" not in score_records.get("decision_safety_score", {}).get("blocked_claim_dependencies", []):
        failures.append("decision safety score should depend on blocked tariff confirmation")
    summaries = production_decision_scoring.get("packet_score_summaries", [])
    if not summaries or summaries[0].get("single_global_readiness_score_created") is not False:
        failures.append("packet score summary must refuse a single global readiness score")
    if production_ai_copilot.get("status") != "production_ai_copilot_engine_ready_no_gate_opening":
        failures.append(
            "production AI copilot status expected production_ai_copilot_engine_ready_no_gate_opening, "
            f"got {production_ai_copilot.get('status')!r}"
        )
    if production_ai_copilot.get("ai_role_count") != 8:
        failures.append("production AI copilot should register the eight AI roles")
    if production_ai_copilot.get("ai_output_contract_count") != 8:
        failures.append("production AI copilot should emit one output contract per AI role")
    if production_ai_copilot.get("prompt_injection_test_count", 0) < 2:
        failures.append("production AI copilot should include prompt-injection safety checks")
    for key in (
        "provider_terms_review_complete",
        "qualified_ai_safety_review_complete",
        "live_model_calls_enabled",
        "can_open_customs_tariff_cfia_buyer_supplier_payment_legal_launch_gate",
        "external_effects_created",
        "claims_opened",
        "public_launch_ready",
        "live_payment_ready",
    ):
        if production_ai_copilot.get(key) is not False:
            failures.append(f"production AI copilot expected {key}=false")
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
        failures.append("production AI copilot role contracts are incomplete")
    allowed_labels = {"draft", "source_backed", "needs_user_confirmation", "needs_expert_review", "blocked"}
    for contract in production_ai_copilot.get("role_contracts", []):
        if contract.get("output_label") not in allowed_labels:
            failures.append(f"production AI role {contract.get('role')} has invalid output label")
        if contract.get("can_open_gate") is not False:
            failures.append(f"production AI role {contract.get('role')} must not open gates")
        if "tariff_confirmed" not in contract.get("blocked_gates", []):
            failures.append(f"production AI role {contract.get('role')} should block tariff_confirmed")
    for contract in production_ai_copilot.get("output_contracts", []):
        if contract.get("can_open_customs_tariff_cfia_buyer_supplier_payment_launch_gate") is not False:
            failures.append(f"production AI output {contract.get('role')} must not open product gates")
        if contract.get("claims_opened") is not False:
            failures.append(f"production AI output {contract.get('role')} must keep claims closed")
    for result in production_ai_copilot.get("prompt_injection_results", []):
        if result.get("result") != "blocked_output_no_gate_opened":
            failures.append(f"prompt injection check {result.get('test_id')} should fail closed")
        if result.get("can_open_gate") is not False:
            failures.append(f"prompt injection check {result.get('test_id')} must not open gates")
    if production_expert_review.get("status") != "production_expert_review_network_ready_scope_limited_no_external_claims":
        failures.append(
            "production expert review status expected production_expert_review_network_ready_scope_limited_no_external_claims, "
            f"got {production_expert_review.get('status')!r}"
        )
    if production_expert_review.get("reviewer_lane_count") != 10:
        failures.append("production expert review should register ten reviewer lanes")
    if production_expert_review.get("profile_requirement_count") != 10:
        failures.append("production expert review should create ten profile requirement records")
    if production_expert_review.get("finding_template_count") != 10:
        failures.append("production expert review should create ten finding templates")
    if production_expert_review.get("review_request_count", 0) < 10:
        failures.append("production expert review should create scoped review requests")
    if production_expert_review.get("gate_impact_count", 0) < 10:
        failures.append("production expert review should create claim-gate impact rows")
    if production_expert_review.get("source_registry_coverage_count", 0) < 9:
        failures.append("production expert review should use source-backed reviewer criteria")
    for key in (
        "real_reviewer_signoff_recorded",
        "qualified_credentials_verified",
        "scope_limited_approval_recorded",
        "can_open_customs_tariff_cfia_buyer_supplier_security_privacy_payment_launch_gate",
        "external_effects_created",
        "claims_opened",
    ):
        if production_expert_review.get(key) is not False:
            failures.append(f"production expert review expected {key}=false")
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
        failures.append("production expert review profile lanes are incomplete")
    for profile in production_expert_review.get("reviewer_profiles", []):
        lane_id = profile.get("reviewer_lane_id")
        if profile.get("profile_status") != "missing_real_reviewer":
            failures.append(f"reviewer profile {lane_id} should require a real reviewer")
        if profile.get("credential_status") != "missing":
            failures.append(f"reviewer profile {lane_id} should require credential evidence")
        if not profile.get("required_credential_evidence"):
            failures.append(f"reviewer profile {lane_id} missing credential evidence requirements")
        if not profile.get("source_requirements"):
            failures.append(f"reviewer profile {lane_id} missing source requirements")
        if profile.get("can_open_external_claim_gate") is not False:
            failures.append(f"reviewer profile {lane_id} must not open external claim gates")
    for request in production_expert_review.get("review_requests", []):
        request_id = request.get("review_request_id")
        if request.get("status") != "draft_ready_to_send_no_external_effect":
            failures.append(f"review request {request_id} should be draft-only")
        if request.get("scoped_review_link_status") != "token_required_not_sent":
            failures.append(f"review request {request_id} should not send an external review link")
        if request.get("external_effects_created") is not False or request.get("claims_opened") is not False:
            failures.append(f"review request {request_id} must not create external effects or claims")
        if "tariff_confirmed" not in request.get("out_of_scope_claims", []):
            failures.append(f"review request {request_id} should keep forbidden claims out of scope")
    for template in production_expert_review.get("finding_templates", []):
        if template.get("can_open_external_claim_gate") is not False:
            failures.append(f"finding template {template.get('finding_template_id')} must not open external gates")
        if not template.get("evidence_attachments_required"):
            failures.append(f"finding template {template.get('finding_template_id')} must require evidence attachments")
    for finding in production_expert_review.get("pending_findings", []):
        if finding.get("status") != "awaiting_real_reviewer_finding" or finding.get("decision") != "not_submitted":
            failures.append(f"pending finding {finding.get('finding_id')} should not record a reviewer decision")
        if finding.get("claims_opened") is not False or finding.get("external_effects_created") is not False:
            failures.append(f"pending finding {finding.get('finding_id')} must keep gates closed")
    for impact in production_expert_review.get("gate_impacts", []):
        if impact.get("can_show_after_local_request_only") is not False:
            failures.append(f"gate impact {impact.get('gate_impact_id')} must not show claims after a local request only")
        if impact.get("can_open_external_claim_gate") is not False:
            failures.append(f"gate impact {impact.get('gate_impact_id')} must not open external gates")
    if production_reports.get("status") != "production_reports_engine_ready_cited_exports_blocked_claims_visible":
        failures.append(
            "production reports status expected production_reports_engine_ready_cited_exports_blocked_claims_visible, "
            f"got {production_reports.get('status')!r}"
        )
    if production_reports.get("report_type_count") != 12:
        failures.append("production reports should register twelve report types")
    if production_reports.get("report_record_count", 0) < 12:
        failures.append("production reports should create report records for the current packet")
    if production_reports.get("export_record_count", 0) < 36:
        failures.append("production reports should create JSON, HTML, and PDF exports")
    if production_reports.get("citation_record_count", 0) < 24:
        failures.append("production reports should create source and evidence citation rows")
    for key in (
        "blocked_claim_sections_required",
        "html_preview_supported",
        "pdf_export_supported",
        "json_export_supported",
        "version_history_supported",
    ):
        if production_reports.get(key) is not True:
            failures.append(f"production reports expected {key}=true")
    for key in ("can_hide_blocked_claims", "claims_opened", "external_effects_created", "public_launch_ready", "live_payment_ready"):
        if production_reports.get(key) is not False:
            failures.append(f"production reports expected {key}=false")
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
        failures.append("production reports are missing required report types")
    citation_types = {row.get("citation_type") for row in production_reports.get("citation_records", [])}
    if not {"source", "evidence"}.issubset(citation_types):
        failures.append("production reports should include both source and evidence citations")
    for record in production_reports.get("report_records", []):
        report_id = record.get("report_id")
        if record.get("watermark") != "DRAFT - NOT APPROVAL":
            failures.append(f"production report {report_id} missing draft watermark")
        if record.get("review_status") != "not_reviewed":
            failures.append(f"production report {report_id} should be not reviewed locally")
        if record.get("blocked_claim_section_included") is not True:
            failures.append(f"production report {report_id} must keep blocked claims visible")
        if record.get("can_hide_blocked_claims") is not False:
            failures.append(f"production report {report_id} must not hide blocked claims")
        if record.get("blocked_claim_count", 0) < 1:
            failures.append(f"production report {report_id} missing blocked claims")
        if record.get("citation_count", 0) < 1:
            failures.append(f"production report {report_id} missing citations")
        if record.get("claims_opened") is not False or record.get("external_effects_created") is not False:
            failures.append(f"production report {report_id} must keep claims/effects closed")
    for export in production_reports.get("export_records", []):
        export_path = ROOT / str(export.get("path", ""))
        if not export_path.exists():
            failures.append(f"production report export missing: {export.get('path')}")
            continue
        if export.get("format") == "pdf" and not export_path.read_bytes().startswith(b"%PDF"):
            failures.append(f"production report PDF is invalid: {export.get('path')}")
        if export.get("blocked_claim_section_included") is not True:
            failures.append(f"production report export {export.get('path')} missing blocked claim section flag")
        if export.get("claims_opened") is not False or export.get("external_effects_created") is not False:
            failures.append(f"production report export {export.get('path')} must keep gates closed")
    if production_portals.get("status") != "production_portal_workflow_engine_ready_routes_gated_business_owner_ux":
        failures.append(
            "production portal workflow status expected production_portal_workflow_engine_ready_routes_gated_business_owner_ux, "
            f"got {production_portals.get('status')!r}"
        )
    if production_portals.get("portal_count") != 6:
        failures.append("production portals should define six portals")
    if production_portals.get("workflow_count") != 6:
        failures.append("production portals should define six workflows")
    if production_portals.get("first_screen_option_count") != 4:
        failures.append("production portals should keep the four default first-screen options")
    for key in (
        "all_required_routes_present",
        "first_screen_routes_present",
        "plain_language_required",
        "accessibility_review_required",
        "mobile_review_required",
        "confusion_testing_required",
    ):
        if production_portals.get(key) is not True:
            failures.append(f"production portals expected {key}=true")
    for key in (
        "claims_opened",
        "external_effects_created",
        "public_launch_ready",
        "live_payment_ready",
        "unrestricted_uploads_enabled",
    ):
        if production_portals.get(key) is not False:
            failures.append(f"production portals expected {key}=false")
    expected_portals = {
        "public_portal",
        "exporter_portal",
        "importer_portal",
        "expert_reviewer_portal",
        "operator_admin_portal",
        "enterprise_portal",
    }
    portal_ids = {row.get("portal_id") for row in production_portals.get("portal_records", [])}
    if portal_ids != expected_portals:
        failures.append("production portals are missing required personas")
    for portal in production_portals.get("portal_records", []):
        if portal.get("route_coverage_status") != "covered":
            failures.append(f"portal {portal.get('portal_id')} has missing routes")
        if portal.get("can_open_approval_payment_or_launch_gate") is not False:
            failures.append(f"portal {portal.get('portal_id')} must keep approval/payment/launch gates closed")
    first_labels = {row.get("label") for row in production_portals.get("first_screen_options", [])}
    if first_labels != {"Explore a market", "Prepare a buyer packet", "Check my documents", "Prepare for broker/expert review"}:
        failures.append("production portals first screen options are incorrect")
    for check in production_portals.get("ux_checks", []):
        if check.get("passed") is not True:
            failures.append(f"production portal UX check failed: {check.get('check_id')}")
    for control in production_portals.get("gate_controls", []):
        if (
            control.get("public_launch_ready") is not False
            or control.get("unrestricted_uploads_enabled") is not False
            or control.get("live_payment_enabled") is not False
            or control.get("approval_claims_enabled") is not False
            or control.get("claims_opened") is not False
            or control.get("external_effects_created") is not False
        ):
            failures.append(f"portal gate control {control.get('gate_control_id')} must stay closed")
    if production_enterprise.get("status") != "production_enterprise_api_platform_ready_local_contracts_external_gates_closed":
        failures.append("production enterprise API platform status is incorrect")
    if production_enterprise.get("api_contract_count", 0) < 17:
        failures.append("production enterprise API platform should define at least 17 API contracts")
    if production_enterprise.get("all_required_api_routes_present") is not True:
        failures.append("production enterprise API platform should have all required local API routes present")
    for key in (
        "hosted_enterprise_ready",
        "live_api_keys_issued",
        "webhook_delivery_enabled",
        "unrestricted_uploads_enabled",
        "white_label_claims_approved",
        "claims_opened",
        "external_effects_created",
        "live_payment_ready",
        "public_launch_ready",
    ):
        if production_enterprise.get(key) is not False:
            failures.append(f"production enterprise expected {key}=false")
    if production_enterprise.get("research_reference_count") != 5:
        failures.append("production enterprise should include five API/enterprise research references")
    if production_enterprise.get("workspace_control_count", 0) < 3:
        failures.append("production enterprise should include workspace controls for all local orgs")
    if production_enterprise.get("api_key_record_count", 0) < 2:
        failures.append("production enterprise should include customer API-key contract records")
    if production_enterprise.get("webhook_record_count", 0) < 2:
        failures.append("production enterprise should include customer webhook contract records")
    for contract in production_enterprise.get("api_contracts", []):
        if contract.get("route_present") is not True:
            failures.append(f"enterprise API route missing: {contract.get('path')}")
        if (
            contract.get("auth_required") is not True
            or contract.get("tenant_filter_required") is not True
            or contract.get("object_level_authorization_required") is not True
            or contract.get("claim_gate_required") is not True
            or contract.get("external_effects_created") is not False
            or contract.get("claims_opened") is not False
            or contract.get("live_mode_enabled") is not False
        ):
            failures.append(f"enterprise API contract {contract.get('path')} must be auth/tenant/claim gated and effect-closed")
    for row in production_enterprise.get("permission_matrix", []):
        if row.get("deny_by_default") is not True or row.get("cross_org_access_allowed") is not False:
            failures.append(f"enterprise permission row {row.get('path')} must deny by default and block cross-org access")
    for row in production_enterprise.get("api_key_records", []):
        if row.get("raw_secret_returned") is not False or row.get("live_key_issued") is not False:
            failures.append(f"enterprise API key {row.get('api_key_id')} must not issue a live secret")
    for row in production_enterprise.get("webhook_records", []):
        if row.get("delivery_enabled") is not False or row.get("external_effects_created") is not False:
            failures.append(f"enterprise webhook {row.get('webhook_id')} must keep delivery closed")
    white_label = production_enterprise.get("white_label_policy", {})
    if "remove blocked claims" not in white_label.get("forbidden_customization", []):
        failures.append("enterprise white-label policy must forbid removing blocked claims")
    if white_label.get("claims_opened") is not False:
        failures.append("enterprise white-label policy must not open claims")
    if production_api_service.get("status") != "production_api_service_ready_repository_backed_safe_reads_effects_closed":
        failures.append("production API service should dispatch repository-backed safe reads with closed effects")
    if (
        production_api_service.get("repository_dependency_status")
        != "production_repository_service_ready_database_backed_packet_context_claim_gates_closed"
    ):
        failures.append("production API service should depend on the production repository service")
    if (
        production_api_service.get("enterprise_dependency_status")
        != "production_enterprise_api_platform_ready_local_contracts_external_gates_closed"
    ):
        failures.append("production API service should depend on the enterprise API contract manifest")
    if production_api_service.get("simulated_request_count", 0) < 10:
        failures.append("production API service should include simulated request/response proof")
    if production_api_service.get("safe_read_success_count", 0) < 5:
        failures.append("production API service should prove safe repository reads")
    if production_api_service.get("tenant_denial_count", 0) < 1:
        failures.append("production API service should deny cross-tenant packet reads")
    if production_api_service.get("unauthenticated_denial_count", 0) < 1:
        failures.append("production API service should deny unauthenticated requests")
    if production_api_service.get("effect_gate_closed_count", 0) < 3:
        failures.append("production API service should close effectful routes")
    sample_responses = {row.get("name"): row.get("response", {}) for row in production_api_service.get("sample_responses", [])}
    for name, status in {
        "customer_packet_read": "ok_repository_packet_context",
        "customer_scores_read": "ok_repository_scores",
        "customer_blocked_claims_read": "ok_repository_blocked_claims",
        "customer_report_context": "ok_repository_report_context_no_write",
        "customer_safe_summary": "ok_safe_summary_no_live_model_call",
        "other_customer_packet_denied": "access_denied",
        "anonymous_packet_denied": "authentication_required",
        "upload_effect_closed": "effect_gate_closed",
    }.items():
        if sample_responses.get(name, {}).get("status") != status:
            failures.append(f"production API service sample {name} expected {status}")
    for key in (
        "hosted_api_ready",
        "live_api_keys_issued",
        "webhook_delivery_enabled",
        "real_uploads_enabled",
        "external_effects_created",
        "claims_opened",
        "public_launch_ready",
    ):
        if production_api_service.get(key) is not False:
            failures.append(f"production API service expected {key}=false")
    for required_source_text in (
        "dispatch_production_api_request",
        "is_production_api_service_route",
        "_send_production_api_service_response",
    ):
        if required_source_text not in operator_app_source:
            failures.append(f"operator app should delegate production API routes through {required_source_text}")
    if production_payments.get("status") != "production_payment_monetization_engine_ready_live_checkout_closed":
        failures.append("production payment monetization status is incorrect")
    if production_payments.get("pricing_tier_count") != 7:
        failures.append("production payments should define seven pricing tiers")
    if production_payments.get("research_reference_count") != 5:
        failures.append("production payments should include five Stripe/payment research references")
    if production_payments.get("payment_activation_evidence_status") != "payment_activation_proof_intake_ready_real_payment_evidence_required_claims_closed":
        failures.append("production payments should consume the payment activation proof manifest")
    if production_payments.get("payment_activation_record_count") != 0:
        failures.append("production payments should show zero returned payment activation records in committed state")
    if production_payments.get("payment_activation_accepted_record_count") != 0:
        failures.append("production payments should not accept payment activation proof in committed state")
    if production_payments.get("payment_activation_blocked_gate_count") != 13:
        failures.append("production payments should keep thirteen payment activation proof gates blocked")
    if production_payments.get("payment_activation_live_ready_by_evidence") is not False:
        failures.append("production payments should keep payment activation evidence readiness false")
    if production_payments.get("blocked_payment_gate_count") != production_payments.get("payment_gate_count"):
        failures.append("production payments should keep every payment gate blocked")
    if "prepared trade readiness packet" not in production_payments.get("allowed_paid_scope", []):
        failures.append("production payments should allow charging for preparation")
    if "customs approval" not in production_payments.get("forbidden_paid_scope", []):
        failures.append("production payments must forbid charging for customs approval")
    for key in (
        "external_charge_created",
        "live_checkout_enabled",
        "live_payment_ready",
        "live_mode_objects_created",
        "checkout_url_created",
        "webhook_delivery_enabled",
        "stripe_secret_key_configured",
        "pricing_approved",
        "refund_support_policy_approved",
        "tax_accounting_review_completed",
        "payment_security_review_completed",
        "claim_language_review_completed",
        "claims_opened",
        "public_launch_ready",
    ):
        if production_payments.get(key) is not False:
            failures.append(f"production payments expected {key}=false")
    for tier in production_payments.get("pricing_tiers", []):
        if tier.get("paid") and (
            tier.get("can_charge_for_approval") is not False
            or tier.get("live_checkout_enabled") is not False
            or "tariff confirmation" not in tier.get("forbidden_scope", [])
        ):
            failures.append(f"paid tier {tier.get('tier_id')} must charge only for preparation")
    for webhook in production_payments.get("webhook_controls", []):
        if (
            webhook.get("delivery_enabled") is not False
            or webhook.get("external_effects_created") is not False
            or webhook.get("signature_verification_required") is not True
            or webhook.get("idempotency_required") is not True
            or webhook.get("duplicate_event_handling_required") is not True
            or webhook.get("out_of_order_event_handling_required") is not True
        ):
            failures.append(f"payment webhook {webhook.get('event_type')} should stay closed and robust")
    if production_trust.get("status") != "production_security_privacy_reliability_engine_ready_local_controls_external_trust_gates_closed":
        failures.append("production trust status is incorrect")
    if production_trust.get("trust_control_count", 0) < 15:
        failures.append("production trust should define at least fifteen controls")
    if production_trust.get("research_reference_count", 0) < 9:
        failures.append("production trust should include current privacy/security/AI research references")
    if production_trust.get("blocked_trust_gate_count") != production_trust.get("trust_gate_count"):
        failures.append("production trust should keep every production trust gate blocked")
    if production_trust.get("unapproved_vendor_count") != production_trust.get("vendor_record_count"):
        failures.append("production trust should keep every vendor unapproved until real review")
    if (
        production_trust.get("legal_privacy_security_approval_evidence_status")
        != "legal_privacy_security_approval_intake_ready_real_approval_evidence_required_claims_closed"
    ):
        failures.append("production trust should consume the legal/privacy/security approval proof manifest")
    if production_trust.get("legal_privacy_security_approval_record_count") != 0:
        failures.append("production trust should show zero returned legal/privacy/security approval records")
    if production_trust.get("legal_privacy_security_accepted_approval_record_count") != 0:
        failures.append("production trust should not accept legal/privacy/security approval proof in committed state")
    if production_trust.get("legal_privacy_security_approval_blocked_gate_count") != 14:
        failures.append("production trust should keep fourteen legal/privacy/security approval gates blocked")
    if production_trust.get("legal_privacy_security_approved_by_evidence") is not False:
        failures.append("production trust should keep legal/privacy/security evidence approval false")
    if production_trust.get("legal_privacy_security_claims_opened_by_intake") is not False:
        failures.append("production trust should keep legal/privacy/security approval claims closed")
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
        "real_file_uploads_allowed",
        "unrestricted_uploads_enabled",
        "hosted_private_beta_ready",
        "production_trust_approved",
        "public_launch_ready",
    ):
        if production_trust.get(key) is not False:
            failures.append(f"production trust expected {key}=false")
    backup_drill = production_trust.get("backup_restore_drill", {})
    if (
        backup_drill.get("status") != "local_backup_restore_hash_drill_passed"
        or backup_drill.get("production_backup_restore_test_passed") is not False
        or backup_drill.get("hash_match_count") != backup_drill.get("existing_artifact_count")
    ):
        failures.append("production trust should pass local artifact restore hash drill while keeping production restore gate closed")
    for vendor in production_trust.get("vendor_register", []):
        if vendor.get("production_approved") is not False or vendor.get("customer_data_allowed") is not False:
            failures.append(f"vendor {vendor.get('vendor_id')} should not be production-approved")
    for gate in production_trust.get("trust_gates", []):
        if gate.get("state") != "blocked" or gate.get("opened_by_local_artifact") is not False:
            failures.append(f"trust gate {gate.get('gate_id')} should stay blocked")
    if production_launch.get("status") != "production_launch_control_plane_ready_exact_scope_public_launch_blocked":
        failures.append("production launch control plane status is incorrect")
    if production_launch.get("launch_gate_count") != 13:
        failures.append("production launch control plane should define thirteen launch gates")
    if production_launch.get("blocked_launch_gate_count", 0) < 8:
        failures.append("production launch control plane should keep public-critical gates blocked")
    if production_launch.get("public_scope_candidate_count") != 6:
        failures.append("production launch control plane should define six candidate public-scope items")
    if production_launch.get("blocked_public_scope_count") != 8:
        failures.append("production launch control plane should define eight blocked public-scope items")
    for key in (
        "exact_public_scope_approved",
        "public_launch_approved",
        "hosted_private_beta_ready",
        "production_infrastructure_ready",
        "real_user_evidence_ready",
        "payment_activation_ready",
        "external_claims_opened",
        "activation_allowed",
        "final_owner_approval_recorded",
    ):
        if production_launch.get(key) is not False:
            failures.append(f"production launch control expected {key}=false")
    blocked_scope_ids = {row.get("scope_id") for row in production_launch.get("blocked_public_scope", [])}
    for required in ("unrestricted_real_uploads", "live_payments", "automated_outreach", "buyer_validated_language", "supplier_verified_language"):
        if required not in blocked_scope_ids:
            failures.append(f"production launch blocked scope missing {required}")
    for row in production_launch.get("public_scope_candidates", []):
        if row.get("activation_allowed") is not False:
            failures.append(f"public scope candidate {row.get('scope_id')} should remain activation-blocked")
    final_owner = next((row for row in production_launch.get("launch_gates", []) if row.get("gate_id") == "final_owner_gate"), {})
    if final_owner.get("state") != "blocked":
        failures.append("final owner gate should remain blocked")
    if not screenshot_manifest_path.exists():
        failures.append("operator screenshot manifest was not generated")
    if screenshot_manifest.get("status") != "screenshots_ready":
        failures.append("operator screenshot manifest should have screenshots_ready status")
    if screenshot_manifest.get("screenshot_count", 0) < 1:
        failures.append("operator screenshot manifest should include at least one generated screenshot")
    if "proof_boundary" not in screenshot_manifest:
        failures.append("operator screenshot manifest must include a proof boundary")
    if continuation.get("status") != "startup_in_progress":
        failures.append(f"continuation status expected startup_in_progress, got {continuation.get('status')!r}")
    if continuation.get("must_continue") is not True:
        failures.append("continuation plan must require continued evidence lanes")
    if continuation.get("lane_count", 0) < 5:
        failures.append("continuation plan should include buyer, compliance, country, data, contract, screening, and launch lanes")
    closed_claims = set(continuation.get("closed_claims", []))
    for claim in ("fully_operational", "launch_ready", "commercially_ready"):
        if claim not in closed_claims:
            failures.append(f"continuation plan must keep {claim} closed")
    if vc_pitch.get("status") != "vc_pitch_ready_with_diligence_gates":
        failures.append(f"VC pitch status expected ready with diligence gates, got {vc_pitch.get('status')!r}")
    if len(vc_pitch.get("diligence_lanes", [])) < 6:
        failures.append("VC pitch packet should include buyer, design-partner, compliance, data, business, and legal diligence lanes")
    pitch_closed_claims = set(vc_pitch.get("closed_claims", []))
    for claim in ("fully_operational", "public_launch_ready", "revenue_proven"):
        if claim not in pitch_closed_claims:
            failures.append(f"VC pitch packet must keep {claim} closed")
    for path in (
        "investor/vc_pitch_deck.md",
        "investor/one_pager.md",
        "investor/demo_script.md",
        "investor/diligence_room_index.md",
        "board/board_go_live_brief.md",
        "board/expert_review_packet.md",
        "board/launch_control_checklist.md",
        "board/financial_operating_model.md",
    ):
        if not (ROOT / path).exists():
            failures.append(f"missing pitch or board artifact: {path}")
    if board.get("status") != "board_go_live_candidate_with_human_approval_gates":
        failures.append(f"board go-live status expected candidate with human gates, got {board.get('status')!r}")
    if board.get("primary_market") != "Canada":
        failures.append(f"board go-live primary market expected Canada, got {board.get('primary_market')!r}")
    if board.get("human_approval_gate_count", 0) < 10:
        failures.append("board go-live packet should include simulated expert and launch human approval gates")
    for key in ("canadian_tools_ready", "simulated_expert_reviews_ready", "launch_controls_ready"):
        if board.get(key) is not True:
            failures.append(f"board go-live packet expected {key}=true")
    board_closed_claims = set(board.get("closed_claims", []))
    for claim in ("public_launch_ready", "legal_advice_ready", "financial_advice_ready"):
        if claim not in board_closed_claims:
            failures.append(f"board go-live packet must keep {claim} closed")
    if workflow.get("status") != "operator_workflow_ready_internal":
        failures.append(f"operator workflow expected internal ready, got {workflow.get('status')!r}")
    if workflow.get("operator_can_use_now") is not True:
        failures.append("operator workflow should be usable for internal review now")
    if workflow.get("work_queue_count", 0) < 20:
        failures.append("operator workflow should include source, gate, lane, and human-approval rows")
    workflow_types = set(workflow.get("work_queue_counts_by_type", {}))
    for row_type in (
        "source_card_review",
        "external_evidence_gate",
        "continuation_lane",
        "human_approval_gate",
    ):
        if row_type not in workflow_types:
            failures.append(f"operator workflow must include {row_type} rows")
    if workflow.get("unsafe_gates_closed") is not True:
        failures.append("operator workflow must keep unsafe gates closed")
    workflow_closed_claims = set(workflow.get("closed_claims", []))
    for claim in ("public_launch_ready", "customs_or_tariff_advice_ready", "supplier_recommendation_ready"):
        if claim not in workflow_closed_claims:
            failures.append(f"operator workflow must keep {claim} closed")
    if customer.get("status") != "customer_workflow_ready_internal":
        failures.append(f"customer workflow expected internal ready, got {customer.get('status')!r}")
    if customer.get("display_status") != "Internal logic ready - external claims blocked":
        failures.append(f"customer workflow display status is unsafe or unexpected: {customer.get('display_status')!r}")
    if customer.get("operator_display_status") != "Operator workbench usable for internal review":
        failures.append("customer workflow should expose operator workbench display status")
    if customer.get("customer_stage_status") != "Customer packet prototype active - real customer use not enabled":
        failures.append("customer workflow should expose customer prototype stage status")
    if customer.get("private_beta_status") != "blocked":
        failures.append("customer workflow should keep private beta blocked")
    if customer.get("packet_count", 0) < 1:
        failures.append("customer workflow should include at least one source packet")
    if customer.get("blocker_count", 0) < 1:
        failures.append("customer workflow must keep external-claim blockers visible")
    if len(customer.get("blocker_groups", [])) < 3:
        failures.append("customer workflow should consolidate blockers into grouped categories")
    if not customer.get("ai_review_runs"):
        failures.append("customer workflow should include AI simulated review runs")
    packet = customer.get("packets", [{}])[0]
    if not str(packet.get("customer_visible_status_label") or "").startswith("Blocked -"):
        failures.append("customer packet should remain blocked with customer-readable status")
    evidence_summary = packet.get("evidence_summary", {})
    if evidence_summary.get("attached", 0) < 3 or evidence_summary.get("missing", 0) < 4:
        failures.append("customer packet should expose evidence quality summary")
    if evidence_summary.get("ai_allowed", 0) < 1:
        failures.append("customer packet should expose AI permission summary")
    group_titles = {row.get("title") for row in packet.get("blocker_groups", [])}
    for group in ("Compliance Review", "Source Rights / Contract", "Buyer Validation"):
        if group not in group_titles:
            failures.append(f"customer packet should include grouped blocker {group}")
    customer_closed_claims = set(customer.get("blocked_claims", []))
    for claim in (
        "tariff_confirmed",
        "cfia_compliant",
        "supplier_recommended",
        "buyer_validated",
        "ready_to_import",
    ):
        if claim not in customer_closed_claims:
            failures.append(f"customer workflow must keep {claim} blocked")
    if evidence_ledger.get("status") != "evidence_ledger_ready_internal":
        failures.append(f"evidence ledger expected internal ready, got {evidence_ledger.get('status')!r}")
    if evidence_ledger.get("evidence_count", 0) < 3:
        failures.append("evidence ledger should include customer, CID, and official Canadian reference evidence")
    if "stale" not in evidence_ledger.get("counts_by_quality", {}):
        failures.append("evidence ledger should expose evidence quality counts")
    if not all("sensitivity_level" in row and "ai_processing_mode" in row for row in evidence_ledger.get("rows", [])):
        failures.append("evidence ledger should include sensitivity and AI permission fields")
    if runtime.get("status") != "private_beta_candidate_with_external_human_gates":
        failures.append(f"runtime state has unexpected status {runtime.get('status')!r}")
    if len(runtime.get("users", [])) < 4 or len(runtime.get("organizations", [])) < 3:
        failures.append("runtime state should include users and organizations")
    if "/api/auth/login" not in runtime.get("api_routes", []):
        failures.append("runtime state should expose auth API routes")
    if runtime.get("product") != "Trade Readiness Copilot":
        failures.append("runtime state should expose Trade Readiness Copilot as the public product")
    if runtime.get("internal_engine") != "Importer Source Readiness Copilot":
        failures.append("runtime state should preserve the internal engine name")
    if runtime.get("public_product_surface", {}).get("status") != "public_quick_check_ready_local_with_external_gates":
        failures.append("runtime state should expose the local public quick-check surface")
    for route in (
        "/start",
        "/tools/export-readiness",
        "/tools/document-check",
        "/opportunities",
        "/country-coverage",
        "/transport-readiness",
        "/reports/sample",
        "/pricing",
        "/billing",
        "/billing/usage",
        "/agent-api",
        "/stages",
        "/research-plan",
        "/expert-network",
        "/team-workspace",
        "/launch-operations",
        "/ai-data-policy",
        "/security",
        "/public/packets/:packetId/result",
        "/public/packets/:packetId/confirm",
        "/workspace",
        "/packets/:packetId/source-monitoring",
        "/packets/:packetId/safe-summary",
    ):
        if route not in runtime.get("ui_routes", {}).get("customer", []):
            failures.append(f"runtime state should expose public UI route {route}")
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
        if route not in runtime.get("api_routes", []):
            failures.append(f"runtime state should expose public API route {route}")
    if "/api/orgs/current/ai-policy" not in runtime.get("api_routes", []):
        failures.append("runtime state should expose AI policy API routes")
    if "/api/evidence/:evidenceId/ai-permission" not in runtime.get("api_routes", []):
        failures.append("runtime state should expose evidence AI permission API routes")
    if "/settings/ai-data-policy" not in runtime.get("ui_routes", {}).get("customer", []):
        failures.append("runtime state should expose customer AI policy settings route")
    if "/review/:reviewToken" not in runtime.get("ui_routes", {}).get("expert", []):
        failures.append("runtime state should expose scoped expert review routes")
    if runtime.get("security_controls", {}).get("organization_isolation") is None:
        failures.append("runtime state should describe organization isolation controls")
    if auth_rbac.get("security_controls", {}).get("rbac") is None:
        failures.append("auth/RBAC matrix should include RBAC controls")
    if claims_gate.get("blocked_by_default") is not True or len(claims_gate.get("claims", [])) < 6:
        failures.append("claims gate matrix should keep claims blocked by default")
    if not review_requests or review_requests[0].get("token") != "review-token-packet-frozen-tuna-canada-001":
        failures.append("review requests should include scoped frozen tuna review token")
    if len(audit_events.get("events", [])) < 3:
        failures.append("audit events should include packet, AI review, and report export events")
    if deployment.get("status") != "deployable_local_stack_ready_with_external_hosting_gates":
        failures.append("deployment readiness should describe hostable local stack with external gates")
    if ai_data_policy.get("status") != "ai_data_policy_ready" or len(ai_data_policy.get("policies", [])) < 2:
        failures.append("AI data policy artifact should expose organization policies")
    if ai_model_router.get("status") != "ai_model_router_ready" or not ai_model_router.get("route_decisions"):
        failures.append("AI model router artifact should expose route decisions")
    if redaction_pipeline.get("status") != "redaction_pipeline_ready" or "emails" not in redaction_pipeline.get("categories", []):
        failures.append("redaction pipeline artifact should expose redaction categories")
    if manual_no_ai_workflow.get("status") != "manual_no_ai_workflow_ready":
        failures.append("manual/no-AI workflow artifact should be ready")
    requirement_ids = {row.get("id") for row in requirements_traceability.get("requirements", [])}
    if len(requirements_traceability.get("requirements", [])) < 44:
        failures.append("requirements traceability matrix should cover public, exporter, policy, completion, all-stage, and operation requirements")
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
            failures.append(f"requirements traceability matrix missing {requirement_id}")
    if public_trade.get("status") != "public_trade_readiness_ready_local":
        failures.append("public trade readiness manifest should be generated")
    if public_trade.get("public_product") != "Trade Readiness Copilot":
        failures.append("public trade readiness manifest should use the public product name")
    if "/api/public/quick-check" not in public_trade.get("routes", {}).get("api", []):
        failures.append("public trade readiness manifest should expose quick-check API")
    if "/api/public/starter" not in public_trade.get("routes", {}).get("api", []):
        failures.append("public trade readiness manifest should expose starter API")
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
            failures.append(f"public trade readiness manifest should expose {route}")
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
            failures.append(f"public trade readiness manifest should expose {route}")
    if "beginner_no_documents" not in public_trade.get("modes", {}):
        failures.append("public trade readiness manifest should expose beginner no-documents mode")
    if public_trade.get("intelligence_hub_policy_monitor", {}).get("status") != "database_style_contract_ready":
        failures.append("public manifest should expose the Intelligence Hub policy monitor contract")
    if "completion_stage_contracts" not in public_trade:
        failures.append("public manifest should expose completion-stage contracts")
    if exporter_mode.get("status") != "exporter_mode_requirements_ready":
        failures.append("exporter mode requirements manifest should be generated")
    if "exporter_side_readiness" not in exporter_mode.get("readiness_lanes", []):
        failures.append("exporter mode manifest should include exporter-side readiness lane")
    if "Broker Review Packet.pdf" not in public_reports.get("reports", []):
        failures.append("public report types should include Broker Review Packet.pdf")
    if "Starter Checklist.pdf" not in public_reports.get("reports", []):
        failures.append("public report types should include Starter Checklist.pdf")
    for report_name in ("Opportunity Research Report.pdf", "Policy Change Impact Report.pdf", "Broker/Freight-Forwarder Packet.pdf"):
        if report_name not in public_reports.get("reports", []):
            failures.append(f"public report types should include {report_name}")
    if public_upload_policy.get("notice_required") is not True:
        failures.append("public upload policy should require upload/AI notice")
    if public_upload_policy.get("quarantine") != "enabled":
        failures.append("public upload policy should quarantine public uploads")
    if public_upload_policy.get("direct_file_serving") is not False:
        failures.append("public upload policy should disable direct file serving")
    if public_upload_policy.get("user_confirmation_required") is not True:
        failures.append("public upload policy should require user confirmation")
    if policy_monitor.get("status") != "intelligence_hub_policy_monitor_ready_with_external_refresh_gates":
        failures.append("policy monitor should be generated with external refresh gates")
    if policy_monitor.get("integration_mode") != "database_style_local_contract":
        failures.append("policy monitor should use database-style local contract mode")
    if policy_monitor.get("monitored_source_count", 0) < 8:
        failures.append("policy monitor should include official Canadian source registry rows")
    if policy_monitor.get("stale_source_blocker_count", 0) < 1:
        failures.append("policy monitor should create stale-source blocker rows")
    if policy_snapshots.get("status") != "policy_source_snapshots_ready":
        failures.append("policy source snapshots artifact should be ready")
    if policy_impact.get("status") != "policy_change_impact_report_ready":
        failures.append("policy change impact report should be ready")
    if completion.get("status") != "all_local_stages_implemented_with_external_gates":
        failures.append(f"completion platform status unexpected: {completion.get('status')!r}")
    if country_coverage.get("status") != "country_coverage_ready_with_claim_gates":
        failures.append("country coverage report should be ready with claim gates")
    if opportunity_scanner.get("status") != "opportunity_scanner_ready_with_research_gates":
        failures.append("opportunity scanner should be ready with research gates")
    if opportunity_scanner.get("signal_count", 0) < 1:
        failures.append("opportunity scanner should include at least one signal row")
    if business_logic.get("status") != "business_logic_implemented_with_external_evidence_gates":
        failures.append("business logic report should expose implemented local rules with external evidence gates")
    if business_logic.get("phase_count") != 13:
        failures.append("business logic report should include thirteen business phase surfaces")
    if set(business_logic.get("phase_ids", [])) != {f"phase-{index}" for index in range(1, 14)}:
        failures.append("business logic report should expose phases 1-13")
    if not business_logic.get("packet_rows"):
        failures.append("business logic phase report should include packet rows")
    else:
        first_business_row = business_logic["packet_rows"][0]
        if first_business_row.get("decision_tree", {}).get("question_count") != 12:
            failures.append("business logic decision tree should include 12 questions")
        if first_business_row.get("business_scores", {}).get("score_count") != 6:
            failures.append("business logic should include six separate scores")
        if first_business_row.get("canonical_packet_contract", {}).get("status") != "canonical_trade_packet_contract_ready":
            failures.append("business logic should include the canonical packet contract")
        if first_business_row.get("business_gate_decision", {}).get("status") != "business_logic_executable_external_gates_blocked":
            failures.append("business logic should include executable allowed/blocked action decisions")
        if first_business_row.get("buyer_supplier_evidence", {}).get("status") != "buyer_supplier_evidence_evaluated_claims_blocked":
            failures.append("business logic should evaluate buyer/supplier evidence levels")
        if first_business_row.get("source_freshness", {}).get("status") != "source_freshness_blocked_until_refresh_and_review":
            failures.append("business logic should evaluate source freshness from evidence rows")
    if business_logic.get("operation_status") != "business_logic_operational_local_with_evidence_gates":
        failures.append("business logic should include local operation proof")
    if business_phase_completion.get("status") != "local_business_logic_implemented_external_gates_preserved":
        failures.append("business phase completion report should preserve external gates after local business logic implementation")
    if business_phase_completion.get("completion_phase_contracts", {}).get("phase_count") != 14:
        failures.append("business phase completion report should include phases 0-13")
    if business_phase_completion.get("completion_phase_contracts", {}).get("local_contract_ready_phase_count") != 14:
        failures.append("business phase completion report should mark phases 0-13 locally contract-ready")
    if business_phase_completion.get("completion_phase_contracts", {}).get("public_launch_ready") is not False:
        failures.append("business phase completion must keep public launch blocked")
    if business_phase_completion.get("operation_status") != "business_phase_completion_operational_local_business_logic_external_gates_preserved":
        failures.append("business phase completion report missing local operation proof")
    required_business_doc_terms = [
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
    ]
    for term in required_business_doc_terms:
        if term not in business_core_doc:
            failures.append(f"business core logic document missing {term}")
    for term in (
        "FR-10",
        "Business Decision Preparation",
        "external_effects_created: false",
        "claims_opened: false",
    ):
        if term not in functional_doc:
            failures.append(f"functional requirements document missing {term}")
    for term in (
        "NFR-01",
        "Keep external effects closed by default",
        "live payment ready remains false",
        "delivery policy audit passes",
    ):
        if term not in non_functional_doc:
            failures.append(f"non-functional requirements document missing {term}")
    if transport_readiness.get("status") != "transport_readiness_ready_with_forwarder_gates":
        failures.append("transport readiness should be ready with forwarder gates")
    if not transport_readiness.get("rows"):
        failures.append("transport readiness should include packet rows")
    if billing_controls.get("status") != "billing_credit_controls_ready_local_no_live_checkout":
        failures.append("billing controls should be local and no-live-checkout")
    if billing_controls.get("live_checkout_enabled") is not False:
        failures.append("billing controls must keep live checkout disabled")
    if agent_api.get("status") != "agent_api_manifest_ready_scoped_and_metered":
        failures.append("agent API manifest should be scoped and metered")
    forbidden_tools = set(agent_api.get("forbidden_tools", []))
    for tool in ("approve_import", "confirm_tariff", "validate_buyer", "ship_goods"):
        if tool not in forbidden_tools:
            failures.append(f"agent API manifest must forbid {tool}")
    if traffic_pages.get("status") != "traffic_pages_manifest_ready":
        failures.append("traffic pages manifest should be ready")
    if len(traffic_pages.get("pages", [])) < 10:
        failures.append("traffic pages manifest should include checklist and generator pages")
    if research_execution.get("status") != "research_execution_ready_with_evidence_gates":
        failures.append("research execution plan should be ready with evidence gates")
    if research_execution.get("operation_status") != "research_execution_operational_local_with_evidence_gates":
        failures.append("research execution should include local operation proof")
    if team_workspace.get("status") != "team_workspace_ready_local_with_approval_gates":
        failures.append("team workspace should be ready with approval gates")
    if team_workspace.get("operation_status") != "team_workspace_operational_local_with_approval_gates":
        failures.append("team workspace should include local operation proof")
    if expert_network.get("status") != "expert_network_ready_local_with_human_review_gates":
        failures.append("expert network should be ready with human review gates")
    if expert_network.get("operation_status") != "expert_network_operational_local_with_human_review_gates":
        failures.append("expert network should include local operation proof")
    if billing_usage.get("status") != "billing_usage_ledger_ready_local_no_charges":
        failures.append("billing usage ledger should be local with no charges")
    if billing_usage.get("executed_usage_event_count", 0) < 1:
        failures.append("billing usage ledger should include executed local usage events")
    if billing_usage.get("external_charge_created") is not False:
        failures.append("billing usage ledger must not create external charges")
    if agent_gateway.get("status") != "agent_api_gateway_ready_local_executor_no_external_effects":
        failures.append("agent API gateway should be ready as local dry run")
    if agent_gateway.get("operation_status") != "agent_api_gateway_executed_local_no_external_effects":
        failures.append("agent API gateway should include local execution proof")
    if agent_gateway.get("executed_tool_count", 0) < 1:
        failures.append("agent API gateway should record executed local tools")
    if launch_operations.get("status") != "launch_operations_ready_for_private_beta_review":
        failures.append("launch operations should be ready for private beta review")
    if launch_operations.get("operation_status") != "launch_operations_operational_local_with_human_approval_gates":
        failures.append("launch operations should include local operation proof")
    if all_stages.get("status") != "all_local_stages_implemented_with_external_gates":
        failures.append("all stage readiness report should mark local stages implemented")
    if all_stages.get("stage_count") != 19:
        failures.append("all stage readiness report should include Stage 0 plus Stages 1-18")
    if all_stages.get("implemented_stage_count") != 19:
        failures.append("all stage readiness report should mark all 19 runbook stages implemented locally")
    if all_stages.get("go_live_state_count") != 18:
        failures.append("all stage readiness report should expose 18 go-live states")
    if all_stages.get("runbook_stage_range") != "0-18":
        failures.append("all stage readiness report should expose runbook stage range 0-18")
    stage_ids = {row.get("stage_id") for row in all_stages.get("stages", [])}
    expected_stage_ids = {f"stage-{index:02d}" for index in range(19)}
    missing_stage_ids = sorted(expected_stage_ids - stage_ids)
    if missing_stage_ids:
        failures.append(f"all stage readiness report missing stages: {', '.join(missing_stage_ids)}")
    public_go_live = next(
        (row for row in all_stages.get("stages", []) if row.get("stage_id") == "stage-18"),
        {},
    )
    if public_go_live.get("status") != "public_go_live_subset_defined_blocked_until_approval":
        failures.append("stage-18 should define the safe public go-live subset while keeping approval blocked")
    if any(row.get("external_claims_opened") is not False for row in all_stages.get("stages", [])):
        failures.append("all stage readiness rows must keep external claims closed")
    if all_stages.get("operation_status") != "local_product_operations_executed":
        failures.append("all stage readiness should include product operation proof")
    if all_stages.get("local_execution_proof_count", 0) < 8:
        failures.append("all stage readiness should include multiple local execution proofs")
    if not all(stage.get("has_local_execution_proof") for stage in all_stages.get("stages", [])):
        failures.append("every all-stage row should point to local execution proof")
    if product_operations.get("status") != "local_product_operations_executed":
        failures.append(f"product operations report expected executed status, got {product_operations.get('status')!r}")
    if product_operations.get("operation_count", 0) < 8:
        failures.append("product operations report should include executed local operations")
    if product_operations.get("external_effects_created") is not False:
        failures.append("product operations must not create external effects")
    if product_operations.get("claims_opened") is not False:
        failures.append("product operations must not open external claims")
    if final_go_live.get("status") != "local_go_live_contract_complete_public_launch_blocked":
        failures.append(f"final go-live status unexpected: {final_go_live.get('status')!r}")
    if final_go_live.get("local_contract_complete") is not True:
        failures.append("final go-live report should confirm the local Stage 0-18 contract is complete")
    if final_go_live.get("public_launch_ready") is not False:
        failures.append("final go-live report must keep public_launch_ready=false")
    if final_go_live.get("hosted_private_beta_ready") is not False:
        failures.append("final go-live report must keep hosted_private_beta_ready=false")
    if final_go_live.get("unsafe_gates_closed") is not True:
        failures.append("final go-live report must keep unsafe gates closed")
    if len(final_go_live.get("public_launch_blockers", [])) < 6:
        failures.append("final go-live report should list concrete public-launch blockers")
    if current_sources.get("status") != "current_external_gate_research_ready":
        failures.append("current external gate research artifact should be ready")
    if current_sources.get("source_count", 0) < 8:
        failures.append("current external gate research should include dated official/primary source anchors")
    if external_validation.get("status") != "external_validation_requirements_ready_all_real_world_gates_blocked":
        failures.append("external validation requirements report should be ready and blocked-safe")
    if external_validation.get("gate_count") != 8:
        failures.append("external validation requirements should cover the eight real-world gates")
    if external_validation.get("source_count", 0) < 24:
        failures.append("external validation requirements should include broad official/primary source coverage")
    if external_validation.get("evidence_requirement_count", 0) < 44:
        failures.append("external validation requirements should include detailed evidence rows")
    if external_validation.get("required_data_category_count", 0) < 14:
        failures.append("external validation requirements should include full-lifecycle project data needs")
    if external_validation.get("public_launch_ready") is not False:
        failures.append("external validation requirements must keep public launch blocked")
    if external_validation.get("hosted_private_beta_ready") is not False:
        failures.append("external validation requirements must keep hosted private beta blocked")
    if external_validation.get("live_payment_ready") is not False:
        failures.append("external validation requirements must keep live payment blocked")
    if external_validation.get("simulated_ai_review_can_open_gate") is not False:
        failures.append("external validation requirements must reject AI-only approvals")
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
        failures.append("external validation requirements must include all expected real-world gates")
    if any(not str(row.get("status", "")).startswith("blocked_") for row in external_validation.get("gates", [])):
        failures.append("every external validation gate must remain blocked until real evidence is attached")
    if external_validation_evidence.get("status") != "external_validation_evidence_requirements_ready":
        failures.append("external validation evidence requirements should be generated")
    if external_validation_evidence.get("evidence_requirement_count") != external_validation.get("evidence_requirement_count"):
        failures.append("external validation evidence requirement count should match the report")
    pdf_path = ROOT / "output" / "pdf" / "external_validation_requirements.pdf"
    if not pdf_path.exists() or not pdf_path.read_bytes().startswith(b"%PDF"):
        failures.append("external validation PDF should exist and be a valid PDF")
    brief_pdf_path = ROOT / "output" / "pdf" / "external_validation_reviewer_brief.pdf"
    if not brief_pdf_path.exists() or not brief_pdf_path.read_bytes().startswith(b"%PDF"):
        failures.append("external validation reviewer brief PDF should exist and be a valid PDF")
    input_pdf_path = ROOT / "output" / "pdf" / "go_live_input_requests.pdf"
    if not input_pdf_path.exists() or not input_pdf_path.read_bytes().startswith(b"%PDF"):
        failures.append("go-live input request PDF should exist and be a valid PDF")
    brief_md = (ROOT / "docs" / "EXTERNAL_VALIDATION_REVIEWER_BRIEF.md").read_text(encoding="utf-8")
    if "What I need from you" not in brief_md or "What is not approved yet" not in brief_md:
        failures.append("external validation reviewer brief should use plain reviewer-facing wording")
    for jargon in ("blocker", "gate"):
        if jargon in brief_md.lower():
            failures.append(f"external validation reviewer brief should avoid reviewer-facing jargon: {jargon}")
    if go_live_input_templates.get("status") != "go_live_input_templates_ready":
        failures.append("go-live input templates should be ready")
    if go_live_input_templates.get("template_count") != 8:
        failures.append("go-live input templates should cover the eight review areas")
    if go_live_input_readiness.get("status") != "waiting_for_real_inputs_not_ready_yet":
        failures.append("go-live input readiness should wait for real returned inputs")
    if go_live_input_readiness.get("public_launch_ready") is not False:
        failures.append("go-live input readiness must keep public launch false until real inputs arrive")
    if go_live_input_readiness.get("missing_input_count") != 8:
        failures.append("go-live input readiness should list the eight missing real inputs")
    if go_live_input_readiness.get("evidence_validation_status") != "go_live_returned_input_evidence_ready_claims_closed":
        failures.append("go-live input readiness should use the returned-input evidence validator")
    if go_live_input_readiness.get("claims_opened_by_evidence_validation") is not False:
        failures.append("go-live input evidence validation must not open claims")
    if go_live_returned_input_evidence.get("status") != "go_live_returned_input_evidence_ready_claims_closed":
        failures.append("go-live returned-input evidence manifest should be generated")
    if go_live_returned_input_evidence.get("review_area_count") != 8:
        failures.append("go-live returned-input evidence manifest should cover the eight review areas")
    if go_live_returned_input_evidence.get("accepted_area_count") != 0:
        failures.append("go-live returned-input evidence manifest should not accept areas without real inputs")
    if go_live_returned_input_evidence.get("not_received_area_count") != 8:
        failures.append("go-live returned-input evidence manifest should show eight not-received areas")
    if go_live_returned_input_evidence.get("public_launch_ready_by_evidence") is not False:
        failures.append("go-live returned-input evidence must not approve public launch")
    if go_live_returned_input_evidence.get("claims_opened_by_evidence_validation") is not False:
        failures.append("go-live returned-input evidence validation must keep claims closed")
    if go_live_returned_input_matrix.get("status") != "go_live_returned_input_validation_matrix_ready_claims_closed":
        failures.append("go-live returned-input validation matrix should be generated")
    if hosted_deployment_contract.get("status") != "hosted_deployment_proof_contract_ready_claims_closed":
        failures.append("hosted deployment proof contract should be generated")
    if hosted_deployment_contract.get("required_evidence_category_count") != 13:
        failures.append("hosted deployment proof contract should require thirteen evidence categories")
    if hosted_deployment_contract.get("source_anchor_count", 0) < 5:
        failures.append("hosted deployment proof contract should include researched deployment/security source anchors")
    if hosted_deployment_contract.get("claims_opened") is not False:
        failures.append("hosted deployment proof contract must not open claims")
    if hosted_deployment_proof.get("status") != "hosted_deployment_proof_intake_ready_real_hosted_evidence_required_claims_closed":
        failures.append("hosted deployment proof manifest should be generated")
    if hosted_deployment_proof.get("hosted_record_count") != 0:
        failures.append("committed hosted deployment proof should show zero hosted records until real hosted proof arrives")
    if hosted_deployment_proof.get("accepted_hosted_record_count") != 0:
        failures.append("hosted deployment proof should not accept records without real hosted proof")
    if hosted_deployment_proof.get("required_evidence_category_count") != 13:
        failures.append("hosted deployment proof should track thirteen evidence categories")
    if hosted_deployment_proof.get("missing_evidence_category_count") != 13:
        failures.append("hosted deployment proof should show all hosted evidence categories missing before real proof")
    if hosted_deployment_proof.get("blocked_gate_count") != 13:
        failures.append("hosted deployment proof should keep all hosted gates blocked before real proof")
    if hosted_deployment_proof.get("blocker_export_count") != 13:
        failures.append("hosted deployment proof should export one blocker per missing hosted evidence category")
    for key in (
        "hosted_private_beta_ready_by_environment_evidence",
        "public_launch_ready_by_environment_evidence",
        "real_file_uploads_allowed_by_environment_evidence",
        "claims_opened_by_intake",
        "external_effects_created",
    ):
        if hosted_deployment_proof.get(key) is not False:
            failures.append(f"hosted deployment proof expected {key}=false")
    if hosted_deployment_gate_matrix.get("status") != "hosted_deployment_gate_matrix_ready_claims_closed":
        failures.append("hosted deployment gate matrix should be generated")
    if hosted_deployment_gate_matrix.get("gate_count") != 13:
        failures.append("hosted deployment gate matrix should include thirteen hosted gates")
    if hosted_deployment_gate_matrix.get("blocked_gate_count") != 13:
        failures.append("hosted deployment gate matrix should keep all gates blocked before hosted proof")
    if hosted_deployment_gate_matrix.get("claims_opened") is not False:
        failures.append("hosted deployment gate matrix must not open claims")
    if len(hosted_deployment_blockers) != 13:
        failures.append("hosted deployment blocker export should include thirteen blocker rows")
    if any(row.get("module") != "hosted_deployment_proof" for row in hosted_deployment_blockers):
        failures.append("hosted deployment blocker rows should be attributed to hosted_deployment_proof")
    if any(row.get("gate") != "closed" for row in hosted_deployment_blockers):
        failures.append("hosted deployment blocker rows must stay closed")
    hosted_deployment_md = (ROOT / "docs" / "HOSTED_DEPLOYMENT_PROOF.md").read_text(encoding="utf-8")
    if "Hosted private beta ready by environment evidence: false" not in hosted_deployment_md:
        failures.append("hosted deployment proof doc should show private beta remains closed")
    if payment_activation_contract.get("status") != "payment_activation_proof_contract_ready_claims_closed":
        failures.append("payment activation proof contract should be generated")
    if payment_activation_contract.get("required_evidence_category_count") != 13:
        failures.append("payment activation proof contract should require thirteen evidence categories")
    if payment_activation_contract.get("source_anchor_count", 0) < 6:
        failures.append("payment activation proof contract should include researched Stripe/payment source anchors")
    if payment_activation_contract.get("claims_opened") is not False:
        failures.append("payment activation proof contract must not open claims")
    if payment_activation_proof.get("status") != "payment_activation_proof_intake_ready_real_payment_evidence_required_claims_closed":
        failures.append("payment activation proof manifest should be generated")
    if payment_activation_proof.get("payment_record_count") != 0:
        failures.append("committed payment activation proof should show zero payment records until real payment proof arrives")
    if payment_activation_proof.get("accepted_payment_record_count") != 0:
        failures.append("payment activation proof should not accept records without real payment proof")
    if payment_activation_proof.get("required_evidence_category_count") != 13:
        failures.append("payment activation proof should track thirteen evidence categories")
    if payment_activation_proof.get("missing_evidence_category_count") != 13:
        failures.append("payment activation proof should show all payment evidence categories missing before real proof")
    if payment_activation_proof.get("blocked_gate_count") != 13:
        failures.append("payment activation proof should keep all payment gates blocked before real proof")
    if payment_activation_proof.get("blocker_export_count") != 13:
        failures.append("payment activation proof should export one blocker per missing payment evidence category")
    for key in (
        "live_payment_ready_by_payment_evidence",
        "live_checkout_enabled_by_intake",
        "external_charge_created",
        "public_launch_ready_by_payment_evidence",
        "claims_opened_by_intake",
        "external_effects_created",
    ):
        if payment_activation_proof.get(key) is not False:
            failures.append(f"payment activation proof expected {key}=false")
    if payment_activation_gate_matrix.get("status") != "payment_activation_gate_matrix_ready_claims_closed":
        failures.append("payment activation gate matrix should be generated")
    if payment_activation_gate_matrix.get("gate_count") != 13:
        failures.append("payment activation gate matrix should include thirteen payment gates")
    if payment_activation_gate_matrix.get("blocked_gate_count") != 13:
        failures.append("payment activation gate matrix should keep all gates blocked before payment proof")
    if payment_activation_gate_matrix.get("claims_opened") is not False:
        failures.append("payment activation gate matrix must not open claims")
    if len(payment_activation_blockers) != 13:
        failures.append("payment activation blocker export should include thirteen blocker rows")
    if any(row.get("module") != "payment_activation_proof" for row in payment_activation_blockers):
        failures.append("payment activation blocker rows should be attributed to payment_activation_proof")
    if any(row.get("gate") != "closed" for row in payment_activation_blockers):
        failures.append("payment activation blocker rows must stay closed")
    payment_activation_md = (ROOT / "docs" / "PAYMENT_ACTIVATION_PROOF.md").read_text(encoding="utf-8")
    if "Live checkout enabled by intake: false" not in payment_activation_md:
        failures.append("payment activation proof doc should show live checkout remains closed")
    if legal_privacy_security_approval_contract.get("status") != "legal_privacy_security_approval_contract_ready_claims_closed":
        failures.append("legal/privacy/security approval proof contract should be generated")
    if legal_privacy_security_approval_contract.get("required_evidence_category_count") != 14:
        failures.append("legal/privacy/security approval contract should require fourteen evidence categories")
    if legal_privacy_security_approval_contract.get("source_anchor_count", 0) < 9:
        failures.append("legal/privacy/security approval contract should include researched privacy/security source anchors")
    if legal_privacy_security_approval_contract.get("claims_opened") is not False:
        failures.append("legal/privacy/security approval contract must not open claims")
    if (
        legal_privacy_security_approval.get("status")
        != "legal_privacy_security_approval_intake_ready_real_approval_evidence_required_claims_closed"
    ):
        failures.append("legal/privacy/security approval manifest should be generated")
    if legal_privacy_security_approval.get("approval_record_count") != 0:
        failures.append("committed legal/privacy/security approval proof should show zero records until real approval arrives")
    if legal_privacy_security_approval.get("accepted_approval_record_count") != 0:
        failures.append("legal/privacy/security approval proof should not accept approval records in committed state")
    if legal_privacy_security_approval.get("required_evidence_category_count") != 14:
        failures.append("legal/privacy/security approval proof should track fourteen evidence categories")
    if legal_privacy_security_approval.get("missing_evidence_category_count") != 14:
        failures.append("legal/privacy/security approval proof should show all approval evidence categories missing")
    if legal_privacy_security_approval.get("blocked_gate_count") != 14:
        failures.append("legal/privacy/security approval proof should keep all approval gates blocked before real proof")
    if legal_privacy_security_approval.get("blocker_export_count") != 14:
        failures.append("legal/privacy/security approval proof should export one blocker per missing evidence category")
    for key in (
        "legal_privacy_security_approved_by_evidence",
        "real_file_uploads_allowed_by_intake",
        "hosted_private_beta_ready_by_approval_evidence",
        "public_launch_ready_by_approval_evidence",
        "claims_opened_by_intake",
        "external_effects_created",
    ):
        if legal_privacy_security_approval.get(key) is not False:
            failures.append(f"legal/privacy/security approval proof expected {key}=false")
    if (
        legal_privacy_security_approval_gate_matrix.get("status")
        != "legal_privacy_security_approval_gate_matrix_ready_claims_closed"
    ):
        failures.append("legal/privacy/security approval gate matrix should be generated")
    if legal_privacy_security_approval_gate_matrix.get("gate_count") != 14:
        failures.append("legal/privacy/security approval gate matrix should include fourteen gates")
    if legal_privacy_security_approval_gate_matrix.get("blocked_gate_count") != 14:
        failures.append("legal/privacy/security approval gate matrix should keep all gates blocked before approval proof")
    if legal_privacy_security_approval_gate_matrix.get("claims_opened") is not False:
        failures.append("legal/privacy/security approval gate matrix must not open claims")
    if len(legal_privacy_security_approval_blockers) != 14:
        failures.append("legal/privacy/security approval blocker export should include fourteen blocker rows")
    if any(row.get("module") != "legal_privacy_security_approval" for row in legal_privacy_security_approval_blockers):
        failures.append("legal/privacy/security approval blocker rows should be attributed to the approval module")
    if any(row.get("gate") != "closed" for row in legal_privacy_security_approval_blockers):
        failures.append("legal/privacy/security approval blocker rows must stay closed")
    approval_md = (ROOT / "docs" / "LEGAL_PRIVACY_SECURITY_APPROVAL_PROOF.md").read_text(encoding="utf-8")
    if "Real file uploads allowed by intake: false" not in approval_md:
        failures.append("legal/privacy/security approval proof doc should show real uploads remain closed")
    if qualified_customs_trade_review_contract.get("status") != "qualified_customs_trade_review_contract_ready_claims_closed":
        failures.append("qualified customs/trade review contract should be generated")
    if qualified_customs_trade_review_contract.get("required_evidence_category_count") != 14:
        failures.append("qualified customs/trade review contract should require fourteen evidence categories")
    if qualified_customs_trade_review_contract.get("source_anchor_count", 0) < 9:
        failures.append("qualified customs/trade review contract should include researched official-source anchors")
    if qualified_customs_trade_review_contract.get("claims_opened") is not False:
        failures.append("qualified customs/trade review contract must not open claims")
    if (
        qualified_customs_trade_review.get("status")
        != "qualified_customs_trade_review_intake_ready_real_review_evidence_required_claims_closed"
    ):
        failures.append("qualified customs/trade review manifest should be generated")
    if qualified_customs_trade_review.get("review_record_count") != 0:
        failures.append("committed qualified customs/trade review proof should show zero records until real review arrives")
    if qualified_customs_trade_review.get("accepted_review_record_count") != 0:
        failures.append("qualified customs/trade review proof should not accept review records in committed state")
    if qualified_customs_trade_review.get("required_evidence_category_count") != 14:
        failures.append("qualified customs/trade review proof should track fourteen evidence categories")
    if qualified_customs_trade_review.get("missing_evidence_category_count") != 14:
        failures.append("qualified customs/trade review proof should show all review evidence categories missing")
    if qualified_customs_trade_review.get("blocked_gate_count") != 14:
        failures.append("qualified customs/trade review proof should keep all review gates blocked before real proof")
    if qualified_customs_trade_review.get("blocker_export_count") != 14:
        failures.append("qualified customs/trade review proof should export one blocker per missing category")
    for key in (
        "customs_trade_reviewed_by_evidence",
        "tariff_confirmed_by_review_evidence",
        "cfia_approved_by_review_evidence",
        "customs_ready_by_review_evidence",
        "shipment_ready_by_review_evidence",
        "public_launch_ready_by_review_evidence",
        "claims_opened_by_intake",
        "external_effects_created",
    ):
        if qualified_customs_trade_review.get(key) is not False:
            failures.append(f"qualified customs/trade review proof expected {key}=false")
    if qualified_customs_trade_review_gate_matrix.get("status") != "qualified_customs_trade_review_gate_matrix_ready_claims_closed":
        failures.append("qualified customs/trade review gate matrix should be generated")
    if qualified_customs_trade_review_gate_matrix.get("gate_count") != 14:
        failures.append("qualified customs/trade review gate matrix should include fourteen gates")
    if qualified_customs_trade_review_gate_matrix.get("blocked_gate_count") != 14:
        failures.append("qualified customs/trade review gate matrix should keep all gates blocked before review proof")
    if qualified_customs_trade_review_gate_matrix.get("claims_opened") is not False:
        failures.append("qualified customs/trade review gate matrix must not open claims")
    if len(qualified_customs_trade_review_blockers) != 14:
        failures.append("qualified customs/trade review blocker export should include fourteen blocker rows")
    if any(row.get("module") != "qualified_customs_trade_review" for row in qualified_customs_trade_review_blockers):
        failures.append("qualified customs/trade review blocker rows should be attributed to the customs/trade module")
    if any(row.get("gate") != "closed" for row in qualified_customs_trade_review_blockers):
        failures.append("qualified customs/trade review blocker rows must stay closed")
    customs_trade_md = (ROOT / "docs" / "QUALIFIED_CUSTOMS_TRADE_REVIEW_PROOF.md").read_text(encoding="utf-8")
    if "Tariff confirmed by review evidence: false" not in customs_trade_md:
        failures.append("qualified customs/trade review doc should show tariff confirmation remains closed")
    input_md = (ROOT / "docs" / "GO_LIVE_INPUT_REQUESTS.md").read_text(encoding="utf-8")
    if "Once Inputs Are Received" not in input_md or "external_inputs/" not in input_md:
        failures.append("go-live input request doc should explain how returned inputs are used")
    input_evidence_md = (ROOT / "docs" / "GO_LIVE_RETURNED_INPUT_EVIDENCE.md").read_text(encoding="utf-8")
    if "Validation Matrix" not in input_evidence_md or "Claims opened by validation: false" not in input_evidence_md:
        failures.append("go-live returned-input evidence doc should show validation without opening claims")
    if production_market_readiness.get("status") != "production_market_readiness_evidence_room_ready_inputs_mapped_gates_closed":
        failures.append("market readiness evidence room should be ready with gate-closed input mapping")
    if production_market_readiness.get("gate_count") != 8:
        failures.append("market readiness evidence room should cover the eight real-world gates")
    if production_market_readiness.get("work_order_count") != 8:
        failures.append("market readiness evidence room should generate one work order per real-world gate")
    if production_market_readiness.get("reviewer_brief_card_count") != 8:
        failures.append("market readiness evidence room should generate reviewer-facing brief cards")
    if production_market_readiness.get("missing_input_count") != go_live_input_readiness.get("missing_input_count"):
        failures.append("market readiness missing input count should match go-live input readiness")
    if production_market_readiness.get("input_capture_enabled_local") is not True:
        failures.append("market readiness evidence room should enable local returned-input capture")
    if production_market_readiness.get("input_capture_route") != "/api/market-readiness/inputs":
        failures.append("market readiness evidence room should expose the returned-input capture route")
    if production_market_readiness.get("input_form_contract", {}).get("status") != "market_readiness_input_form_contract_ready":
        failures.append("market readiness evidence room should include a ready input form contract")
    if production_market_readiness.get("input_ledger_status") != "production_market_readiness_input_ledger_ready_claims_closed":
        failures.append("market readiness evidence room should include the returned-input ledger")
    if production_market_readiness.get("returned_input_evidence_status") != "go_live_returned_input_evidence_ready_claims_closed":
        failures.append("market readiness evidence room should include strict returned-input evidence validation")
    if production_market_readiness.get("returned_input_evidence_route") != "/system_review_graph/go_live_returned_input_evidence_manifest.json":
        failures.append("market readiness evidence room should expose the returned-input evidence manifest")
    if production_market_readiness.get("input_ledger_route") != "/api/market-readiness/input-ledger":
        failures.append("market readiness evidence room should expose the returned-input ledger route")
    if production_market_readiness.get("input_history_status") != "production_market_readiness_input_history_ready_local_audit_trail":
        failures.append("market readiness evidence room should include the returned-input history")
    if production_market_readiness.get("input_history_route") != "/api/market-readiness/input-history":
        failures.append("market readiness evidence room should expose the returned-input history route")
    if production_market_readiness_input_ledger.get("status") != "production_market_readiness_input_ledger_ready_claims_closed":
        failures.append("market readiness input ledger should be generated")
    if production_market_readiness_input_history.get("status") != "production_market_readiness_input_history_ready_local_audit_trail":
        failures.append("market readiness input history should be generated")
    if production_market_readiness_input_ledger.get("review_area_count") != 8:
        failures.append("market readiness input ledger should cover the eight review areas")
    if production_market_readiness_input_ledger.get("accepted_area_count") != production_market_readiness.get("ready_input_count"):
        failures.append("market readiness input ledger accepted count should match ready inputs")
    unaccepted_input_areas = (
        production_market_readiness_input_ledger.get("review_area_count", 0)
        - production_market_readiness_input_ledger.get("accepted_area_count", 0)
    )
    if unaccepted_input_areas != production_market_readiness.get("missing_input_count"):
        failures.append("market readiness input ledger unaccepted count should match missing inputs")
    if production_market_readiness_input_ledger.get("claims_opened_by_ledger") is not False:
        failures.append("market readiness input ledger must not open claims")
    if production_market_readiness_input_ledger.get("public_launch_ready_by_ledger") is not False:
        failures.append("market readiness input ledger must not approve public launch")
    if production_market_readiness_input_ledger.get("invalid_record_count") != 0:
        failures.append("market readiness input ledger should not contain invalid records in committed artifacts")
    if production_market_readiness_input_ledger.get("missing_required_evidence_area_count") != 0:
        failures.append("market readiness input ledger should not contain half-ready evidence records in committed artifacts")
    if production_market_readiness_input_ledger.get("unqualified_area_count") != 0:
        failures.append("market readiness input ledger should not contain unqualified reviewer records in committed artifacts")
    if production_market_readiness_input_history.get("claims_opened_by_history") is not False:
        failures.append("market readiness input history must not open claims")
    if production_market_readiness_input_history.get("invalid_history_record_count") != 0:
        failures.append("market readiness input history should not contain invalid records in committed artifacts")
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
            failures.append(f"market readiness evidence room expected {key}=false")
    if production_market_readiness.get("must_continue") is not True:
        failures.append("market readiness evidence room should preserve the continuation requirement")
    if production_market_readiness.get("source_anchor_count", 0) < 24:
        failures.append("market readiness evidence room should carry researched source anchors into the work orders")
    market_work_orders = production_market_readiness.get("work_orders", [])
    market_gate_ids = {row.get("gate_id") for row in market_work_orders}
    if market_gate_ids != expected_external_validation_gates:
        failures.append("market readiness evidence room missing expected work-order gate IDs")
    allowed_market_input_states = {"missing_real_input", "real_input_received_for_scope_review"}
    if any(row.get("input_state") not in allowed_market_input_states for row in market_work_orders):
        failures.append("market readiness evidence room should show missing or scoped-received input states only")
    if any(not str(row.get("drop_path", "")).startswith("external_inputs/") for row in market_work_orders):
        failures.append("market readiness evidence room work orders must show external input drop paths")
    if any(row.get("claims_opened_by_this_work_order") is not False for row in market_work_orders):
        failures.append("market readiness evidence room work orders must not open claims")
    if "market_ready" not in production_market_readiness.get("blocked_claims", []):
        failures.append("market readiness evidence room must keep market_ready claim blocked")
    if reviewer_wave_plan.get("status") != "reviewer_wave_execution_plan_ready":
        failures.append("reviewer wave execution plan should be ready")
    if reviewer_wave_plan.get("wave_count") != 3:
        failures.append("reviewer wave execution plan should include three waves")
    if private_beta_smoke.get("status") != "private_beta_smoke_test_plan_ready_blocked_until_wave_1_and_staging":
        failures.append("private beta smoke test plan should stay blocked until Wave 1 and staging")
    if private_beta_session_schema.get("status") != "private_beta_session_evidence_schema_ready_claims_closed":
        failures.append("private beta session evidence schema should be generated")
    if private_beta_session_schema.get("required_session_count") != 5:
        failures.append("private beta session schema should require five real target-user sessions")
    if private_beta_session_schema.get("task_count") != 9:
        failures.append("private beta session schema should cover the nine smoke-test tasks")
    for evidence_category in (
        "participant_profile",
        "consent_or_permission",
        "task_results",
        "claim_comprehension",
        "privacy_or_deletion_result",
        "issues_and_changes",
        "artifact_or_recording_references",
    ):
        if evidence_category not in private_beta_session_schema.get("required_evidence_categories", []):
            failures.append(f"private beta session schema missing evidence category {evidence_category}")
    if private_beta_outcome.get("status") != "private_beta_outcome_contract_ready_real_users_required_claims_closed":
        failures.append("private beta outcome contract should be generated")
    if private_beta_outcome.get("required_session_count") != 5:
        failures.append("private beta outcome contract should require five sessions")
    if private_beta_outcome.get("current_real_session_count") != 0:
        failures.append("committed private beta outcome contract should show zero real sessions until evidence is returned")
    if private_beta_outcome.get("current_accepted_session_count") != 0:
        failures.append("private beta outcome contract should not accept sessions without real beta records")
    if private_beta_outcome.get("accepted_required_session_count") != 0:
        failures.append("private beta outcome contract should not count required sessions without real beta records")
    if private_beta_outcome.get("required_segments_met") is not False:
        failures.append("private beta outcome contract should keep segment requirements unmet")
    for key in ("real_user_evidence_ready", "hosted_private_beta_ready", "public_launch_ready", "claims_opened", "external_effects_created"):
        if private_beta_outcome.get(key) is not False:
            failures.append(f"private beta outcome contract expected {key}=false")
    if private_beta_outcome.get("simulated_or_internal_session_count") != 0:
        failures.append("private beta outcome contract should not count internal/simulated sessions in committed artifacts")
    if private_beta_outcome.get("unsafe_approval_misunderstanding_count") != 0:
        failures.append("private beta outcome contract should show no recorded unsafe misunderstandings before sessions exist")
    beta_segment_ids = {row.get("segment") for row in private_beta_outcome.get("segment_rows", [])}
    for segment in ("beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"):
        if segment not in beta_segment_ids:
            failures.append(f"private beta outcome contract missing required segment {segment}")
    if private_beta_outcome_gate_matrix.get("status") != "private_beta_outcome_gate_matrix_ready_claims_closed":
        failures.append("private beta outcome gate matrix should be generated")
    if private_beta_outcome_gate_matrix.get("gate_count", 0) < 7:
        failures.append("private beta outcome gate matrix should include pre-beta and post-session gates")
    if private_beta_outcome_gate_matrix.get("blocked_gate_count", 0) < 7:
        failures.append("private beta outcome gate matrix should keep all beta gates blocked before evidence")
    if private_beta_outcome_gate_matrix.get("claims_opened") is not False:
        failures.append("private beta outcome gate matrix must not open claims")
    beta_contract_md = (ROOT / "docs" / "PRIVATE_BETA_OUTCOME_CONTRACT.md").read_text(encoding="utf-8")
    if "Internal demos" not in beta_contract_md or "Real user evidence ready: false" not in beta_contract_md:
        failures.append("private beta outcome contract doc should distinguish internal QA from real beta evidence")
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
            failures.append(f"product operations missing execution coverage for {key}")
    if not isinstance(research_runs, list) or not research_runs:
        failures.append("research execution runs should include at least one completed local run")
    elif research_runs[-1].get("status") != "research_execution_completed_local":
        failures.append("latest research execution run should be completed locally")
    if not isinstance(expert_work_orders, list) or not expert_work_orders:
        failures.append("expert review work orders should be generated")
    if not isinstance(team_activity, list) or not team_activity:
        failures.append("team workspace activity should be recorded")
    if not isinstance(launch_events, list) or not launch_events:
        failures.append("launch operation events should be recorded")
    elif any(row.get("public_launch_allowed") is not False for row in launch_events):
        failures.append("launch operation events must keep public launch disabled")
    if external_review.get("status") != "external_review_ready_findings_pending":
        failures.append(f"external review report has unexpected status {external_review.get('status')!r}")
    if external_review.get("actual_external_review_completed") is not False:
        failures.append("external review report must not mark actual external review complete without evidence")
    if external_review.get("required_review_count") != 9:
        failures.append("external review report must require nine reviewer roles")
    if external_review.get("completed_review_count") != 0:
        failures.append("external review report must keep completed_review_count=0 until real findings are recorded")
    if external_review.get("pending_review_count") != 9:
        failures.append("external review report must keep all nine reviewer roles pending")
    if external_review.get("private_beta_blocked_until_wave_1_complete") is not True:
        failures.append("external review report must block private beta until Wave 1 completes")
    if external_review.get("public_launch_ready") is not False:
        failures.append("external review report must not mark public launch ready")
    if external_review.get("hosted_private_beta_ready") is not False:
        failures.append("external review report must not mark hosted private beta ready")
    if external_review.get("unsafe_gates_closed") is not True:
        failures.append("external review report must keep unsafe gates closed")
    if external_review.get("solo_ai_assisted_review_supported") is not True:
        failures.append("external review report must expose the solo AI-assisted review path")
    if set(external_review.get("finding_schema", [])) != REQUIRED_EXTERNAL_REVIEW_FIELDS:
        failures.append("external review report must include the complete structured finding schema")
    if set(external_review.get("package_variants_required", [])) != {
        "executive_expert_audit_package",
        "technical_source_review_package",
    }:
        failures.append("external review report must require executive and technical source package variants")
    reviewer_roles = external_review.get("reviewer_roles", [])
    if {row.get("reviewer_role") for row in reviewer_roles} != EXPECTED_REVIEW_ROLES:
        failures.append("external review report must include all expected reviewer roles")
    if external_review_summary.get("actual_external_review_completed") is not False:
        failures.append("external review summary must keep actual_external_review_completed=false")
    if external_review_summary.get("completed_review_count") != 0:
        failures.append("external review summary must keep completed_review_count=0")
    if len(external_review_blockers) != 9:
        failures.append("external review blocker ledger must include nine pending reviewer blockers")
    if any(row.get("gate") != "closed" for row in external_review_blockers):
        failures.append("external review blocker ledger must keep every reviewer gate closed")
    if any(row.get("unsafe_to_bypass") is not True for row in external_review_blockers):
        failures.append("external review blocker ledger must mark every row unsafe to bypass")
    if any(row.get("blocks_public_launch") is not True for row in external_review_blockers):
        failures.append("external review blocker ledger must block public launch for every pending reviewer role")
    if sum(1 for row in external_review_blockers if row.get("blocks_private_beta") is True) != 5:
        failures.append("external review blocker ledger must block private beta for all five Wave 1 reviewers")
    if external_review_intake_contract.get("status") != "external_review_returned_finding_contract_ready_claims_closed":
        failures.append("external review returned-finding contract should be generated")
    if external_review_intake_contract.get("review_role_count") != 9:
        failures.append("external review returned-finding contract should cover nine roles")
    for evidence_category in (
        "reviewer_identity",
        "credential_or_qualification",
        "scope_reviewed",
        "package_or_commit_reference",
        "signed_decision",
        "findings_or_no_findings_rationale",
    ):
        if evidence_category not in external_review_intake_contract.get("required_evidence_categories", []):
            failures.append(f"external review returned-finding contract missing {evidence_category}")
    if external_review_intake.get("status") != "external_review_returned_findings_intake_ready_real_reviews_required_claims_closed":
        failures.append("external review returned findings intake should be generated")
    if external_review_intake.get("review_role_count") != 9:
        failures.append("external review returned findings intake should cover nine roles")
    if external_review_intake.get("returned_record_count") != 0:
        failures.append("committed returned-review intake should show zero returned records until real files arrive")
    if external_review_intake.get("accepted_review_evidence_count") != 0:
        failures.append("returned-review intake should not accept evidence without real returned reviews")
    if external_review_intake.get("pending_review_count") != 9:
        failures.append("returned-review intake should keep all nine reviews pending")
    if external_review_intake.get("blocker_export_count") != 9:
        failures.append("returned-review intake should export one pending blocker per reviewer role")
    for key in (
        "wave_1_scope_ready_by_evidence",
        "wave_2_scope_ready_by_evidence",
        "wave_3_scope_ready_by_evidence",
        "hosted_private_beta_ready_by_review_evidence",
        "public_launch_ready_by_review_evidence",
        "live_payment_ready_by_review_evidence",
        "claims_opened_by_intake",
        "external_effects_created",
    ):
        if external_review_intake.get(key) is not False:
            failures.append(f"returned-review intake expected {key}=false")
    if external_review_intake_matrix.get("status") != "external_review_returned_review_matrix_ready_claims_closed":
        failures.append("external review returned review matrix should be generated")
    if external_review_intake_matrix.get("review_role_count") != 9:
        failures.append("external review returned review matrix should cover nine roles")
    if external_review_intake_matrix.get("accepted_review_evidence_count") != 0:
        failures.append("external review returned review matrix should not accept reviews without evidence")
    if len(external_review_intake_matrix.get("rows", [])) != 9:
        failures.append("external review returned review matrix should include one row per reviewer role")
    if any(row.get("status") != "not_received" for row in external_review_intake_matrix.get("rows", [])):
        failures.append("external review returned review matrix should show all roles not_received before real files")
    if len(external_review_intake_blockers) != 9:
        failures.append("external review returned blocker export should include nine pending blocker rows")
    if any(row.get("gate") != "closed" for row in external_review_intake_blockers):
        failures.append("external review returned blocker export must keep every row closed")
    if any(row.get("module") != "external_review_intake" for row in external_review_intake_blockers):
        failures.append("external review returned blocker export rows should be attributed to external_review_intake")
    returned_review_md = (ROOT / "docs" / "EXTERNAL_REVIEW_RETURNED_FINDINGS.md").read_text(encoding="utf-8")
    if "Where Returned Reviews Go" not in returned_review_md or "Claims opened by intake: false" not in returned_review_md:
        failures.append("external review returned findings doc should show drop path and closed claims")
    if ai_assisted_review.get("status") != "ai_assisted_external_review_ready":
        failures.append("AI-assisted external review plan must be ready")
    if ai_assisted_review.get("solo_developer_mode") is not True:
        failures.append("AI-assisted external review plan must support solo developer mode")
    if ai_assisted_review.get("human_equivalent_approval") is not False:
        failures.append("AI-assisted review must not be treated as human-equivalent approval")
    if ai_assisted_review.get("can_open_private_beta_gate") is not False:
        failures.append("AI-assisted review must not open the private-beta gate by itself")
    if ai_assisted_review.get("can_open_public_launch_gate") is not False:
        failures.append("AI-assisted review must not open the public-launch gate by itself")
    if ai_assisted_review.get("can_reduce_findings_before_real_review") is not True:
        failures.append("AI-assisted review should be allowed to reduce findings before real review")
    if ai_assisted_review.get("required_role_count") != 9:
        failures.append("AI-assisted review plan must include all nine reviewer roles")
    if len(ai_assisted_review.get("research_anchors", {})) < 4:
        failures.append("AI-assisted review plan must include web-research anchors for source-sensitive roles")
    if ai_assisted_review.get("wave_1_simulated_review_status") != "ai_assisted_wave_1_reviewed_with_blockers":
        failures.append("AI-assisted review plan must record completed Wave 1 simulated review blockers")
    if ai_assisted_review.get("simulated_review_count") != 5:
        failures.append("AI-assisted review plan must include five Wave 1 simulated review outputs")
    if ai_assisted_review.get("simulated_finding_count") != 5:
        failures.append("AI-assisted review plan must include five Wave 1 simulated findings")
    if ai_assisted_findings.get("status") != "ai_assisted_wave_1_reviewed_with_blockers":
        failures.append("AI-assisted findings report must record Wave 1 simulated blockers")
    if ai_assisted_findings.get("review_origin") != "ai_assisted_simulated_review":
        failures.append("AI-assisted findings report must be labeled as simulated review")
    if ai_assisted_findings.get("real_external_review_count") != 0:
        failures.append("AI-assisted findings must not change real external review count")
    if ai_assisted_findings.get("human_equivalent_approval") is not False:
        failures.append("AI-assisted findings must not be human-equivalent approval")
    if ai_assisted_findings.get("can_open_private_beta_gate") is not False:
        failures.append("AI-assisted findings must not open private beta gate")
    if ai_assisted_findings.get("can_open_public_launch_gate") is not False:
        failures.append("AI-assisted findings must not open public launch gate")
    if ai_assisted_findings.get("simulated_review_count") != 5:
        failures.append("AI-assisted findings report must include five Wave 1 simulated reviews")
    if ai_assisted_findings.get("simulated_finding_count") != 5:
        failures.append("AI-assisted findings report must include five Wave 1 simulated findings")
    if ai_assisted_findings.get("private_beta_blocking_findings") != 5:
        failures.append("Every Wave 1 simulated finding should block private beta until resolved or reviewed")
    simulated_reviews = ai_assisted_findings.get("simulated_reviews", [])
    if {row.get("reviewer_role") for row in simulated_reviews} != EXPECTED_WAVE_1_REVIEW_ROLES:
        failures.append("AI-assisted findings report must include all five Wave 1 reviewer roles")
    for review in simulated_reviews:
        if review.get("review_origin") != "ai_assisted_simulated_review":
            failures.append(f"simulated review {review.get('reviewer_role')} missing simulated label")
        if review.get("human_followup_required") is not True:
            failures.append(f"simulated review {review.get('reviewer_role')} must require human follow-up")
        if review.get("verdict") != "blocked":
            failures.append(f"simulated review {review.get('reviewer_role')} must remain blocked")
        for finding in review.get("findings", []):
            missing = sorted(REQUIRED_AI_ASSISTED_FINDING_FIELDS - set(finding))
            if missing:
                failures.append(
                    f"simulated finding {finding.get('finding_id')} missing {', '.join(missing)}"
                )
            if finding.get("review_origin") != "ai_assisted_simulated_review":
                failures.append(f"simulated finding {finding.get('finding_id')} missing simulated label")
            if finding.get("human_followup_required") is not True:
                failures.append(f"simulated finding {finding.get('finding_id')} must require human follow-up")
            if finding.get("blocks_private_beta") is not True:
                failures.append(f"simulated finding {finding.get('finding_id')} must block private beta")
            if finding.get("blocks_public_launch") is not True:
                failures.append(f"simulated finding {finding.get('finding_id')} must block public launch")
    store_path = ROOT / "system_review_graph" / "customer_workflow.sqlite"
    if store_path.exists():
        with sqlite3.connect(store_path) as conn:
            tables = {
                row[0]
                for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
            }
        for table in (
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
        ):
            if table not in tables:
                failures.append(f"customer workflow store missing table {table}")
    policy_store_path = ROOT / "system_review_graph" / "policy_intelligence.sqlite"
    if policy_store_path.exists():
        with sqlite3.connect(policy_store_path) as conn:
            policy_tables = {
                row[0]
                for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
            }
        for table in (
            "monitored_sources",
            "source_snapshots",
            "source_change_classifications",
            "packet_source_impacts",
            "stale_source_blockers",
        ):
            if table not in policy_tables:
                failures.append(f"policy intelligence store missing table {table}")
    production_store_path = ROOT / "system_review_graph" / "production_domain.sqlite"
    if production_store_path.exists():
        with sqlite3.connect(production_store_path) as conn:
            production_tables = {
                row[0]
                for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
            }
            production_counts = {
                table: conn.execute(f"select count(*) from {table}").fetchone()[0]
                for table in production_persistence.get("table_order", [])
                if table in production_tables
            }
            opened_claim_boundaries = conn.execute(
                "select count(*) from trade_readiness_packets where claim_boundary_status != 'external_claims_closed'"
            ).fetchone()[0]
        for table in production_persistence.get("table_order", []):
            if table not in production_tables:
                failures.append(f"production domain store missing table {table}")
            elif production_counts.get(table) != production_persistence.get("row_counts", {}).get(table):
                failures.append(
                    f"production domain store table {table} count mismatch "
                    f"{production_counts.get(table)} != {production_persistence.get('row_counts', {}).get(table)}"
                )
        if opened_claim_boundaries:
            failures.append("production domain store must keep packet claim boundaries closed")
    else:
        failures.append("production domain store missing system_review_graph/production_domain.sqlite")
    if production_repository.get("status") != "production_repository_service_ready_database_backed_packet_context_claim_gates_closed":
        failures.append("production repository service should be ready from database-backed packet context")
    if production_repository.get("packet_context_status") != "packet_context_ready_from_production_repository":
        failures.append("production repository packet context should read from production domain store")
    if production_repository.get("report_context_status") != "database_backed_report_context_ready":
        failures.append("production repository report context should be database backed")
    if production_repository.get("safe_claim_count", 0) < 7:
        failures.append("production repository should expose safe preparation claims from claim gates")
    if production_repository.get("blocked_claim_decision_count", 0) < 10:
        failures.append("production repository should expose blocked claim decisions")
    if production_repository.get("report_export_count", 0) < 12:
        failures.append("production repository should expose report exports")
    if production_repository.get("tenant_access_control", {}).get("wrong_org_status") != "access_denied":
        failures.append("production repository should deny wrong-organization packet access")
    sample_claims = {row.get("claim_type"): row for row in production_repository.get("sample_claim_decisions", [])}
    if sample_claims.get("product_context_recorded", {}).get("can_show_claim") is not True:
        failures.append("repository should allow product_context_recorded preparation claim")
    for claim_type in ("tariff_confirmed", "unknown_future_claim"):
        if sample_claims.get(claim_type, {}).get("can_show_claim") is not False:
            failures.append(f"repository should fail closed for {claim_type}")
    for key in ("external_claims_opened", "hosted_postgres_ready", "public_launch_ready"):
        if production_repository.get(key) is not False:
            failures.append(f"production repository expected {key}=false")
    failures.extend(_validate_blockers(ROOT / "system_review_graph" / "blockers.jsonl"))
    failures.extend(_validate_blockers(ROOT / "system_review_graph" / "external_review_blocker_ledger.jsonl"))
    failures.extend(_validate_blocker_rows(external_review_blockers, "external_review_blocker_ledger"))
    failures.extend(_validate_blocker_rows(external.get("blockers", []), "external_gate_report.blockers"))

    if failures:
        print("Product check: FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("Product check: PASS")
    print(f"status={report['status']}")
    print(f"blocker_count={report['blocker_count']}")
    print(f"external_blocker_count={external['blocker_count']}")
    print(f"continuation_lanes={continuation['lane_count']}")
    print(f"startup_status={continuation['status']}")
    print(f"vc_pitch_status={vc_pitch['status']}")
    print(f"board_go_live_status={board['status']}")
    print(f"operator_workflow_status={workflow['status']}")
    print(f"operator_work_queue_count={workflow['work_queue_count']}")
    print(f"customer_workflow_status={customer['status']}")
    print(f"customer_packet_count={customer['packet_count']}")
    print(f"customer_blocker_count={customer['blocker_count']}")
    print(f"customer_blocker_groups={len(customer['blocker_groups'])}")
    print(f"evidence_ledger_status={evidence_ledger['status']}")
    print(f"runtime_status={runtime['status']}")
    print(f"public_surface_status={runtime['public_product_surface']['status']}")
    print(f"runtime_users={len(runtime['users'])}")
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
    print(f"stage_count={all_stages['stage_count']}")
    print(f"go_live_state_count={all_stages['go_live_state_count']}")
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
    print(f"production_repository_status={production_repository['status']}")
    print(f"production_repository_safe_claims={production_repository['safe_claim_count']}")
    print(f"production_repository_blocked_claims={production_repository['blocked_claim_decision_count']}")
    print(f"production_repository_wrong_org_status={production_repository['tenant_access_control']['wrong_org_status']}")
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
    print(f"production_api_service_status={production_api_service['status']}")
    print(f"production_api_service_safe_reads={production_api_service['safe_read_success_count']}")
    print(f"production_api_service_effect_gates_closed={production_api_service['effect_gate_closed_count']}")
    print(f"production_api_service_tenant_denials={production_api_service['tenant_denial_count']}")
    print(f"production_payments_status={production_payments['status']}")
    print(f"production_payment_tiers={production_payments['pricing_tier_count']}")
    print(f"production_live_checkout_enabled={production_payments['live_checkout_enabled']}")
    print(f"payment_activation_status={payment_activation_proof['status']}")
    print(f"payment_activation_records={payment_activation_proof['payment_record_count']}")
    print(f"payment_activation_blocked_gates={payment_activation_proof['blocked_gate_count']}")
    print(f"payment_activation_live_ready={payment_activation_proof['live_payment_ready_by_payment_evidence']}")
    print(f"legal_privacy_security_approval_status={legal_privacy_security_approval['status']}")
    print(f"legal_privacy_security_approval_records={legal_privacy_security_approval['approval_record_count']}")
    print(f"legal_privacy_security_approval_blocked_gates={legal_privacy_security_approval['blocked_gate_count']}")
    print(
        "legal_privacy_security_approved_by_evidence="
        f"{legal_privacy_security_approval['legal_privacy_security_approved_by_evidence']}"
    )
    print(f"qualified_customs_trade_review_status={qualified_customs_trade_review['status']}")
    print(f"qualified_customs_trade_review_records={qualified_customs_trade_review['review_record_count']}")
    print(f"qualified_customs_trade_review_blocked_gates={qualified_customs_trade_review['blocked_gate_count']}")
    print(
        "qualified_customs_trade_reviewed_by_evidence="
        f"{qualified_customs_trade_review['customs_trade_reviewed_by_evidence']}"
    )
    print(f"tariff_confirmed_by_review_evidence={qualified_customs_trade_review['tariff_confirmed_by_review_evidence']}")
    print(f"production_trust_status={production_trust['status']}")
    print(f"production_trust_controls={production_trust['trust_control_count']}")
    print(f"production_real_file_uploads_allowed={production_trust['real_file_uploads_allowed']}")
    print(f"production_launch_status={production_launch['status']}")
    print(f"production_launch_gates={production_launch['launch_gate_count']}")
    print(f"production_public_launch_approved={production_launch['public_launch_approved']}")
    print(f"external_validation_pdf={pdf_path.relative_to(ROOT)}")
    print(f"external_validation_reviewer_brief_pdf={brief_pdf_path.relative_to(ROOT)}")
    print(f"go_live_input_status={go_live_input_readiness['status']}")
    print(f"go_live_missing_inputs={go_live_input_readiness['missing_input_count']}")
    print(f"go_live_input_pdf={input_pdf_path.relative_to(ROOT)}")
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
    print("unsafe_gates=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
