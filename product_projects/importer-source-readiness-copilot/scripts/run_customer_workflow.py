#!/usr/bin/env python3
"""Generate the customer source-packet workflow artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import load_json
from importer_source_readiness.source_packet_workflow import (
    build_customer_workflow,
    expert_review_packet_markdown,
    load_json_list,
    markdown_report,
    write_json,
)
from importer_source_readiness.customer_store import inspect_customer_store, write_customer_store


def main() -> int:
    workflow = build_customer_workflow(
        source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
        evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
        official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
        generated_at="2026-06-25T00:00:00+00:00",
    )
    write_json(workflow, ROOT / "system_review_graph" / "customer_readiness_report.json")
    write_json(workflow["packets"], ROOT / "system_review_graph" / "customer_source_packets.json")
    write_json(workflow["evidence_ledger"], ROOT / "system_review_graph" / "evidence_ledger.json")
    write_json(workflow["ai_review_runs"], ROOT / "system_review_graph" / "customer_ai_review_runs.json")
    first_packet = workflow["packets"][0]["packet_id"] if workflow["packets"] else ""
    if first_packet:
        (ROOT / "system_review_graph" / "customer_readiness_report.md").write_text(
            markdown_report(workflow, first_packet),
            encoding="utf-8",
        )
        (ROOT / "system_review_graph" / f"expert_review_packet_{first_packet}.md").write_text(
            expert_review_packet_markdown(workflow, first_packet),
            encoding="utf-8",
        )
    store_path = write_customer_store(
        workflow,
        ROOT / "system_review_graph" / "customer_workflow.sqlite",
    )
    store = inspect_customer_store(store_path)
    print(
        json.dumps(
            {
                "status": workflow["status"],
                "display_status": workflow["display_status"],
                "customer_stage_status": workflow["customer_stage_status"],
                "private_beta_status": workflow["private_beta_status"],
                "packet_count": workflow["packet_count"],
                "evidence_count": workflow["evidence_count"],
                "blocker_count": workflow["blocker_count"],
                "blocker_group_count": len(workflow["blocker_groups"]),
                "ai_review_run_count": len(workflow["ai_review_runs"]),
                "store_tables": len(store["tables"]),
                "out": "system_review_graph/customer_readiness_report.json",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
