#!/usr/bin/env python3
"""Generate production trade discovery artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_trade_discovery_engine import (
    build_production_trade_discovery_engine,
    write_production_trade_discovery_engine_artifacts,
)


def main() -> int:
    payload = build_production_trade_discovery_engine(ROOT)
    paths = write_production_trade_discovery_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "category_count": payload["category_count"],
                "country_lane_count": payload["country_lane_count"],
                "beginner_flow_count": payload["beginner_flow_count"],
                "dataset_route_count": payload["dataset_route_count"],
                "claims_opened": payload["claims_opened"],
                "external_effects_created": payload["external_effects_created"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "categories": str(paths["categories"].relative_to(ROOT)),
                "country_lanes": str(paths["country_lanes"].relative_to(ROOT)),
                "beginner_flows": str(paths["beginner_flows"].relative_to(ROOT)),
                "sources": str(paths["sources"].relative_to(ROOT)),
                "audit": str(paths["audit"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
