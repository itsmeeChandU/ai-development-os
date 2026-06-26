#!/usr/bin/env python3
"""Build the generated operator workbench queue."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import build_operator_workflow, load_json, write_operator_workflow


def main() -> int:
    report = build_operator_workflow(
        readiness=load_json(ROOT / "system_review_graph" / "readiness_report.json"),
        external=load_json(ROOT / "system_review_graph" / "external_gate_report.json"),
        continuation=load_json(ROOT / "system_review_graph" / "continuation_plan.json"),
        board=load_json(ROOT / "system_review_graph" / "board_go_live_readiness_report.json"),
        canada_tools=load_json(ROOT / "data" / "canada_tool_registry.json"),
        generated_at="2026-06-25T00:00:00+00:00",
    )
    out = write_operator_workflow(
        report,
        ROOT / "system_review_graph" / "operator_workflow_report.json",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "work_queue_count": report["work_queue_count"],
                "operator_can_use_now": report["operator_can_use_now"],
                "out": str(out),
            }
        )
    )
    return 0 if report["operator_can_use_now"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
