#!/usr/bin/env python3
"""Generate the production redevelopment contract artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_redevelopment import (
    build_production_redevelopment_plan,
    write_production_redevelopment_artifacts,
)


def main() -> int:
    payload = build_production_redevelopment_plan()
    paths = write_production_redevelopment_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "production_layer_count": payload["production_layer_count"],
                "phase_count": payload["phase_count"],
                "domain_entity_count": payload["domain_entity_count"],
                "research_anchor_count": payload["research_anchor_count"],
                "public_launch_ready": payload["public_launch_ready"],
                "hosted_production_ready": payload["hosted_production_ready"],
                "live_payment_ready": payload["live_payment_ready"],
                "plan": str(paths["plan"].relative_to(ROOT)),
                "research": str(paths["research"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
