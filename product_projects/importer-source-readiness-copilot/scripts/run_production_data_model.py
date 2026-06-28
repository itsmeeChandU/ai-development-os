#!/usr/bin/env python3
"""Generate the production data model schema package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_data_model import (
    build_production_data_model,
    write_production_data_model_artifacts,
)


def main() -> int:
    payload = build_production_data_model()
    paths = write_production_data_model_artifacts(payload, ROOT)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "table_count": payload["table_count"],
                "foreign_key_count": payload["foreign_key_count"],
                "index_count": payload["index_count"],
                "row_level_security_table_count": payload["row_level_security_table_count"],
                "domain_event_count": payload["domain_event_count"],
                "hosted_database_ready": payload["hosted_database_ready"],
                "migration": str(paths["migration"].relative_to(ROOT)),
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "seed": str(paths["seed"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
