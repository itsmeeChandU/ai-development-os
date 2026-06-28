#!/usr/bin/env python3
"""Generate production AI copilot artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_ai_copilot_engine import (
    build_production_ai_copilot_engine,
    write_production_ai_copilot_engine_artifacts,
)


def main() -> int:
    payload = build_production_ai_copilot_engine(ROOT)
    paths = write_production_ai_copilot_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "ai_role_count": payload["ai_role_count"],
                "ai_output_contract_count": payload["ai_output_contract_count"],
                "prompt_injection_test_count": payload["prompt_injection_test_count"],
                "live_model_calls_enabled": payload["live_model_calls_enabled"],
                "claims_opened": payload["claims_opened"],
                "external_effects_created": payload["external_effects_created"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "output_contracts": str(paths["output_contracts"].relative_to(ROOT)),
                "safety": str(paths["safety"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
