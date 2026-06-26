#!/usr/bin/env python3
"""Generate the Intelligence Hub-style policy/source monitoring artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import load_json
from importer_source_readiness.policy_intelligence import build_policy_monitor, write_policy_monitor_artifacts
from importer_source_readiness.source_packet_workflow import build_customer_workflow, load_json_list


def main() -> int:
    workflow = build_customer_workflow(
        source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
        evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
        official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
        generated_at="2026-06-25T00:00:00+00:00",
    )
    monitor = build_policy_monitor(
        official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
        workflow=workflow,
        generated_at="2026-06-25T00:00:00+00:00",
    )
    result = write_policy_monitor_artifacts(monitor, ROOT)
    print(
        json.dumps(
            {
                "status": result["status"],
                "integration_mode": result["integration_mode"],
                "monitored_source_count": result["monitored_source_count"],
                "packet_impact_count": result["packet_impact_count"],
                "stale_source_blocker_count": result["stale_source_blocker_count"],
                "store_tables": result["store"]["tables"],
                "out": "system_review_graph/intelligence_hub_policy_monitor.json",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
