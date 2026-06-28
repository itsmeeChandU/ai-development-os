#!/usr/bin/env python3
"""Generate production trade data catalog artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_trade_data_catalog_engine import (
    build_production_trade_data_catalog_engine,
    write_production_trade_data_catalog_engine_artifacts,
)


def main() -> int:
    payload = build_production_trade_data_catalog_engine(ROOT)
    paths = write_production_trade_data_catalog_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "template_count": payload["template_count"],
                "browse_card_count": payload["browse_card_count"],
                "query_work_order_count": payload["query_work_order_count"],
                "values_loaded": payload["values_loaded"],
                "claims_opened": payload["claims_opened"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "templates": str(paths["templates"].relative_to(ROOT)),
                "work_orders": str(paths["work_orders"].relative_to(ROOT)),
                "browse_cards": str(paths["browse_cards"].relative_to(ROOT)),
                "ingestion_policy": str(paths["ingestion_policy"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
