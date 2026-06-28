#!/usr/bin/env python3
"""Generate production decision scoring artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_decision_scoring_engine import (
    build_production_decision_scoring_engine,
    write_production_decision_scoring_engine_artifacts,
)


def main() -> int:
    payload = build_production_decision_scoring_engine(ROOT)
    paths = write_production_decision_scoring_engine_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "score_count": payload["score_count"],
                "packet_count": payload["packet_count"],
                "decision_score_record_count": payload["decision_score_record_count"],
                "single_global_readiness_score_created": payload["single_global_readiness_score_created"],
                "approval_language_allowed": payload["approval_language_allowed"],
                "claims_opened": payload["claims_opened"],
                "external_effects_created": payload["external_effects_created"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "records": str(paths["records"].relative_to(ROOT)),
                "policy": str(paths["policy"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
