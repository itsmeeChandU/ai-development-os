"""Markdown and Mermaid rendering."""

from __future__ import annotations

import json
import re
from html import escape

from system_review_graph.models import SystemReviewGraph

REPORT_DEPTHS = {"overview", "standard", "deep", "blueprint"}
STANDARD_DEPTHS = {"standard", "deep", "blueprint"}
DEEP_DEPTHS = {"deep", "blueprint"}


def _row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def _code_list(values: list[str]) -> str:
    if not values:
        return "`none`"
    return ", ".join(f"`{value}`" for value in values)


def _value(value: object) -> str:
    if isinstance(value, bool | int | float) or value is None:
        return json.dumps(value)
    if isinstance(value, list | dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _node_id(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]", "_", value)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return "node"
    if cleaned[0].isdigit():
        return f"n_{cleaned}"
    return cleaned


def _label(value: str) -> str:
    return value.replace('"', "'")


def _report_relative_child_manifest_path(report_path: str, manifest_path: str) -> str:
    if (
        report_path.startswith("../")
        and manifest_path
        and not manifest_path.startswith("../")
        and "://" not in manifest_path
    ):
        return f"../{manifest_path}"
    return manifest_path


def _relation(value: str) -> str:
    return value.replace("_", " ")


def _as_set(values: list[str]) -> set[str]:
    return {value for value in values if value}


def _label_map(graph: SystemReviewGraph) -> dict[str, str]:
    labels: dict[str, str] = {}
    labels.update({system.system_id: system.name for system in graph.systems})
    labels.update({artifact.artifact_id: artifact.name for artifact in graph.artifacts})
    labels.update({gate.gate_id: gate.name for gate in graph.gates})
    labels.update({step.step_id: step.name for step in graph.workflows})
    labels.update({schema.name: schema.name for schema in graph.schemas})
    labels.update({child_map.map_id: child_map.name for child_map in graph.child_maps})
    labels.update(
        {section.section_id: section.title for section in graph.blueprint_sections}
    )
    labels.update({node.node_id: node.label for node in graph.knowledge_nodes})
    return labels


def _artifact_map(graph: SystemReviewGraph):
    return {artifact.artifact_id: artifact for artifact in graph.artifacts}


def _gate_map(graph: SystemReviewGraph):
    return {gate.gate_id: gate for gate in graph.gates}


def _schema_map(graph: SystemReviewGraph):
    return {schema.name: schema for schema in graph.schemas}


def _touches_system(step, system) -> bool:
    system_refs = _as_set(system.artifacts + system.decision_gates + system.code_surfaces)
    system_refs.update({system.system_id, system.name})
    step_refs = _as_set(step.consumes + step.produces + step.gates + step.next_steps)
    step_refs.update({step.actor})
    return bool(system_refs & step_refs) or step.actor == system.name


def render_lifecycle_mermaid(graph: SystemReviewGraph) -> str:
    """Render the workflow lifecycle as a compact left-to-right map."""

    labels = _label_map(graph)
    lines = ["flowchart LR"]
    for step in graph.workflows:
        lines.append(f'  {_node_id(step.step_id)}["{_label(labels.get(step.step_id, step.name))}"]')
    for step in graph.workflows:
        for next_step in step.next_steps:
            next_label = labels.get(next_step, next_step)
            lines.append(
                f'  {_node_id(step.step_id)} --> {_node_id(next_step)}["{_label(next_label)}"]'
            )
    if len(lines) == 1:
        lines.append('  empty["No workflow steps declared"]')
    return "\n".join(lines)


def render_child_maps_mermaid(graph: SystemReviewGraph) -> str:
    """Render a root atlas -> child subsystem maps graph."""

    lines = ["flowchart TD", f'  root["{_label(graph.title)}"]']
    for child_map in graph.child_maps:
        node = _node_id(f"child_{child_map.map_id}")
        label = child_map.name
        if child_map.status:
            label = f"{label}\\n{child_map.status}"
        lines.append(f'  root --> {node}["{_label(label)}"]')
        for system_id in child_map.systems[:8]:
            system_node = _node_id(f"child_{child_map.map_id}_{system_id}")
            lines.append(f'  {node} --> {system_node}["{_label(system_id)}"]')
    if len(lines) == 2:
        lines.append('  empty["No child maps declared"]')
    return "\n".join(lines)


def render_blueprint_mermaid(graph: SystemReviewGraph) -> str:
    """Render blueprint sections and their subsystem coverage."""

    lines = ["flowchart TD", f'  root["{_label(graph.title)}"]']
    if not graph.blueprint_sections:
        lines.append('  empty["No blueprint sections declared"]')
        return "\n".join(lines)
    for section in graph.blueprint_sections:
        section_node = _node_id(f"blueprint_{section.section_id}")
        lines.append(f'  root --> {section_node}["{_label(section.title)}"]')
        for subsystem in section.subsystems[:10]:
            subsystem_node = _node_id(f"blueprint_{section.section_id}_{subsystem}")
            lines.append(f'  {section_node} --> {subsystem_node}["{_label(subsystem)}"]')
    return "\n".join(lines)


def render_artifact_mermaid(graph: SystemReviewGraph) -> str:
    """Render system -> artifact -> schema relationships."""

    labels = _label_map(graph)
    lines = ["flowchart LR"]
    for system in graph.systems:
        system_id = _node_id(f"system_{system.system_id}")
        lines.append(f'  {system_id}["{_label(system.name)}"]')
        for artifact_id in system.artifacts:
            artifact_label = labels.get(artifact_id, artifact_id)
            artifact_node = _node_id(f"artifact_{artifact_id}")
            lines.append(f'  {system_id} --> {artifact_node}["{_label(artifact_label)}"]')
            artifact = _artifact_map(graph).get(artifact_id)
            if artifact and artifact.schema:
                schema_node = _node_id(f"schema_{artifact.schema}")
                lines.append(
                    f'  {artifact_node} --> {schema_node}["{_label(artifact.schema)}"]'
                )
    if len(lines) == 1:
        lines.append('  empty["No artifacts declared"]')
    return "\n".join(lines)


def render_gate_mermaid(graph: SystemReviewGraph) -> str:
    """Render gates around workflow steps."""

    labels = _label_map(graph)
    lines = ["flowchart LR"]
    for gate in graph.gates:
        gate_node = _node_id(f"gate_{gate.gate_id}")
        lines.append(f'  {gate_node}{{"{_label(gate.name)}"}}')
        for output in gate.outputs:
            output_node = _node_id(f"out_{gate.gate_id}_{output}")
            lines.append(f'  {gate_node} --> {output_node}["{_label(output)}"]')
    for step in graph.workflows:
        step_node = _node_id(f"step_{step.step_id}")
        for gate_id in step.gates:
            gate_label = labels.get(gate_id, gate_id)
            gate_node = _node_id(f"gate_{gate_id}")
            lines.append(
                f'  {gate_node}{{"{_label(gate_label)}"}} '
                f'--> {step_node}["{_label(step.name)}"]'
            )
    if len(lines) == 1:
        lines.append('  empty["No decision gates declared"]')
    return "\n".join(lines)


def render_mermaid(graph: SystemReviewGraph) -> str:
    """Render a compact Mermaid flowchart."""

    labels = _label_map(graph)
    lines = ["flowchart TD"]
    for edge in graph.edges[:80]:
        source = _node_id(edge.source)
        target = _node_id(edge.target)
        label = _label(_relation(edge.relation))
        source_label = _label(labels.get(edge.source, edge.source))
        target_label = _label(labels.get(edge.target, edge.target))
        lines.append(
            f'  {source}["{source_label}"] -- "{label}" --> {target}["{target_label}"]'
        )
    for child_map in graph.child_maps[:40]:
        target = _node_id(child_map.map_id)
        target_label = _label(labels.get(child_map.map_id, child_map.name))
        lines.append(f'  root_atlas["Atlas"] -- "links to" --> {target}["{target_label}"]')
    return "\n".join(lines)


def render_graphviz_dot(graph: SystemReviewGraph) -> str:
    """Render the relationship graph as Graphviz DOT."""

    labels = _label_map(graph)
    lines = [
        "digraph system_review_graph {",
        "  rankdir=LR;",
        '  graph [fontname="Helvetica"];',
        '  node [shape=box, style="rounded", fontname="Helvetica"];',
        '  edge [fontname="Helvetica"];',
    ]
    for edge in graph.edges:
        source = _node_id(edge.source)
        target = _node_id(edge.target)
        source_label = labels.get(edge.source, edge.source).replace('"', "'")
        target_label = labels.get(edge.target, edge.target).replace('"', "'")
        relation = _relation(edge.relation).replace('"', "'")
        lines.append(f'  {source} [label="{source_label}"];')
        lines.append(f'  {target} [label="{target_label}"];')
        lines.append(f'  {source} -> {target} [label="{relation}"];')
    for child_map in graph.child_maps:
        target = _node_id(child_map.map_id)
        target_label = child_map.name.replace('"', "'")
        lines.append('  root_atlas [label="Atlas"];')
        lines.append(f'  {target} [label="{target_label}"];')
        lines.append(f'  root_atlas -> {target} [label="links to"];')
    lines.append("}")
    return "\n".join(lines)


def _blueprint_evidence_count(graph: SystemReviewGraph) -> int:
    return sum(len(section.source_evidence) for section in graph.blueprint_sections)


def _coverage_register_rows(graph: SystemReviewGraph) -> list[list[object]]:
    return [
        [
            "Systems",
            len(graph.systems),
            "Bounded contexts, services, subsystems, or product surfaces.",
            "Use this to see whether the report maps the main operating areas.",
        ],
        [
            "Artifacts",
            len(graph.artifacts),
            "Inspectable files, APIs, tables, dashboards, reports, or outputs.",
            "Use this to trace where system claims can be inspected.",
        ],
        [
            "Schemas/contracts",
            len(graph.schemas),
            "Public or sanitized contracts for artifacts and handoffs.",
            "Use this to rebuild examples without touching private data.",
        ],
        [
            "Decision gates",
            len(graph.gates),
            "Rules that advance, wait, block, or require human review.",
            "Use this to find where the system controls action.",
        ],
        [
            "Workflows",
            len(graph.workflows),
            "Lifecycle steps from input to output.",
            "Use this to follow what happens end to end.",
        ],
        [
            "Graph edges",
            len(graph.edges),
            "Explicit and derived relationships between manifest nodes.",
            "Use this to audit connectivity and missing relationships.",
        ],
        [
            "Child maps",
            len(graph.child_maps),
            "Linked subsystem maps for large repositories.",
            "Use this to drill into a map-of-maps instead of one flat report.",
        ],
        [
            "Blueprint sections",
            len(graph.blueprint_sections),
            "Source-evidence-backed operating flows.",
            "Use this to review deep behavior claims with proof anchors.",
        ],
        [
            "Blueprint evidence rows",
            _blueprint_evidence_count(graph),
            "Source paths, symbols, roles, and proof levels.",
            "Use this to verify whether blueprint claims are source-backed.",
        ],
        [
            "Documentation sources",
            len(graph.documentation_sources),
            "Generated or maintained docs/catalogs used by the report.",
            "Use this to see where repo knowledge entered the review graph.",
        ],
        [
            "Knowledge nodes",
            len(graph.knowledge_nodes),
            "Concept, file, owner, stage, status, or other documentation graph nodes.",
            "Use this to traverse the repo documentation rather than reading prose only.",
        ],
        [
            "Knowledge edges",
            len(graph.knowledge_edges),
            "Relationships between documentation graph nodes.",
            "Use this to answer linked questions such as concept -> files -> cleanup state.",
        ],
        [
            "Source links",
            len(graph.source_links),
            "External or public references used by the report.",
            "Use this to confirm the report's public evidence base.",
        ],
        [
            "Known boundaries",
            len(graph.known_boundaries)
            + sum(len(section.known_boundaries) for section in graph.blueprint_sections),
            "Open limits, unproven claims, redactions, or scope exclusions.",
            "Use this to avoid treating the report as stronger than it is.",
        ],
        [
            "Review questions",
            len(graph.review_questions)
            + sum(len(section.review_questions) for section in graph.blueprint_sections),
            "Questions a maintainer, auditor, or agent should answer next.",
            "Use this as the human follow-up queue.",
        ],
        [
            "Rebuild phases",
            len(graph.rebuild_recipe),
            "Documented commands or phases for reproducing the report.",
            "Use this to regenerate or verify the report locally.",
        ],
    ]


def _evidence_register_rows(graph: SystemReviewGraph) -> list[list[object]]:
    rows: list[list[object]] = []
    for source in graph.source_links:
        label = source.get("label", "") or source.get("url", "") or "source"
        url = source.get("url", "")
        notes = source.get("notes", "")
        evidence = f"[{label}]({url})" if label and url else label
        rows.append([evidence, "source link", "whole report", "declared", notes])
    for source in graph.documentation_sources:
        rows.append(
            [
                source.artifact,
                "documentation source",
                source.role,
                "declared",
                ", ".join(source.incorporated_information) or source.notes,
            ]
        )
    for section in graph.blueprint_sections:
        for evidence in section.source_evidence:
            path = evidence.get("path", "")
            symbol = evidence.get("symbol", "")
            role = evidence.get("role", "")
            proof_level = evidence.get("proof_level", "") or "declared"
            notes = evidence.get("notes", "")
            label = path if not symbol else f"{path} ({symbol})"
            coverage = section.title
            if role:
                coverage = f"{coverage}: {role}"
            rows.append([label, "blueprint evidence", coverage, proof_level, notes])
    for artifact in graph.artifacts:
        if not artifact.path:
            continue
        proof = artifact.redaction or "declared"
        coverage = artifact.owner or "artifact"
        rows.append([artifact.path, artifact.kind or "artifact", coverage, proof, artifact.purpose])
    for schema in graph.schemas:
        fields = ", ".join(schema.required_fields) if schema.required_fields else "no fields listed"
        rows.append(
            [
                schema.name,
                schema.kind or "schema",
                fields,
                "contract declared",
                schema.purpose,
            ]
        )
    if not rows:
        rows.append(
            [
                "No evidence rows declared",
                "gap",
                "whole report",
                "not proven",
                "Add source links, artifacts, schemas, or blueprint evidence.",
            ]
        )
    return rows


def _gap_register_rows(graph: SystemReviewGraph) -> list[list[object]]:
    rows: list[list[object]] = []
    for item in graph.known_boundaries:
        rows.append(
            [
                "Known boundary",
                "whole report",
                "open",
                item,
                "Accept the boundary or add evidence that closes it.",
            ]
        )
    for system in graph.systems:
        if system.truth_boundary:
            rows.append(
                [
                    "System truth boundary",
                    system.name,
                    "review",
                    system.truth_boundary,
                    "Inspect this boundary before making stronger behavior claims.",
                ]
            )
    for section in graph.blueprint_sections:
        for item in section.known_boundaries:
            rows.append(
                [
                    "Blueprint gap",
                    section.title,
                    "open",
                    item,
                    "Add source evidence, tests, traces, or child-map detail.",
                ]
            )
        if not section.source_evidence:
            rows.append(
                [
                    "Blueprint evidence missing",
                    section.title,
                    "open",
                    "Blueprint section has no source evidence rows.",
                    "Add source paths, symbols, roles, and proof levels.",
                ]
            )
    if not graph.source_links:
        rows.append(
            [
                "Source links missing",
                "whole report",
                "open",
                "No external source links were declared.",
                "Add public repo, docs, issue, or design references.",
            ]
        )
    if not graph.gates:
        rows.append(
            [
                "Decision gates missing",
                "whole report",
                "open",
                "No decision gates were declared.",
                "Add the rules that advance, wait, block, or require human review.",
            ]
        )
    if not graph.workflows:
        rows.append(
            [
                "Workflow missing",
                "whole report",
                "open",
                "No lifecycle workflow was declared.",
                "Add the input -> transform -> gate -> output path.",
            ]
        )
    if graph.systems and not graph.artifacts:
        rows.append(
            [
                "Artifacts missing",
                "whole report",
                "open",
                "Systems exist without inspectable artifacts.",
                "Add files, APIs, tables, dashboards, reports, or logs.",
            ]
        )
    if len(graph.systems) > 12 and not graph.child_maps:
        rows.append(
            [
                "Large map without child maps",
                "whole report",
                "review",
                "Many systems are declared but no linked child maps exist.",
                "Split into an atlas if the report becomes hard to navigate.",
            ]
        )
    if graph.documentation_sources and not graph.knowledge_nodes:
        rows.append(
            [
                "Documentation graph not imported",
                "documentation",
                "review",
                "Documentation sources exist but no knowledge nodes were declared.",
                "Import concept/file/status nodes or load graph JSONL through MCP.",
            ]
        )
    if not graph.blueprint_sections:
        rows.append(
            [
                "Blueprint not declared",
                "whole report",
                "optional",
                "No source-backed blueprint sections were declared.",
                "Add blueprint sections when the report needs source-level proof.",
            ]
        )
    if not rows:
        rows.append(
            [
                "No open gaps declared",
                "whole report",
                "clear",
                "The report declared no known boundaries or generated gaps.",
                "Still verify against source, runtime behavior, and maintainer review.",
            ]
        )
    return rows


def _action_register_rows(graph: SystemReviewGraph) -> list[list[object]]:
    rows: list[list[object]] = []
    for question in graph.review_questions:
        rows.append(
            [
                "Review question",
                "maintainer / auditor",
                "open",
                question,
                "Answer from source, tests, docs, logs, or maintainer knowledge.",
            ]
        )
    for section in graph.blueprint_sections:
        for question in section.review_questions:
            rows.append(
                [
                    "Blueprint review",
                    "maintainer / auditor",
                    "open",
                    f"{section.title}: {question}",
                    "Answer before using this blueprint as a final architecture claim.",
                ]
            )
        for boundary in section.known_boundaries:
            rows.append(
                [
                    "Close blueprint gap",
                    "maintainer / auditor",
                    "open",
                    f"{section.title}: {boundary}",
                    "Add evidence or explicitly preserve the boundary.",
                ]
            )
    for boundary in graph.known_boundaries:
        rows.append(
            [
                "Resolve boundary",
                "maintainer / auditor",
                "open",
                boundary,
                "Accept as scope or add proof that closes it.",
            ]
        )
    for phase in graph.rebuild_recipe:
        rows.append(
            [
                "Rebuild phase",
                "maintainer / agent",
                "repeatable",
                phase.get("phase", "phase"),
                phase.get("goal", ""),
            ]
        )
    if not rows:
        rows.append(
            [
                "Add action queue",
                "maintainer",
                "open",
                "No review questions, boundaries, or rebuild phases were declared.",
                "Add at least one concrete next action for reviewers.",
            ]
        )
    return rows


def _register_limit(depth: str) -> int:
    if depth == "overview":
        return 20
    if depth == "standard":
        return 80
    return 200


def _limited_rows(rows: list[list[object]], depth: str) -> tuple[list[list[object]], int]:
    limit = _register_limit(depth)
    return rows[:limit], max(0, len(rows) - limit)


def _html_table(headers: list[str], rows: list[list[object]], class_name: str = "") -> str:
    class_attr = f' class="{escape(class_name)}"' if class_name else ""
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{_html_cell(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f"<table{class_attr}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _html_cell(value: object) -> str:
    text = str(value)
    markdown_link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", text)
    if markdown_link:
        label, url = markdown_link.groups()
        return f'<a href="{escape(url)}">{escape(label)}</a>'
    return escape(text)


def _html_register_section(graph: SystemReviewGraph, depth: str) -> str:
    evidence_rows, evidence_omitted = _limited_rows(_evidence_register_rows(graph), depth)
    gap_rows, gap_omitted = _limited_rows(_gap_register_rows(graph), depth)
    action_rows, action_omitted = _limited_rows(_action_register_rows(graph), depth)
    coverage_table = _html_table(
        ["Area", "Count", "What It Means", "Reviewer Use"],
        _coverage_register_rows(graph),
    )
    evidence_table = _html_table(
        ["Evidence", "Kind", "Coverage", "Proof", "Reviewer Use"], evidence_rows
    )
    gap_table = _html_table(["Gap", "Area", "Status", "Boundary", "Next Step"], gap_rows)
    action_table = _html_table(
        ["Action", "Owner", "Status", "Trigger", "Expected Output"], action_rows
    )
    omitted_parts = [
        f"{count} {name} rows omitted"
        for name, count in [
            ("evidence", evidence_omitted),
            ("gap", gap_omitted),
            ("action", action_omitted),
        ]
        if count
    ]
    omitted = ""
    if omitted_parts:
        omitted = f"<p>{escape('; '.join(omitted_parts))}. Use Markdown or JSON for full audit.</p>"
    return f"""
    <section>
      <h2>Report Registers</h2>
      <h3>Coverage Register</h3>
      {coverage_table}
      <h3>Evidence Register</h3>
      {evidence_table}
      <h3>Gap Register</h3>
      {gap_table}
      <h3>Action Register</h3>
      {action_table}
      {omitted}
    </section>
    """


def render_html(graph: SystemReviewGraph, depth: str = "deep") -> str:
    """Render a standalone HTML report with Mermaid diagrams."""

    if depth not in REPORT_DEPTHS:
        raise ValueError(f"depth must be one of: {', '.join(sorted(REPORT_DEPTHS))}")
    source_links = "\n".join(
        f'<li><a href="{escape(source.get("url", ""))}">{escape(source.get("label", ""))}</a>'
        f' - {escape(source.get("notes", ""))}</li>'
        for source in graph.source_links
    )
    system_cards = "\n".join(
        f"""
        <article class="card" id="{escape(system.system_id)}">
          <h3>{escape(system.name)}</h3>
          <p>{escape(system.purpose)}</p>
          <dl>
            <dt>Architecture</dt><dd>{escape(system.architecture_style)}</dd>
            <dt>Lifecycle</dt><dd>{escape(system.lifecycle)}</dd>
            <dt>Boundary</dt><dd>{escape(system.truth_boundary)}</dd>
          </dl>
        </article>
        """
        for system in graph.systems
    )
    review_questions = "\n".join(f"<li>{escape(item)}</li>" for item in graph.review_questions)
    child_report_href = {
        child_map.map_id: escape(child_map.report_path or child_map.path)
        for child_map in graph.child_maps
    }
    child_manifest_href = {
        child_map.map_id: escape(
            _report_relative_child_manifest_path(child_map.report_path, child_map.path)
        )
        for child_map in graph.child_maps
    }
    child_rows = "\n".join(
        f"""
        <tr>
          <td><a href="{child_report_href[child_map.map_id]}">{escape(child_map.name)}</a></td>
          <td><a href="{child_manifest_href[child_map.map_id]}">manifest</a></td>
          <td>{escape(child_map.status)}</td>
          <td>{escape(child_map.scope)}</td>
          <td>{escape(child_map.review_hint)}</td>
        </tr>
        """
        for child_map in graph.child_maps
    )
    child_map_section = (
        f"""
        <section>
          <h2>Map Of Maps</h2>
          <pre class="mermaid">{escape(render_child_maps_mermaid(graph))}</pre>
          <table>
            <thead>
              <tr>
                <th>Child map</th><th>Manifest</th><th>Status</th>
                <th>Scope</th><th>Review hint</th>
              </tr>
            </thead>
            <tbody>{child_rows}</tbody>
          </table>
        </section>
        """
        if graph.child_maps
        else ""
    )
    blueprint_rows = "\n".join(
        f"""
        <tr>
          <td>{escape(section.title)}</td>
          <td>{escape(section.purpose)}</td>
          <td>{escape(", ".join(section.subsystems))}</td>
          <td>{len(section.source_evidence)}</td>
          <td>{len(section.flow)}</td>
          <td>{len(section.control_points)}</td>
        </tr>
        """
        for section in graph.blueprint_sections
    )
    blueprint_detail_section = (
        f"""
        <section>
          <h2>Blueprint Sections</h2>
          <table>
            <thead>
              <tr>
                <th>Section</th><th>Purpose</th><th>Subsystems</th>
                <th>Evidence</th><th>Flow</th><th>Controls</th>
              </tr>
            </thead>
            <tbody>{blueprint_rows}</tbody>
          </table>
        </section>
        """
        if graph.blueprint_sections
        else ""
    )
    artifact_map = (
        f"""
        <section>
          <h2>Artifact And Schema Map</h2>
          <pre class="mermaid">{escape(render_artifact_mermaid(graph))}</pre>
        </section>
        <section>
          <h2>Gate Map</h2>
          <pre class="mermaid">{escape(render_gate_mermaid(graph))}</pre>
        </section>
        """
        if depth in STANDARD_DEPTHS
        else ""
    )
    relationship_graph = (
        f"""
        <section>
          <h2>Relationship Graph</h2>
          <pre class="mermaid">{escape(render_mermaid(graph))}</pre>
        </section>
        """
        if depth in DEEP_DEPTHS
        else ""
    )
    blueprint_section = (
        f"""
        <section>
          <h2>Blueprint Map</h2>
          <pre class="mermaid">{escape(render_blueprint_mermaid(graph))}</pre>
        </section>
        """
        if graph.blueprint_sections
        else ""
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(graph.title)}</title>
  <style>
    body {{
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
      margin: 0;
      color: #18202a;
      background: #f8fafc;
    }}
    header {{ padding: 40px 32px; background: #172033; color: white; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px; }}
    section {{
      margin: 24px 0;
      padding: 24px;
      background: white;
      border: 1px solid #dbe3ee;
      border-radius: 10px;
    }}
    h1, h2, h3 {{ line-height: 1.2; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .pill {{ padding: 6px 10px; border: 1px solid rgba(255,255,255,.32); border-radius: 999px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
    }}
    .card {{ padding: 18px; border: 1px solid #dbe3ee; border-radius: 10px; background: #fbfdff; }}
    dt {{ font-weight: 700; margin-top: 10px; }}
    dd {{ margin-left: 0; color: #465466; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #dbe3ee; padding: 10px 8px; text-align: left; }}
    a {{ color: #1456cc; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(graph.title)}</h1>
    <p>{escape(graph.one_line)}</p>
    <div class="meta">
      <span class="pill">Depth: {escape(depth)}</span>
      <span class="pill">Systems: {len(graph.systems)}</span>
      <span class="pill">Artifacts: {len(graph.artifacts)}</span>
      <span class="pill">Gates: {len(graph.gates)}</span>
      <span class="pill">Workflows: {len(graph.workflows)}</span>
    </div>
  </header>
  <main>
    <section>
      <h2>Bigger Picture</h2>
      <p>{escape(graph.bigger_picture)}</p>
    </section>
    <section>
      <h2>Source Links</h2>
      <ul>{source_links}</ul>
    </section>
    {_html_register_section(graph, depth)}
    <section>
      <h2>Lifecycle Map</h2>
      <pre class="mermaid">{escape(render_lifecycle_mermaid(graph))}</pre>
    </section>
    {blueprint_section}
    {blueprint_detail_section}
    {child_map_section}
    {artifact_map}
    {relationship_graph}
    <section>
      <h2>Systems</h2>
      <div class="grid">{system_cards}</div>
    </section>
    <section>
      <h2>Review Questions</h2>
      <ul>{review_questions}</ul>
    </section>
  </main>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true, securityLevel: 'strict' }});
  </script>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def _add_visuals(lines: list[str], graph: SystemReviewGraph, depth: str) -> None:
    if graph.child_maps:
        lines.extend(
            [
                "",
                "## Map Of Maps",
                "",
                "```mermaid",
                render_child_maps_mermaid(graph),
                "```",
            ]
        )
    if graph.blueprint_sections:
        lines.extend(
            [
                "",
                "## Blueprint Map",
                "",
                "```mermaid",
                render_blueprint_mermaid(graph),
                "```",
            ]
        )
    lines.extend(
        [
            "",
            "## Lifecycle Map",
            "",
            "```mermaid",
            render_lifecycle_mermaid(graph),
            "```",
        ]
    )
    if depth in STANDARD_DEPTHS:
        lines.extend(
            [
                "",
                "## Artifact And Schema Map",
                "",
                "```mermaid",
                render_artifact_mermaid(graph),
                "```",
                "",
                "## Gate Map",
                "",
                "```mermaid",
                render_gate_mermaid(graph),
                "```",
            ]
        )
    if depth in DEEP_DEPTHS:
        lines.extend(
            [
                "",
                "## Relationship Graph",
                "",
                "```mermaid",
                render_mermaid(graph),
                "```",
            ]
        )


def _add_report_registers(lines: list[str], graph: SystemReviewGraph, depth: str) -> None:
    evidence_rows, evidence_omitted = _limited_rows(_evidence_register_rows(graph), depth)
    gap_rows, gap_omitted = _limited_rows(_gap_register_rows(graph), depth)
    action_rows, action_omitted = _limited_rows(_action_register_rows(graph), depth)
    lines.extend(
        [
            "",
            "## Report Registers",
            "",
            "These registers turn the map into an audit surface: what is covered, "
            "what evidence supports it, what remains open, and what a reviewer "
            "should do next.",
            "",
            "### Coverage Register",
            "",
            "| Area | Count | What It Means | Reviewer Use |",
            "|---|---:|---|---|",
        ]
    )
    for row in _coverage_register_rows(graph):
        lines.append(_row(row))
    lines.extend(
        [
            "",
            "### Evidence Register",
            "",
            "| Evidence | Kind | Coverage | Proof | Reviewer Use |",
            "|---|---|---|---|---|",
        ]
    )
    for row in evidence_rows:
        lines.append(_row(row))
    if evidence_omitted:
        lines.extend(
            [
                "",
                f"{evidence_omitted} additional evidence rows omitted at `{depth}` depth.",
            ]
        )
    lines.extend(
        [
            "",
            "### Gap Register",
            "",
            "| Gap | Area | Status | Boundary | Next Step |",
            "|---|---|---|---|---|",
        ]
    )
    for row in gap_rows:
        lines.append(_row(row))
    if gap_omitted:
        lines.extend(["", f"{gap_omitted} additional gap rows omitted at `{depth}` depth."])
    lines.extend(
        [
            "",
            "### Action Register",
            "",
            "| Action | Owner | Status | Trigger | Expected Output |",
            "|---|---|---|---|---|",
        ]
    )
    for row in action_rows:
        lines.append(_row(row))
    if action_omitted:
        lines.extend(["", f"{action_omitted} additional action rows omitted at `{depth}` depth."])


def _add_expansion_index(lines: list[str], graph: SystemReviewGraph, depth: str) -> None:
    lines.extend(
        [
            "",
            "## Expansion Index",
            "",
            "| Level | Use It To Answer | Report Section |",
            "|---|---|---|",
            _row(["0. Situation", "What is true now?", "Current Truth"]),
            _row(
                [
                    "0.25. Registers",
                    "What is covered, proven, open, and actionable?",
                    "Report Registers",
                ]
            ),
            _row(["0.5. Atlas", "Which child map should I open next?", "Map Of Maps"]),
            _row(
                [
                    "0.6. Documentation",
                    "How do repo docs, files, concepts, and cleanup states connect?",
                    "Documentation Knowledge Graph",
                ]
            ),
            _row(
                [
                    "0.75. Blueprint",
                    "Which source-backed flows explain the whole system?",
                    "Blueprint Sections",
                ]
            ),
            _row(["1. Flow", "How does the system move end to end?", "Lifecycle Map"]),
            _row(
                [
                    "2. Ownership",
                    "Which subsystem owns which artifact?",
                    "Artifact And Schema Map",
                ]
            ),
            _row(["3. Control", "Which rules advance, wait, or block?", "Gate Map"]),
            _row(
                [
                    "4. Implementation",
                    "Which files, APIs, docs, or outputs should I inspect?",
                    "System Details",
                ]
            ),
            _row(["5. Audit", "What should an external reviewer ask next?", "Review Questions"]),
        ]
    )
    if depth == "overview":
        lines.extend(
            [
                "",
                "This is an overview report. Rebuild with `--depth standard` or `--depth deep` "
                "to expand artifacts, gates, schemas, workflows, and per-system drill-downs.",
            ]
        )


def _add_system_details(lines: list[str], graph: SystemReviewGraph, depth: str) -> None:
    artifacts = _artifact_map(graph)
    gates = _gate_map(graph)
    lines.extend(["", "## System Details", ""])
    for system in graph.systems:
        lines.extend(
            [
                f"### {system.name}",
                "",
                f"- Purpose: {system.purpose}",
                f"- Code surfaces: {_code_list(system.code_surfaces)}",
                f"- Artifacts: {_code_list(system.artifacts)}",
                f"- Decision gates: {_code_list(system.decision_gates)}",
                f"- Boundary: {system.truth_boundary or 'Not declared.'}",
                f"- Ideal target: {system.ideal_target or 'Not declared.'}",
                "",
            ]
        )
        if depth not in DEEP_DEPTHS:
            continue
        if system.artifacts:
            lines.extend(
                [
                    "Artifact expansion:",
                    "",
                    "| Artifact | Kind | Schema | Path | Why It Matters |",
                    "|---|---|---|---|---|",
                ]
            )
            for artifact_id in system.artifacts:
                artifact = artifacts.get(artifact_id)
                if not artifact:
                    lines.append(
                        _row(
                            [
                                artifact_id,
                                "missing",
                                "",
                                "",
                                "Manifest reference not found.",
                            ]
                        )
                    )
                    continue
                lines.append(
                    _row(
                        [
                            artifact.name,
                            artifact.kind,
                            artifact.schema,
                            artifact.path,
                            artifact.purpose,
                        ]
                    )
                )
            lines.append("")
        if system.decision_gates:
            lines.extend(
                [
                    "Gate expansion:",
                    "",
                    "| Gate | Inputs | Outputs | Risk Boundary |",
                    "|---|---|---|---|",
                ]
            )
            for gate_id in system.decision_gates:
                gate = gates.get(gate_id)
                if not gate:
                    lines.append(_row([gate_id, "missing", "", "Manifest reference not found."]))
                    continue
                lines.append(
                    _row(
                        [
                            gate.name,
                            ", ".join(gate.inputs),
                            ", ".join(gate.outputs),
                            gate.risk_boundary,
                        ]
                    )
                )
            lines.append("")
        touchpoints = [step for step in graph.workflows if _touches_system(step, system)]
        if touchpoints:
            lines.extend(
                [
                    "Workflow touchpoints:",
                    "",
                    "| Step | Actor | Consumes | Produces | Gates |",
                    "|---|---|---|---|---|",
                ]
            )
            for step in touchpoints:
                lines.append(
                    _row(
                        [
                            step.name,
                            step.actor,
                            ", ".join(step.consumes),
                            ", ".join(step.produces),
                            ", ".join(step.gates),
                        ]
                    )
                )
            lines.append("")


def _add_child_maps(lines: list[str], graph: SystemReviewGraph) -> None:
    if not graph.child_maps:
        return
    lines.extend(
        [
            "",
            "## Child Maps",
            "",
            "| Map | Manifest | Status | Scope | Systems | Review Hint |",
            "|---|---|---|---|---|---|",
        ]
    )
    for child_map in graph.child_maps:
        link_path = child_map.report_path or child_map.path
        link = f"[{child_map.name}]({link_path})" if link_path else child_map.name
        manifest_path = _report_relative_child_manifest_path(child_map.report_path, child_map.path)
        manifest_link = f"[manifest]({manifest_path})" if manifest_path else ""
        lines.append(
            _row(
                [
                    link,
                    manifest_link,
                    child_map.status,
                    child_map.scope,
                    ", ".join(child_map.systems),
                    child_map.review_hint,
                ]
            )
        )


def _add_documentation_knowledge_graph(
    lines: list[str], graph: SystemReviewGraph, depth: str
) -> None:
    if not graph.documentation_sources and not graph.knowledge_nodes and not graph.knowledge_edges:
        return
    lines.extend(["", "## Documentation Knowledge Graph", ""])
    if graph.documentation_sources:
        lines.extend(
            [
                "| Source Artifact | Role | Information Incorporated | Notes |",
                "|---|---|---|---|",
            ]
        )
        for source in graph.documentation_sources:
            lines.append(
                _row(
                    [
                        source.artifact,
                        source.role,
                        ", ".join(source.incorporated_information),
                        source.notes,
                    ]
                )
            )
        lines.append("")
    node_counts: dict[str, int] = {}
    for node in graph.knowledge_nodes:
        node_counts[node.type] = node_counts.get(node.type, 0) + 1
    edge_counts: dict[str, int] = {}
    for edge in graph.knowledge_edges:
        edge_counts[edge.relation] = edge_counts.get(edge.relation, 0) + 1
    if node_counts:
        lines.extend(["Node types:", "", "| Type | Count |", "|---|---:|"])
        for key, value in sorted(node_counts.items()):
            lines.append(_row([key, value]))
        lines.append("")
    if edge_counts:
        lines.extend(["Edge relations:", "", "| Relation | Count |", "|---|---:|"])
        for key, value in sorted(edge_counts.items()):
            lines.append(_row([key, value]))
        lines.append("")
    limit = 20 if depth == "overview" else 80 if depth == "standard" else 200
    if graph.knowledge_nodes:
        lines.extend(
            [
                "Sample nodes:",
                "",
                "| Node | Type | Label | Key Attributes |",
                "|---|---|---|---|",
            ]
        )
        for node in graph.knowledge_nodes[:limit]:
            attributes = {
                key: value
                for key, value in node.attributes.items()
                if key
                in {
                    "path",
                    "owner_system_module",
                    "flow_stage",
                    "file_kind",
                    "cleanup_action",
                }
            }
            if not attributes:
                attributes = dict(list(node.attributes.items())[:4])
            lines.append(_row([node.node_id, node.type, node.label, _value(attributes)]))
        if len(graph.knowledge_nodes) > limit:
            lines.append(
                _row(
                    [
                        "omitted",
                        "",
                        "",
                        f"{len(graph.knowledge_nodes) - limit} nodes omitted at {depth} depth.",
                    ]
                )
            )
        lines.append("")
    if graph.knowledge_edges and depth in DEEP_DEPTHS:
        lines.extend(
            [
                "Sample edges:",
                "",
                "| Source | Relation | Target | Why |",
                "|---|---|---|---|",
            ]
        )
        for edge in graph.knowledge_edges[:limit]:
            lines.append(_row([edge.source, edge.relation, edge.target, edge.why]))
        if len(graph.knowledge_edges) > limit:
            lines.append(
                _row(
                    [
                        "omitted",
                        "",
                        "",
                        f"{len(graph.knowledge_edges) - limit} edges omitted at {depth} depth.",
                    ]
                )
            )


def _add_blueprint_sections(lines: list[str], graph: SystemReviewGraph, depth: str) -> None:
    if not graph.blueprint_sections:
        return
    lines.extend(
        [
            "",
            "## Blueprint Sections",
            "",
            "| Section | Purpose | Subsystems | Evidence | Flow Steps | Control Points |",
            "|---|---|---|---|---|---|",
        ]
    )
    for section in graph.blueprint_sections:
        lines.append(
            _row(
                [
                    section.title,
                    section.purpose,
                    ", ".join(section.subsystems),
                    len(section.source_evidence),
                    len(section.flow),
                    len(section.control_points),
                ]
            )
        )
    if depth == "overview":
        lines.extend(
            [
                "",
                "This overview lists blueprint sections only. Rebuild with `--depth standard`, "
                "`--depth deep`, or `--depth blueprint` for source evidence, flow tables, "
                "control points, and reviewer gaps.",
            ]
        )
        return
    for section in graph.blueprint_sections:
        lines.extend(["", f"### {section.title}", "", section.purpose or "No purpose declared."])
        if section.subsystems:
            lines.extend(["", f"- Subsystems: {_code_list(section.subsystems)}"])
        if section.source_evidence:
            lines.extend(
                [
                    "",
                    "Source evidence:",
                    "",
                    "| Path | Symbol | Role | Notes | Proof Level |",
                    "|---|---|---|---|---|",
                ]
            )
            for evidence in section.source_evidence:
                lines.append(
                    _row(
                        [
                            evidence.get("path", ""),
                            evidence.get("symbol", ""),
                            evidence.get("role", ""),
                            evidence.get("notes", ""),
                            evidence.get("proof_level", ""),
                        ]
                    )
                )
        if section.flow:
            lines.extend(
                [
                    "",
                    "Operational flow:",
                    "",
                    "| Step | Actor | Consumes | Produces | Next | Evidence |",
                    "|---|---|---|---|---|---|",
                ]
            )
            for step in section.flow:
                lines.append(
                    _row(
                        [
                            step.get("step", ""),
                            step.get("actor", ""),
                            step.get("consumes", ""),
                            step.get("produces", ""),
                            step.get("next", ""),
                            step.get("evidence", ""),
                        ]
                    )
                )
        if section.control_points:
            lines.extend(
                [
                    "",
                    "Control points:",
                    "",
                    "| Gate | Location | Decision | Failure Mode | Evidence |",
                    "|---|---|---|---|---|",
                ]
            )
            for point in section.control_points:
                lines.append(
                    _row(
                        [
                            point.get("gate", ""),
                            point.get("location", ""),
                            point.get("decision", ""),
                            point.get("failure_mode", ""),
                            point.get("evidence", ""),
                        ]
                    )
                )
        if section.review_questions:
            lines.extend(["", "Review questions:"])
            lines.extend(f"- {item}" for item in section.review_questions)
        if depth == "blueprint" and section.known_boundaries:
            lines.extend(["", "Known gaps:"])
            lines.extend(f"- {item}" for item in section.known_boundaries)
        lines.append("")


def _add_artifacts(lines: list[str], graph: SystemReviewGraph) -> None:
    lines.extend(
        [
            "## Artifacts",
            "",
            "| Artifact | Kind | Schema | Owner | Path | Redaction | Purpose |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for artifact in graph.artifacts:
        lines.append(
            _row(
                [
                    artifact.name,
                    artifact.kind,
                    artifact.schema,
                    artifact.owner,
                    artifact.path,
                    artifact.redaction,
                    artifact.purpose,
                ]
            )
        )


def _add_schemas(lines: list[str], graph: SystemReviewGraph, depth: str) -> None:
    lines.extend(
        [
            "",
            "## Schemas And Contracts",
            "",
            "| Name | Kind | Required Fields | Privacy Notes | Purpose |",
            "|---|---|---|---|---|",
        ]
    )
    for schema in graph.schemas:
        lines.append(
            _row(
                [
                    schema.name,
                    schema.kind,
                    ", ".join(schema.required_fields),
                    schema.privacy_notes,
                    schema.purpose,
                ]
            )
        )
        if depth in DEEP_DEPTHS and schema.example:
            lines.extend(["", f"Example `{schema.name}`:", "", "```json"])
            lines.append(json.dumps(schema.example, indent=2, sort_keys=True))
            lines.extend(["```", ""])


def _add_gates(lines: list[str], graph: SystemReviewGraph) -> None:
    lines.extend(["", "## Decision Gates", ""])
    for gate in graph.gates:
        lines.extend(
            [
                f"### {gate.name}",
                "",
                f"- Inputs: `{', '.join(gate.inputs)}`",
                f"- Outputs: `{', '.join(gate.outputs)}`",
                f"- Human gate: `{_value(gate.human_gate)}`",
                f"- Risk boundary: {gate.risk_boundary}",
                "",
                "| If | Then |",
                "|---|---|",
            ]
        )
        for rule in gate.rules:
            lines.append(_row([rule.get("if", ""), rule.get("then", "")]))
        lines.append("")


def _add_workflows(lines: list[str], graph: SystemReviewGraph) -> None:
    lines.extend(
        [
            "## Workflows",
            "",
            "| Step | Actor | Consumes | Gates | Produces | Next | Purpose |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for step in graph.workflows:
        lines.append(
            _row(
                [
                    step.name,
                    step.actor,
                    ", ".join(step.consumes),
                    ", ".join(step.gates),
                    ", ".join(step.produces),
                    ", ".join(step.next_steps),
                    step.purpose,
                ]
            )
        )


def render_markdown(graph: SystemReviewGraph, depth: str = "deep") -> str:
    """Render a full system review report."""

    if depth not in REPORT_DEPTHS:
        raise ValueError(f"depth must be one of: {', '.join(sorted(REPORT_DEPTHS))}")
    lines = [
        f"# {graph.title}",
        "",
        f"Generated: `{graph.generated_at}`",
        f"Scope: {graph.scope}",
        f"One line: {graph.one_line}",
        f"Depth: `{depth}`",
        "",
        "## Bigger Picture",
        "",
        graph.bigger_picture or "No bigger-picture narrative was provided.",
        "",
        "## Current Truth",
        "",
    ]
    if graph.current_truth:
        lines.extend(f"- `{key}`: `{_value(value)}`" for key, value in graph.current_truth.items())
    else:
        lines.append("- No current-truth fields were provided.")
    if graph.source_links:
        lines.extend(["", "## Source Links", "", "| Source | Notes |", "|---|---|"])
        for source in graph.source_links:
            label = source.get("label", "")
            url = source.get("url", "")
            notes = source.get("notes", "")
            link = f"[{label}]({url})" if label and url else url
            lines.append(_row([link, notes]))
    _add_report_registers(lines, graph, depth)
    _add_visuals(lines, graph, depth)
    _add_expansion_index(lines, graph, depth)
    lines.extend(
        [
            "",
            "## Systems",
            "",
            "| System | Owner | Stack | Architecture | Lifecycle | Boundary | Ideal Target |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for system in graph.systems:
        lines.append(
            _row(
                [
                    system.name,
                    system.owner,
                    ", ".join(system.language_stack),
                    system.architecture_style,
                    system.lifecycle,
                    system.truth_boundary,
                    system.ideal_target,
                ]
            )
        )
    _add_child_maps(lines, graph)
    _add_documentation_knowledge_graph(lines, graph, depth)
    _add_blueprint_sections(lines, graph, depth)
    if depth in STANDARD_DEPTHS:
        _add_system_details(lines, graph, depth)
        _add_artifacts(lines, graph)
        _add_schemas(lines, graph, depth)
        _add_gates(lines, graph)
        _add_workflows(lines, graph)
    lines.extend(["", "## Architecture Patterns", ""])
    for pattern in graph.architecture_patterns:
        lines.extend(
            [
                f"### {pattern.get('name', 'Unnamed pattern')}",
                "",
                f"- Works for: {pattern.get('works_for', '')}",
                f"- How to map it: {pattern.get('mapping', '')}",
                f"- What to redact: {pattern.get('redaction', '')}",
                "",
            ]
        )
    lines.extend(["## Walkthroughs", ""])
    for walkthrough in graph.walkthroughs:
        lines.extend(
            [
                f"### {walkthrough.get('name', 'Unnamed walkthrough')}",
                "",
                walkthrough.get("story", ""),
                "",
                "```json",
                json.dumps(walkthrough.get("example", {}), indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    if graph.review_questions:
        lines.extend(["## Review Questions", ""])
        lines.extend(f"- {item}" for item in graph.review_questions)
        lines.append("")
    lines.extend(["## Rebuild Recipe", ""])
    for phase in graph.rebuild_recipe:
        commands = phase.get("commands") if isinstance(phase.get("commands"), list) else []
        lines.extend(
            [
                f"### {phase.get('phase', 'phase')}",
                "",
                f"- Goal: {phase.get('goal', '')}",
                "",
                "```bash",
                "\n".join(str(command) for command in commands),
                "```",
                "",
            ]
        )
    lines.extend(["## Known Boundaries", ""])
    lines.extend(f"- {item}" for item in graph.known_boundaries)
    lines.append("")
    return "\n".join(lines)
