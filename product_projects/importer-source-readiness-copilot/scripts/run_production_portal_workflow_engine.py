#!/usr/bin/env python3
"""Generate production portal workflow artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_portal_workflow_engine import (
    build_production_portal_workflow_engine,
    write_production_portal_workflow_engine_artifacts,
)


def main() -> int:
    manifest = build_production_portal_workflow_engine(ROOT)
    write_production_portal_workflow_engine_artifacts(manifest, ROOT)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "portal_count": manifest["portal_count"],
                "workflow_count": manifest["workflow_count"],
                "first_screen_option_count": manifest["first_screen_option_count"],
                "all_required_routes_present": manifest["all_required_routes_present"],
                "claims_opened": manifest["claims_opened"],
                "external_effects_created": manifest["external_effects_created"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
