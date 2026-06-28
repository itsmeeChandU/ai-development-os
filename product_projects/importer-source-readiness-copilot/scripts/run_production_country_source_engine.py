#!/usr/bin/env python3
"""Generate production country/source intelligence artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_country_source_engine import (
    build_production_country_source_engine,
    write_production_country_source_engine_artifacts,
)


def main() -> int:
    payload = build_production_country_source_engine(ROOT)
    paths = write_production_country_source_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "country_pack_count": payload["country_pack_count"],
                "source_lifecycle_count": payload["source_lifecycle_count"],
                "researched_source_fact_count": payload["researched_source_fact_count"],
                "packet_impact_count": payload["packet_impact_count"],
                "source_refresh_record_count": payload["source_refresh_record_count"],
                "external_effects_created": payload["external_effects_created"],
                "claims_opened": payload["claims_opened"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "country_packs": str(paths["country_packs"].relative_to(ROOT)),
                "source_lifecycle": str(paths["source_lifecycle"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
