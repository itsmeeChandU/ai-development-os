#!/usr/bin/env python3
"""Generate a concrete product readiness scorecard from generated reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "product_projects" / "importer-source-readiness-copilot"
DEFAULT_OUT = ROOT / "system_review_graph" / "product_readiness_scorecard.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"missing": True, "path": str(path.relative_to(ROOT))}
    return json.loads(path.read_text(encoding="utf-8"))


def build_scorecard() -> dict[str, Any]:
    graph = PROJECT / "system_review_graph"
    readiness = _read_json(graph / "readiness_report.json")
    continuation = _read_json(graph / "continuation_plan.json")
    final_go_live = _read_json(graph / "final_go_live_decision_report.json")
    external_review = _read_json(graph / "external_review_findings_report.json")
    input_readiness = _read_json(graph / "go_live_input_readiness_report.json")
    no_scaffold = _read_json(ROOT / "system_review_graph" / "no_scaffold_audit_report.json")

    checks = [
        {
            "id": "local_software_loop",
            "passed": readiness.get("status") == "ready_with_external_gates",
            "evidence": "readiness_report.json",
            "meaning": "Local software loop can be reviewed internally.",
        },
        {
            "id": "continuation_required",
            "passed": continuation.get("must_continue") is True,
            "evidence": "continuation_plan.json",
            "meaning": "The product is still startup_in_progress and cannot be called complete.",
        },
        {
            "id": "public_launch_closed",
            "passed": final_go_live.get("public_launch_ready") is False,
            "evidence": "final_go_live_decision_report.json",
            "meaning": "Public launch is not approved.",
        },
        {
            "id": "real_external_review_pending",
            "passed": external_review.get("completed_review_count") == 0,
            "evidence": "external_review_findings_report.json",
            "meaning": "External review has not been completed by real reviewers.",
        },
        {
            "id": "go_live_inputs_pending",
            "passed": input_readiness.get("missing_input_count") == 8
            and input_readiness.get("public_launch_ready") is False,
            "evidence": "go_live_input_readiness_report.json",
            "meaning": "Eight real go-live inputs are still required.",
        },
        {
            "id": "no_scaffold_completion_claims",
            "passed": no_scaffold.get("status") == "pass_no_scaffold_completion_claims",
            "evidence": "no_scaffold_audit_report.json",
            "meaning": "No scaffold-like artifact is allowed to count as completion.",
        },
    ]
    passed = sum(1 for row in checks if row["passed"])
    return {
        "status": "internal_review_ready_external_completion_not_ready"
        if passed == len(checks)
        else "readiness_scorecard_failed",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project": str(PROJECT.relative_to(ROOT)),
        "score": {
            "passed": passed,
            "total": len(checks),
            "percent": round((passed / len(checks)) * 100, 2),
        },
        "checks": checks,
        "final_truth": {
            "complete_development_ready": False,
            "public_launch_ready": False,
            "external_review_completed": False,
            "go_live_missing_inputs": input_readiness.get("missing_input_count"),
            "next_valid_move": "Collect real reviewer, hosted, payment, beta/user, buyer/supplier, and launch-owner inputs.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    scorecard = build_scorecard()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Product readiness scorecard: PASS" if scorecard["status"].endswith("not_ready") else "Product readiness scorecard: FAIL")
    print(f"status={scorecard['status']}")
    print(f"score={scorecard['score']['passed']}/{scorecard['score']['total']}")
    print(f"public_launch_ready={scorecard['final_truth']['public_launch_ready']}")
    print(f"out={args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}")
    return 0 if scorecard["status"].endswith("not_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
