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
        PROJECT / "src" / "importer_source_readiness" / "ai_review_validation.py",
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
        PROJECT / "tests" / "test_external_package_audit.py",
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
        PROJECT / "scripts" / "audit_external_package.py",
        PROJECT / "scripts" / "check_product.py",
        PROJECT / "docs" / "PRODUCT_AUTOMATION_RUNBOOK.md",
        PROJECT / "docs" / "PRODUCT_STATUS.md",
        PROJECT / "docs" / "REQUIREMENTS_ANALYSIS.md",
        PROJECT / "docs" / "PUBLIC_TRADE_READINESS.md",
        PROJECT / "docs" / "STARTUP_LIFECYCLE.md",
        PROJECT / "docs" / "OPERATOR_GUIDE.md",
        PROJECT / "docs" / "UI_UX_COMPONENT_SYSTEM.md",
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
        PROJECT / "system_review_graph" / "source_refresh_runs.json",
        PROJECT / "system_review_graph" / "source_refresh_report_packet-frozen-tuna-canada-001.json",
        PROJECT / "system_review_graph" / "expert_review_packet_packet-frozen-tuna-canada-001.md",
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
    if len(customer.get("blocker_groups", [])) < 4 or not customer.get("ai_review_runs"):
        print("Product project check: FAIL")
        print("customer source-packet workflow missing grouped blockers or AI review runs")
        return 1
    packet = customer.get("packets", [{}])[0]
    if packet.get("customer_visible_status_label") != "Blocked - source freshness missing":
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
    required_groups = {"Source Freshness", "Compliance Review", "Source Rights / Contract", "Buyer Validation"}
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
        "/public/packets/:packetId/result",
        "/public/packets/:packetId/confirm",
        "/workspace",
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
    if len(requirements_traceability.get("requirements", [])) < 31:
        print("Product project check: FAIL")
        print("requirements traceability matrix is incomplete")
        return 1
    for requirement_id in ("REQ-PUBLIC-01", "REQ-EXPORT-01", "REQ-EXPORT-09", "REQ-STARTER-01", "REQ-PDF-01", "REQ-CONFIRM-01", "REQ-IH-01"):
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
    if "beginner_no_documents" not in public_trade.get("modes", {}):
        print("Product project check: FAIL")
        print("public trade readiness manifest missing beginner mode")
        return 1
    if public_trade.get("intelligence_hub_policy_monitor", {}).get("status") != "database_style_contract_ready":
        print("Product project check: FAIL")
        print("public trade readiness manifest missing policy monitor contract")
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
    print(f"review_requests={len(review_requests)}")
    print(f"audit_events={len(audit_events['events'])}")
    print(f"deployment_status={deployment['status']}")
    print("customer_store=ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
