#!/usr/bin/env python3
"""Serve the local operator application."""

from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.operator_app import make_server


def _refresh_artifacts() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_product.py"],
        cwd=ROOT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve Importer Source Readiness Copilot locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--skip-refresh", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    if not args.skip_refresh:
        _refresh_artifacts()

    server = make_server(ROOT, args.host, args.port)
    url = f"http://{args.host}:{args.port}/"
    print(f"Importer Source Readiness Copilot running at {url}", flush=True)
    print("Routes: /, /api, /api/operator-workflow, /api/readiness, /api/external-gates", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping operator app.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
