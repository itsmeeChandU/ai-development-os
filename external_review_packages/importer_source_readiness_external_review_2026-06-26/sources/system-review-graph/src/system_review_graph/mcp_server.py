"""Minimal MCP stdio server for System Review Graph."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from system_review_graph import __version__
from system_review_graph.builder import build_system_review
from system_review_graph.doctor import doctor_manifest, format_doctor_findings
from system_review_graph.documentation_graph import load_documentation_graph_context
from system_review_graph.io import read_json, write_json
from system_review_graph.render import (
    REPORT_DEPTHS,
    render_graphviz_dot,
    render_html,
    render_markdown,
)
from system_review_graph.repo_context_bundle import load_repo_context_bundle
from system_review_graph.scanner import scan_repository, scan_repository_atlas
from system_review_graph.serialize import to_dict
from system_review_graph.validate import validate_manifest

PROTOCOL_VERSION = "2025-11-25"


def _tool_schema(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str] | None = None,
    read_only: bool = False,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": read_only,
            "idempotentHint": True,
        },
    }


TOOLS: list[dict[str, Any]] = [
    _tool_schema(
        "srg_validate_manifest",
        "Validate a System Review Graph manifest and return structured errors.",
        {"manifest_path": {"type": "string"}},
        ["manifest_path"],
        read_only=True,
    ),
    _tool_schema(
        "srg_doctor_manifest",
        "Run manifest quality checks for audit readiness and missing review surfaces.",
        {"manifest_path": {"type": "string"}},
        ["manifest_path"],
        read_only=True,
    ),
    _tool_schema(
        "srg_build_report",
        "Build Markdown/JSON reports from a manifest, with optional HTML and DOT outputs.",
        {
            "manifest_path": {"type": "string"},
            "out_dir": {"type": "string"},
            "depth": {"type": "string", "enum": sorted(REPORT_DEPTHS), "default": "deep"},
            "html": {"type": "boolean", "default": False},
            "dot": {"type": "boolean", "default": False},
        },
        ["manifest_path", "out_dir"],
    ),
    _tool_schema(
        "srg_scan_repository",
        "Generate a starter manifest or large-repo atlas from a local repository path.",
        {
            "repo_path": {"type": "string"},
            "out": {"type": "string"},
            "title": {"type": "string"},
            "file_limit": {"type": "integer", "default": 6000, "minimum": 1},
            "atlas": {"type": "boolean", "default": False},
            "max_subsystems": {"type": "integer", "default": 24, "minimum": 1},
            "build_reports": {"type": "boolean", "default": False},
            "depth": {"type": "string", "enum": sorted(REPORT_DEPTHS), "default": "overview"},
            "html": {"type": "boolean", "default": False},
            "dot": {"type": "boolean", "default": False},
        },
        ["repo_path", "out"],
    ),
    _tool_schema(
        "srg_load_atlas_context",
        "Load a compact context bundle from a root atlas manifest and optional child maps.",
        {
            "manifest_path": {"type": "string"},
            "include_children": {"type": "boolean", "default": False},
            "max_child_maps": {"type": "integer", "default": 12, "minimum": 0},
            "max_blueprint_sections": {"type": "integer", "default": 12, "minimum": 0},
            "max_chars": {"type": "integer", "default": 30000, "minimum": 1000},
        },
        ["manifest_path"],
        read_only=True,
    ),
    _tool_schema(
        "srg_load_documentation_graph_context",
        "Load a compact context slice from documentation knowledge graph nodes/edges JSONL files.",
        {
            "nodes_path": {"type": "string"},
            "edges_path": {"type": "string"},
            "start_node": {"type": "string", "default": ""},
            "node_type": {"type": "string", "default": ""},
            "relation": {"type": "string", "default": ""},
            "max_nodes": {"type": "integer", "default": 80, "minimum": 1},
            "max_edges": {"type": "integer", "default": 160, "minimum": 1},
            "max_chars": {"type": "integer", "default": 30000, "minimum": 1000},
        },
        ["nodes_path", "edges_path"],
        read_only=True,
    ),
    _tool_schema(
        "srg_load_repo_context_bundle",
        "Load bounded SRG, documentation graph, and code-review graph context for agents.",
        {
            "manifest_path": {"type": "string"},
            "documentation_nodes_path": {"type": "string", "default": ""},
            "documentation_edges_path": {"type": "string", "default": ""},
            "code_review_graph_path": {"type": "string", "default": ""},
            "agentic_workflow_path": {"type": "string", "default": ""},
            "start_node": {"type": "string", "default": ""},
            "node_type": {"type": "string", "default": ""},
            "relation": {"type": "string", "default": ""},
            "max_nodes": {"type": "integer", "default": 80, "minimum": 1},
            "max_edges": {"type": "integer", "default": 160, "minimum": 1},
            "max_chars": {"type": "integer", "default": 30000, "minimum": 1000},
        },
        ["manifest_path"],
        read_only=True,
    ),
]


def _bool(args: dict[str, Any], key: str, default: bool = False) -> bool:
    return bool(args.get(key, default))


def _int(args: dict[str, Any], key: str, default: int) -> int:
    value = args.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _str(args: dict[str, Any], key: str, default: str = "") -> str:
    value = args.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _path(args: dict[str, Any], key: str) -> Path:
    value = _str(args, key)
    if not value:
        raise ValueError(f"{key} is required")
    return Path(value)


def _write_report_outputs(
    manifest: dict[str, Any],
    out_dir: Path,
    depth: str,
    html: bool = False,
    dot: bool = False,
) -> dict[str, str]:
    graph = build_system_review(manifest)
    write_json(out_dir / "system_review_graph.json", to_dict(graph))
    md_path = out_dir / "system_review_graph.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(graph, depth=depth), encoding="utf-8")
    outputs = {
        "markdown": str(md_path),
        "json": str(out_dir / "system_review_graph.json"),
    }
    if html:
        html_path = out_dir / "system_review_graph.html"
        html_path.write_text(render_html(graph, depth=depth), encoding="utf-8")
        outputs["html"] = str(html_path)
    if dot:
        dot_path = out_dir / "system_review_graph.dot"
        dot_path.write_text(render_graphviz_dot(graph), encoding="utf-8")
        outputs["dot"] = str(dot_path)
    return outputs


def _tool_result(payload: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, indent=2, sort_keys=True)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": payload,
    }


def _tool_validate(args: dict[str, Any]) -> dict[str, Any]:
    manifest_path = _path(args, "manifest_path")
    errors = validate_manifest(read_json(manifest_path))
    return _tool_result(
        {"valid": not errors, "errors": errors, "manifest_path": str(manifest_path)}
    )


def _tool_doctor(args: dict[str, Any]) -> dict[str, Any]:
    manifest_path = _path(args, "manifest_path")
    findings = doctor_manifest(read_json(manifest_path))
    return _tool_result(
        {
            "clean": not findings,
            "findings": findings,
            "summary": format_doctor_findings(findings),
            "manifest_path": str(manifest_path),
        }
    )


def _tool_build(args: dict[str, Any]) -> dict[str, Any]:
    manifest_path = _path(args, "manifest_path")
    out_dir = _path(args, "out_dir")
    depth = _str(args, "depth", "deep")
    if depth not in REPORT_DEPTHS:
        raise ValueError(f"depth must be one of {', '.join(sorted(REPORT_DEPTHS))}")
    manifest = read_json(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        return _tool_result({"ok": False, "errors": errors, "manifest_path": str(manifest_path)})
    outputs = _write_report_outputs(
        manifest,
        out_dir,
        depth,
        _bool(args, "html"),
        _bool(args, "dot"),
    )
    return _tool_result({"ok": True, "manifest_path": str(manifest_path), "outputs": outputs})


def _tool_scan(args: dict[str, Any]) -> dict[str, Any]:
    repo_path = _path(args, "repo_path")
    out = _path(args, "out")
    title = _str(args, "title") or None
    file_limit = _int(args, "file_limit", 6000)
    depth = _str(args, "depth", "overview")
    if depth not in REPORT_DEPTHS:
        raise ValueError(f"depth must be one of {', '.join(sorted(REPORT_DEPTHS))}")
    if _bool(args, "atlas"):
        atlas = scan_repository_atlas(
            repo_path,
            title=title,
            file_limit=file_limit,
            max_subsystems=_int(args, "max_subsystems", 24),
        )
        root_manifest = atlas["root"]
        root_path = out / "system_review_manifest.json"
        write_json(root_path, root_manifest)
        child_paths: list[str] = []
        child_reports: list[dict[str, str]] = []
        for child in atlas["children"]:
            child_path = out / child["manifest_path"]
            write_json(child_path, child["manifest"])
            child_paths.append(str(child_path))
        root_reports: dict[str, str] = {}
        if _bool(args, "build_reports"):
            root_reports = _write_report_outputs(
                root_manifest,
                out / "reports",
                depth,
                _bool(args, "html"),
                _bool(args, "dot"),
            )
            for child in atlas["children"]:
                child_dir = (out / child["manifest_path"]).parent / "reports"
                child_reports.append(_write_report_outputs(child["manifest"], child_dir, depth))
        return _tool_result(
            {
                "ok": True,
                "atlas": True,
                "root_manifest": str(root_path),
                "child_manifests": child_paths,
                "root_reports": root_reports,
                "child_report_count": len(child_reports),
            }
        )
    manifest = scan_repository(repo_path, title=title, file_limit=file_limit)
    write_json(out, manifest)
    return _tool_result({"ok": True, "atlas": False, "manifest_path": str(out)})


def _resolve_child_path(root_manifest_path: Path, child_path: str) -> Path:
    path = Path(child_path)
    if path.is_absolute():
        return path
    return root_manifest_path.parent / path


def _tool_load_atlas_context(args: dict[str, Any]) -> dict[str, Any]:
    manifest_path = _path(args, "manifest_path")
    manifest = read_json(manifest_path)
    max_child_maps = _int(args, "max_child_maps", 12)
    max_blueprint_sections = _int(args, "max_blueprint_sections", 12)
    context: dict[str, Any] = {
        "title": manifest.get("title"),
        "one_line": manifest.get("one_line"),
        "scope": manifest.get("scope"),
        "current_truth": manifest.get("current_truth", {}),
        "systems": manifest.get("systems", []),
        "child_maps": (manifest.get("child_maps") or [])[:max_child_maps],
        "blueprint_sections": (manifest.get("blueprint_sections") or [])[
            :max_blueprint_sections
        ],
        "review_questions": manifest.get("review_questions", []),
        "known_boundaries": manifest.get("known_boundaries", []),
        "source_links": manifest.get("source_links", []),
    }
    if _bool(args, "include_children"):
        children = []
        for child_map in context["child_maps"]:
            child_manifest_path = _resolve_child_path(manifest_path, str(child_map.get("path", "")))
            if not child_manifest_path.exists():
                children.append(
                    {"path": str(child_manifest_path), "error": "child manifest not found"}
                )
                continue
            child_manifest = read_json(child_manifest_path)
            children.append(
                {
                    "path": str(child_manifest_path),
                    "title": child_manifest.get("title"),
                    "current_truth": child_manifest.get("current_truth", {}),
                    "systems": child_manifest.get("systems", []),
                    "review_questions": child_manifest.get("review_questions", []),
                    "known_boundaries": child_manifest.get("known_boundaries", []),
                }
            )
        context["children"] = children
    text = json.dumps(context, indent=2, sort_keys=True)
    max_chars = _int(args, "max_chars", 30000)
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + "\n...TRUNCATED..."
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": {
            "context": context if not truncated else {},
            "truncated": truncated,
            "manifest_path": str(manifest_path),
        },
    }


def _tool_load_documentation_graph_context(args: dict[str, Any]) -> dict[str, Any]:
    context = load_documentation_graph_context(
        nodes_path=_path(args, "nodes_path"),
        edges_path=_path(args, "edges_path"),
        start_node=_str(args, "start_node"),
        node_type=_str(args, "node_type"),
        relation=_str(args, "relation"),
        max_nodes=_int(args, "max_nodes", 80),
        max_edges=_int(args, "max_edges", 160),
        max_chars=_int(args, "max_chars", 30000),
    )
    return _tool_result(context)


def _optional_path(args: dict[str, Any], key: str) -> Path | None:
    value = _str(args, key)
    return Path(value) if value else None


def _tool_load_repo_context_bundle(args: dict[str, Any]) -> dict[str, Any]:
    context = load_repo_context_bundle(
        manifest_path=_path(args, "manifest_path"),
        documentation_nodes_path=_optional_path(args, "documentation_nodes_path"),
        documentation_edges_path=_optional_path(args, "documentation_edges_path"),
        code_review_graph_path=_optional_path(args, "code_review_graph_path"),
        agentic_workflow_path=_optional_path(args, "agentic_workflow_path"),
        start_node=_str(args, "start_node"),
        node_type=_str(args, "node_type"),
        relation=_str(args, "relation"),
        max_nodes=_int(args, "max_nodes", 80),
        max_edges=_int(args, "max_edges", 160),
        max_chars=_int(args, "max_chars", 30000),
    )
    return _tool_result(context)


TOOL_HANDLERS = {
    "srg_validate_manifest": _tool_validate,
    "srg_doctor_manifest": _tool_doctor,
    "srg_build_report": _tool_build,
    "srg_scan_repository": _tool_scan,
    "srg_load_atlas_context": _tool_load_atlas_context,
    "srg_load_documentation_graph_context": _tool_load_documentation_graph_context,
    "srg_load_repo_context_bundle": _tool_load_repo_context_bundle,
}


def _success(message_id: str | int | None, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(
    message_id: str | int | None,
    code: int,
    message: str,
    data: Any | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": message_id, "error": error}


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC MCP message."""

    message_id = message.get("id")
    method = message.get("method")
    if method is None:
        return None
    if message_id is None and method.startswith("notifications/"):
        return None
    if method == "initialize":
        return _success(
            message_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "system-review-graph",
                    "title": "System Review Graph MCP Server",
                    "version": __version__,
                },
                "instructions": (
                    "Use this server to scan repositories, build System Review Graph "
                    "reports, validate manifests, run doctor checks, and load atlas "
                    "context for large repos."
                ),
            },
        )
    if method == "tools/list":
        return _success(message_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        if not isinstance(params, dict):
            return _error(message_id, -32602, "params must be an object")
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or name not in TOOL_HANDLERS:
            return _error(message_id, -32602, f"unknown tool {name!r}")
        if not isinstance(arguments, dict):
            return _error(message_id, -32602, "tool arguments must be an object")
        try:
            return _success(message_id, TOOL_HANDLERS[name](arguments))
        except Exception as exc:  # pragma: no cover - defensive MCP boundary
            return _error(message_id, -32603, str(exc), {"tool": name})
    if method == "ping":
        return _success(message_id, {})
    return _error(message_id, -32601, f"method not found: {method}")


def _handle_json_line(line: str) -> list[dict[str, Any]]:
    try:
        message = json.loads(line)
    except json.JSONDecodeError as exc:
        return [_error(None, -32700, "parse error", str(exc))]
    messages = message if isinstance(message, list) else [message]
    responses: list[dict[str, Any]] = []
    for item in messages:
        if not isinstance(item, dict):
            responses.append(_error(None, -32600, "invalid request"))
            continue
        response = handle_message(item)
        if response is not None:
            responses.append(response)
    return responses


def main() -> int:
    """Run the MCP server over newline-delimited stdio."""

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        responses = _handle_json_line(line)
        for response in responses:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
