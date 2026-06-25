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
    "startup_continuation_rule",
    "vc_pitch_readiness_rule",
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
