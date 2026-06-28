#!/usr/bin/env python3
"""Generate production payment monetization artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_payment_monetization_engine import (
    build_production_payment_monetization_engine,
    write_production_payment_monetization_engine_artifacts,
)


def main() -> int:
    manifest = build_production_payment_monetization_engine(ROOT)
    write_production_payment_monetization_engine_artifacts(manifest, ROOT)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "pricing_tier_count": manifest["pricing_tier_count"],
                "payment_gate_count": manifest["payment_gate_count"],
                "blocked_payment_gate_count": manifest["blocked_payment_gate_count"],
                "live_checkout_enabled": manifest["live_checkout_enabled"],
                "external_charge_created": manifest["external_charge_created"],
                "claims_opened": manifest["claims_opened"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
