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


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "scripts/run_readiness.py"],
        [sys.executable, "scripts/run_external_gates.py"],
        [sys.executable, "scripts/plan_continuation.py"],
        [sys.executable, "scripts/build_vc_pitch_packet.py"],
        [sys.executable, "scripts/build_board_go_live_packet.py"],
        [sys.executable, "scripts/run_operator_workflow.py"],
        [sys.executable, "scripts/run_customer_workflow.py"],
        [sys.executable, "scripts/export_operator_dashboard.py"],
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
        "src/importer_source_readiness/ai_review_validation.py",
        "tests/test_operator_app.py",
        "tests/test_source_packet_workflow.py",
        "tests/test_customer_store.py",
        "tests/test_product_runtime.py",
        "tests/test_external_package_audit.py",
        "scripts/run_customer_workflow.py",
        "scripts/audit_external_package.py",
        "data/customer_source_packets.json",
        "data/evidence_ledger.json",
        "CUSTOMER_SOURCE_PACKET_SPEC.md",
        "SOURCE_OF_TRUTH.md",
        "RUN_RESULTS.md",
        "REDACTION_REPORT.md",
        "REVIEW_USE_TERMS.md",
        "OFFLINE_REPRODUCTION.md",
        "PACKAGE_AUDIT.md",
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
        "system_review_graph/source_refresh_runs.json",
        "system_review_graph/source_refresh_report_packet-frozen-tuna-canada-001.json",
        "system_review_graph/expert_review_packet_packet-frozen-tuna-canada-001.md",
        "migrations/0001_product_runtime.sql",
        "Dockerfile",
        "compose.yaml",
        ".env.example",
        "docs/SECURITY_PRIVACY.md",
        "docs/DEPLOYMENT.md",
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
    if len(customer.get("blocker_groups", [])) < 4:
        failures.append("customer workflow should consolidate blockers into grouped categories")
    if not customer.get("ai_review_runs"):
        failures.append("customer workflow should include AI simulated review runs")
    packet = customer.get("packets", [{}])[0]
    if packet.get("customer_visible_status_label") != "Blocked - source freshness missing":
        failures.append("customer packet should use customer-readable stale-source status")
    evidence_summary = packet.get("evidence_summary", {})
    if evidence_summary.get("attached", 0) < 3 or evidence_summary.get("missing", 0) < 4:
        failures.append("customer packet should expose evidence quality summary")
    if evidence_summary.get("ai_allowed", 0) < 1:
        failures.append("customer packet should expose AI permission summary")
    group_titles = {row.get("title") for row in packet.get("blocker_groups", [])}
    for group in ("Source Freshness", "Compliance Review", "Source Rights / Contract", "Buyer Validation"):
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
    if len(requirements_traceability.get("requirements", [])) < 17:
        failures.append("requirements traceability matrix should cover the full requirements analysis")
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
    failures.extend(_validate_blockers(ROOT / "system_review_graph" / "blockers.jsonl"))
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
    print(f"runtime_users={len(runtime['users'])}")
    print(f"review_requests={len(review_requests)}")
    print(f"audit_events={len(audit_events['events'])}")
    print(f"deployment_status={deployment['status']}")
    print("customer_store=ready")
    print("unsafe_gates=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
