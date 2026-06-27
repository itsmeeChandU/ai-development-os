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
