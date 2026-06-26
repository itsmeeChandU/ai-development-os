#!/usr/bin/env python3
"""Generate the final local go-live decision and review handoff artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.final_go_live import write_final_go_live_artifacts


def main() -> int:
    result = write_final_go_live_artifacts(ROOT)
    print(f"final_go_live_status={result['status']}")
    print(f"local_contract_complete={result['local_contract_complete']}")
    print(f"public_launch_ready={result['public_launch_ready']}")
    print(f"hosted_private_beta_ready={result['hosted_private_beta_ready']}")
    print(f"source_count={result['source_count']}")
    print(f"reviewer_role_count={result['reviewer_role_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
