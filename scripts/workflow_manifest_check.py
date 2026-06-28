"""Validate the AI Development OS agentic workflow manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifests" / "agentic_workflow_manifest.json"

REQUIRED_TOP_LEVEL = {
    "version",
    "date_checked",
    "name",
    "purpose",
    "execution_manifest",
    "canonical_truth",
    "startup_lifecycle_development_rule",
    "startup_continuation_rule",
    "vc_pitch_readiness_rule",
    "board_go_live_readiness_rule",
    "external_harness_integration",
    "repo_roles",
    "agent_modes",
    "version_control_rules",
    "ruflo_rules",
    "worktree_lifecycle",
    "automation_templates",
    "proof_boundaries",
    "code_review_graph_contract",
    "blocker_schema",
}
REQUIRED_MODES = {"research", "architect", "surgeon", "reviewer", "merge", "goal"}
REQUIRED_CODE_GRAPH_SECTIONS = {
    "files",
    "modules",
    "symbols",
    "imports",
    "edges",
    "tests",
    "generated_artifacts",
    "risk_ownership_hints",
}


def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(manifest))
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")

    modes = {str(mode.get("id")) for mode in manifest.get("agent_modes", [])}
    missing_modes = sorted(REQUIRED_MODES - modes)
    if missing_modes:
        errors.append(f"missing agent modes: {', '.join(missing_modes)}")

    contract = manifest.get("code_review_graph_contract") or {}
    sections = {str(section) for section in contract.get("required_sections", [])}
    missing_sections = sorted(REQUIRED_CODE_GRAPH_SECTIONS - sections)
    if missing_sections:
        errors.append(f"missing code-review graph sections: {', '.join(missing_sections)}")

    ruflo_boundary = str((manifest.get("ruflo_rules") or {}).get("required_boundary") or "")
    if "repo truth" not in ruflo_boundary.lower():
        errors.append("ruflo boundary must say repo truth remains outside Ruflo")

    execution_manifest = manifest.get("execution_manifest") or {}
    execution_path = execution_manifest.get("path")
    if execution_path != "manifests/agentic_execution_manifest.json":
        errors.append("execution_manifest.path must be manifests/agentic_execution_manifest.json")
    elif not (ROOT / execution_path).exists():
        errors.append("execution manifest path does not exist")

    gates = set((manifest.get("blocker_schema") or {}).get("gate_values", []))
    if gates != {"closed", "open", "not_applicable"}:
        errors.append("blocker_schema.gate_values must be closed/open/not_applicable")

    lifecycle = manifest.get("startup_lifecycle_development_rule") or {}
    if lifecycle.get("required_doc") != "docs/STARTUP_LIFECYCLE_DEVELOPMENT.md":
        errors.append("startup_lifecycle_development_rule.required_doc must be docs/STARTUP_LIFECYCLE_DEVELOPMENT.md")
    if lifecycle.get("required_template") != "templates/STARTUP_LIFECYCLE.md":
        errors.append("startup_lifecycle_development_rule.required_template must be templates/STARTUP_LIFECYCLE.md")
    lifecycle_stages = set(lifecycle.get("stage_sequence", []))
    for stage in ("rd_exploration", "operator_evidence", "learning_loop"):
        if stage not in lifecycle_stages:
            errors.append(f"startup_lifecycle_development_rule must include {stage}")
    rd_fields = set(lifecycle.get("r_and_d_loop_fields", []))
    if "hypothesis" not in rd_fields or "next_valid_move" not in rd_fields:
        errors.append("startup_lifecycle_development_rule must define R&D hypothesis and next_valid_move fields")
    if "system_review_graph/operator_screenshot_manifest.json" not in lifecycle.get(
        "operator_evidence_artifacts", []
    ):
        errors.append("startup_lifecycle_development_rule must include operator screenshot manifest")
    if "system_review_graph/operator_workflow_report.json" not in lifecycle.get(
        "operator_evidence_artifacts", []
    ):
        errors.append("startup_lifecycle_development_rule must include operator workflow report")

    continuation = manifest.get("startup_continuation_rule") or {}
    if continuation.get("trigger_status") != "ready_with_external_gates":
        errors.append("startup_continuation_rule.trigger_status must be ready_with_external_gates")
    required_artifact = continuation.get("required_artifact")
    if required_artifact != "system_review_graph/continuation_plan.json":
        errors.append("startup_continuation_rule.required_artifact must be system_review_graph/continuation_plan.json")
    if "fully_operational" not in continuation.get("closed_claims_while_continuing", []):
        errors.append("startup_continuation_rule must close fully_operational claims while continuing")

    pitch_rule = manifest.get("vc_pitch_readiness_rule") or {}
    if pitch_rule.get("required_artifact") != "system_review_graph/vc_pitch_readiness_report.json":
        errors.append("vc_pitch_readiness_rule.required_artifact must be system_review_graph/vc_pitch_readiness_report.json")
    if pitch_rule.get("ready_status") != "vc_pitch_ready_with_diligence_gates":
        errors.append("vc_pitch_readiness_rule.ready_status must be vc_pitch_ready_with_diligence_gates")
    if "revenue_proven" not in pitch_rule.get("closed_claims_without_proof", []):
        errors.append("vc_pitch_readiness_rule must close revenue_proven claims without proof")

    board_rule = manifest.get("board_go_live_readiness_rule") or {}
    if board_rule.get("required_artifact") != "system_review_graph/board_go_live_readiness_report.json":
        errors.append("board_go_live_readiness_rule.required_artifact must be system_review_graph/board_go_live_readiness_report.json")
    if board_rule.get("ready_status") != "board_go_live_candidate_with_human_approval_gates":
        errors.append("board_go_live_readiness_rule.ready_status must be board_go_live_candidate_with_human_approval_gates")
    if "public_launch_ready" not in board_rule.get("closed_claims_without_approval", []):
        errors.append("board_go_live_readiness_rule must close public_launch_ready claims without approval")

    proof_boundaries = manifest.get("proof_boundaries") or {}
    no_scaffold_boundary = str(proof_boundaries.get("no_scaffold_delivery") or "")
    if "scripts/no_scaffold_audit.py --check" not in no_scaffold_boundary:
        errors.append("proof_boundaries.no_scaffold_delivery must require scripts/no_scaffold_audit.py --check")
    if "completion" not in no_scaffold_boundary.lower() or "go-live" not in no_scaffold_boundary.lower():
        errors.append("proof_boundaries.no_scaffold_delivery must block scaffold completion and go-live claims")

    harness_rule = manifest.get("external_harness_integration") or {}
    if harness_rule.get("required_doc") != "docs/EXTERNAL_AGENT_HARNESS_INTEGRATION.md":
        errors.append("external_harness_integration.required_doc must be docs/EXTERNAL_AGENT_HARNESS_INTEGRATION.md")
    if harness_rule.get("packet_artifact") != "system_review_graph/external_harness_integration_packet.json":
        errors.append("external_harness_integration.packet_artifact must be system_review_graph/external_harness_integration_packet.json")
    modes = set(harness_rule.get("integration_modes", []))
    if "observe" not in modes or "project_local_optional" not in modes:
        errors.append("external_harness_integration must include observe and project_local_optional modes")
    harness_ids = {str(row.get("id")) for row in harness_rule.get("known_harnesses", [])}
    if "ecc" not in harness_ids:
        errors.append("external_harness_integration must include the ecc harness record")
    if "fully_operational" not in harness_rule.get("blocked_claims", []):
        errors.append("external_harness_integration must block fully_operational claims")

    return errors


def main() -> int:
    if not MANIFEST.exists():
        print("Workflow manifest check: FAIL")
        print(f"missing: {MANIFEST.relative_to(ROOT)}")
        return 1
    errors = validate_manifest(_load_manifest())
    if errors:
        print("Workflow manifest check: FAIL")
        for error in errors:
            print(f"error: {error}")
        return 1
    print("Workflow manifest check: PASS")
    print(f"manifest={MANIFEST.relative_to(ROOT)}")
    print(f"agent_modes={len(REQUIRED_MODES)}")
    print(f"code_review_graph_sections={len(REQUIRED_CODE_GRAPH_SECTIONS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
