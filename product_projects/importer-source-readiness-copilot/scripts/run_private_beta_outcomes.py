#!/usr/bin/env python3
"""Generate the private-beta outcome contract artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.private_beta_outcomes import write_private_beta_outcome_artifacts


def main() -> int:
    result = write_private_beta_outcome_artifacts(ROOT)
    print(f"private_beta_outcome_status={result['status']}")
    print(f"private_beta_required_sessions={result['required_session_count']}")
    print(f"private_beta_current_real_sessions={result['current_real_session_count']}")
    print(f"private_beta_real_user_evidence_ready={result['real_user_evidence_ready']}")
    print(f"private_beta_public_launch_ready={result['public_launch_ready']}")
    print(f"private_beta_claims_opened={result['claims_opened']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
