#!/usr/bin/env python3
"""Execute the local end-to-end product operation loop."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.product_operations import execute_all_local_product_operations, reset_product_operations


def main() -> int:
    reset_product_operations(ROOT)
    payload = execute_all_local_product_operations(ROOT)
    report = payload["report"]
    print(
        json.dumps(
            {
                "status": payload["status"],
                "packet_id": payload["packet_id"],
                "operation_count": report["operation_count"],
                "coverage": report["execution_coverage"],
                "external_effects_created": payload["external_effects_created"],
                "claims_opened": payload["claims_opened"],
                "out": "system_review_graph/product_operations_report.json",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
