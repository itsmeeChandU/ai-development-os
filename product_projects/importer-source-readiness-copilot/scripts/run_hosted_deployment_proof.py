#!/usr/bin/env python3
"""Generate hosted deployment proof intake artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.hosted_deployment_proof import write_hosted_deployment_proof_artifacts


def main() -> int:
    result = write_hosted_deployment_proof_artifacts(ROOT)
    print(f"hosted_deployment_proof_status={result['status']}")
    print(f"hosted_record_count={result['hosted_record_count']}")
    print(f"accepted_hosted_record_count={result['accepted_hosted_record_count']}")
    print(f"blocked_gate_count={result['blocked_gate_count']}")
    print(f"blocker_export_count={result['blocker_export_count']}")
    print(
        "hosted_private_beta_ready_by_environment_evidence="
        f"{result['hosted_private_beta_ready_by_environment_evidence']}"
    )
    print(f"claims_opened_by_intake={result['claims_opened_by_intake']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
