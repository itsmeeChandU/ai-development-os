"""Load bounded repo context from SRG, documentation graph, and code-review graph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from system_review_graph.documentation_graph import load_documentation_graph_context

REQUIRED_CODE_REVIEW_CONTRACT_SECTIONS = [
    "files",
    "modules",
    "symbols",
    "imports",
    "edges",
    "tests",
    "generated_artifacts",
    "risk_ownership_hints",
]
REQUIRED_AGENTIC_WORKFLOW_SECTIONS = [
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
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _trim(payload: dict[str, Any], max_chars: int) -> tuple[dict[str, Any], bool]:
    text = json.dumps(payload, sort_keys=True)
    if len(text) <= max_chars:
        return payload, False
    trimmed = dict(payload)
    manifest = dict(trimmed.get("system_review_graph") or {})
    manifest["systems"] = manifest.get("systems", [])[:5]
    manifest["review_questions"] = manifest.get("review_questions", [])[:8]
    manifest["known_boundaries"] = manifest.get("known_boundaries", [])[:8]
    trimmed["system_review_graph"] = manifest
    docs = dict(trimmed.get("documentation_graph_context") or {})
    docs["nodes"] = docs.get("nodes", [])[:12]
    docs["edges"] = docs.get("edges", [])[:24]
    trimmed["documentation_graph_context"] = docs
    text = json.dumps(trimmed, sort_keys=True)
    if len(text) <= max_chars:
        return trimmed, True
    return {
        "agent_context_contract": payload.get("agent_context_contract", {}),
        "summary": payload.get("summary", {}),
        "system_review_graph": manifest,
        "code_review_graph_reference": payload.get("code_review_graph_reference", {}),
        "agentic_workflow_reference": payload.get("agentic_workflow_reference", {}),
        "truncated": True,
        "next_valid_move": "Use narrower documentation graph filters or raise max_chars.",
    }, True


def _manifest_context(manifest_path: Path) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    return {
        "manifest_path": str(manifest_path),
        "title": manifest.get("title"),
        "one_line": manifest.get("one_line"),
        "scope": manifest.get("scope"),
        "current_truth": manifest.get("current_truth", {}),
        "counts": {
            "systems": len(manifest.get("systems", [])),
            "artifacts": len(manifest.get("artifacts", [])),
            "schemas": len(manifest.get("schemas", [])),
            "decision_gates": len(manifest.get("decision_gates", [])),
            "workflows": len(manifest.get("workflows", [])),
            "child_maps": len(manifest.get("child_maps", [])),
            "blueprint_sections": len(manifest.get("blueprint_sections", [])),
            "knowledge_nodes": len(manifest.get("knowledge_nodes", [])),
            "knowledge_edges": len(manifest.get("knowledge_edges", [])),
        },
        "systems": manifest.get("systems", [])[:12],
        "child_maps": manifest.get("child_maps", [])[:12],
        "blueprint_sections": manifest.get("blueprint_sections", [])[:12],
        "review_questions": manifest.get("review_questions", [])[:20],
        "known_boundaries": manifest.get("known_boundaries", [])[:20],
        "source_links": manifest.get("source_links", [])[:20],
    }


def _code_review_graph_reference(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "provided": False,
            "status": "missing_input",
            "next_valid_move": (
                "Pass --code-review-graph with a contract or source graph JSON path."
            ),
        }
    if not path.exists():
        return {
            "provided": True,
            "path": str(path),
            "status": "missing_file",
            "next_valid_move": (
                "Build or export the code-review graph contract before loading context."
            ),
        }
    payload = _read_json(path)
    present = [section for section in REQUIRED_CODE_REVIEW_CONTRACT_SECTIONS if section in payload]
    missing = [
        section for section in REQUIRED_CODE_REVIEW_CONTRACT_SECTIONS if section not in payload
    ]
    summary = payload.get("summary") or {}
    if not summary and "nodes" in payload and "edges" in payload:
        summary = {
            "nodes": len(payload.get("nodes") or []),
            "edges": len(payload.get("edges") or []),
        }
    generated_artifacts = payload.get("generated_artifacts") or []
    generated_artifact_types = sorted(
        {
            str(row.get("type"))
            for row in generated_artifacts
            if isinstance(row, dict) and row.get("type")
        }
    )
    return {
        "provided": True,
        "path": str(path),
        "status": "ready" if not missing else "partial",
        "contract_version": payload.get("contract_version") or "legacy_source_graph",
        "summary": summary,
        "generated_artifacts": generated_artifacts[:20],
        "generated_artifact_types": generated_artifact_types[:40],
        "startup_continuation_plan_present": (
            "startup_continuation_plan" in generated_artifact_types
        ),
        "required_sections_present": present,
        "required_sections_missing": missing,
        "proof_boundary": payload.get(
            "proof_boundary",
            "Code-review graph data is orientation context. Read source and run "
            "proof commands before behavior claims.",
        ),
    }


def _agentic_workflow_reference(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "provided": False,
            "status": "missing_input",
            "next_valid_move": (
                "Pass --agentic-workflow with the AI Development OS execution manifest."
            ),
        }
    if not path.exists():
        return {
            "provided": True,
            "path": str(path),
            "status": "missing_file",
            "next_valid_move": (
                "Generate or locate the agentic execution manifest before lane assignment."
            ),
        }
    payload = _read_json(path)
    present = [section for section in REQUIRED_AGENTIC_WORKFLOW_SECTIONS if section in payload]
    missing = [
        section for section in REQUIRED_AGENTIC_WORKFLOW_SECTIONS if section not in payload
    ]
    orchestration = payload.get("multi_repo_orchestration") or {}
    return {
        "provided": True,
        "path": str(path),
        "status": "ready" if not missing else "partial",
        "name": payload.get("name"),
        "version": payload.get("version"),
        "summary": {
            "slash_commands": len(payload.get("slash_commands") or []),
            "skills": len(payload.get("skills") or []),
            "background_routines": len(payload.get("background_routines") or []),
            "parallel_agent_lanes": len(payload.get("parallel_agent_lanes") or []),
            "ci_cd_agent_jobs": len(payload.get("ci_cd_agent_jobs") or []),
            "eval_loops": len(payload.get("eval_loops") or []),
            "repos": len(orchestration.get("repos") or []),
        },
        "required_sections_present": present,
        "required_sections_missing": missing,
        "proof_boundary": (
            "Agentic workflow data is lane coordination context. It does not "
            "replace source inspection, generated artifacts, tests, or GitHub proof."
        ),
    }


def load_repo_context_bundle(
    *,
    manifest_path: Path,
    documentation_nodes_path: Path | None = None,
    documentation_edges_path: Path | None = None,
    code_review_graph_path: Path | None = None,
    agentic_workflow_path: Path | None = None,
    start_node: str = "",
    node_type: str = "",
    relation: str = "",
    max_nodes: int = 80,
    max_edges: int = 160,
    max_chars: int = 30000,
) -> dict[str, Any]:
    """Load one bounded bundle for agents from SRG and code-review graph inputs."""

    if documentation_nodes_path and documentation_edges_path:
        documentation_context: dict[str, Any] = load_documentation_graph_context(
            nodes_path=documentation_nodes_path,
            edges_path=documentation_edges_path,
            start_node=start_node,
            node_type=node_type,
            relation=relation,
            max_nodes=max_nodes,
            max_edges=max_edges,
            max_chars=max_chars,
        )
    else:
        documentation_context = {
            "status": "missing_input",
            "next_valid_move": (
                "Pass both documentation node and edge JSONL paths for graph slices."
            ),
        }

    payload = {
        "agent_context_contract": {
            "primary_users": ["agents", "LLMs", "review automation", "maintainers"],
            "use": (
                "Load bounded SRG, documentation graph, and code-review graph context "
                "before assigning or executing a repo lane."
            ),
            "do_not_use_as": (
                "Runtime proof, deletion approval, private data disclosure, or permission "
                "to bypass safety/legal/release gates."
            ),
        },
        "summary": {
            "manifest_path": str(manifest_path),
            "documentation_graph_included": bool(
                documentation_nodes_path and documentation_edges_path
            ),
            "code_review_graph_included": bool(code_review_graph_path),
            "agentic_workflow_included": bool(agentic_workflow_path),
        },
        "system_review_graph": _manifest_context(manifest_path),
        "documentation_graph_context": documentation_context,
        "code_review_graph_reference": _code_review_graph_reference(code_review_graph_path),
        "agentic_workflow_reference": _agentic_workflow_reference(agentic_workflow_path),
        "proof_boundaries": [
            "SRG describes systems and gates from a sanitized manifest.",
            "Documentation graph slices are context windows, not complete source proof.",
            "Code-review graph contracts orient source inspection; source files "
            "and tests remain required.",
            "Generated artifact references, including continuation plans, are "
            "truth pointers; inspect the artifact and run proof commands before "
            "completion claims.",
            "Agentic workflow manifests define lane coordination; GitHub, source, "
            "generated artifacts, and checks remain authoritative.",
        ],
        "next_moves": [
            "Open source files named in the bundle before editing.",
            "Run lane-specific tests and generated artifact checks after edits.",
            "Write blocker rows with next_valid_move when any required context is "
            "partial or missing.",
        ],
    }
    trimmed, truncated = _trim(payload, max_chars)
    trimmed["truncated"] = truncated
    return trimmed
