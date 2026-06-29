#!/usr/bin/env python3
"""Generate legal/privacy/security approval proof intake artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.legal_privacy_security_approval import (  # noqa: E402
    write_legal_privacy_security_approval_artifacts,
)


def main() -> int:
    result = write_legal_privacy_security_approval_artifacts(ROOT)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
