#!/usr/bin/env python3
"""Validate the bundled importer source readiness product project."""

from __future__ import annotations

import json
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
        PROJECT / "tests" / "test_readiness.py",
        PROJECT / "tests" / "test_external_gates.py",
        PROJECT / "tests" / "test_continuation.py",
        PROJECT / "tests" / "test_investor_readiness.py",
        PROJECT / "tests" / "test_board_go_live.py",
        PROJECT / "tests" / "test_operator_app.py",
        PROJECT / "tests" / "test_operator_workflow.py",
        PROJECT / "tests" / "test_operator_screenshots.py",
        PROJECT / "tests" / "test_source_packet_workflow.py",
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
        PROJECT / "scripts" / "audit_external_package.py",
        PROJECT / "scripts" / "check_product.py",
        PROJECT / "docs" / "PRODUCT_AUTOMATION_RUNBOOK.md",
        PROJECT / "docs" / "PRODUCT_STATUS.md",
        PROJECT / "docs" / "STARTUP_LIFECYCLE.md",
        PROJECT / "docs" / "OPERATOR_GUIDE.md",
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
        PROJECT / "investor" / "vc_pitch_deck.md",
        PROJECT / "investor" / "one_pager.md",
        PROJECT / "investor" / "demo_script.md",
        PROJECT / "investor" / "diligence_room_index.md",
        PROJECT / "board" / "board_go_live_brief.md",
        PROJECT / "board" / "expert_review_packet.md",
        PROJECT / "board" / "launch_control_checklist.md",
        PROJECT / "board" / "financial_operating_model.md",
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
    if customer.get("status") != "customer_workflow_ready_internal":
        print("Product project check: FAIL")
        print("customer source-packet workflow is not internal ready")
        return 1
    if customer.get("display_status") != "Internal operator ready - external claims blocked":
        print("Product project check: FAIL")
        print("customer source-packet workflow missing safe display status")
        return 1
    if customer.get("packet_count", 0) < 1 or customer.get("blocker_count", 0) < 1:
        print("Product project check: FAIL")
        print("customer source-packet workflow missing packets or blockers")
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
    print(f"evidence_ledger_status={evidence_ledger['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
