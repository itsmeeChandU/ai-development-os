"""Validate and emit AI Development OS multi-repo execution lane packets."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_MANIFEST = ROOT / "manifests" / "agentic_workflow_manifest.json"
EXECUTION_MANIFEST = ROOT / "manifests" / "agentic_execution_manifest.json"

REQUIRED_EXECUTION_FIELDS = {
    "version",
    "date_checked",
    "name",
    "purpose",
    "source_workflow_manifest",
    "canonical_truth",
    "slash_commands",
    "skills",
    "background_routines",
    "parallel_agent_lanes",
    "ci_cd_agent_jobs",
    "eval_loops",
    "agent_supervision",
    "multi_repo_orchestration",
    "handoff_schema",
    "proof_boundaries",
}
REQUIRED_COMMANDS = {
    "/ados:normalize",
    "/ados:context-bundle",
    "/ados:lane",
    "/ados:proof",
    "/ados:review",
    "/ados:merge",
    "/ados:goal",
}
REQUIRED_ROUTINES = {
    "branch_freshness_check",
    "context_bundle_refresh",
    "stale_blocker_sweep",
    "nightly_eval_loop",
    "ci_failure_triage",
}
REQUIRED_EVALS = {
    "lane_packet_completeness",
    "contract_section_coverage",
    "branch_freshness",
    "handoff_completeness",
    "main_push_readiness",
}
REQUIRED_LANE_FIELDS = {
    "id",
    "mode",
    "repo_id",
    "goal",
    "allowed_files",
    "forbidden_files",
    "proof_commands",
    "handoff_template",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ids(rows: list[dict[str, Any]], key: str = "id") -> set[str]:
    return {str(row.get(key)) for row in rows}


def validate_execution_manifest(
    workflow: dict[str, Any], execution: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_EXECUTION_FIELDS - set(execution))
    if missing:
        errors.append(f"missing execution manifest fields: {', '.join(missing)}")

    workflow_path = execution.get("source_workflow_manifest")
    if workflow_path != "manifests/agentic_workflow_manifest.json":
        errors.append("source_workflow_manifest must point at manifests/agentic_workflow_manifest.json")

    workflow_execution = workflow.get("execution_manifest") or {}
    if workflow_execution.get("path") != "manifests/agentic_execution_manifest.json":
        errors.append("workflow manifest must point at manifests/agentic_execution_manifest.json")

    commands = {str(row.get("command")) for row in execution.get("slash_commands", [])}
    missing_commands = sorted(REQUIRED_COMMANDS - commands)
    if missing_commands:
        errors.append(f"missing slash commands: {', '.join(missing_commands)}")

    routines = _ids(execution.get("background_routines", []))
    missing_routines = sorted(REQUIRED_ROUTINES - routines)
    if missing_routines:
        errors.append(f"missing background routines: {', '.join(missing_routines)}")

    evals = _ids(execution.get("eval_loops", []))
    missing_evals = sorted(REQUIRED_EVALS - evals)
    if missing_evals:
        errors.append(f"missing eval loops: {', '.join(missing_evals)}")

    workflow_modes = _ids(workflow.get("agent_modes", []))
    workflow_repos = _ids(workflow.get("repo_roles", []))
    execution_repos = {
        str(repo.get("id"))
        for repo in (execution.get("multi_repo_orchestration") or {}).get("repos", [])
    }
    missing_repos = sorted(execution_repos - workflow_repos - {"intelligence-hub", "multi-repo"})
    if missing_repos:
        errors.append(f"execution repos missing from workflow roles: {', '.join(missing_repos)}")

    for lane in execution.get("parallel_agent_lanes", []):
        lane_id = str(lane.get("id") or "<missing>")
        lane_missing = sorted(REQUIRED_LANE_FIELDS - set(lane))
        if lane_missing:
            errors.append(f"lane {lane_id} missing fields: {', '.join(lane_missing)}")
        if lane.get("mode") not in workflow_modes:
            errors.append(f"lane {lane_id} uses unknown mode {lane.get('mode')!r}")
        if not lane.get("proof_commands"):
            errors.append(f"lane {lane_id} must define proof commands")
        if not lane.get("allowed_files"):
            errors.append(f"lane {lane_id} must define allowed_files")
        if not lane.get("forbidden_files"):
            errors.append(f"lane {lane_id} must define forbidden_files")

    boundary = str((execution.get("canonical_truth") or {}).get("boundary") or "").lower()
    if "repo files" not in boundary or "ruflo" not in boundary:
        errors.append("canonical_truth.boundary must keep Ruflo separate from repo truth")

    handoff_fields = set((execution.get("handoff_schema") or {}).get("required_fields", []))
    required_handoff = {
        "lane",
        "branch_or_worktree",
        "changed_files",
        "commands_run",
        "blockers",
        "next_valid_move",
        "commit",
        "push_state",
    }
    missing_handoff = sorted(required_handoff - handoff_fields)
    if missing_handoff:
        errors.append(f"handoff schema missing fields: {', '.join(missing_handoff)}")

    return errors


def _repo_lookup(execution: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(repo.get("id")): repo
        for repo in (execution.get("multi_repo_orchestration") or {}).get("repos", [])
    }


def build_plan(
    *,
    workflow: dict[str, Any],
    execution: dict[str, Any],
    goal: str,
    repo_filter: str = "",
    run_id: str = "",
) -> dict[str, Any]:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    date_id = run_id or datetime.now(UTC).strftime("%Y%m%d")
    orchestration = execution["multi_repo_orchestration"]
    worktree_root = orchestration["worktree_root"]
    branch_prefix = orchestration["branch_prefix"]
    repos = _repo_lookup(execution)
    selected_lanes = []
    for lane in execution["parallel_agent_lanes"]:
        repo_id = str(lane["repo_id"])
        if repo_filter and repo_id != repo_filter:
            continue
        branch = f"{branch_prefix}{lane['id']}-{date_id}"
        if repo_id in repos:
            worktree = f"{worktree_root}/{repo_id}-{lane['id']}"
            remote = repos[repo_id]["remote"]
            role = repos[repo_id]["role"]
        else:
            worktree = ""
            remote = ""
            role = "cross_repo_review"
        selected_lanes.append(
            {
                "id": lane["id"],
                "mode": lane["mode"],
                "repo_id": repo_id,
                "repo_role": role,
                "goal": lane["goal"],
                "branch": branch,
                "target_branch": orchestration["target_branch"],
                "worktree": worktree,
                "remote": remote,
                "allowed_files": lane["allowed_files"],
                "forbidden_files": lane["forbidden_files"],
                "proof_commands": lane["proof_commands"],
                "handoff_template": lane["handoff_template"],
                "worktree_commands": [
                    "git fetch origin",
                    f"git worktree add {worktree} -b {branch} origin/{orchestration['target_branch']}"
                    if worktree
                    else "read-only multi-repo review",
                ],
                "handoff_required_fields": execution["handoff_schema"]["required_fields"],
            }
        )
    return {
        "generated_at": generated_at,
        "run_id": date_id,
        "goal": goal,
        "workflow_manifest": str(WORKFLOW_MANIFEST.relative_to(ROOT)),
        "execution_manifest": str(EXECUTION_MANIFEST.relative_to(ROOT)),
        "canonical_truth": execution["canonical_truth"],
        "repos": orchestration["repos"],
        "lane_packets": selected_lanes,
        "slash_commands": execution["slash_commands"],
        "background_routines": execution["background_routines"],
        "ci_cd_agent_jobs": execution["ci_cd_agent_jobs"],
        "eval_loops": execution["eval_loops"],
        "agent_supervision": execution["agent_supervision"],
        "proof_boundaries": execution["proof_boundaries"],
        "coordinator_checks": [
            "fetch every repo before merge",
            "run lane proof commands before push",
            "refresh generated artifacts from the final tree",
            "write blocker rows for missing context or failing checks",
            "push main only when explicitly requested and checks pass",
        ],
    }


def _format_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Agentic Execution Plan",
        "",
        f"Generated: {plan['generated_at']}",
        f"Run ID: {plan['run_id']}",
        f"Goal: {plan['goal']}",
        "",
        "## Lane Packets",
        "",
        "| lane | mode | repo | branch | proof commands |",
        "|---|---|---|---|---|",
    ]
    for lane in plan["lane_packets"]:
        commands = "<br>".join(lane["proof_commands"])
        lines.append(
            f"| {lane['id']} | {lane['mode']} | {lane['repo_id']} | {lane['branch']} | {commands} |"
        )
    lines.extend(
        [
            "",
            "## Proof Boundaries",
            "",
        ]
    )
    lines.extend(f"- {boundary}" for boundary in plan["proof_boundaries"])
    lines.extend(
        [
            "",
            "## Coordinator Checks",
            "",
        ]
    )
    lines.extend(f"- {check}" for check in plan["coordinator_checks"])
    lines.append("")
    return "\n".join(lines)


def _load_pair() -> tuple[dict[str, Any], dict[str, Any]]:
    return _read_json(WORKFLOW_MANIFEST), _read_json(EXECUTION_MANIFEST)


def _cmd_validate(_args: argparse.Namespace) -> int:
    workflow, execution = _load_pair()
    errors = validate_execution_manifest(workflow, execution)
    if errors:
        print("Agentic workflow orchestrator: FAIL")
        for error in errors:
            print(f"error: {error}")
        return 1
    print("Agentic workflow orchestrator: PASS")
    print(f"manifest={EXECUTION_MANIFEST.relative_to(ROOT)}")
    print(f"slash_commands={len(execution['slash_commands'])}")
    print(f"lanes={len(execution['parallel_agent_lanes'])}")
    print(f"routines={len(execution['background_routines'])}")
    print(f"eval_loops={len(execution['eval_loops'])}")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    workflow, execution = _load_pair()
    errors = validate_execution_manifest(workflow, execution)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    plan = build_plan(
        workflow=workflow,
        execution=execution,
        goal=args.goal,
        repo_filter=args.repo,
        run_id=args.run_id,
    )
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def _cmd_emit(args: argparse.Namespace) -> int:
    workflow, execution = _load_pair()
    errors = validate_execution_manifest(workflow, execution)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    plan = build_plan(
        workflow=workflow,
        execution=execution,
        goal=args.goal,
        repo_filter=args.repo,
        run_id=args.run_id,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / "agentic_execution_plan.json"
    md_path = out_dir / "agentic_execution_plan.md"
    _write_json(json_path, plan)
    _write_text(md_path, _format_plan_markdown(plan))
    print(json_path)
    print(md_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agentic_workflow_orchestrator",
        description="Validate and emit AI Development OS agentic execution lane packets.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate workflow and execution manifests")
    validate.set_defaults(func=_cmd_validate)

    plan = sub.add_parser("plan", help="Print a machine-readable execution plan")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--repo", default="", help="Optional repo_id filter")
    plan.add_argument("--run-id", default="", help="Stable run id used in branch names")
    plan.set_defaults(func=_cmd_plan)

    emit = sub.add_parser("emit", help="Write JSON and Markdown execution plans")
    emit.add_argument("--goal", required=True)
    emit.add_argument("--repo", default="", help="Optional repo_id filter")
    emit.add_argument("--run-id", default="", help="Stable run id used in branch names")
    emit.add_argument("--out-dir", default="system_review_graph")
    emit.set_defaults(func=_cmd_emit)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
