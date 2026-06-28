#!/usr/bin/env python3
"""Generate production market-readiness evidence room artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_market_readiness_evidence_room import (
    build_production_market_readiness_evidence_room,
    write_production_market_readiness_evidence_room_artifacts,
)


def main() -> int:
    payload = build_production_market_readiness_evidence_room(ROOT)
    paths = write_production_market_readiness_evidence_room_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "gate_count": payload["gate_count"],
                "required_input_count": payload["required_input_count"],
                "ready_input_count": payload["ready_input_count"],
                "missing_input_count": payload["missing_input_count"],
                "public_launch_ready": payload["public_launch_ready"],
                "claims_opened_by_room": payload["claims_opened_by_room"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "work_orders": str(paths["work_orders"].relative_to(ROOT)),
                "reviewer_cards": str(paths["reviewer_cards"].relative_to(ROOT)),
                "matrix": str(paths["matrix"].relative_to(ROOT)),
                "input_ledger": str(paths["input_ledger"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
