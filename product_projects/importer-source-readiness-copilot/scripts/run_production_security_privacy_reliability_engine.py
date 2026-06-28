#!/usr/bin/env python3
"""Generate Phase 19 production trust artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_security_privacy_reliability_engine import (
    build_production_security_privacy_reliability_engine,
    write_production_security_privacy_reliability_engine_artifacts,
)


def main() -> int:
    manifest = build_production_security_privacy_reliability_engine(ROOT)
    write_production_security_privacy_reliability_engine_artifacts(manifest, ROOT)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "trust_control_count": manifest["trust_control_count"],
                "trust_gate_count": manifest["trust_gate_count"],
                "blocked_trust_gate_count": manifest["blocked_trust_gate_count"],
                "vendor_record_count": manifest["vendor_record_count"],
                "backup_restore_status": manifest["backup_restore_drill"]["status"],
                "real_file_uploads_allowed": manifest["real_file_uploads_allowed"],
                "hosted_private_beta_ready": manifest["hosted_private_beta_ready"],
                "production_trust_approved": manifest["production_trust_approved"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
