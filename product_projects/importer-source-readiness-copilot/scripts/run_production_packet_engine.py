#!/usr/bin/env python3
"""Generate the production packet engine artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_packet_engine import (
    build_production_packet_engine,
    write_production_packet_engine_artifacts,
)


def main() -> int:
    payload = build_production_packet_engine(ROOT)
    paths = write_production_packet_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "packet_count": payload["packet_count"],
                "state_count": payload["state_count"],
                "packet_event_count": payload["packet_event_count"],
                "packet_view_type_count": payload["packet_view_type_count"],
                "packet_view_count": payload["packet_view_count"],
                "claim_gate_count": payload["claim_gate_count"],
                "external_effects_created": payload["external_effects_created"],
                "claims_opened": payload["claims_opened"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "events": str(paths["events"].relative_to(ROOT)),
                "views_root": str(paths["views_root"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
