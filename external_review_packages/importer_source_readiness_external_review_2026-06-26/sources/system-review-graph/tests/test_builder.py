from pathlib import Path

from system_review_graph.builder import build_system_review
from system_review_graph.io import read_json
from system_review_graph.render import render_markdown, render_mermaid
from system_review_graph.validate import validate_manifest


def test_build_fictional_example():
    manifest = read_json(Path("examples/fictional_ai_ops/system_review_manifest.json"))

    errors = validate_manifest(manifest)
    graph = build_system_review(manifest)

    assert errors == []
    assert graph.title == "Fictional AI Ops System Review Graph"
    assert graph.systems
    assert graph.artifacts
    assert graph.gates
    assert graph.workflows
    assert graph.review_questions
    assert any(edge.relation == "owns_or_uses" for edge in graph.edges)


def test_markdown_contains_review_sections():
    manifest = read_json(Path("examples/actual_repos/fastapi/system_review_manifest.json"))
    graph = build_system_review(manifest)

    markdown = render_markdown(graph)
    mermaid = render_mermaid(graph)

    assert "## Source Links" in markdown
    assert "## Report Registers" in markdown
    assert "### Coverage Register" in markdown
    assert "### Evidence Register" in markdown
    assert "### Gap Register" in markdown
    assert "### Action Register" in markdown
    assert "## Artifact And Schema Map" in markdown
    assert "## Gate Map" in markdown
    assert "## Expansion Index" in markdown
    assert "0.25. Registers" in markdown
    assert "Workflow touchpoints" in markdown
    assert "## Review Questions" in markdown
    assert "FastAPI Public Repo System Review Graph" in markdown
    assert "flowchart TD" in mermaid


def test_overview_depth_omits_deep_sections():
    manifest = read_json(Path("examples/actual_repos/duckdb/system_review_manifest.json"))
    graph = build_system_review(manifest)

    markdown = render_markdown(graph, depth="overview")

    assert "Depth: `overview`" in markdown
    assert "## Report Registers" in markdown
    assert "## Expansion Index" in markdown
    assert "## Artifact And Schema Map" not in markdown
    assert "Workflow touchpoints" not in markdown


def test_validation_catches_unknown_references():
    manifest = {
        "title": "Broken",
        "systems": [
            {
                "system_id": "system",
                "name": "System",
                "purpose": "Broken reference test",
                "artifacts": ["missing_artifact"],
            }
        ],
        "artifacts": [],
        "schemas": [],
        "decision_gates": [],
        "workflows": [],
    }

    errors = validate_manifest(manifest)

    assert "systems[0] references unknown artifact missing_artifact" in errors


def test_validation_catches_duplicates_and_bad_edges():
    manifest = {
        "title": "Broken",
        "systems": [
            {"system_id": "system", "name": "System", "purpose": "One"},
            {"system_id": "system", "name": "System Copy", "purpose": "Duplicate"},
        ],
        "artifacts": [],
        "schemas": [],
        "decision_gates": [],
        "workflows": [],
        "edges": [{"source": "system", "target": "missing", "relation": "points_to"}],
    }

    errors = validate_manifest(manifest)

    assert "duplicate system_id: system" in errors
    assert "edges[0] references unknown target node missing" in errors


def test_child_maps_render_as_atlas_section():
    manifest = {
        "title": "Atlas",
        "systems": [
            {"system_id": "kernel", "name": "kernel/", "purpose": "Kernel core"},
            {"system_id": "drivers", "name": "drivers/", "purpose": "Drivers"},
        ],
        "artifacts": [],
        "schemas": [],
        "decision_gates": [],
        "workflows": [],
        "child_maps": [
            {
                "map_id": "drivers",
                "name": "drivers/ subsystem map",
                "path": "subsystems/drivers/system_review_manifest.json",
                "report_path": "../subsystems/drivers/reports/system_review_graph.md",
                "systems": ["c_cpp"],
                "status": "inferred_from_source_tree",
            }
        ],
    }

    errors = validate_manifest(manifest)
    graph = build_system_review(manifest)
    markdown = render_markdown(graph, depth="overview")

    assert errors == []
    assert graph.child_maps[0].map_id == "drivers"
    assert graph.child_maps[0].report_path.endswith("system_review_graph.md")
    assert "## Map Of Maps" in markdown
    assert "## Child Maps" in markdown


def test_blueprint_sections_render_source_evidence():
    manifest = {
        "title": "Blueprint",
        "systems": [{"system_id": "kernel", "name": "kernel/", "purpose": "Kernel core"}],
        "artifacts": [],
        "schemas": [],
        "decision_gates": [],
        "workflows": [],
        "blueprint_sections": [
            {
                "section_id": "boot",
                "title": "Boot Flow",
                "purpose": "Track boot into init.",
                "subsystems": ["init", "kernel"],
                "source_evidence": [
                    {
                        "path": "init/main.c:1017",
                        "symbol": "start_kernel",
                        "role": "entry",
                        "notes": "Generic entry point.",
                        "proof_level": "source-confirmed",
                    }
                ],
                "flow": [
                    {
                        "step": "Start",
                        "actor": "kernel",
                        "consumes": "boot state",
                        "produces": "init state",
                        "next": "rest_init",
                        "evidence": "init/main.c",
                    }
                ],
                "control_points": [
                    {
                        "gate": "Init order",
                        "location": "include/linux/module.h",
                        "decision": "order initcalls",
                        "failure_mode": "late dependency",
                        "evidence": "module_init",
                    }
                ],
            }
        ],
    }

    errors = validate_manifest(manifest)
    graph = build_system_review(manifest)
    markdown = render_markdown(graph, depth="blueprint")

    assert errors == []
    assert graph.blueprint_sections[0].section_id == "boot"
    assert "## Blueprint Sections" in markdown
    assert "Source evidence:" in markdown
    assert "init/main.c:1017" in markdown
