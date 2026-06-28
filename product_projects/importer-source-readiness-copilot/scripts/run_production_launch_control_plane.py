#!/usr/bin/env python3
"""Generate Phase 20 production launch control plane artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_launch_control_plane import (
    build_production_launch_control_plane,
    write_production_launch_control_plane_artifacts,
)


def main() -> int:
    manifest = build_production_launch_control_plane(ROOT)
    write_production_launch_control_plane_artifacts(manifest, ROOT)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "launch_gate_count": manifest["launch_gate_count"],
                "blocked_launch_gate_count": manifest["blocked_launch_gate_count"],
                "public_scope_candidate_count": manifest["public_scope_candidate_count"],
                "blocked_public_scope_count": manifest["blocked_public_scope_count"],
                "public_launch_approved": manifest["public_launch_approved"],
                "activation_allowed": manifest["activation_allowed"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
