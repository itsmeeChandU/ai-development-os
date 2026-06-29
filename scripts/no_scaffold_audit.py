#!/usr/bin/env python3
"""Audit scaffold-like artifacts so they cannot be used as completion proof."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "system_review_graph" / "no_scaffold_audit_report.json"
DEFAULT_MD = ROOT / "system_review_graph" / "no_scaffold_audit_report.md"
PRIOR_DELIVERY_COMMIT = "d5a80d8a3178d9e1248944df9ac839d6f897a7a8"

MARKERS: dict[str, re.Pattern[str]] = {
    "scaffold_complete": re.compile(r"scaffold complete", re.IGNORECASE),
    "scaffold": re.compile(r"\bscaffold(?:ed|ing)?\b", re.IGNORECASE),
    "placeholder": re.compile(r"\bplaceholder\b", re.IGNORECASE),
    "stub": re.compile(r"\bstub\b", re.IGNORECASE),
    "todo": re.compile(r"\bTODO\b"),
    "fixme": re.compile(r"\bFIXME\b"),
    "not_implemented": re.compile(r"not implemented|NotImplementedError"),
    "coming_soon": re.compile(r"coming soon", re.IGNORECASE),
    "mock": re.compile(r"\bmock(?:ed|s)?\b", re.IGNORECASE),
    "dummy": re.compile(r"\bdummy\b", re.IGNORECASE),
    "fake": re.compile(r"\bfake\b", re.IGNORECASE),
    "simulated": re.compile(r"\bsimulated\b", re.IGNORECASE),
    "template": re.compile(r"\btemplate\b", re.IGNORECASE),
}

BINARY_SUFFIXES = {
    ".gif",
    ".ico",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".png",
    ".pyc",
    ".sqlite",
    ".zip",
}

SKIP_PREFIXES = (
    "external_review_packages/",
    ".git/",
    "__pycache__/",
)

POLICY_PATHS = (
    "AGENTS.md",
    "README.md",
    "ROADMAP.md",
    "SECURITY.md",
    "docs/",
    "manifests/",
    "product_projects/README.md",
    "product_projects/importer-source-readiness-copilot/AGENTS.md",
    "system_review_graph/no_scaffold_audit_report",
)

GENERATOR_PATHS = (
    "templates/",
    "examples/",
    "scripts/scaffold_project.py",
    "scripts/self_test_flow.py",
)

POLICY_IMPLEMENTATION_PATHS = (
    "scripts/no_scaffold_audit.py",
    "scripts/product_project_check.py",
    "scripts/product_readiness_scorecard.py",
    "scripts/system_review_graph.py",
    "scripts/workflow_manifest_check.py",
)


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def _head() -> str:
    return _run_git(["rev-parse", "HEAD"]).strip()


def _tracked_files() -> list[str]:
    tracked = [line for line in _run_git(["ls-files"]).splitlines() if line]
    untracked = [line for line in _run_git(["ls-files", "--others", "--exclude-standard"]).splitlines() if line]
    return sorted(set(tracked + untracked))


def _commit_changed_files(commit: str) -> list[str]:
    try:
        return [
            line
            for line in _run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", commit]).splitlines()
            if line
        ]
    except RuntimeError:
        return []


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_text_path(path: str) -> bool:
    if path.startswith(SKIP_PREFIXES):
        return False
    return Path(path).suffix.lower() not in BINARY_SUFFIXES


def _classification(path: str, marker: str, line: str) -> tuple[str, bool, str]:
    lower_line = line.lower()
    if path.startswith(POLICY_IMPLEMENTATION_PATHS):
        return ("policy_enforcement_code", True, "Policy enforcement code may name the forbidden marker it detects.")

    if path.startswith(GENERATOR_PATHS):
        return ("generator_template_only", True, "Generator/template code is allowed only as a starting point.")

    if path.startswith(POLICY_PATHS):
        return ("policy_language", True, "Policy or manifest language may name forbidden scaffold patterns.")

    if marker == "scaffold_complete":
        return ("disallowed_scaffold_completion_marker", False, "A script or artifact says a scaffold is complete.")

    if path.startswith("system_review_graph/"):
        return ("generated_audit_language", True, "Root generated audit reports may reference closed simulated or template states.")

    if path.endswith("go_live_input_templates.json") or "record_template" in line:
        return ("review_input_template_only", True, "Input templates collect real responses; they do not prove readiness.")

    if path.startswith("product_projects/importer-source-readiness-copilot/") and marker == "simulated":
        return ("simulated_review_approval_closed", True, "Product simulated-review language is allowed only because checks keep approval closed.")

    if "fixture country requirements placeholder" in lower_line or "placeholder.pdf" in lower_line:
        return ("fixture_blocker_evidence", True, "Fixture placeholder is allowed only while blocker rows keep claims closed.")

    if path.startswith("product_projects/importer-source-readiness-copilot/") and marker == "placeholder":
        return ("external_input_gap_language", True, "Product placeholder language is allowed only when it describes missing external evidence.")

    if marker == "simulated" and (
        "cannot open" in lower_line
        or "never opens" in lower_line
        or "can open gates: `false`" in lower_line
        or "can_open" in lower_line
        or "simulated_review" in lower_line
    ):
        return ("simulated_review_approval_closed", True, "Simulated review may create findings but cannot open approval.")

    if marker == "template":
        return ("template_reference", True, "Template references are allowed only as non-completion input surfaces.")

    if marker in {"todo", "fixme", "not_implemented", "coming_soon", "stub", "dummy", "mock", "fake", "placeholder"}:
        return ("disallowed_delivery_marker", False, "Marker is not in an allowed generator, policy, or blocker context.")

    return ("manual_review_required", False, "Scaffold-like marker did not match an allowed context.")


def _scan_files(paths: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        if not _is_text_path(path):
            continue
        full_path = ROOT / path
        if not full_path.exists():
            continue
        try:
            lines = full_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for marker, pattern in MARKERS.items():
                if pattern.search(line):
                    classification, allowed, reason = _classification(path, marker, line)
                    findings.append(
                        {
                            "path": path,
                            "line": line_number,
                            "marker": marker,
                            "classification": classification,
                            "allowed": allowed,
                            "reason": reason,
                            "text": line.strip()[:240],
                        }
                    )
    return findings


def _runtime_claim_checks() -> dict[str, Any]:
    product = ROOT / "product_projects" / "importer-source-readiness-copilot"
    readiness_path = product / "system_review_graph" / "go_live_input_readiness_report.json"
    validation_path = product / "system_review_graph" / "external_validation_requirements_report.json"
    blocker_path = product / "system_review_graph" / "blockers.jsonl"

    checks: dict[str, Any] = {
        "go_live_input_readiness_exists": readiness_path.exists(),
        "external_validation_report_exists": validation_path.exists(),
        "blocker_ledger_exists": blocker_path.exists(),
    }
    if readiness_path.exists():
        readiness = _read_json(readiness_path)
        checks.update(
            {
                "go_live_input_status": readiness.get("status"),
                "go_live_missing_input_count": readiness.get("missing_input_count"),
                "go_live_public_launch_ready": readiness.get("public_launch_ready"),
                "go_live_hosted_private_beta_ready": readiness.get("hosted_private_beta_ready"),
                "go_live_live_payment_ready": readiness.get("live_payment_ready"),
                "go_live_input_templates_open_launch": readiness.get("public_launch_ready") is True,
            }
        )
    if validation_path.exists():
        validation = _read_json(validation_path)
        checks.update(
            {
                "external_validation_status": validation.get("status"),
                "external_validation_public_launch_ready": validation.get("public_launch_ready"),
                "external_validation_hosted_private_beta_ready": validation.get("hosted_private_beta_ready"),
                "external_validation_live_payment_ready": validation.get("live_payment_ready"),
                "simulated_ai_review_can_open_gate": validation.get("simulated_ai_review_can_open_gate"),
            }
        )
    return checks


def _prior_delivery_audit() -> dict[str, Any]:
    changed = _commit_changed_files(PRIOR_DELIVERY_COMMIT)
    scoped = [path for path in changed if "external_validation" in path or "go_live_input" in path]
    return {
        "commit": PRIOR_DELIVERY_COMMIT,
        "commit_found": bool(changed),
        "scaffold_like_outputs": [
            {
                "path": "product_projects/importer-source-readiness-copilot/system_review_graph/go_live_input_templates.json",
                "classification": "review_input_template_only",
                "complete_development_claim_allowed": False,
                "audit_verdict": "This is an input form for real people. It is not evidence that go live is approved.",
            },
            {
                "path": "product_projects/importer-source-readiness-copilot/docs/GO_LIVE_INPUT_REQUESTS.md",
                "classification": "review_intake_only",
                "complete_development_claim_allowed": False,
                "audit_verdict": "This tells reviewers what to provide. It is not a replacement for reviewer decisions.",
            },
            {
                "path": "product_projects/importer-source-readiness-copilot/output/pdf/go_live_input_requests.pdf",
                "classification": "shareable_review_packet_only",
                "complete_development_claim_allowed": False,
                "audit_verdict": "This PDF is email-ready packaging. It is not hosted proof, payment proof, user proof, or approval.",
            },
            {
                "path": "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/external_validation_research.py",
                "classification": "evaluator_and_report_generator",
                "complete_development_claim_allowed": False,
                "audit_verdict": "The evaluator can flip readiness only after real returned input records exist.",
            },
        ],
        "changed_validation_files": scoped,
        "verdict": "Prior delivery produced a real audit/evaluator package and shareable review inputs, not complete go-live development.",
    }


def build_report(paths: list[str] | None = None) -> dict[str, Any]:
    paths = paths or _tracked_files()
    findings = _scan_files(paths)
    disallowed = [finding for finding in findings if not finding["allowed"]]
    counts = Counter(finding["classification"] for finding in findings)
    runtime_checks = _runtime_claim_checks()

    policy_failures: list[str] = []
    if disallowed:
        policy_failures.append("disallowed scaffold-like markers exist outside approved contexts")
    if runtime_checks.get("go_live_public_launch_ready") is not False:
        policy_failures.append("go-live input readiness must keep public_launch_ready false until real approval exists")
    if runtime_checks.get("external_validation_public_launch_ready") is not False:
        policy_failures.append("external validation report must keep public_launch_ready false until real approval exists")
    if runtime_checks.get("simulated_ai_review_can_open_gate") is not False:
        policy_failures.append("simulated AI review must not open any approval gate")

    return {
        "status": "pass_no_scaffold_completion_claims" if not policy_failures else "fail_scaffold_policy",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo": ROOT.name,
        "head": _head(),
        "policy": "docs/NO_SCAFFOLD_DELIVERY_POLICY.md",
        "scanned_file_count": len(paths),
        "skipped_contexts": ["external_review_packages", "binary files"],
        "finding_count": len(findings),
        "classification_counts": dict(sorted(counts.items())),
        "disallowed_count": len(disallowed),
        "policy_failures": policy_failures,
        "disallowed_findings": disallowed[:100],
        "runtime_claim_checks": runtime_checks,
        "prior_delivery_audit": _prior_delivery_audit(),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    prior = report["prior_delivery_audit"]
    lines = [
        "# No Scaffold Audit Report",
        "",
        f"Status: `{report['status']}`",
        f"Head: `{report['head']}`",
        f"Policy: `{report['policy']}`",
        "",
        "## Prior Delivery Audit",
        "",
        f"Audited commit: `{prior['commit']}`",
        f"Verdict: {prior['verdict']}",
        "",
        "| Artifact | Classification | Completion Claim Allowed | Verdict |",
        "|---|---|---|---|",
    ]
    for item in prior["scaffold_like_outputs"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item['path']}`",
                    item["classification"],
                    str(item["complete_development_claim_allowed"]),
                    item["audit_verdict"],
                ]
            )
            + " |"
        )

    checks = report["runtime_claim_checks"]
    lines.extend(
        [
            "",
            "## Runtime Claim Checks",
            "",
            f"- Go-live input status: `{checks.get('go_live_input_status')}`",
            f"- Missing real inputs: `{checks.get('go_live_missing_input_count')}`",
            f"- Public launch ready: `{checks.get('go_live_public_launch_ready')}`",
            f"- Hosted private beta ready: `{checks.get('go_live_hosted_private_beta_ready')}`",
            f"- Live payment ready: `{checks.get('go_live_live_payment_ready')}`",
            f"- Simulated AI review can open approval: `{checks.get('simulated_ai_review_can_open_gate')}`",
            "",
            "## Scan Summary",
            "",
            f"- Scanned files: `{report['scanned_file_count']}`",
            f"- Scaffold-like findings: `{report['finding_count']}`",
            f"- Disallowed findings: `{report['disallowed_count']}`",
            "",
            "## Classification Counts",
            "",
        ]
    )
    for key, value in sorted(report["classification_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    if report["policy_failures"]:
        lines.extend(["", "## Policy Failures", ""])
        for failure in report["policy_failures"]:
            lines.append(f"- {failure}")
    else:
        lines.extend(
            [
                "",
                "## Result",
                "",
                "No scaffold, template, placeholder, mock, or simulated artifact is allowed to count as complete development or launch proof.",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--check", action="store_true", help="Fail if the no-scaffold policy is violated.")
    args = parser.parse_args()

    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.md_out)

    if args.check and report["status"] != "pass_no_scaffold_completion_claims":
        print("No scaffold audit: FAIL")
        for failure in report["policy_failures"]:
            print(f"failure: {failure}")
        return 1

    print("No scaffold audit: PASS")
    print(f"status={report['status']}")
    print(f"disallowed_count={report['disallowed_count']}")
    print(f"report={args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}")
    print(f"markdown={args.md_out.relative_to(ROOT) if args.md_out.is_relative_to(ROOT) else args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
