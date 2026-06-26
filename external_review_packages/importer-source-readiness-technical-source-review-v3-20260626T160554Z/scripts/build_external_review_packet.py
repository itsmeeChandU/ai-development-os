#!/usr/bin/env python3
"""Generate external review packets, finding templates, and blockers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.external_review import write_external_review_artifacts


def main() -> int:
    result = write_external_review_artifacts(ROOT)
    print(f"external_review_status={result['status']}")
    print(f"required_review_count={result['required_review_count']}")
    print(f"completed_review_count={result['completed_review_count']}")
    print(f"external_review_blocker_count={result['blocker_count']}")
    print(f"ai_assisted_review_status={result['ai_assisted_review_status']}")
    print(f"ai_assisted_wave_1_status={result['ai_assisted_wave_1_status']}")
    print(f"simulated_review_count={result['simulated_review_count']}")
    print(f"simulated_finding_count={result['simulated_finding_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
