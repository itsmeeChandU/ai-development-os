#!/usr/bin/env python3
"""Run the standalone product proof gate."""

from __future__ import annotations

import json
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
        [sys.executable, "scripts/export_operator_dashboard.py"],
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
    for path in (
        "scripts/serve_operator_app.py",
        "src/importer_source_readiness/operator_app.py",
        "tests/test_operator_app.py",
    ):
        if not (ROOT / path).exists():
            failures.append(f"missing local operator app file: {path}")
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
    print("unsafe_gates=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
