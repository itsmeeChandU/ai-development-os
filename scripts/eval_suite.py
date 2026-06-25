#!/usr/bin/env python3
"""Run lightweight AI Development OS eval checks from the execution manifest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "manifests" / "agentic_execution_manifest.json"

REQUIRED_EVAL_FIELDS = {
    "id",
    "predicate",
    "measurement",
    "pass_condition",
    "failure_output",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_eval_suite(manifest_path: Path) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    rows = []
    blockers = []
    for eval_row in manifest.get("eval_loops", []):
        missing = sorted(REQUIRED_EVAL_FIELDS - set(eval_row))
        status = "pass" if not missing else "fail"
        rows.append(
            {
                "id": eval_row.get("id"),
                "status": status,
                "missing_fields": missing,
                "measurement": eval_row.get("measurement"),
                "pass_condition": eval_row.get("pass_condition"),
            }
        )
        if missing:
            blockers.append(
                {
                    "id": f"eval:{eval_row.get('id', 'unknown')}:missing-fields",
                    "module": "eval_suite",
                    "issue": "eval loop is missing required fields",
                    "owner": "workflow-coordinator",
                    "evidence": str(manifest_path),
                    "gate": "closed",
                    "next_valid_move": f"Add fields: {', '.join(missing)}",
                    "unsafe_to_bypass": True,
                }
            )
    return {
        "generated_at": _now(),
        "manifest": str(manifest_path),
        "status": "pass" if not blockers else "fail",
        "eval_count": len(rows),
        "rows": rows,
        "blockers": blockers,
        "proof_boundary": (
            "This eval suite validates execution-loop structure. It does not "
            "replace lane-specific tests or runtime smoke checks."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval_suite")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=ROOT / "system_review_graph" / "eval_report.json")
    args = parser.parse_args(argv)

    report = run_eval_suite(args.manifest)
    _write_json(args.out, report)
    print(args.out)
    print(f"Eval suite: {report['status'].upper()}")
    print(f"eval_count={report['eval_count']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
