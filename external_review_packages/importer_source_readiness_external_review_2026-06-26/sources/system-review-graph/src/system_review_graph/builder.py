"""Build a System Review Graph from a public or sanitized manifest."""

from __future__ import annotations

import datetime as dt
from typing import Any

from system_review_graph.models import (
    Artifact,
    BlueprintSection,
    ChildMap,
    DecisionGate,
    DocumentationSource,
    GraphEdge,
    KnowledgeEdge,
    KnowledgeNode,
    SchemaContract,
    SystemNode,
    SystemReviewGraph,
    WorkflowStep,
)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _schema(row: dict[str, Any]) -> SchemaContract:
    return SchemaContract(
        name=str(row.get("name") or ""),
        kind=str(row.get("kind") or "contract"),
        required_fields=[str(item) for item in _list(row.get("required_fields"))],
        purpose=str(row.get("purpose") or ""),
        example=_dict(row.get("example")),
        privacy_notes=str(row.get("privacy_notes") or ""),
    )


def _artifact(row: dict[str, Any]) -> Artifact:
    return Artifact(
        artifact_id=str(row.get("artifact_id") or ""),
        name=str(row.get("name") or ""),
        kind=str(row.get("kind") or ""),
        path=str(row.get("path") or ""),
        owner=str(row.get("owner") or ""),
        schema=str(row.get("schema") or ""),
        purpose=str(row.get("purpose") or ""),
        redaction=str(row.get("redaction") or "safe_to_share"),
    )


def _gate(row: dict[str, Any]) -> DecisionGate:
    return DecisionGate(
        gate_id=str(row.get("gate_id") or ""),
        name=str(row.get("name") or ""),
        inputs=[str(item) for item in _list(row.get("inputs"))],
        rules=[
            {str(k): str(v) for k, v in _dict(rule).items()}
            for rule in _list(row.get("rules"))
        ],
        outputs=[str(item) for item in _list(row.get("outputs"))],
        human_gate=bool(row.get("human_gate")),
        risk_boundary=str(row.get("risk_boundary") or ""),
    )


def _workflow(row: dict[str, Any]) -> WorkflowStep:
    return WorkflowStep(
        step_id=str(row.get("step_id") or ""),
        name=str(row.get("name") or ""),
        actor=str(row.get("actor") or ""),
        consumes=[str(item) for item in _list(row.get("consumes"))],
        produces=[str(item) for item in _list(row.get("produces"))],
        gates=[str(item) for item in _list(row.get("gates"))],
        next_steps=[str(item) for item in _list(row.get("next_steps"))],
        purpose=str(row.get("purpose") or ""),
    )


def _system(row: dict[str, Any]) -> SystemNode:
    return SystemNode(
        system_id=str(row.get("system_id") or ""),
        name=str(row.get("name") or ""),
        purpose=str(row.get("purpose") or ""),
        owner=str(row.get("owner") or ""),
        language_stack=[str(item) for item in _list(row.get("language_stack"))],
        architecture_style=str(row.get("architecture_style") or ""),
        lifecycle=str(row.get("lifecycle") or ""),
        code_surfaces=[str(item) for item in _list(row.get("code_surfaces"))],
        artifacts=[str(item) for item in _list(row.get("artifacts"))],
        decision_gates=[str(item) for item in _list(row.get("decision_gates"))],
        truth_boundary=str(row.get("truth_boundary") or ""),
        ideal_target=str(row.get("ideal_target") or ""),
        example=_dict(row.get("example")),
    )


def _edge(row: dict[str, Any]) -> GraphEdge:
    return GraphEdge(
        source=str(row.get("source") or ""),
        target=str(row.get("target") or ""),
        relation=str(row.get("relation") or ""),
        why=str(row.get("why") or ""),
    )


def _child_map(row: dict[str, Any]) -> ChildMap:
    return ChildMap(
        map_id=str(row.get("map_id") or ""),
        name=str(row.get("name") or ""),
        path=str(row.get("path") or ""),
        report_path=str(row.get("report_path") or ""),
        purpose=str(row.get("purpose") or ""),
        scope=str(row.get("scope") or ""),
        owner=str(row.get("owner") or ""),
        systems=[str(item) for item in _list(row.get("systems"))],
        status=str(row.get("status") or "inferred"),
        review_hint=str(row.get("review_hint") or ""),
    )


def _documentation_source(row: dict[str, Any]) -> DocumentationSource:
    return DocumentationSource(
        artifact=str(row.get("artifact") or row.get("path") or ""),
        role=str(row.get("role") or ""),
        incorporated_information=[
            str(item) for item in _list(row.get("incorporated_information"))
        ],
        notes=str(row.get("notes") or ""),
    )


def _knowledge_node(row: dict[str, Any]) -> KnowledgeNode:
    attributes = _dict(row.get("attributes")).copy()
    for key, value in row.items():
        if key not in {"node_id", "id", "type", "node_type", "label", "attributes"}:
            attributes[str(key)] = value
    return KnowledgeNode(
        node_id=str(row.get("node_id") or row.get("id") or ""),
        type=str(row.get("type") or row.get("node_type") or "unknown"),
        label=str(row.get("label") or row.get("node_id") or row.get("id") or ""),
        attributes=attributes,
    )


def _knowledge_edge(row: dict[str, Any]) -> KnowledgeEdge:
    attributes = _dict(row.get("attributes")).copy()
    for key, value in row.items():
        if key not in {"source", "src", "target", "dst", "relation", "type", "why", "attributes"}:
            attributes[str(key)] = value
    return KnowledgeEdge(
        source=str(row.get("source") or row.get("src") or ""),
        target=str(row.get("target") or row.get("dst") or ""),
        relation=str(row.get("relation") or row.get("type") or ""),
        why=str(row.get("why") or ""),
        attributes=attributes,
    )


def _string_dict_list(value: Any) -> list[dict[str, str]]:
    return [
        {str(k): str(v) for k, v in _dict(row).items()}
        for row in _list(value)
    ]


def _blueprint_section(row: dict[str, Any]) -> BlueprintSection:
    return BlueprintSection(
        section_id=str(row.get("section_id") or ""),
        title=str(row.get("title") or ""),
        purpose=str(row.get("purpose") or ""),
        subsystems=[str(item) for item in _list(row.get("subsystems"))],
        source_evidence=_string_dict_list(row.get("source_evidence")),
        flow=_string_dict_list(row.get("flow")),
        control_points=_string_dict_list(row.get("control_points")),
        review_questions=[str(item) for item in _list(row.get("review_questions"))],
        known_boundaries=[str(item) for item in _list(row.get("known_boundaries"))],
    )


def _derived_edges(systems: list[SystemNode], workflows: list[WorkflowStep]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for system in systems:
        for artifact_id in system.artifacts:
            edges.append(
                GraphEdge(
                    source=system.system_id,
                    target=artifact_id,
                    relation="owns_or_uses",
                    why="system manifest declared artifact ownership/usage",
                )
            )
        for gate_id in system.decision_gates:
            edges.append(
                GraphEdge(
                    source=system.system_id,
                    target=gate_id,
                    relation="is_gated_by",
                    why="system manifest declared decision gate",
                )
            )
    for step in workflows:
        for item in step.consumes:
            edges.append(
                GraphEdge(source=item, target=step.step_id, relation="feeds", why=step.purpose)
            )
        for item in step.produces:
            edges.append(
                GraphEdge(
                    source=step.step_id,
                    target=item,
                    relation="produces",
                    why=step.purpose,
                )
            )
        for item in step.gates:
            edges.append(
                GraphEdge(source=item, target=step.step_id, relation="gates", why=step.purpose)
            )
        for item in step.next_steps:
            edges.append(
                GraphEdge(
                    source=step.step_id,
                    target=item,
                    relation="routes_to",
                    why=step.purpose,
                )
            )
    return edges


def build_system_review(manifest: dict[str, Any]) -> SystemReviewGraph:
    """Build a graph object from a manifest dictionary."""

    schemas = [_schema(row) for row in _list(manifest.get("schemas"))]
    artifacts = [_artifact(row) for row in _list(manifest.get("artifacts"))]
    gates = [_gate(row) for row in _list(manifest.get("decision_gates"))]
    workflows = [_workflow(row) for row in _list(manifest.get("workflows"))]
    systems = [_system(row) for row in _list(manifest.get("systems"))]
    explicit_edges = [_edge(row) for row in _list(manifest.get("edges"))]
    child_maps = [_child_map(row) for row in _list(manifest.get("child_maps"))]
    documentation_sources = [
        _documentation_source(row) for row in _list(manifest.get("documentation_sources"))
    ]
    knowledge_nodes = [_knowledge_node(row) for row in _list(manifest.get("knowledge_nodes"))]
    knowledge_edges = [_knowledge_edge(row) for row in _list(manifest.get("knowledge_edges"))]
    blueprint_sections = [
        _blueprint_section(row) for row in _list(manifest.get("blueprint_sections"))
    ]
    derived_edges = _derived_edges(systems, workflows)
    return SystemReviewGraph(
        title=str(manifest.get("title") or "System Review Graph"),
        one_line=str(
            manifest.get("one_line")
            or (
                "Code-review graph shows what code exists; "
                "system-review graph shows what the system does."
            )
        ),
        generated_at=_utc_now(),
        scope=str(manifest.get("scope") or ""),
        systems=systems,
        artifacts=artifacts,
        schemas=schemas,
        gates=gates,
        workflows=workflows,
        edges=[*explicit_edges, *derived_edges],
        child_maps=child_maps,
        documentation_sources=documentation_sources,
        knowledge_nodes=knowledge_nodes,
        knowledge_edges=knowledge_edges,
        blueprint_sections=blueprint_sections,
        current_truth=_dict(manifest.get("current_truth")),
        bigger_picture=str(manifest.get("bigger_picture") or ""),
        source_links=[_dict(row) for row in _list(manifest.get("source_links"))],
        architecture_patterns=[_dict(row) for row in _list(manifest.get("architecture_patterns"))],
        walkthroughs=[_dict(row) for row in _list(manifest.get("walkthroughs"))],
        review_questions=[str(item) for item in _list(manifest.get("review_questions"))],
        rebuild_recipe=[_dict(row) for row in _list(manifest.get("rebuild_recipe"))],
        known_boundaries=[str(item) for item in _list(manifest.get("known_boundaries"))],
    )
