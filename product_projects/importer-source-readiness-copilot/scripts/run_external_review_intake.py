#!/usr/bin/env python3
"""Generate returned external-review intake artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.external_review_intake import write_returned_external_review_intake_artifacts


def main() -> int:
    result = write_returned_external_review_intake_artifacts(ROOT)
    print(f"external_review_intake_status={result['status']}")
    print(f"returned_review_records={result['returned_record_count']}")
    print(f"accepted_review_evidence={result['accepted_review_evidence_count']}")
    print(f"pending_review_count={result['pending_review_count']}")
    print(f"blocker_export_count={result['blocker_export_count']}")
    print(f"public_launch_ready_by_review_evidence={result['public_launch_ready_by_review_evidence']}")
    print(f"claims_opened_by_intake={result['claims_opened_by_intake']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
