#!/usr/bin/env python3
"""Build the startup continuation plan from generated gate reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import (  # noqa: E402
    build_continuation_plan,
    build_external_gate_report,
    evaluate_cards,
    load_cards,
    load_json,
    write_json,
    write_report,
)


def _ensure_readiness() -> dict:
    path = ROOT / "system_review_graph" / "readiness_report.json"
    if path.exists():
        return load_json(path)
    report = evaluate_cards(load_cards(ROOT / "data" / "sample_source_cards.json"))
    write_report(report, path)
    return report


def _ensure_external() -> dict:
    path = ROOT / "system_review_graph" / "external_gate_report.json"
    if path.exists():
        return load_json(path)
    report = build_external_gate_report(
        country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
        evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
        official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
    )
    write_json(report, path)
    return report


def main() -> int:
    plan = build_continuation_plan(readiness=_ensure_readiness(), external=_ensure_external())
    out = write_json(plan, ROOT / "system_review_graph" / "continuation_plan.json")
    print(
        json.dumps(
            {
                "out": str(out),
                "status": plan["status"],
                "must_continue": plan["must_continue"],
                "lane_count": plan["lane_count"],
                "blocker_count": plan["blocker_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
