#!/usr/bin/env python3
"""Build the external evidence gate report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import build_external_gate_report, load_json, write_json


def main() -> int:
    report = build_external_gate_report(
        country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
        evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
        official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
        generated_at="2026-06-25T00:00:00+00:00",
    )
    out = write_json(report, ROOT / "system_review_graph" / "external_gate_report.json")
    print(json.dumps({"status": report["status"], "blocker_count": report["blocker_count"], "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
