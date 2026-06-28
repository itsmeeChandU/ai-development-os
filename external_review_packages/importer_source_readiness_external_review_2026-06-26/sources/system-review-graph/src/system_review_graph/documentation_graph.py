"""Load compact context from documentation knowledge graph JSONL artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(path)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _node_id(row: dict[str, Any]) -> str:
    return str(row.get("node_id") or row.get("id") or "")


def _edge_source(row: dict[str, Any]) -> str:
    return str(row.get("source") or row.get("src") or "")


def _edge_target(row: dict[str, Any]) -> str:
    return str(row.get("target") or row.get("dst") or "")


def _edge_relation(row: dict[str, Any]) -> str:
    return str(row.get("relation") or row.get("type") or "")


def _trim(payload: dict[str, Any], max_chars: int) -> tuple[dict[str, Any], bool]:
    text = json.dumps(payload, sort_keys=True)
    if len(text) <= max_chars:
        return payload, False
    trimmed = dict(payload)
    trimmed["nodes"] = trimmed.get("nodes", [])[: max(1, len(trimmed.get("nodes", [])) // 2)]
    trimmed["edges"] = trimmed.get("edges", [])[: max(1, len(trimmed.get("edges", [])) // 2)]
    text = json.dumps(trimmed, sort_keys=True)
    if len(text) <= max_chars:
        return trimmed, True
    return {
        "summary": payload.get("summary", {}),
        "query": payload.get("query", {}),
        "nodes": trimmed.get("nodes", [])[:5],
        "edges": trimmed.get("edges", [])[:10],
        "truncated": True,
        "next_move": "Use a narrower start_node, node_type, relation, or higher max_chars.",
    }, True


def load_documentation_graph_context(
    *,
    nodes_path: Path,
    edges_path: Path,
    start_node: str = "",
    node_type: str = "",
    relation: str = "",
    max_nodes: int = 80,
    max_edges: int = 160,
    max_chars: int = 30000,
) -> dict[str, Any]:
    """Load a bounded, agent-friendly slice from documentation graph JSONL files."""

    nodes = _read_jsonl(nodes_path)
    edges = _read_jsonl(edges_path)
    node_by_id = {_node_id(node): node for node in nodes if _node_id(node)}
    selected_edges = edges
    if start_node:
        selected_edges = [
            edge
            for edge in selected_edges
            if _edge_source(edge) == start_node or _edge_target(edge) == start_node
        ]
    if relation:
        selected_edges = [
            edge for edge in selected_edges if _edge_relation(edge) == relation
        ]
    selected_node_ids: set[str] = set()
    if start_node:
        selected_node_ids.add(start_node)
    for edge in selected_edges[:max_edges]:
        selected_node_ids.add(_edge_source(edge))
        selected_node_ids.add(_edge_target(edge))
    if node_type:
        for node in nodes:
            if str(node.get("type") or node.get("node_type") or "") == node_type:
                selected_node_ids.add(_node_id(node))
                if len(selected_node_ids) >= max_nodes:
                    break
    if not selected_node_ids:
        priority_types = {"system", "concept", "owner_module", "flow_stage"}
        for node in nodes:
            if str(node.get("type") or node.get("node_type") or "") in priority_types:
                selected_node_ids.add(_node_id(node))
            if len(selected_node_ids) >= max_nodes:
                break
    selected_nodes = [
        node_by_id[node_id]
        for node_id in sorted(selected_node_ids)
        if node_id in node_by_id
    ][:max_nodes]
    selected_node_ids = {_node_id(node) for node in selected_nodes}
    selected_edges = [
        edge
        for edge in selected_edges
        if _edge_source(edge) in selected_node_ids or _edge_target(edge) in selected_node_ids
    ][:max_edges]
    payload = {
        "agent_context_contract": {
            "primary_users": ["agents", "LLMs", "review automation", "maintainers"],
            "use": (
                "Load a bounded graph slice, follow stable node IDs and relations, then "
                "open source artifacts only when deeper proof is needed."
            ),
            "do_not_use_as": (
                "A complete source-code substitute, deletion approval, runtime proof, "
                "or permission to take external action."
            ),
        },
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "selected_nodes": len(selected_nodes),
            "selected_edges": len(selected_edges),
            "node_type_counts": dict(
                sorted(
                    Counter(
                        str(node.get("type") or node.get("node_type") or "")
                        for node in nodes
                    ).items()
                )
            ),
            "edge_relation_counts": dict(
                sorted(Counter(_edge_relation(edge) for edge in edges).items())
            ),
        },
        "query": {
            "nodes_path": str(nodes_path),
            "edges_path": str(edges_path),
            "start_node": start_node,
            "node_type": node_type,
            "relation": relation,
            "max_nodes": max_nodes,
            "max_edges": max_edges,
            "max_chars": max_chars,
        },
        "nodes": selected_nodes,
        "edges": selected_edges,
        "next_moves": [
            "Start from concept nodes such as concept:stock_selection or concept:algorithm_usage.",
            "Use node_type=file for file-level rows and relation filters for a single edge class.",
            (
                "Pair this context with source-code graph/report artifacts before making "
                "cleanup or behavior claims."
            ),
        ],
        "llm_usage_notes": [
            "Prefer stable IDs over label text when asking follow-up questions.",
            "Quote paths and node IDs exactly when handing work to another agent.",
            "Use selected counts to decide whether to narrow context before loading more.",
        ],
    }
    trimmed, truncated = _trim(payload, max_chars)
    trimmed["truncated"] = truncated
    return trimmed
