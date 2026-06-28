"""Validate and emit AI Development OS prompt-to-product automation packets."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_MANIFEST = ROOT / "manifests" / "agentic_workflow_manifest.json"
EXECUTION_MANIFEST = ROOT / "manifests" / "agentic_execution_manifest.json"
INTERNAL_REPO_REGISTRY = ROOT / "manifests" / "internal_repo_registry.json"
RESEARCH_DATA_ROUTER = ROOT / "manifests" / "research_data_router.json"
DEVELOPMENT_STRATEGY_ROUTER = ROOT / "manifests" / "development_strategy_router.json"

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
    "external_harnesses",
}
REQUIRED_COMMANDS = {
    "/ados:normalize",
    "/ados:context-bundle",
    "/ados:repo-intake",
    "/ados:research-plan",
    "/ados:strategy-plan",
    "/ados:harness-intake",
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
    "startup_continuation_sweep",
    "vc_pitch_readiness_sweep",
    "board_go_live_readiness_sweep",
    "external_harness_safety_check",
    "nightly_eval_loop",
    "ci_failure_triage",
}
REQUIRED_EVALS = {
    "lane_packet_completeness",
    "contract_section_coverage",
    "branch_freshness",
    "handoff_completeness",
    "ready_with_external_gates_continuation",
    "vc_pitch_readiness",
    "board_go_live_readiness",
    "external_harness_boundary",
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
        "repo-intake",
        "research-plan",
        "strategy-plan",
        "harness-intake",
    }
    missing_runtime = sorted(required_runtime - set(runtime_commands))
    if missing_runtime:
        errors.append(f"automation runtime missing commands: {', '.join(missing_runtime)}")

    harnesses = _ids(execution.get("external_harnesses", []))
    if "ecc" not in harnesses:
        errors.append("execution manifest must include ecc in external_harnesses")
    for harness in execution.get("external_harnesses", []):
        harness_id = str(harness.get("id") or "<missing>")
        if not harness.get("source_url"):
            errors.append(f"external harness {harness_id} must define source_url")
        if not harness.get("license"):
            errors.append(f"external harness {harness_id} must define license")
        if "observe" not in harness.get("integration_modes", []):
            errors.append(f"external harness {harness_id} must support observe mode")
        if not harness.get("blocked_effects"):
            errors.append(f"external harness {harness_id} must define blocked_effects")

    return errors


def validate_support_manifests(
    registry: dict[str, Any], research_router: dict[str, Any], strategy_router: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    repo_ids = _ids(registry.get("repos", []))
    required_repos = {"ai-development-os", "system-review-graph", "code-review-graph", "intelligence-hub"}
    missing_repos = sorted(required_repos - repo_ids)
    if missing_repos:
        errors.append(f"internal repo registry missing repos: {', '.join(missing_repos)}")
    research_ids = _ids(research_router.get("research_depths", []))
    data_ids = _ids(research_router.get("data_routes", []))
    if "R0_MODEL_PRIOR" not in research_ids or "R5_EXPERT_OR_USER_VALIDATION" not in research_ids:
        errors.append("research router must include model-prior and expert-validation depths")
    if "D1_NORMAL_WEB_SEARCH" not in data_ids or "D4_HUMAN_EXPERT_OR_USER" not in data_ids:
        errors.append("research router must include normal web and human expert data routes")
    mode_ids = _ids(strategy_router.get("development_modes", []))
    required_modes = {
        "M0_SOFTWARE_LOCAL",
        "M1_DATA_API_PRODUCT",
        "M2_AI_ML_PRODUCT",
        "M3_REGULATED_OR_HIGH_STAKES",
        "M4_HARDWARE_MANUFACTURING",
        "M5_CROSS_BORDER_SUPPLY_CHAIN",
        "M6_COMMERCIAL_CONTRACT_DEPENDENT",
    }
    missing_modes = sorted(required_modes - mode_ids)
    if missing_modes:
        errors.append(f"development strategy router missing modes: {', '.join(missing_modes)}")
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
        "external_harness_safety_check": [
            "python3 scripts/agentic_workflow_orchestrator.py harness-intake "
            "--harness ecc --install-mode observe --target-repo ai-development-os "
            "--out-dir system_review_graph",
            "python3 scripts/workflow_manifest_check.py",
            "python3 scripts/agentic_workflow_orchestrator.py validate",
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


def build_repo_intake_packet(
    registry: dict[str, Any], *, idea_source: str = "intelligence-hub", target_repo: str = ""
) -> dict[str, Any]:
    repos = _rows_by_id(registry.get("repos", []))
    source = repos.get(idea_source)
    target = repos.get(target_repo) if target_repo else repos.get("future-product-repo")
    blockers = []
    if source is None:
        blockers.append(
            {
                "id": f"repo-intake:{idea_source}:unknown-source",
                "module": "internal_repo_registry",
                "issue": "idea source repo is not registered",
                "owner": "workflow-coordinator",
                "evidence": str(INTERNAL_REPO_REGISTRY.relative_to(ROOT)),
                "gate": "closed",
                "next_valid_move": "Add the repo to the internal registry or select a registered idea source.",
                "unsafe_to_bypass": True,
            }
        )
    if target is None:
        blockers.append(
            {
                "id": f"repo-intake:{target_repo}:unknown-target",
                "module": "internal_repo_registry",
                "issue": "target repo is not registered",
                "owner": "workflow-coordinator",
                "evidence": str(INTERNAL_REPO_REGISTRY.relative_to(ROOT)),
                "gate": "closed",
                "next_valid_move": "Add the target repo or use future-product-repo until created.",
                "unsafe_to_bypass": True,
            }
        )
    return {
        "generated_at": _now(),
        "kind": "internal_repo_intake",
        "idea_source": source or {"id": idea_source, "status": "unknown"},
        "target_repo": target or {"id": target_repo, "status": "unknown"},
        "repo_groups": registry.get("repo_groups", []),
        "intake_rules": registry.get("intake_rules", []),
        "status": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "next_valid_move": (
            "Load source idea packet, select product target repo, then emit lane packet."
            if not blockers
            else "Resolve repo intake blockers before assigning implementation lanes."
        ),
    }


def _route_research(problem: str, domain: str = "", data_need: str = "") -> tuple[list[str], list[str]]:
    text = " ".join([problem, domain, data_need]).lower()
    research = ["R0_MODEL_PRIOR"]
    data_routes = ["D0_NO_EXTERNAL_DATA"]
    if any(term in text for term in ["latest", "current", "today", "competitor", "market", "web"]):
        research.append("R1_NORMAL_WEB_SCAN")
        data_routes.append("D1_NORMAL_WEB_SEARCH")
    if any(
        term in text
        for term in [
            "api",
            "sdk",
            "law",
            "legal",
            "standard",
            "regulation",
            "pricing",
            "official",
            "country",
            "import",
            "export",
            "tariff",
            "customs",
            "certification",
        ]
    ):
        research.append("R2_OFFICIAL_SOURCE_REVIEW")
        data_routes.append("D2_PRIMARY_OFFICIAL_SOURCE")
    if any(
        term in text
        for term in [
            "dataset",
            "data",
            "database",
            "feed",
            "credential",
            "fresh",
            "rate limit",
            "paid",
            "supplier",
            "manufacturer",
            "tariff",
            "logistics",
        ]
    ):
        research.append("R3_STRUCTURED_DATA_REQUIRED")
        data_routes.append("D3_DATASET_OR_API")
    if any(term in text for term in ["ambiguous", "unknown", "feasibility", "deep", "manufacturing", "supply", "import", "export"]):
        research.append("R4_DEEP_RESEARCH")
    if any(
        term in text
        for term in [
            "medical",
            "clinical",
            "finance",
            "trading",
            "legal",
            "safety",
            "expert",
            "buyer",
            "manufacturing",
            "import",
            "export",
            "contract",
            "country",
        ]
    ):
        research.append("R5_EXPERT_OR_USER_VALIDATION")
        data_routes.append("D4_HUMAN_EXPERT_OR_USER")
    return list(dict.fromkeys(research)), list(dict.fromkeys(data_routes))


def build_research_plan(
    router: dict[str, Any], *, problem: str, domain: str = "", data_need: str = ""
) -> dict[str, Any]:
    research_ids, data_route_ids = _route_research(problem, domain, data_need)
    research_by_id = _rows_by_id(router.get("research_depths", []))
    data_by_id = _rows_by_id(router.get("data_routes", []))
    research_rows = [research_by_id[item] for item in research_ids if item in research_by_id]
    data_rows = [data_by_id[item] for item in data_route_ids if item in data_by_id]
    blockers = []
    for row in research_rows:
        if row.get("id") in {"R3_STRUCTURED_DATA_REQUIRED", "R5_EXPERT_OR_USER_VALIDATION"}:
            blockers.append(
                {
                    "id": f"research:{row['id'].lower()}:external-input",
                    "module": "research_data_router",
                    "issue": "external data or human validation is required before final product claims",
                    "owner": "research",
                    "evidence": str(RESEARCH_DATA_ROUTER.relative_to(ROOT)),
                    "gate": "closed",
                    "next_valid_move": "Create the source/expert plan and collect dated evidence.",
                    "unsafe_to_bypass": True,
                }
            )
    return {
        "generated_at": _now(),
        "kind": "research_data_plan",
        "problem": problem,
        "domain": domain,
        "data_need": data_need,
        "research_depths": research_rows,
        "data_routes": data_rows,
        "routing_rules": router.get("routing_rules", []),
        "expert_validation_rule": router.get("expert_validation_rule", ""),
        "blockers": blockers,
        "status": "ready_with_external_gates" if blockers else "ready",
        "next_valid_move": (
            "Run model-prior synthesis, then collect the listed external evidence before final claims."
            if blockers
            else "Proceed with model-prior synthesis and local proof loop."
        ),
    }


def _route_strategy(idea: str, field: str = "", country: str = "") -> list[str]:
    text = " ".join([idea, field, country]).lower()
    tokens = set(re.findall(r"[a-z0-9]+", text))
    modes = []
    if any(term in text for term in ["manufacturing", "factory", "hardware", "device", "bom", "supplier"]):
        modes.append("M4_HARDWARE_MANUFACTURING")
    if any(term in text for term in ["import", "export", "country", "tariff", "customs", "logistics"]):
        modes.append("M5_CROSS_BORDER_SUPPLY_CHAIN")
    if any(term in text for term in ["contract", "license", "partner", "sla", "manufacturer agreement"]):
        modes.append("M6_COMMERCIAL_CONTRACT_DEPENDENT")
    if any(term in text for term in ["medical", "legal", "finance", "trading", "safety", "regulated"]):
        modes.append("M3_REGULATED_OR_HIGH_STAKES")
    if any(term in text for term in ["model", "retrieval", "training", "evaluation"]) or tokens.intersection(
        {"ai", "ml", "llm"}
    ):
        modes.append("M2_AI_ML_PRODUCT")
    if any(term in text for term in ["data", "api", "feed", "database", "credential"]):
        modes.append("M1_DATA_API_PRODUCT")
    if not modes:
        modes.append("M0_SOFTWARE_LOCAL")
    return list(dict.fromkeys(modes))


def build_strategy_plan(
    strategy_router: dict[str, Any], *, idea: str, field: str = "", country: str = ""
) -> dict[str, Any]:
    mode_ids = _route_strategy(idea, field, country)
    modes_by_id = _rows_by_id(strategy_router.get("development_modes", []))
    modes = [modes_by_id[item] for item in mode_ids if item in modes_by_id]
    playbooks = [
        row
        for row in strategy_router.get("field_playbooks", [])
        if row.get("default_mode") in mode_ids or (field and row.get("field") == field)
    ]
    external_blockers = []
    for mode in modes:
        if mode.get("external_inputs"):
            external_blockers.append(
                {
                    "id": f"strategy:{mode['id'].lower()}:external-inputs",
                    "module": "development_strategy_router",
                    "issue": "development mode needs external inputs before final readiness",
                    "owner": "architect",
                    "evidence": str(DEVELOPMENT_STRATEGY_ROUTER.relative_to(ROOT)),
                    "gate": "closed",
                    "next_valid_move": f"Collect or block: {', '.join(mode['external_inputs'])}",
                    "unsafe_to_bypass": True,
                }
            )
    return {
        "generated_at": _now(),
        "kind": "development_strategy_plan",
        "idea": idea,
        "field": field,
        "country": country,
        "modes": modes,
        "field_playbooks": playbooks,
        "country_requirements_template": strategy_router.get("country_requirements_template", {}),
        "external_contract_template": strategy_router.get("external_contract_template", {}),
        "blockers": external_blockers,
        "status": "ready_with_external_gates" if external_blockers else "ready",
        "next_valid_move": (
            "Assign agents by mode, collect external inputs, and keep final claims blocked until evidence exists."
            if external_blockers
            else "Proceed with software-local proof loop."
        ),
    }


def build_harness_intake_packet(
    *,
    workflow: dict[str, Any],
    execution: dict[str, Any],
    harness_id: str,
    install_mode: str = "observe",
    target_repo: str = "",
    goal: str = "",
) -> dict[str, Any]:
    harnesses = _rows_by_id(execution.get("external_harnesses", []))
    workflow_rule = workflow.get("external_harness_integration") or {}
    workflow_harnesses = _rows_by_id(workflow_rule.get("known_harnesses", []))
    workflow_harness = workflow_harnesses.get(harness_id, {})
    harness = harnesses.get(harness_id) or workflow_harness
    blockers = []
    if harness is None:
        blockers.append(
            {
                "id": f"harness:{harness_id}:unknown",
                "module": "external_harness_integration",
                "issue": "external harness is not registered in the execution manifest",
                "owner": "workflow-coordinator",
                "evidence": str(EXECUTION_MANIFEST.relative_to(ROOT)),
                "gate": "closed",
                "next_valid_move": "Add the harness to external_harnesses or select a registered harness.",
                "unsafe_to_bypass": True,
            }
        )
        harness = {"id": harness_id, "status": "unknown"}
    integration_modes = set(harness.get("integration_modes", workflow_rule.get("integration_modes", [])))
    if install_mode not in integration_modes:
        blockers.append(
            {
                "id": f"harness:{harness_id}:unsupported-mode",
                "module": "external_harness_integration",
                "issue": "requested install mode is not registered for this harness",
                "owner": "workflow-coordinator",
                "evidence": str(EXECUTION_MANIFEST.relative_to(ROOT)),
                "gate": "closed",
                "next_valid_move": f"Use one of: {', '.join(sorted(integration_modes))}.",
                "unsafe_to_bypass": True,
            }
        )
    if install_mode != "observe":
        blockers.append(
            {
                "id": f"harness:{harness_id}:operator-install-approval",
                "module": "external_harness_integration",
                "issue": "installing or copying an external harness surface requires explicit operator approval and security scan proof",
                "owner": "operator",
                "evidence": "docs/EXTERNAL_AGENT_HARNESS_INTEGRATION.md",
                "gate": "closed",
                "next_valid_move": "Get explicit scoped approval, record exact version, check duplicate hooks/plugins, and run config/security scan.",
                "unsafe_to_bypass": True,
            }
        )
    blocked_effects = list(harness.get("blocked_effects", [])) or [
        "push",
        "publish",
        "deploy",
        "paid_api",
        "credential_change",
        "third_party_mutation",
        "legal_or_commercial_claim",
    ]
    blocked_claims = list(workflow_rule.get("blocked_claims", [])) or [
        "fully_operational",
        "launch_ready",
        "commercially_ready",
    ]
    return {
        "generated_at": _now(),
        "kind": "external_harness_integration_packet",
        "harness": harness,
        "target_repo": target_repo,
        "goal": goal,
        "install_mode": install_mode,
        "status": "ready_for_observation" if not blockers else "ready_with_operator_or_config_gates",
        "adopted_patterns": harness.get("usable_patterns", []),
        "command_mapping": harness.get("command_mapping", []),
        "adoption_gates": harness.get("adoption_gates", workflow_harness.get("adoption_gates", [])),
        "blocked_effects": blocked_effects,
        "blocked_claims": blocked_claims,
        "blockers": blockers,
        "proof_commands": [
            "python3 scripts/workflow_manifest_check.py",
            "python3 scripts/agentic_workflow_orchestrator.py validate",
            "python3 scripts/agentic_workflow_orchestrator.py automation-check",
            "python3 scripts/ai_dev_os_check.py",
            "python3 scripts/self_test_flow.py",
        ],
        "next_valid_move": (
            "Use the mapped harness patterns as optional accelerators while running ADOS proof commands."
            if install_mode == "observe"
            else "Resolve operator install approval and security scan blockers before relying on the harness."
        ),
        "proof_boundary": (
            "External harness packets are coordination surfaces. Source files, tests, generated artifacts, "
            "GitHub history, blocker ledgers, and required human approvals prove completion."
        ),
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
    *,
    workflow: dict[str, Any],
    execution: dict[str, Any],
    registry: dict[str, Any],
    research_router: dict[str, Any],
    strategy_router: dict[str, Any],
    name: str,
    idea: str,
    field: str = "",
    country: str = "",
    idea_source: str = "intelligence-hub",
    target_repo: str = "",
) -> dict[str, Any]:
    complexity = _estimate_complexity(idea)
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-{_slug(name)}"
    plan = build_plan(workflow=workflow, execution=execution, goal=idea, run_id=run_id)
    research_plan = build_research_plan(
        research_router,
        problem=idea,
        domain=field,
        data_need="",
    )
    strategy_plan = build_strategy_plan(
        strategy_router,
        idea=idea,
        field=field,
        country=country,
    )
    repo_intake = build_repo_intake_packet(
        registry,
        idea_source=idea_source,
        target_repo=target_repo,
    )
    return {
        "generated_at": _now(),
        "kind": "prompt_to_product_packet",
        "product": {"name": name, "idea": idea, "complexity": complexity},
        "repo_intake": repo_intake,
        "research_data_plan": research_plan,
        "development_strategy_plan": strategy_plan,
        "normalized_contract": {
            "goal": idea,
            "constraints": [
                "Use repo truth over chat memory.",
                "Keep unsafe, paid, legal, live, or external effects closed by default.",
                "Produce code/data/tests/generated artifacts or a blocker row.",
                "Treat AI model subject expertise as a first-pass hypothesis until external evidence or experts validate high-impact claims.",
            ],
            "evidence_required": [
                "git branch/status proof",
                "system review graph or context bundle",
                "code-review graph contract when source scope is broad",
                "research/data plan with source, data, and expert gates",
                "development strategy plan for the product field",
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
            "/ados:repo-intake",
            "/ados:research-plan",
            "/ados:strategy-plan",
            "/ados:harness-intake",
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


def _load_all() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        _read_json(WORKFLOW_MANIFEST),
        _read_json(EXECUTION_MANIFEST),
        _read_json(INTERNAL_REPO_REGISTRY),
        _read_json(RESEARCH_DATA_ROUTER),
        _read_json(DEVELOPMENT_STRATEGY_ROUTER),
    )


def _cmd_validate(_args: argparse.Namespace) -> int:
    workflow, execution, registry, research_router, strategy_router = _load_all()
    errors = validate_execution_manifest(workflow, execution)
    errors.extend(validate_support_manifests(registry, research_router, strategy_router))
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
    workflow, execution, registry, research_router, strategy_router = _load_all()
    errors = validate_execution_manifest(workflow, execution)
    errors.extend(validate_support_manifests(registry, research_router, strategy_router))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    packet = build_prompt_to_product_packet(
        workflow=workflow,
        execution=execution,
        registry=registry,
        research_router=research_router,
        strategy_router=strategy_router,
        name=args.name,
        idea=args.idea,
        field=args.field,
        country=args.country,
        idea_source=args.idea_source,
        target_repo=args.target_repo,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / "prompt_to_product_packet.json"
    md_path = out_dir / "prompt_to_product_packet.md"
    _write_json(json_path, packet)
    _write_text(md_path, _format_key_value_markdown("Prompt To Product Packet", packet))
    print(json_path)
    print(md_path)
    return 0


def _cmd_repo_intake(args: argparse.Namespace) -> int:
    registry = _read_json(INTERNAL_REPO_REGISTRY)
    packet = build_repo_intake_packet(
        registry,
        idea_source=args.idea_source,
        target_repo=args.target_repo,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / "internal_repo_intake_packet.json"
    md_path = out_dir / "internal_repo_intake_packet.md"
    _write_json(json_path, packet)
    _write_text(md_path, _format_key_value_markdown("Internal Repo Intake Packet", packet))
    print(json_path)
    print(md_path)
    return 0 if packet["status"] == "ready" else 1


def _cmd_research_plan(args: argparse.Namespace) -> int:
    router = _read_json(RESEARCH_DATA_ROUTER)
    plan = build_research_plan(
        router,
        problem=args.problem,
        domain=args.domain,
        data_need=args.data_need,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / "research_data_plan.json"
    md_path = out_dir / "research_data_plan.md"
    _write_json(json_path, plan)
    _write_text(md_path, _format_key_value_markdown("Research Data Plan", plan))
    print(json_path)
    print(md_path)
    return 0


def _cmd_strategy_plan(args: argparse.Namespace) -> int:
    router = _read_json(DEVELOPMENT_STRATEGY_ROUTER)
    plan = build_strategy_plan(
        router,
        idea=args.idea,
        field=args.field,
        country=args.country,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / "development_strategy_plan.json"
    md_path = out_dir / "development_strategy_plan.md"
    _write_json(json_path, plan)
    _write_text(md_path, _format_key_value_markdown("Development Strategy Plan", plan))
    print(json_path)
    print(md_path)
    return 0


def _cmd_harness_intake(args: argparse.Namespace) -> int:
    workflow, execution = _load_pair()
    packet = build_harness_intake_packet(
        workflow=workflow,
        execution=execution,
        harness_id=args.harness,
        install_mode=args.install_mode,
        target_repo=args.target_repo,
        goal=args.goal,
    )
    out_dir = Path(args.out_dir)
    json_path = out_dir / "external_harness_integration_packet.json"
    md_path = out_dir / "external_harness_integration_packet.md"
    _write_json(json_path, packet)
    _write_text(md_path, _format_key_value_markdown("External Harness Integration Packet", packet))
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
    workflow, execution, registry, research_router, strategy_router = _load_all()
    errors = validate_execution_manifest(workflow, execution)
    errors.extend(validate_support_manifests(registry, research_router, strategy_router))
    if errors:
        print("Automation check: FAIL")
        for error in errors:
            print(f"error: {error}")
        return 1
    packet = build_prompt_to_product_packet(
        workflow=workflow,
        execution=execution,
        registry=registry,
        research_router=research_router,
        strategy_router=strategy_router,
        name="smoke",
        idea="Build a small local app with proof gates.",
    )
    specs = build_slash_command_specs(execution)
    routines = build_routine_report(execution)
    scheduler = build_scheduler_plan(execution)
    ci_fix = build_ci_fix_packet(execution=execution, check_name="workflow_manifest_ci")
    repo_intake = build_repo_intake_packet(registry, idea_source="intelligence-hub")
    research_plan = build_research_plan(
        research_router,
        problem="Manufacturing product with import/export country requirements and data sources.",
        domain="manufacturing",
    )
    strategy_plan = build_strategy_plan(
        strategy_router,
        idea="Manufacturing product with import/export country requirements.",
        field="manufacturing",
        country="US",
    )
    harness_packet = build_harness_intake_packet(
        workflow=workflow,
        execution=execution,
        harness_id="ecc",
        install_mode="observe",
        target_repo="ai-development-os",
        goal="Evaluate optional same-day product harness patterns.",
    )
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
    if repo_intake["status"] != "ready":
        print("Automation check: FAIL")
        print("error: repo intake packet is blocked")
        return 1
    if "R5_EXPERT_OR_USER_VALIDATION" not in [row["id"] for row in research_plan["research_depths"]]:
        print("Automation check: FAIL")
        print("error: manufacturing/import/export route must include expert validation")
        return 1
    if "M4_HARDWARE_MANUFACTURING" not in [row["id"] for row in strategy_plan["modes"]]:
        print("Automation check: FAIL")
        print("error: manufacturing strategy mode missing")
        return 1
    if harness_packet["status"] != "ready_for_observation":
        print("Automation check: FAIL")
        print("error: harness intake packet should be ready for observation")
        return 1
    if "push" not in harness_packet["blocked_effects"]:
        print("Automation check: FAIL")
        print("error: harness packet must keep push blocked")
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
    prompt_to_product.add_argument("--field", default="")
    prompt_to_product.add_argument("--country", default="")
    prompt_to_product.add_argument("--idea-source", default="intelligence-hub")
    prompt_to_product.add_argument("--target-repo", default="")
    prompt_to_product.add_argument("--out-dir", default="system_review_graph")
    prompt_to_product.set_defaults(func=_cmd_prompt_to_product)

    repo_intake = sub.add_parser("repo-intake", help="Write internal repo intake packet")
    repo_intake.add_argument("--idea-source", default="intelligence-hub")
    repo_intake.add_argument("--target-repo", default="")
    repo_intake.add_argument("--out-dir", default="system_review_graph")
    repo_intake.set_defaults(func=_cmd_repo_intake)

    research_plan = sub.add_parser("research-plan", help="Write research and data routing plan")
    research_plan.add_argument("--problem", required=True)
    research_plan.add_argument("--domain", default="")
    research_plan.add_argument("--data-need", default="")
    research_plan.add_argument("--out-dir", default="system_review_graph")
    research_plan.set_defaults(func=_cmd_research_plan)

    strategy_plan = sub.add_parser("strategy-plan", help="Write field-specific development strategy plan")
    strategy_plan.add_argument("--idea", required=True)
    strategy_plan.add_argument("--field", default="")
    strategy_plan.add_argument("--country", default="")
    strategy_plan.add_argument("--out-dir", default="system_review_graph")
    strategy_plan.set_defaults(func=_cmd_strategy_plan)

    harness_intake = sub.add_parser("harness-intake", help="Write external harness integration packet")
    harness_intake.add_argument("--harness", default="ecc")
    harness_intake.add_argument("--install-mode", default="observe")
    harness_intake.add_argument("--target-repo", default="")
    harness_intake.add_argument("--goal", default="")
    harness_intake.add_argument("--out-dir", default="system_review_graph")
    harness_intake.set_defaults(func=_cmd_harness_intake)

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
