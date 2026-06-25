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
        [sys.executable, "scripts/export_operator_dashboard.py"],
        [sys.executable, "scripts/plan_continuation.py"],
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
    print("unsafe_gates=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
