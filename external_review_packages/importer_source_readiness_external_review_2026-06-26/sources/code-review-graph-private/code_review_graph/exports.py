"""Additional export formats: GraphML, Neo4j Cypher, Obsidian vault, SVG, contract JSON."""

from __future__ import annotations

import html
import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .graph import GraphStore, _sanitize_name
from .visualization import export_graph_data

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Agent contract export (for SRG / AI Development OS context bundles)
# -------------------------------------------------------------------

CONTRACT_VERSION = "code-review-graph.agent-contract.v1"
KNOWN_GENERATED_ARTIFACTS = {
    "docs/STARTUP_LIFECYCLE.md": "startup_lifecycle_surface",
    "system_review_graph/readiness_report.json": "product_readiness_report",
    "system_review_graph/external_gate_report.json": "external_gate_report",
    "system_review_graph/continuation_plan.json": "startup_continuation_plan",
    "system_review_graph/vc_pitch_readiness_report.json": "vc_pitch_readiness_report",
    "system_review_graph/board_go_live_readiness_report.json": "board_go_live_readiness_report",
    "system_review_graph/operator_workflow_report.json": "operator_workflow_report",
    "system_review_graph/operator_dashboard.html": "operator_dashboard",
    "system_review_graph/operator_screenshot_manifest.json": "operator_screenshot_manifest",
    "system_review_graph/blockers.jsonl": "blocker_ledger",
    "system_review_graph/prompt_to_product_packet.json": "prompt_to_product_packet",
    "system_review_graph/internal_repo_intake_packet.json": "internal_repo_intake_packet",
    "system_review_graph/research_data_plan.json": "research_data_plan",
    "system_review_graph/development_strategy_plan.json": "development_strategy_plan",
    "system_review_graph/lane_packet_workflow-coordinator.json": "lane_packet",
    "system_review_graph/automation_runtime_report.json": "automation_runtime_report",
    "system_review_graph/eval_report.json": "eval_report",
    "investor/vc_pitch_deck.md": "vc_pitch_deck",
    "investor/one_pager.md": "investor_one_pager",
    "investor/demo_script.md": "investor_demo_script",
    "investor/diligence_room_index.md": "investor_diligence_index",
    "board/board_go_live_brief.md": "board_go_live_brief",
    "board/expert_review_packet.md": "board_expert_review_packet",
    "board/launch_control_checklist.md": "board_launch_control_checklist",
    "board/financial_operating_model.md": "board_financial_operating_model",
}
KNOWN_SCREENSHOT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".svg", ".webp"}


def _stable_edge_id(edge: dict) -> str:
    detail = f"{edge.get('file_path') or ''}:{edge.get('line') or 0}"
    return (
        f"edge:{edge.get('kind') or 'RELATED'}:"
        f"{edge.get('source') or ''}->{edge.get('target') or ''}:{detail}"
    )


def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    parts = normalized.split("/")
    name = parts[-1] if parts else normalized
    return (
        "tests" in parts
        or "__tests__" in parts
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.ts")
        or name.endswith(".spec.ts")
        or name.endswith(".test.tsx")
        or name.endswith(".spec.tsx")
    )


def _risk_level(symbol_count: int, edge_count: int, has_tests: bool) -> str:
    if edge_count >= 50 or symbol_count >= 75:
        return "high"
    if not has_tests and (edge_count >= 10 or symbol_count >= 20):
        return "medium"
    if edge_count >= 20 or symbol_count >= 35:
        return "medium"
    return "low"


def _repo_generated_artifacts(repo_root: Path | None) -> list[dict]:
    if repo_root is None:
        return []
    artifacts = []
    for relative_path, artifact_type in sorted(KNOWN_GENERATED_ARTIFACTS.items()):
        path = repo_root / relative_path
        if not path.exists():
            continue
        artifacts.append(
            {
                "id": f"artifact:{relative_path}",
                "path": relative_path,
                "type": artifact_type,
                "producer": "repo proof or AI Development OS workflow",
            }
        )
    screenshot_dir = repo_root / "system_review_graph" / "operator_screenshots"
    if screenshot_dir.exists():
        for path in sorted(screenshot_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() not in KNOWN_SCREENSHOT_EXTENSIONS:
                continue
            relative_path = path.relative_to(repo_root).as_posix()
            artifacts.append(
                {
                    "id": f"artifact:{relative_path}",
                    "path": relative_path,
                    "type": "operator_screenshot",
                    "producer": "operator screenshot proof surface",
                }
            )
    return artifacts


def build_agent_contract(
    store: GraphStore,
    *,
    repo_root: Path | None = None,
    output_path: Path | None = None,
) -> dict:
    """Build a stable JSON contract for agent and SRG consumers.

    The contract is intentionally derived from the existing graph database. It
    does not claim runtime behavior; it gives agents stable IDs and bounded
    code-review context before they open source files.
    """

    data = export_graph_data(store)
    nodes = sorted(data["nodes"], key=lambda row: str(row.get("qualified_name") or ""))
    edges = sorted(
        data["edges"],
        key=lambda row: (
            str(row.get("kind") or ""),
            str(row.get("source") or ""),
            str(row.get("target") or ""),
            str(row.get("file_path") or ""),
            int(row.get("line") or 0),
        ),
    )
    stats = data.get("stats") or {}

    nodes_by_file: dict[str, list[dict]] = defaultdict(list)
    for node in nodes:
        nodes_by_file[str(node.get("file_path") or "")].append(node)

    edge_counts_by_file: Counter[str] = Counter()
    imports: list[dict] = []
    contract_edges: list[dict] = []
    for edge in edges:
        file_path = str(edge.get("file_path") or "")
        edge_counts_by_file[file_path] += 1
        stable_id = _stable_edge_id(edge)
        row = {
            "id": stable_id,
            "kind": edge.get("kind"),
            "source": edge.get("source"),
            "target": edge.get("target"),
            "file_path": edge.get("file_path"),
            "line": edge.get("line"),
            "confidence": edge.get("confidence"),
            "confidence_tier": edge.get("confidence_tier"),
        }
        contract_edges.append(row)
        if str(edge.get("kind") or "").upper() == "IMPORTS_FROM":
            imports.append(row)

    files: list[dict] = []
    modules: list[dict] = []
    symbols: list[dict] = []
    tests: list[dict] = []
    risk_hints: list[dict] = []

    for file_path, file_nodes in sorted(nodes_by_file.items()):
        if not file_path:
            continue
        file_node = next((node for node in file_nodes if node.get("kind") == "File"), None)
        language = str((file_node or file_nodes[0]).get("language") or "")
        is_test_file = _is_test_path(file_path) or any(
            bool(node.get("is_test")) for node in file_nodes
        )
        symbol_nodes = [node for node in file_nodes if node.get("kind") != "File"]
        test_nodes = [
            node
            for node in symbol_nodes
            if bool(node.get("is_test")) or node.get("kind") == "Test" or _is_test_path(file_path)
        ]
        edge_count = int(edge_counts_by_file[file_path])
        files.append(
            {
                "id": f"file:{file_path}",
                "path": file_path,
                "language": language,
                "is_test": is_test_file,
                "node_count": len(file_nodes),
                "symbol_count": len(symbol_nodes),
                "edge_count": edge_count,
            }
        )
        modules.append(
            {
                "id": f"module:{file_path}",
                "path": file_path,
                "language": language,
                "symbol_ids": [
                    f"symbol:{node.get('qualified_name')}"
                    for node in symbol_nodes
                ],
                "test_ids": [
                    f"test:{node.get('qualified_name')}"
                    for node in test_nodes
                ],
            }
        )
        risk_hints.append(
            {
                "id": f"risk:{file_path}",
                "file_id": f"file:{file_path}",
                "owner_hint": file_path.split("/", 1)[0],
                "risk_level": _risk_level(len(symbol_nodes), edge_count, bool(test_nodes)),
                "reasons": [
                    f"symbol_count={len(symbol_nodes)}",
                    f"edge_count={edge_count}",
                    f"has_tests={bool(test_nodes)}",
                ],
            }
        )

    for node in nodes:
        if node.get("kind") == "File":
            continue
        symbol = {
            "id": f"symbol:{node.get('qualified_name')}",
            "kind": str(node.get("kind") or "").lower(),
            "name": node.get("name"),
            "qualified_name": node.get("qualified_name"),
            "file_id": f"file:{node.get('file_path')}",
            "file_path": node.get("file_path"),
            "line_start": node.get("line_start"),
            "line_end": node.get("line_end"),
            "language": node.get("language"),
            "parent_name": node.get("parent_name"),
            "is_test": bool(node.get("is_test")),
        }
        symbols.append(symbol)
        if symbol["is_test"] or symbol["kind"] == "test" or _is_test_path(str(symbol["file_path"])):
            tests.append(
                {
                    "id": f"test:{node.get('qualified_name')}",
                    "symbol_id": symbol["id"],
                    "name": symbol["name"],
                    "qualified_name": symbol["qualified_name"],
                    "file_path": symbol["file_path"],
                    "line_start": symbol["line_start"],
                    "line_end": symbol["line_end"],
                }
            )

    generated_artifacts = [
        {
            "id": "artifact:graph_database",
            "path": str(store.db_path),
            "type": "sqlite_graph_database",
            "producer": "code-review-graph build/update",
        }
    ]
    generated_artifacts.extend(_repo_generated_artifacts(repo_root))
    if output_path is not None:
        generated_artifacts.append(
            {
                "id": "artifact:agent_contract",
                "path": str(output_path),
                "type": "code_review_graph_agent_contract",
                "producer": "code-review-graph visualize --format contract",
            }
        )

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo": str(repo_root) if repo_root else "",
        "source_graph": {
            "database": str(store.db_path),
            "stats": stats,
        },
        "summary": {
            **stats,
            "files": len(files),
            "modules": len(modules),
            "symbols": len(symbols),
            "imports": len(imports),
            "edges": len(contract_edges),
            "tests": len(tests),
            "generated_artifacts": len(generated_artifacts),
            "risk_ownership_hints": len(risk_hints),
        },
        "proof_boundary": (
            "This contract is structural code-review context. Use it to orient "
            "agents and SRG context bundles, then read source files and run tests "
            "before making behavior, runtime, safety, or completion claims."
        ),
        "files": files,
        "modules": modules,
        "symbols": symbols,
        "imports": imports,
        "edges": contract_edges,
        "tests": tests,
        "generated_artifacts": generated_artifacts,
        "risk_ownership_hints": risk_hints,
    }


def export_agent_contract(
    store: GraphStore,
    output_path: Path,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Export the graph as a stable JSON contract for agents and SRG."""

    contract = build_agent_contract(store, repo_root=repo_root, output_path=output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(contract, indent=2, sort_keys=True), encoding="utf-8")
    logger.info(
        "Agent contract exported to %s (%d files, %d symbols, %d edges)",
        output_path,
        len(contract["files"]),
        len(contract["symbols"]),
        len(contract["edges"]),
    )
    return output_path


# -------------------------------------------------------------------
# GraphML export (for Gephi, yEd, Cytoscape)
# -------------------------------------------------------------------

def export_graphml(store: GraphStore, output_path: Path) -> Path:
    """Export the graph as GraphML XML for Gephi/yEd/Cytoscape.

    Returns the path to the written file.
    """
    data = export_graph_data(store)
    nodes = data["nodes"]
    edges = data["edges"]

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphstruct.org/graphml"',
        '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '  xsi:schemaLocation="http://graphml.graphstruct.org/graphml">',
        '  <key id="kind" for="node" attr.name="kind" '
        'attr.type="string"/>',
        '  <key id="file" for="node" attr.name="file" '
        'attr.type="string"/>',
        '  <key id="language" for="node" attr.name="language" '
        'attr.type="string"/>',
        '  <key id="community" for="node" attr.name="community" '
        'attr.type="int"/>',
        '  <key id="edge_kind" for="edge" attr.name="kind" '
        'attr.type="string"/>',
        '  <graph id="code-review-graph" edgedefault="directed">',
    ]

    for n in nodes:
        nid = html.escape(n["qualified_name"], quote=True)
        lines.append(f'    <node id="{nid}">')
        lines.append(f'      <data key="kind">'
                     f'{html.escape(n.get("kind", ""))}</data>')
        lines.append(f'      <data key="file">'
                     f'{html.escape(n.get("file_path", ""))}</data>')
        lang = n.get("language", "") or ""
        lines.append(f'      <data key="language">'
                     f'{html.escape(lang)}</data>')
        cid = n.get("community_id")
        if cid is not None:
            lines.append(f'      <data key="community">'
                         f'{cid}</data>')
        lines.append('    </node>')

    for i, e in enumerate(edges):
        src = html.escape(e["source"], quote=True)
        tgt = html.escape(e["target"], quote=True)
        kind = html.escape(e.get("kind", ""), quote=True)
        lines.append(
            f'    <edge id="e{i}" source="{src}" target="{tgt}">'
        )
        lines.append(f'      <data key="edge_kind">{kind}</data>')
        lines.append('    </edge>')

    lines.append('  </graph>')
    lines.append('</graphml>')

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("GraphML exported to %s (%d nodes, %d edges)",
                output_path, len(nodes), len(edges))
    return output_path


# -------------------------------------------------------------------
# Neo4j Cypher export
# -------------------------------------------------------------------

def export_neo4j_cypher(store: GraphStore, output_path: Path) -> Path:
    """Export the graph as Neo4j Cypher CREATE statements.

    Returns the path to the written file.
    """
    data = export_graph_data(store)
    nodes = data["nodes"]
    edges = data["edges"]

    lines = [
        "// Generated by code-review-graph",
        "// Import: paste into Neo4j Browser or run via cypher-shell",
        "",
    ]

    # Create nodes
    for n in nodes:
        kind = n.get("kind", "Node")
        props = {
            "qualified_name": n["qualified_name"],
            "name": n.get("name", ""),
            "file_path": n.get("file_path", ""),
            "language": n.get("language", "") or "",
        }
        cid = n.get("community_id")
        if cid is not None:
            props["community_id"] = cid
        props_str = _cypher_props(props)
        lines.append(f"CREATE (:{kind} {props_str});")

    lines.append("")

    # Create edges via MATCH
    for e in edges:
        kind = e.get("kind", "RELATES_TO")
        src_qn = _cypher_escape(e["source"])
        tgt_qn = _cypher_escape(e["target"])
        lines.append(
            f"MATCH (a {{qualified_name: '{src_qn}'}}), "
            f"(b {{qualified_name: '{tgt_qn}'}}) "
            f"CREATE (a)-[:{kind}]->(b);"
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Neo4j Cypher exported to %s (%d nodes, %d edges)",
                output_path, len(nodes), len(edges))
    return output_path


def _cypher_escape(s: str) -> str:
    """Escape a string for Cypher single-quoted literals."""
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _cypher_props(d: dict) -> str:
    """Format a dict as Cypher property map."""
    parts = []
    for k, v in d.items():
        if isinstance(v, str):
            parts.append(f"{k}: '{_cypher_escape(v)}'")
        elif isinstance(v, (int, float)):
            parts.append(f"{k}: {v}")
        elif isinstance(v, bool):
            parts.append(f"{k}: {'true' if v else 'false'}")
    return "{" + ", ".join(parts) + "}"


# -------------------------------------------------------------------
# Obsidian vault export
# -------------------------------------------------------------------

def export_obsidian_vault(
    store: GraphStore, output_dir: Path
) -> Path:
    """Export the graph as an Obsidian vault with wikilinks.

    Creates:
    - One .md per node with YAML frontmatter and [[wikilinks]]
    - _COMMUNITY_*.md overview notes per community
    - _INDEX.md with links to all nodes

    Returns the output directory path.
    """
    data = export_graph_data(store)
    nodes = data["nodes"]
    edges = data["edges"]
    communities = data.get("communities", [])

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build adjacency for wikilinks
    neighbors: dict[str, list[dict]] = {}
    for e in edges:
        src = e["source"]
        tgt = e["target"]
        kind = e.get("kind", "RELATES_TO")
        neighbors.setdefault(src, []).append(
            {"target": tgt, "kind": kind}
        )
        neighbors.setdefault(tgt, []).append(
            {"target": src, "kind": kind}
        )

    # Node name -> slug mapping
    slugs: dict[str, str] = {}
    for n in nodes:
        slug = _obsidian_slug(n.get("name", n["qualified_name"]))
        # Handle collisions
        base_slug = slug
        counter = 1
        while slug in slugs.values():
            slug = f"{base_slug}-{counter}"
            counter += 1
        slugs[n["qualified_name"]] = slug

    # Write node pages
    for n in nodes:
        qn = n["qualified_name"]
        slug = slugs[qn]
        name = n.get("name", qn)

        frontmatter = {
            "kind": n.get("kind", ""),
            "file": n.get("file_path", ""),
            "language": n.get("language", "") or "",
            "community": n.get("community_id"),
            "tags": [n.get("kind", "").lower()],
        }

        lines = ["---"]
        for k, v in frontmatter.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            elif v is not None:
                lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append(f"# {_sanitize_name(name)}")
        lines.append("")
        lines.append(f"**Kind:** {n.get('kind', '')}")
        lines.append(f"**File:** `{n.get('file_path', '')}`")
        lines.append("")

        # Wikilinks to neighbors
        nbrs = neighbors.get(qn, [])
        if nbrs:
            lines.append("## Connections")
            lines.append("")
            seen = set()
            for nb in nbrs:
                tgt_slug = slugs.get(nb["target"])
                if tgt_slug and tgt_slug not in seen:
                    seen.add(tgt_slug)
                    tgt_name = tgt_slug.replace("-", " ").title()
                    lines.append(
                        f"- {nb['kind']}: "
                        f"[[{tgt_slug}|{tgt_name}]]"
                    )

        page_path = output_dir / f"{slug}.md"
        page_path.write_text("\n".join(lines), encoding="utf-8")

    # Write community overview pages
    community_map: dict[int, list[str]] = {}
    for n in nodes:
        cid = n.get("community_id")
        if cid is not None:
            community_map.setdefault(cid, []).append(
                n["qualified_name"]
            )

    for c in communities:
        cid = c.get("id")
        cname = c.get("name", f"community-{cid}")
        members = community_map.get(cid, [])

        lines = [f"# Community: {_sanitize_name(cname)}", ""]
        lines.append(f"**Size:** {c.get('size', len(members))}")
        lines.append(f"**Cohesion:** {c.get('cohesion', 0):.2f}")
        lang = c.get("dominant_language", "")
        if lang:
            lines.append(f"**Language:** {lang}")
        lines.append("")
        lines.append("## Members")
        lines.append("")
        for qn in members[:50]:
            slug = slugs.get(qn)
            if slug:
                lines.append(f"- [[{slug}]]")

        page_path = output_dir / f"_COMMUNITY_{cid}.md"
        page_path.write_text("\n".join(lines), encoding="utf-8")

    # Write index
    index_lines = ["# Code Graph Index", ""]
    index_lines.append(f"**Nodes:** {len(nodes)}")
    index_lines.append(f"**Edges:** {len(edges)}")
    index_lines.append(
        f"**Communities:** {len(communities)}"
    )
    index_lines.append("")
    index_lines.append("## All Nodes")
    index_lines.append("")
    for n in sorted(nodes, key=lambda x: x.get("name", "")):
        slug = slugs.get(n["qualified_name"])
        if slug:
            index_lines.append(
                f"- [[{slug}]] ({n.get('kind', '')})"
            )

    (output_dir / "_INDEX.md").write_text(
        "\n".join(index_lines), encoding="utf-8"
    )

    logger.info(
        "Obsidian vault exported to %s (%d pages)",
        output_dir, len(nodes)
    )
    return output_dir


def _obsidian_slug(name: str) -> str:
    """Convert a name to an Obsidian-friendly filename slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:100] or "unnamed"


# -------------------------------------------------------------------
# SVG export (matplotlib-based)
# -------------------------------------------------------------------

def export_svg(store: GraphStore, output_path: Path) -> Path:
    """Export a static SVG graph visualization.

    Requires matplotlib (optional dependency).
    Returns the path to the written file.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for SVG export. "
            "Install with: pip install matplotlib"
        )

    import networkx as nx

    data = export_graph_data(store)
    nodes_data = data["nodes"]
    edges_data = data["edges"]

    nxg: nx.DiGraph = nx.DiGraph()  # type: ignore[type-arg]
    for n in nodes_data:
        nxg.add_node(
            n["qualified_name"],
            label=n.get("name", ""),
            kind=n.get("kind", ""),
        )
    for e in edges_data:
        if e["source"] in nxg and e["target"] in nxg:
            nxg.add_edge(e["source"], e["target"])

    if nxg.number_of_nodes() == 0:
        raise ValueError("Graph is empty, nothing to export")

    # Color by kind
    kind_colors = {
        "File": "#6c757d",
        "Class": "#0d6efd",
        "Function": "#198754",
        "Type": "#ffc107",
        "Test": "#dc3545",
    }
    colors = [
        kind_colors.get(
            nxg.nodes[n].get("kind", ""), "#adb5bd"
        )
        for n in nxg.nodes()
    ]

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    pos = nx.spring_layout(
        nxg, k=2 / (nxg.number_of_nodes() ** 0.5),
        iterations=50, seed=42
    )

    # Limit labels to avoid clutter
    labels = {}
    if nxg.number_of_nodes() <= 100:
        labels = {
            n: nxg.nodes[n].get("label", n.split("::")[-1])
            for n in nxg.nodes()
        }

    nx.draw_networkx_nodes(
        nxg, pos, ax=ax, node_color=colors,
        node_size=30, alpha=0.8
    )
    nx.draw_networkx_edges(
        nxg, pos, ax=ax, alpha=0.2,
        arrows=True, arrowsize=5
    )
    if labels:
        nx.draw_networkx_labels(
            nxg, pos, labels=labels, ax=ax,
            font_size=6
        )

    ax.set_title("Code Review Graph", fontsize=14)
    ax.axis("off")

    fig.savefig(
        str(output_path), format="svg",
        bbox_inches="tight", dpi=150
    )
    plt.close(fig)

    logger.info("SVG exported to %s (%d nodes)",
                output_path, nxg.number_of_nodes())
    return output_path
