#!/usr/bin/env python3
"""Generate production market intelligence artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_market_intelligence_engine import (
    build_production_market_intelligence_engine,
    write_production_market_intelligence_engine_artifacts,
)


def main() -> int:
    payload = build_production_market_intelligence_engine(ROOT)
    paths = write_production_market_intelligence_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "metric_count": payload["metric_count"],
                "market_signal_count": payload["market_signal_count"],
                "dataset_connector_count": payload["dataset_connector_count"],
                "claims_opened": payload["claims_opened"],
                "external_effects_created": payload["external_effects_created"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "signals": str(paths["signals"].relative_to(ROOT)),
                "connectors": str(paths["connectors"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
