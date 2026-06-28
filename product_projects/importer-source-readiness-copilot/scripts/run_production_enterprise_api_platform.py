#!/usr/bin/env python3
"""Generate production enterprise SaaS/API platform artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_enterprise_api_platform import (
    build_production_enterprise_api_platform,
    write_production_enterprise_api_platform_artifacts,
)


def main() -> int:
    manifest = build_production_enterprise_api_platform(ROOT)
    write_production_enterprise_api_platform_artifacts(manifest, ROOT)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "api_contract_count": manifest["api_contract_count"],
                "all_required_api_routes_present": manifest["all_required_api_routes_present"],
                "workspace_control_count": manifest["workspace_control_count"],
                "api_key_record_count": manifest["api_key_record_count"],
                "webhook_record_count": manifest["webhook_record_count"],
                "claims_opened": manifest["claims_opened"],
                "external_effects_created": manifest["external_effects_created"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
