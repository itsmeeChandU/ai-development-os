#!/usr/bin/env python3
"""Generate live-payment activation proof intake artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.payment_activation_proof import write_payment_activation_proof_artifacts


def main() -> int:
    result = write_payment_activation_proof_artifacts(ROOT)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
