#!/usr/bin/env python3
"""Validate machine-readable blocker ledgers for AI Development OS."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_BLOCKER_FIELDS = {
    "id",
    "module",
    "issue",
    "owner",
    "evidence",
    "gate",
    "next_valid_move",
    "unsafe_to_bypass",
}
VALID_GATES = {"closed", "open", "not_applicable"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            rows.append(
                {
                    "id": f"parse-error:{line_number}",
                    "module": "blocker_ledger",
                    "issue": f"invalid JSONL row: {exc}",
                    "owner": "workflow-coordinator",
                    "evidence": f"{path}:{line_number}",
                    "gate": "closed",
                    "next_valid_move": "Rewrite the row as valid JSON.",
                    "unsafe_to_bypass": True,
                    "_invalid": True,
                }
            )
            continue
        if isinstance(row, dict):
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def validate_blocker_ledger(path: Path, *, allow_missing: bool = False) -> dict[str, Any]:
    if not path.exists():
        status = "missing_allowed" if allow_missing else "fail"
        blockers = []
        if not allow_missing:
            blockers.append(
                {
                    "id": "blocker-ledger:missing",
                    "module": "blocker_ledger",
                    "issue": "blocker ledger file is missing",
                    "owner": "workflow-coordinator",
                    "evidence": str(path),
                    "gate": "closed",
                    "next_valid_move": "Create the blocker ledger or pass --allow-missing.",
                    "unsafe_to_bypass": True,
                }
            )
        return {
            "generated_at": _now(),
            "path": str(path),
            "status": status,
            "row_count": 0,
            "blockers": blockers,
        }

    rows = _read_jsonl(path)
    blockers = []
    for row in rows:
        if row.get("_invalid"):
            blockers.append(row)
            continue
        missing = sorted(REQUIRED_BLOCKER_FIELDS - set(row))
        if missing:
            blockers.append(
                {
                    "id": f"blocker-ledger:row-{row.get('_line_number')}:missing-fields",
                    "module": "blocker_ledger",
                    "issue": f"blocker row missing fields: {', '.join(missing)}",
                    "owner": row.get("owner", "workflow-coordinator"),
                    "evidence": f"{path}:{row.get('_line_number')}",
                    "gate": "closed",
                    "next_valid_move": f"Add fields: {', '.join(missing)}",
                    "unsafe_to_bypass": True,
                }
            )
        if row.get("gate") not in VALID_GATES:
            blockers.append(
                {
                    "id": f"blocker-ledger:row-{row.get('_line_number')}:bad-gate",
                    "module": "blocker_ledger",
                    "issue": f"invalid gate value: {row.get('gate')}",
                    "owner": row.get("owner", "workflow-coordinator"),
                    "evidence": f"{path}:{row.get('_line_number')}",
                    "gate": "closed",
                    "next_valid_move": "Use closed, open, or not_applicable.",
                    "unsafe_to_bypass": True,
                }
            )
    return {
        "generated_at": _now(),
        "path": str(path),
        "status": "pass" if not blockers else "fail",
        "row_count": len(rows),
        "blockers": blockers,
        "proof_boundary": (
            "The blocker ledger validates blocker shape. It does not close blockers "
            "without evidence."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="blocker_ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a blocker JSONL file")
    validate.add_argument("--input", type=Path, required=True)
    validate.add_argument("--out", type=Path, default=ROOT / "system_review_graph" / "blocker_ledger_report.json")
    validate.add_argument("--allow-missing", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "validate":
        report = validate_blocker_ledger(args.input, allow_missing=args.allow_missing)
        _write_json(args.out, report)
        print(args.out)
        print(f"Blocker ledger: {report['status'].upper()}")
        print(f"row_count={report['row_count']}")
        return 0 if report["status"] in {"pass", "missing_allowed"} else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
