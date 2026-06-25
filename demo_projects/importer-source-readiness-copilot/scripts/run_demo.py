#!/usr/bin/env python3
"""Run the importer source readiness demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import evaluate_cards, load_cards, write_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "sample_source_cards.json")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "system_review_graph" / "demo_readiness_report.json",
    )
    parser.add_argument(
        "--blockers-out",
        type=Path,
        default=ROOT / "system_review_graph" / "blockers.jsonl",
    )
    parser.add_argument("--generated-at", default="2026-06-25T00:00:00+00:00")
    args = parser.parse_args()

    report = evaluate_cards(load_cards(args.input), generated_at=args.generated_at)
    write_report(report, args.out)
    args.blockers_out.parent.mkdir(parents=True, exist_ok=True)
    args.blockers_out.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in report["blockers"]),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "blocker_count": report["blocker_count"],
                "out": str(args.out),
                "blockers_out": str(args.blockers_out),
            }
        )
    )
    return 0 if report["status"] != "blocked_unsafe" else 1


if __name__ == "__main__":
    raise SystemExit(main())
