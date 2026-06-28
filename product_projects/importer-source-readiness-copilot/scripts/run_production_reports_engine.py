#!/usr/bin/env python3
"""Generate production report and deliverable artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_reports_engine import (
    build_production_reports_engine,
    write_production_reports_engine_artifacts,
)


def main() -> int:
    manifest = build_production_reports_engine(ROOT)
    write_production_reports_engine_artifacts(manifest, ROOT)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "report_type_count": manifest["report_type_count"],
                "report_record_count": manifest["report_record_count"],
                "export_record_count": manifest["export_record_count"],
                "citation_record_count": manifest["citation_record_count"],
                "claims_opened": manifest["claims_opened"],
                "external_effects_created": manifest["external_effects_created"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
