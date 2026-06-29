#!/usr/bin/env python3
"""Generate production repository/service proof artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_repository import (
    build_production_repository_service,
    write_production_repository_artifacts,
)


def main() -> int:
    payload = build_production_repository_service(ROOT)
    paths = write_production_repository_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "packet_count": len(payload["packet_ids"]),
                "safe_claim_count": payload["safe_claim_count"],
                "blocked_claim_decision_count": payload["blocked_claim_decision_count"],
                "report_export_count": payload["report_export_count"],
                "wrong_org_status": payload["tenant_access_control"]["wrong_org_status"],
                "external_claims_opened": payload["external_claims_opened"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "packet_context": str(paths["packet_context"].relative_to(ROOT)),
                "report_context": str(paths["report_context"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
