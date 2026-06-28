#!/usr/bin/env python3
"""Generate the production expert-review network artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_expert_review_network import (
    build_production_expert_review_network,
    write_production_expert_review_network_artifacts,
)


def main() -> int:
    manifest = build_production_expert_review_network(ROOT)
    write_production_expert_review_network_artifacts(manifest, ROOT)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "reviewer_lane_count": manifest["reviewer_lane_count"],
                "review_request_count": manifest["review_request_count"],
                "finding_template_count": manifest["finding_template_count"],
                "real_reviewer_signoff_recorded": manifest["real_reviewer_signoff_recorded"],
                "claims_opened": manifest["claims_opened"],
                "external_effects_created": manifest["external_effects_created"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
