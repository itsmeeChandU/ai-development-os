#!/usr/bin/env python3
"""Export a static operator dashboard from generated product reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import (
    build_external_gate_report,
    build_operator_workflow,
    build_screenshot_manifest,
    evaluate_cards,
    load_cards,
    load_json,
    write_dashboard,
    write_json,
    write_operator_workflow,
    write_report,
    write_screenshot_manifest,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    readiness_path = ROOT / "system_review_graph" / "readiness_report.json"
    external_path = ROOT / "system_review_graph" / "external_gate_report.json"
    if not readiness_path.exists():
        readiness = evaluate_cards(
            load_cards(ROOT / "data" / "sample_source_cards.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        write_report(readiness, readiness_path)
    if not external_path.exists():
        external = build_external_gate_report(
            country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
            evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        write_json(external, external_path)
    readiness = _read(readiness_path)
    external = _read(external_path)
    workflow = None
    workflow_inputs = [
        ROOT / "system_review_graph" / "continuation_plan.json",
        ROOT / "system_review_graph" / "board_go_live_readiness_report.json",
        ROOT / "data" / "canada_tool_registry.json",
    ]
    if all(path.exists() for path in workflow_inputs):
        workflow = build_operator_workflow(
            readiness=readiness,
            external=external,
            continuation=load_json(ROOT / "system_review_graph" / "continuation_plan.json"),
            board=load_json(ROOT / "system_review_graph" / "board_go_live_readiness_report.json"),
            canada_tools=load_json(ROOT / "data" / "canada_tool_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        write_operator_workflow(
            workflow,
            ROOT / "system_review_graph" / "operator_workflow_report.json",
        )
    screenshots = build_screenshot_manifest(
        repo_root=ROOT,
        screenshot_dir=ROOT / "system_review_graph" / "operator_screenshots",
        generated_at="2026-06-25T00:00:00+00:00",
    )
    manifest_path = write_screenshot_manifest(
        screenshots,
        ROOT / "system_review_graph" / "operator_screenshot_manifest.json",
    )
    out = write_dashboard(
        readiness,
        external,
        ROOT / "system_review_graph" / "operator_dashboard.html",
        screenshot_manifest=screenshots,
        operator_workflow=workflow,
    )
    print(
        json.dumps(
            {
                "out": str(out),
                "screenshot_manifest": str(manifest_path),
                "screenshot_count": screenshots["screenshot_count"],
                "total_blockers": readiness["blocker_count"] + external["blocker_count"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
