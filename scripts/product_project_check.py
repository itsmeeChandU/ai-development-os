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
        PROJECT / "data" / "sample_source_cards.json",
        PROJECT / "data" / "country_requirements_matrix.json",
        PROJECT / "data" / "evidence_packets.json",
        PROJECT / "data" / "official_source_registry.json",
        PROJECT / "data" / "investor_evidence.json",
        PROJECT / "src" / "importer_source_readiness" / "readiness.py",
        PROJECT / "src" / "importer_source_readiness" / "external_gates.py",
        PROJECT / "src" / "importer_source_readiness" / "continuation.py",
        PROJECT / "src" / "importer_source_readiness" / "investor_readiness.py",
        PROJECT / "src" / "importer_source_readiness" / "operator_report.py",
        PROJECT / "tests" / "test_readiness.py",
        PROJECT / "tests" / "test_external_gates.py",
        PROJECT / "tests" / "test_continuation.py",
        PROJECT / "tests" / "test_investor_readiness.py",
        PROJECT / "scripts" / "run_readiness.py",
        PROJECT / "scripts" / "run_external_gates.py",
        PROJECT / "scripts" / "export_operator_dashboard.py",
        PROJECT / "scripts" / "plan_continuation.py",
        PROJECT / "scripts" / "build_vc_pitch_packet.py",
        PROJECT / "scripts" / "check_product.py",
        PROJECT / "docs" / "PRODUCT_AUTOMATION_RUNBOOK.md",
        PROJECT / "docs" / "PRODUCT_STATUS.md",
        PROJECT / "docs" / "OPERATOR_GUIDE.md",
        PROJECT / "system_review_graph" / "external_gate_report.json",
        PROJECT / "system_review_graph" / "continuation_plan.json",
        PROJECT / "system_review_graph" / "vc_pitch_readiness_report.json",
        PROJECT / "system_review_graph" / "operator_dashboard.html",
        PROJECT / "investor" / "vc_pitch_deck.md",
        PROJECT / "investor" / "one_pager.md",
        PROJECT / "investor" / "demo_script.md",
        PROJECT / "investor" / "diligence_room_index.md",
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
        ["python3", "scripts/export_operator_dashboard.py"],
        ["python3", "scripts/plan_continuation.py"],
        ["python3", "scripts/build_vc_pitch_packet.py"],
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

    print("Product project check: PASS")
    print(f"project={PROJECT.relative_to(ROOT)}")
    print(f"status={report['status']}")
    print(f"blocker_count={report['blocker_count']}")
    print(f"external_blocker_count={external['blocker_count']}")
    print(f"continuation_lanes={continuation['lane_count']}")
    print(f"startup_status={continuation['status']}")
    print(f"vc_pitch_status={vc_pitch['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
