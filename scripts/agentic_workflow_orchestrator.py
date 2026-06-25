"""Validate and emit AI Development OS prompt-to-product automation packets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

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
    "automation_runtime",
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


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slug(text: str) -> str:
    lowered = text.strip().lower()
    chars = [char if char.isalnum() else "-" for char in lowered]
    compact = "-".join(part for part in "".join(chars).split("-") if part)
    return compact[:80] or "run"


def _rows_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows}


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

    runtime = execution.get("automation_runtime") or {}
    runtime_commands = runtime.get("commands") or {}
    required_runtime = {
        "prompt-to-product",
        "emit-slash-commands",
        "lane-packet",
        "routine-report",
        "scheduler-plan",
        "ci-fix",
        "automation-check",
    }
    missing_runtime = sorted(required_runtime - set(runtime_commands))
    if missing_runtime:
        errors.append(f"automation runtime missing commands: {', '.join(missing_runtime)}")

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
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    date_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d")
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
        "automation_runtime": execution["automation_runtime"],
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


def build_slash_command_specs(execution: dict[str, Any]) -> dict[str, Any]:
    specs = []
    for command in execution["slash_commands"]:
        specs.append(
            {
                "id": command["id"],
                "command": command["command"],
                "mode": command["mode"],
                "purpose": command["purpose"],
                "required_inputs": command["required_inputs"],
                "outputs": command["outputs"],
                "proof_gates": command["proof_gates"],
                "runner": {
                    "script": "scripts/agentic_workflow_orchestrator.py",
                    "dry_run_default": True,
                    "materialize_command": (
                        "python3 scripts/agentic_workflow_orchestrator.py command-spec "
                        f"--command {command['id']}"
                    ),
                },
            }
        )
    return {
        "generated_at": _now(),
        "kind": "slash_command_specs",
        "count": len(specs),
        "specs": specs,
        "proof_boundary": (
            "Slash command specs materialize bounded packets. They do not execute "
            "external or unsafe actions without a separate proof gate."
        ),
    }


def build_command_spec(
    execution: dict[str, Any], command_key: str, inputs: dict[str, str]
) -> dict[str, Any]:
    commands = {
        str(row["id"]): row for row in execution["slash_commands"]
    } | {
        str(row["command"]): row for row in execution["slash_commands"]
    }
    if command_key not in commands:
        available = ", ".join(sorted(commands))
        raise ValueError(f"unknown command {command_key!r}; available: {available}")
    command = commands[command_key]
    missing = [name for name in command["required_inputs"] if name not in inputs]
    return {
        "generated_at": _now(),
        "kind": "slash_command_packet",
        "command": command,
        "provided_inputs": inputs,
        "missing_inputs": missing,
        "status": "ready" if not missing else "needs_input",
        "next_valid_move": (
            "Run the command with the provided inputs and write declared outputs."
            if not missing
            else f"Provide missing inputs: {', '.join(missing)}"
        ),
        "proof_boundary": (
            "This packet is an execution contract. Source files, tests, generated "
            "artifacts, and GitHub state prove completion."
        ),
    }


def build_lane_packet(
    *, workflow: dict[str, Any], execution: dict[str, Any], lane_id: str, goal: str
) -> dict[str, Any]:
    plan = build_plan(workflow=workflow, execution=execution, goal=goal)
    lanes = _rows_by_id(plan["lane_packets"])
    if lane_id not in lanes:
        available = ", ".join(sorted(lanes))
        raise ValueError(f"unknown lane {lane_id!r}; available: {available}")
    lane = lanes[lane_id]
    return {
        "generated_at": _now(),
        "kind": "lane_packet",
        "goal": goal,
        "lane": lane,
        "worker_prompt": (
            "Read AGENTS.md and the lane packet. Work only inside allowed_files, "
            "avoid forbidden_files, run proof_commands, refresh generated artifacts "
            "when applicable, and write a handoff or blocker row."
        ),
        "handoff_required_fields": lane["handoff_required_fields"],
        "unsafe_or_external_gates": "closed unless explicit user intent and repo proof open them",
    }


def _routine_commands(routine_id: str) -> list[str]:
    mapping = {
        "branch_freshness_check": [
            "git fetch origin --prune",
            "git status --short --branch",
            "git merge-base --is-ancestor origin/main HEAD",
        ],
        "context_bundle_refresh": [
            "system-review-graph load-repo-context-bundle "
            "--manifest ${SRG_MANIFEST} "
            "--code-review-graph ${CODE_REVIEW_GRAPH_CONTRACT} "
            "--agentic-workflow manifests/agentic_execution_manifest.json"
        ],
        "stale_blocker_sweep": [
            "python3 scripts/blocker_ledger.py validate "
            "--input system_review_graph/blockers.jsonl --allow-missing"
        ],
        "nightly_eval_loop": [
            "python3 scripts/eval_suite.py --manifest manifests/agentic_execution_manifest.json "
            "--out system_review_graph/eval_report.json"
        ],
        "ci_failure_triage": [
            "python3 scripts/agentic_workflow_orchestrator.py ci-fix "
            "--check-name ${CHECK_NAME} --failure-log ${FAILURE_LOG} "
            "--out-dir handoffs"
        ],
    }
    return mapping.get(routine_id, [])


def _routine_missing_inputs(routine_id: str) -> list[str]:
    mapping = {
        "context_bundle_refresh": ["SRG_MANIFEST", "CODE_REVIEW_GRAPH_CONTRACT"],
        "ci_failure_triage": ["CHECK_NAME", "FAILURE_LOG"],
    }
    return mapping.get(routine_id, [])


def build_routine_report(execution: dict[str, Any], routine_id: str = "") -> dict[str, Any]:
    routines = execution["background_routines"]
    if routine_id:
        routines_by_id = _rows_by_id(routines)
        if routine_id not in routines_by_id:
            available = ", ".join(sorted(routines_by_id))
            raise ValueError(f"unknown routine {routine_id!r}; available: {available}")
        routines = [routines_by_id[routine_id]]
    rows = []
    blockers = []
    for routine in routines:
        commands = _routine_commands(str(routine["id"]))
        missing_inputs = _routine_missing_inputs(str(routine["id"]))
        status = "ready" if not missing_inputs else "needs_input"
        row = {
            "id": routine["id"],
            "cadence": routine["cadence"],
            "trigger": routine["trigger"],
            "allowed_effects": routine["allowed_effects"],
            "prohibited_effects": routine["prohibited_effects"],
            "commands": commands,
            "status": status,
            "missing_inputs": missing_inputs,
            "proof_output": routine["proof_output"],
            "dry_run_default": True,
        }
        rows.append(row)
        if missing_inputs:
            blockers.append(
                {
                    "id": f"routine:{routine['id']}:missing-inputs",
                    "module": "automation_runtime",
                    "issue": "routine needs runtime inputs before execution",
                    "owner": routine["id"],
                    "evidence": "manifests/agentic_execution_manifest.json",
                    "gate": "closed",
                    "next_valid_move": f"Provide {', '.join(missing_inputs)}.",
                    "unsafe_to_bypass": True,
                }
            )
    return {
        "generated_at": _now(),
        "kind": "background_routine_report",
        "status": "ready" if not blockers else "ready_with_input_blockers",
        "routine_count": len(rows),
        "routines": rows,
        "blockers": blockers,
        "proof_boundary": (
            "Routine reports describe safe commands and blockers. Effectful "
            "execution still requires explicit operator intent."
        ),
    }


def build_scheduler_plan(execution: dict[str, Any]) -> dict[str, Any]:
    schedule = []
    for routine in execution["background_routines"]:
        schedule.append(
            {
                "id": routine["id"],
                "cadence": routine["cadence"],
                "trigger": routine["trigger"],
                "command": (
                    "python3 scripts/agentic_workflow_orchestrator.py routine-report "
                    f"--routine {routine['id']} --out-dir system_review_graph"
                ),
                "effectful": False,
                "proof_output": routine["proof_output"],
            }
        )
    return {
        "generated_at": _now(),
        "kind": "scheduler_plan",
        "scheduler": "operator, cron, CI, or Codex goal loop can call these commands",
        "entries": schedule,
        "proof_boundary": (
            "This is a scheduler plan, not a daemon. It is safe to commit and "
            "can be handed to an external runner."
        ),
    }


def build_ci_fix_packet(
    *, execution: dict[str, Any], check_name: str, failure_log: str = ""
) -> dict[str, Any]:
    jobs = _rows_by_id(execution["ci_cd_agent_jobs"])
    selected = jobs.get(check_name)
    failure_text = ""
    if failure_log:
        path = Path(failure_log)
        if path.exists():
            failure_text = path.read_text(encoding="utf-8")[:4000]
        else:
            failure_text = failure_log[:4000]
    return {
        "generated_at": _now(),
        "kind": "ci_fix_handoff",
        "check_name": check_name,
        "known_job": selected or {},
        "failure_excerpt": failure_text,
        "lane": {
            "id": f"ci-fix-{_slug(check_name)}",
            "mode": "surgeon",
            "goal": "Fix the failing CI check without weakening proof gates.",
            "allowed_files": [".github/**", "scripts/**", "tests/**", "docs/**"],
            "forbidden_files": ["LICENSE", "NOTICE.md", "CONTRIBUTOR_TERMS.md", "DCO.txt"],
            "proof_commands": (selected or {}).get("commands", ["python3 scripts/ai_dev_os_check.py"]),
        },
        "blocker_schema": execution["handoff_schema"]["blocker_fields"],
        "next_valid_move": "Inspect the failing log, make the smallest fix, run the listed proof commands.",
        "unsafe_or_external_gates": "closed",
    }


def _estimate_complexity(idea: str) -> dict[str, str]:
    text = idea.lower()
    if any(term in text for term in ["hardware", "firmware", "robot", "device", "chip", "os"]):
        return {"level": "S4", "reason": "physical, OS, firmware, or hardware terms present"}
    if any(term in text for term in ["medical", "broker", "trading", "legal", "bank", "regulated"]):
        return {"level": "S5", "reason": "regulated or high-stakes terms present"}
    if any(term in text for term in ["api", "auth", "database", "data", "payment", "source"]):
        return {"level": "S2", "reason": "data, API, credential, or source dependency present"}
    if any(term in text for term in ["saas", "marketplace", "platform", "multi", "team"]):
        return {"level": "S3", "reason": "multi-module or platform terms present"}
    return {"level": "S0/S1", "reason": "small local product terms only"}


def build_prompt_to_product_packet(
    *, workflow: dict[str, Any], execution: dict[str, Any], name: str, idea: str
) -> dict[str, Any]:
    complexity = _estimate_complexity(idea)
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-{_slug(name)}"
    plan = build_plan(workflow=workflow, execution=execution, goal=idea, run_id=run_id)
    return {
        "generated_at": _now(),
        "kind": "prompt_to_product_packet",
        "product": {"name": name, "idea": idea, "complexity": complexity},
        "normalized_contract": {
            "goal": idea,
            "constraints": [
                "Use repo truth over chat memory.",
                "Keep unsafe, paid, legal, live, or external effects closed by default.",
                "Produce code/data/tests/generated artifacts or a blocker row.",
            ],
            "evidence_required": [
                "git branch/status proof",
                "system review graph or context bundle",
                "code-review graph contract when source scope is broad",
                "focused tests or smoke checks",
                "handoff with next_valid_move",
            ],
            "first_action": "Emit lane packet and run the smallest proof loop.",
        },
        "execution_plan": plan,
        "slash_commands": [
            "/ados:normalize",
            "/ados:context-bundle",
            "/ados:lane",
            "/ados:proof",
            "/ados:review",
            "/ados:merge",
            "/ados:goal",
        ],
        "next_valid_move": (
            "Create or select the target repo, load bounded context, claim the "
            "first lane, and run its proof commands."
        ),
    }


def _format_key_value_markdown(title: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )


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


def _cmd_prompt_to_product(args: argparse.Namespace) -> int:
    workflow, execution = _load_pair()
    errors = validate_execution_manifest(workflow, execution)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    packet = build_prompt_to_product_packet(
        workflow=workflow,
        execution=execution,
        name=args.name,
        idea=args.idea,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / "prompt_to_product_packet.json"
    md_path = out_dir / "prompt_to_product_packet.md"
    _write_json(json_path, packet)
    _write_text(md_path, _format_key_value_markdown("Prompt To Product Packet", packet))
    print(json_path)
    print(md_path)
    return 0


def _cmd_command_spec(args: argparse.Namespace) -> int:
    _workflow, execution = _load_pair()
    inputs = {}
    for raw in args.input:
        if "=" not in raw:
            print(f"ERROR: --input expects key=value, got {raw!r}")
            return 2
        key, value = raw.split("=", 1)
        inputs[key] = value
    try:
        packet = build_command_spec(execution, args.command, inputs)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


def _cmd_emit_slash_commands(args: argparse.Namespace) -> int:
    _workflow, execution = _load_pair()
    specs = build_slash_command_specs(execution)
    out_dir = Path(args.out_dir)
    json_path = out_dir / "slash_command_specs.json"
    md_path = out_dir / "slash_command_specs.md"
    _write_json(json_path, specs)
    _write_text(md_path, _format_key_value_markdown("Slash Command Specs", specs))
    print(json_path)
    print(md_path)
    return 0


def _cmd_lane_packet(args: argparse.Namespace) -> int:
    workflow, execution = _load_pair()
    try:
        packet = build_lane_packet(
            workflow=workflow,
            execution=execution,
            lane_id=args.lane,
            goal=args.goal,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    out_dir = Path(args.out_dir)
    json_path = out_dir / f"lane_packet_{_slug(args.lane)}.json"
    md_path = out_dir / f"lane_packet_{_slug(args.lane)}.md"
    _write_json(json_path, packet)
    _write_text(md_path, _format_key_value_markdown("Lane Packet", packet))
    print(json_path)
    print(md_path)
    return 0


def _cmd_routine_report(args: argparse.Namespace) -> int:
    _workflow, execution = _load_pair()
    try:
        report = build_routine_report(execution, args.routine)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    out_dir = Path(args.out_dir)
    json_path = out_dir / "automation_runtime_report.json"
    md_path = out_dir / "automation_runtime_report.md"
    _write_json(json_path, report)
    _write_text(md_path, _format_key_value_markdown("Automation Runtime Report", report))
    print(json_path)
    print(md_path)
    return 0


def _cmd_scheduler_plan(args: argparse.Namespace) -> int:
    _workflow, execution = _load_pair()
    plan = build_scheduler_plan(execution)
    out_dir = Path(args.out_dir)
    json_path = out_dir / "scheduler_plan.json"
    md_path = out_dir / "scheduler_plan.md"
    _write_json(json_path, plan)
    _write_text(md_path, _format_key_value_markdown("Scheduler Plan", plan))
    print(json_path)
    print(md_path)
    return 0


def _cmd_ci_fix(args: argparse.Namespace) -> int:
    _workflow, execution = _load_pair()
    packet = build_ci_fix_packet(
        execution=execution,
        check_name=args.check_name,
        failure_log=args.failure_log,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / f"ci_fix_{_slug(args.check_name)}.json"
    md_path = out_dir / f"ci_fix_{_slug(args.check_name)}.md"
    _write_json(json_path, packet)
    _write_text(md_path, _format_key_value_markdown("CI Fix Handoff", packet))
    print(json_path)
    print(md_path)
    return 0


def _cmd_automation_check(_args: argparse.Namespace) -> int:
    workflow, execution = _load_pair()
    errors = validate_execution_manifest(workflow, execution)
    if errors:
        print("Automation check: FAIL")
        for error in errors:
            print(f"error: {error}")
        return 1
    packet = build_prompt_to_product_packet(
        workflow=workflow,
        execution=execution,
        name="smoke",
        idea="Build a small local app with proof gates.",
    )
    specs = build_slash_command_specs(execution)
    routines = build_routine_report(execution)
    scheduler = build_scheduler_plan(execution)
    ci_fix = build_ci_fix_packet(execution=execution, check_name="workflow_manifest_ci")
    if not packet["execution_plan"]["lane_packets"]:
        print("Automation check: FAIL")
        print("error: prompt-to-product packet has no lanes")
        return 1
    if specs["count"] != len(REQUIRED_COMMANDS):
        print("Automation check: FAIL")
        print("error: slash command specs count mismatch")
        return 1
    if routines["routine_count"] != len(REQUIRED_ROUTINES):
        print("Automation check: FAIL")
        print("error: routine count mismatch")
        return 1
    if len(scheduler["entries"]) != len(REQUIRED_ROUTINES):
        print("Automation check: FAIL")
        print("error: scheduler entries mismatch")
        return 1
    if not ci_fix["lane"]["proof_commands"]:
        print("Automation check: FAIL")
        print("error: ci fix packet has no proof commands")
        return 1
    print("Automation check: PASS")
    print(f"slash_commands={specs['count']}")
    print(f"routines={routines['routine_count']}")
    print(f"lanes={len(packet['execution_plan']['lane_packets'])}")
    print(f"run_id={uuid4().hex[:8]}")
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

    prompt_to_product = sub.add_parser(
        "prompt-to-product",
        help="Write a normalized prompt-to-product packet with lane plan",
    )
    prompt_to_product.add_argument("--name", required=True)
    prompt_to_product.add_argument("--idea", required=True)
    prompt_to_product.add_argument("--out-dir", default="system_review_graph")
    prompt_to_product.set_defaults(func=_cmd_prompt_to_product)

    command_spec = sub.add_parser("command-spec", help="Print one slash command packet")
    command_spec.add_argument("--command", required=True)
    command_spec.add_argument("--input", action="append", default=[], help="key=value input")
    command_spec.set_defaults(func=_cmd_command_spec)

    slash = sub.add_parser("emit-slash-commands", help="Write slash command specs")
    slash.add_argument("--out-dir", default="system_review_graph")
    slash.set_defaults(func=_cmd_emit_slash_commands)

    lane = sub.add_parser("lane-packet", help="Write one bounded lane packet")
    lane.add_argument("--lane", required=True)
    lane.add_argument("--goal", required=True)
    lane.add_argument("--out-dir", default="system_review_graph")
    lane.set_defaults(func=_cmd_lane_packet)

    routine = sub.add_parser("routine-report", help="Write safe background routine report")
    routine.add_argument("--routine", default="", help="Optional routine id")
    routine.add_argument("--out-dir", default="system_review_graph")
    routine.set_defaults(func=_cmd_routine_report)

    scheduler = sub.add_parser("scheduler-plan", help="Write scheduler plan")
    scheduler.add_argument("--out-dir", default="system_review_graph")
    scheduler.set_defaults(func=_cmd_scheduler_plan)

    ci_fix = sub.add_parser("ci-fix", help="Write a CI-fix handoff packet")
    ci_fix.add_argument("--check-name", required=True)
    ci_fix.add_argument("--failure-log", default="")
    ci_fix.add_argument("--out-dir", default="handoffs")
    ci_fix.set_defaults(func=_cmd_ci_fix)

    automation_check = sub.add_parser(
        "automation-check",
        help="Validate runtime packet builders without external side effects",
    )
    automation_check.set_defaults(func=_cmd_automation_check)

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
