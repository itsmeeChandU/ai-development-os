#!/usr/bin/env python3
"""Generate executable production-domain persistence artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_persistence import (
    build_production_persistence_snapshot,
    inspect_sqlite_proof_store,
    write_production_persistence_artifacts,
)


def main() -> int:
    snapshot = build_production_persistence_snapshot(ROOT)
    paths = write_production_persistence_artifacts(snapshot, ROOT)
    store = inspect_sqlite_proof_store(paths["sqlite"])
    print(
        json.dumps(
            {
                "status": snapshot["status"],
                "table_count": len(snapshot["table_order"]),
                "total_row_count": snapshot["total_row_count"],
                "validation_error_count": snapshot["validation_error_count"],
                "hosted_postgres_ready": snapshot["hosted_postgres_ready"],
                "external_claims_opened": snapshot["external_claims_opened"],
                "sqlite_table_counts": store["table_counts"],
                "manifest": str(paths["manifest"].relative_to(ROOT)),
                "row_counts": str(paths["row_counts"].relative_to(ROOT)),
                "sqlite": str(paths["sqlite"].relative_to(ROOT)),
                "doc": str(paths["doc"].relative_to(ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0 if snapshot["validation_error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
