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
        [sys.executable, "scripts/build_external_review_packet.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "scripts/run_readiness.py"],
        [sys.executable, "scripts/run_external_gates.py"],
        [sys.executable, "scripts/plan_continuation.py"],
        [sys.executable, "scripts/build_vc_pitch_packet.py"],
        [sys.executable, "scripts/build_board_go_live_packet.py"],
        [sys.executable, "scripts/run_operator_workflow.py"],
        [sys.executable, "scripts/run_customer_workflow.py"],
        [sys.executable, "scripts/run_policy_intelligence.py"],
        [sys.executable, "scripts/run_completion_platform.py"],
        [sys.executable, "scripts/run_product_operations.py"],
        [sys.executable, "scripts/export_operator_dashboard.py"],
        [sys.executable, "scripts/run_final_go_live_review.py"],
        [sys.executable, "scripts/run_external_validation_requirements.py"],
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
    go_live_input_readiness = _load_json(ROOT / "system_review_graph" / "go_live_input_readiness_report.json")
    reviewer_wave_plan = _load_json(ROOT / "system_review_graph" / "reviewer_wave_execution_plan.json")
    private_beta_smoke = _load_json(ROOT / "system_review_graph" / "private_beta_smoke_test_plan.json")
    external_review = _load_json(ROOT / "system_review_graph" / "external_review_findings_report.json")
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
        "src/importer_source_readiness/external_validation_research.py",
        "tests/test_operator_app.py",
        "tests/test_source_packet_workflow.py",
        "tests/test_customer_store.py",
        "tests/test_product_runtime.py",
        "tests/test_completion_platform.py",
        "tests/test_external_package_audit.py",
        "tests/test_external_review_workflow.py",
        "tests/test_external_validation_research.py",
        "scripts/run_customer_workflow.py",
        "scripts/run_policy_intelligence.py",
        "scripts/run_completion_platform.py",
        "scripts/run_product_operations.py",
        "scripts/audit_external_package.py",
        "scripts/build_external_review_packet.py",
        "scripts/run_final_go_live_review.py",
        "scripts/run_external_validation_requirements.py",
        "scripts/package_external_review.py",
        "data/customer_source_packets.json",
        "data/evidence_ledger.json",
        "START_HERE.md",
        "WHAT_WE_ARE_BUILDING.md",
        "CURRENT_SLICE_VS_TARGET_PRODUCT.md",
        "FINAL_GO_LIVE_HANDOFF.md",
        "CUSTOMER_SOURCE_PACKET_SPEC.md",
        "SOURCE_OF_TRUTH.md",
        "RUN_RESULTS.md",
        "EXTERNAL_REVIEW_SUMMARY.md",
        "REDACTION_REPORT.md",
        "REVIEW_USE_TERMS.md",
        "OFFLINE_REPRODUCTION.md",
        "PACKAGE_AUDIT.md",
        "docs/EXTERNAL_REVIEW_PROCESS.md",
        "docs/EXTERNAL_VALIDATION_REQUIREMENTS.md",
        "docs/EXTERNAL_VALIDATION_REVIEWER_BRIEF.md",
        "docs/GO_LIVE_INPUT_REQUESTS.md",
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
        "system_review_graph/reviewer_wave_execution_plan.json",
        "system_review_graph/private_beta_smoke_test_plan.json",
        "system_review_graph/external_review_findings_report.json",
        "system_review_graph/external_review_blocker_ledger.jsonl",
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
    if business_logic.get("status") != "business_logic_phases_ready_with_evidence_gates":
        failures.append("business logic phase report should be ready with evidence gates")
    if business_logic.get("phase_count") != 5:
        failures.append("business logic phase report should include five phases")
    if not business_logic.get("packet_rows"):
        failures.append("business logic phase report should include packet rows")
    else:
        first_business_row = business_logic["packet_rows"][0]
        if first_business_row.get("decision_tree", {}).get("question_count") != 12:
            failures.append("business logic decision tree should include 12 questions")
        if first_business_row.get("business_scores", {}).get("score_count") != 5:
            failures.append("business logic should include five separate scores")
        if first_business_row.get("canonical_packet_contract", {}).get("status") != "canonical_trade_packet_contract_ready":
            failures.append("business logic should include the canonical packet contract")
    if business_logic.get("operation_status") != "business_logic_operational_local_with_evidence_gates":
        failures.append("business logic should include local operation proof")
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
    input_md = (ROOT / "docs" / "GO_LIVE_INPUT_REQUESTS.md").read_text(encoding="utf-8")
    if "Once Inputs Are Received" not in input_md or "external_inputs/" not in input_md:
        failures.append("go-live input request doc should explain how returned inputs are used")
    if reviewer_wave_plan.get("status") != "reviewer_wave_execution_plan_ready":
        failures.append("reviewer wave execution plan should be ready")
    if reviewer_wave_plan.get("wave_count") != 3:
        failures.append("reviewer wave execution plan should include three waves")
    if private_beta_smoke.get("status") != "private_beta_smoke_test_plan_ready_blocked_until_wave_1_and_staging":
        failures.append("private beta smoke test plan should stay blocked until Wave 1 and staging")
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
