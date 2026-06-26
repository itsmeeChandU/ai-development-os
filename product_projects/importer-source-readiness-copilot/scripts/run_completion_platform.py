#!/usr/bin/env python3
"""Generate completion-stage local product contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import load_json
from importer_source_readiness.completion_platform import build_completion_platform, write_completion_platform_artifacts
from importer_source_readiness.source_packet_workflow import build_customer_workflow, load_json_list


def main() -> int:
    official_sources = load_json(ROOT / "data" / "official_source_registry.json")
    workflow = build_customer_workflow(
        source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
        evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
        official_sources=official_sources,
        generated_at="2026-06-25T00:00:00+00:00",
    )
    payload = build_completion_platform(workflow, official_sources)
    write_completion_platform_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "all_stage_status": payload["all_stage_readiness"]["status"],
                "opportunity_status": payload["opportunity_scanner"]["status"],
                "coverage_status": payload["country_coverage"]["status"],
                "billing_status": payload["billing_credit_controls"]["status"],
                "agent_api_status": payload["agent_api_manifest"]["status"],
                "research_status": payload["research_execution_plan"]["status"],
                "expert_network_status": payload["expert_network"]["status"],
                "team_workspace_status": payload["team_workspace"]["status"],
                "launch_operations_status": payload["launch_operations"]["status"],
                "traffic_page_count": len(payload["traffic_pages_manifest"]["pages"]),
                "stage_count": payload["all_stage_readiness"]["stage_count"],
                "out": "system_review_graph/completion_platform_manifest.json",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
