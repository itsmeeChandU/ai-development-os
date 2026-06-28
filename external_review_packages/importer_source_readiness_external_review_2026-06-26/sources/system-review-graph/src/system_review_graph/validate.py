"""Manifest validation."""

from __future__ import annotations

from typing import Any

REQUIRED_TOP_LEVEL = {"title", "systems", "artifacts", "schemas", "decision_gates", "workflows"}


def _seen_duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _ids(rows: list[Any], key: str) -> list[str]:
    return [
        str(row.get(key))
        for row in rows
        if isinstance(row, dict) and row.get(key) is not None
    ]


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return validation errors for a manifest."""

    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(manifest))
    if missing:
        errors.append(f"missing top-level keys: {', '.join(missing)}")
    for key in (
        "systems",
        "artifacts",
        "schemas",
        "decision_gates",
        "workflows",
        "child_maps",
        "documentation_sources",
        "knowledge_nodes",
        "knowledge_edges",
        "blueprint_sections",
    ):
        if key in manifest and not isinstance(manifest[key], list):
            errors.append(f"{key} must be a list")
    systems = manifest.get("systems") or []
    artifacts = manifest.get("artifacts") or []
    gates = manifest.get("decision_gates") or []
    workflows = manifest.get("workflows") or []
    schemas = manifest.get("schemas") or []
    edges = manifest.get("edges") or []
    child_maps = manifest.get("child_maps") or []
    documentation_sources = manifest.get("documentation_sources") or []
    knowledge_nodes = manifest.get("knowledge_nodes") or []
    knowledge_edges = manifest.get("knowledge_edges") or []
    blueprint_sections = manifest.get("blueprint_sections") or []
    for label, values in (
        ("system_id", _ids(systems, "system_id")),
        ("artifact_id", _ids(artifacts, "artifact_id")),
        ("gate_id", _ids(gates, "gate_id")),
        ("step_id", _ids(workflows, "step_id")),
        ("schema name", _ids(schemas, "name")),
        ("child map_id", _ids(child_maps, "map_id")),
        (
            "knowledge node_id",
            [
                str(row.get("node_id") or row.get("id"))
                for row in knowledge_nodes
                if isinstance(row, dict) and (row.get("node_id") or row.get("id"))
            ],
        ),
        ("blueprint section_id", _ids(blueprint_sections, "section_id")),
    ):
        for duplicate in _seen_duplicates(values):
            errors.append(f"duplicate {label}: {duplicate}")
    for index, system in enumerate(manifest.get("systems") or []):
        if not isinstance(system, dict):
            errors.append(f"systems[{index}] must be an object")
            continue
        for field in ("system_id", "name", "purpose"):
            if not system.get(field):
                errors.append(f"systems[{index}] missing {field}")
    for index, child_map in enumerate(manifest.get("child_maps") or []):
        if not isinstance(child_map, dict):
            errors.append(f"child_maps[{index}] must be an object")
            continue
        for field in ("map_id", "name", "path"):
            if not child_map.get(field):
                errors.append(f"child_maps[{index}] missing {field}")
    for index, source in enumerate(documentation_sources):
        if not isinstance(source, dict):
            errors.append(f"documentation_sources[{index}] must be an object")
            continue
        if not source.get("artifact") and not source.get("path"):
            errors.append(f"documentation_sources[{index}] missing artifact")
    for index, node in enumerate(knowledge_nodes):
        if not isinstance(node, dict):
            errors.append(f"knowledge_nodes[{index}] must be an object")
            continue
        if not node.get("node_id") and not node.get("id"):
            errors.append(f"knowledge_nodes[{index}] missing node_id")
    for index, edge in enumerate(knowledge_edges):
        if not isinstance(edge, dict):
            errors.append(f"knowledge_edges[{index}] must be an object")
            continue
        if not edge.get("source") and not edge.get("src"):
            errors.append(f"knowledge_edges[{index}] missing source")
        if not edge.get("target") and not edge.get("dst"):
            errors.append(f"knowledge_edges[{index}] missing target")
        if not edge.get("relation") and not edge.get("type"):
            errors.append(f"knowledge_edges[{index}] missing relation")
    for index, section in enumerate(manifest.get("blueprint_sections") or []):
        if not isinstance(section, dict):
            errors.append(f"blueprint_sections[{index}] must be an object")
            continue
        for field in ("section_id", "title"):
            if not section.get(field):
                errors.append(f"blueprint_sections[{index}] missing {field}")
    for index, artifact in enumerate(manifest.get("artifacts") or []):
        if not isinstance(artifact, dict):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        if not artifact.get("artifact_id"):
            errors.append(f"artifacts[{index}] missing artifact_id")
    artifact_ids = {
        str(artifact.get("artifact_id"))
        for artifact in manifest.get("artifacts") or []
        if isinstance(artifact, dict) and artifact.get("artifact_id")
    }
    gate_ids = {
        str(gate.get("gate_id"))
        for gate in manifest.get("decision_gates") or []
        if isinstance(gate, dict) and gate.get("gate_id")
    }
    workflow_ids = {
        str(step.get("step_id"))
        for step in manifest.get("workflows") or []
        if isinstance(step, dict) and step.get("step_id")
    }
    schema_names = {
        str(schema.get("name"))
        for schema in manifest.get("schemas") or []
        if isinstance(schema, dict) and schema.get("name")
    }
    for index, artifact in enumerate(manifest.get("artifacts") or []):
        if not isinstance(artifact, dict):
            continue
        schema = artifact.get("schema")
        if schema and str(schema) not in schema_names:
            errors.append(f"artifacts[{index}] references unknown schema {schema}")
    for index, system in enumerate(manifest.get("systems") or []):
        if not isinstance(system, dict):
            continue
        for artifact_id in system.get("artifacts") or []:
            if str(artifact_id) not in artifact_ids:
                errors.append(f"systems[{index}] references unknown artifact {artifact_id}")
        for gate_id in system.get("decision_gates") or []:
            if str(gate_id) not in gate_ids:
                errors.append(f"systems[{index}] references unknown decision gate {gate_id}")
    for index, step in enumerate(manifest.get("workflows") or []):
        if not isinstance(step, dict):
            continue
        for gate_id in step.get("gates") or []:
            if str(gate_id) not in gate_ids:
                errors.append(f"workflows[{index}] references unknown decision gate {gate_id}")
        for next_step in step.get("next_steps") or []:
            if str(next_step) not in workflow_ids:
                errors.append(f"workflows[{index}] routes to unknown workflow step {next_step}")
    known_graph_nodes = artifact_ids | gate_ids | workflow_ids | schema_names
    known_graph_nodes.update(
        str(system.get("system_id"))
        for system in systems
        if isinstance(system, dict) and system.get("system_id")
    )
    knowledge_node_ids = {
        str(node.get("node_id") or node.get("id"))
        for node in knowledge_nodes
        if isinstance(node, dict) and (node.get("node_id") or node.get("id"))
    }
    known_graph_nodes.update(knowledge_node_ids)
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edges[{index}] must be an object")
            continue
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source:
            errors.append(f"edges[{index}] missing source")
        elif source not in known_graph_nodes:
            errors.append(f"edges[{index}] references unknown source node {source}")
        if not target:
            errors.append(f"edges[{index}] missing target")
        elif target not in known_graph_nodes:
            errors.append(f"edges[{index}] references unknown target node {target}")
    for index, edge in enumerate(knowledge_edges):
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("source") or edge.get("src") or "")
        target = str(edge.get("target") or edge.get("dst") or "")
        if source and source not in known_graph_nodes:
            errors.append(f"knowledge_edges[{index}] references unknown source node {source}")
        if target and target not in known_graph_nodes:
            errors.append(f"knowledge_edges[{index}] references unknown target node {target}")
    return errors
