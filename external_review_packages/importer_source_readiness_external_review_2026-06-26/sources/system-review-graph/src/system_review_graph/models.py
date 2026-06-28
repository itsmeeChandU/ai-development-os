"""Typed data structures for System Review Graph manifests and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SchemaContract:
    """A public or sanitized contract a system object promises to follow."""

    name: str
    kind: str
    required_fields: list[str]
    purpose: str = ""
    example: dict[str, Any] = field(default_factory=dict)
    privacy_notes: str = ""


@dataclass(frozen=True)
class Artifact:
    """An inspectable output, report, table, API response, file, or UI surface."""

    artifact_id: str
    name: str
    kind: str
    path: str = ""
    owner: str = ""
    schema: str = ""
    purpose: str = ""
    redaction: str = "safe_to_share"


@dataclass(frozen=True)
class DecisionGate:
    """A rule or gate that decides whether the system advances, waits, or blocks."""

    gate_id: str
    name: str
    inputs: list[str]
    rules: list[dict[str, str]]
    outputs: list[str]
    human_gate: bool = False
    risk_boundary: str = ""


@dataclass(frozen=True)
class WorkflowStep:
    """One step in a system lifecycle path."""

    step_id: str
    name: str
    actor: str
    consumes: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    purpose: str = ""


@dataclass(frozen=True)
class SystemNode:
    """A major subsystem, bounded context, service, lane, or product surface."""

    system_id: str
    name: str
    purpose: str
    owner: str = ""
    language_stack: list[str] = field(default_factory=list)
    architecture_style: str = ""
    lifecycle: str = ""
    code_surfaces: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    decision_gates: list[str] = field(default_factory=list)
    truth_boundary: str = ""
    ideal_target: str = ""
    example: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    """A relationship in the generated system review graph."""

    source: str
    target: str
    relation: str
    why: str = ""


@dataclass(frozen=True)
class ChildMap:
    """A linked subsystem map in a larger system atlas."""

    map_id: str
    name: str
    path: str
    report_path: str = ""
    purpose: str = ""
    scope: str = ""
    owner: str = ""
    systems: list[str] = field(default_factory=list)
    status: str = "inferred"
    review_hint: str = ""


@dataclass(frozen=True)
class DocumentationSource:
    """A generated or maintained documentation artifact used by a review graph."""

    artifact: str
    role: str
    incorporated_information: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class KnowledgeNode:
    """A documentation-knowledge node imported from a catalog, atlas, or manifest."""

    node_id: str
    type: str
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeEdge:
    """A relationship between documentation-knowledge nodes."""

    source: str
    target: str
    relation: str
    why: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BlueprintSection:
    """A source-evidence-backed system flow for blueprint-level review."""

    section_id: str
    title: str
    purpose: str = ""
    subsystems: list[str] = field(default_factory=list)
    source_evidence: list[dict[str, str]] = field(default_factory=list)
    flow: list[dict[str, str]] = field(default_factory=list)
    control_points: list[dict[str, str]] = field(default_factory=list)
    review_questions: list[str] = field(default_factory=list)
    known_boundaries: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SystemReviewGraph:
    """Complete system review graph plus report-ready metadata."""

    title: str
    one_line: str
    generated_at: str
    scope: str
    systems: list[SystemNode]
    artifacts: list[Artifact]
    schemas: list[SchemaContract]
    gates: list[DecisionGate]
    workflows: list[WorkflowStep]
    edges: list[GraphEdge]
    child_maps: list[ChildMap]
    documentation_sources: list[DocumentationSource]
    knowledge_nodes: list[KnowledgeNode]
    knowledge_edges: list[KnowledgeEdge]
    blueprint_sections: list[BlueprintSection]
    current_truth: dict[str, Any]
    bigger_picture: str
    source_links: list[dict[str, str]]
    architecture_patterns: list[dict[str, str]]
    walkthroughs: list[dict[str, Any]]
    review_questions: list[str]
    rebuild_recipe: list[dict[str, Any]]
    known_boundaries: list[str]
