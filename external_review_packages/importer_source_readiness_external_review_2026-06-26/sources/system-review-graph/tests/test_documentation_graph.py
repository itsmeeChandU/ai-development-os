import json
from pathlib import Path

from system_review_graph.builder import build_system_review
from system_review_graph.cli import main
from system_review_graph.documentation_graph import load_documentation_graph_context
from system_review_graph.mcp_server import handle_message
from system_review_graph.render import render_markdown
from system_review_graph.repo_context_bundle import load_repo_context_bundle
from system_review_graph.validate import validate_manifest


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_manifest_documentation_graph_renders_and_validates():
    manifest = {
        "title": "Documentation graph",
        "systems": [],
        "artifacts": [],
        "schemas": [],
        "decision_gates": [],
        "workflows": [],
        "documentation_sources": [
            {
                "artifact": "data/intelligence/global_repository_documentation_rows.jsonl",
                "role": "complete row-per-file documentation catalog",
                "incorporated_information": ["path", "owner", "purpose"],
            }
        ],
        "knowledge_nodes": [
            {"node_id": "concept:stock_selection", "type": "concept", "label": "Stock selection"},
            {
                "node_id": "file:graph/trading_command_board.py",
                "type": "file",
                "label": "graph/trading_command_board.py",
                "attributes": {"flow_stage": "lane_engines", "cleanup_action": "KEEP"},
            },
        ],
        "knowledge_edges": [
            {
                "source": "concept:stock_selection",
                "relation": "HAS_FILE",
                "target": "file:graph/trading_command_board.py",
            }
        ],
    }

    errors = validate_manifest(manifest)
    graph = build_system_review(manifest)
    markdown = render_markdown(graph, depth="deep")

    assert errors == []
    assert graph.documentation_sources[0].artifact.endswith(
        "global_repository_documentation_rows.jsonl"
    )
    assert graph.knowledge_nodes[0].node_id == "concept:stock_selection"
    assert "## Documentation Knowledge Graph" in markdown
    assert "Stock selection" in markdown


def test_manifest_validation_catches_unknown_knowledge_edge():
    manifest = {
        "title": "Broken documentation graph",
        "systems": [],
        "artifacts": [],
        "schemas": [],
        "decision_gates": [],
        "workflows": [],
        "knowledge_nodes": [{"node_id": "concept:known", "type": "concept", "label": "Known"}],
        "knowledge_edges": [
            {"source": "concept:known", "relation": "POINTS_TO", "target": "concept:missing"}
        ],
    }

    errors = validate_manifest(manifest)

    assert "knowledge_edges[0] references unknown target node concept:missing" in errors


def test_documentation_graph_context_loader_filters_from_start_node(tmp_path):
    nodes = tmp_path / "nodes.jsonl"
    edges = tmp_path / "edges.jsonl"
    _write_jsonl(
        nodes,
        [
            {"id": "concept:stock_selection", "type": "concept", "label": "Stock selection"},
            {"id": "owner:stock_market_system", "type": "owner_module", "label": "stock"},
            {"id": "file:graph/trading_command_board.py", "type": "file", "label": "board"},
        ],
    )
    _write_jsonl(
        edges,
        [
            {
                "src": "concept:stock_selection",
                "type": "USES_OWNER",
                "dst": "owner:stock_market_system",
            },
            {
                "src": "owner:stock_market_system",
                "type": "OWNS_FILE",
                "dst": "file:graph/trading_command_board.py",
            },
        ],
    )

    context = load_documentation_graph_context(
        nodes_path=nodes,
        edges_path=edges,
        start_node="concept:stock_selection",
    )

    assert context["summary"]["total_nodes"] == 3
    assert context["summary"]["selected_edges"] == 1
    assert "LLMs" in context["agent_context_contract"]["primary_users"]
    assert any(node["id"] == "concept:stock_selection" for node in context["nodes"])


def test_cli_load_documentation_graph_context(tmp_path, capsys):
    nodes = tmp_path / "nodes.jsonl"
    edges = tmp_path / "edges.jsonl"
    _write_jsonl(
        nodes,
        [{"id": "concept:algorithm_usage", "type": "concept", "label": "Algorithms"}],
    )
    _write_jsonl(edges, [])

    exit_code = main(
        [
            "load-documentation-graph-context",
            "--nodes",
            str(nodes),
            "--edges",
            str(edges),
            "--node-type",
            "concept",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "concept:algorithm_usage" in captured.out


def test_mcp_load_documentation_graph_context_tool(tmp_path):
    nodes = tmp_path / "nodes.jsonl"
    edges = tmp_path / "edges.jsonl"
    _write_jsonl(nodes, [{"id": "concept:source_data", "type": "concept", "label": "Source data"}])
    _write_jsonl(edges, [])

    tools = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert tools is not None
    names = [tool["name"] for tool in tools["result"]["tools"]]
    assert "srg_load_documentation_graph_context" in names

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "srg_load_documentation_graph_context",
                "arguments": {
                    "nodes_path": str(nodes),
                    "edges_path": str(edges),
                    "node_type": "concept",
                },
            },
        }
    )

    assert response is not None
    text = response["result"]["content"][0]["text"]
    assert "concept:source_data" in text


def test_repo_context_bundle_combines_manifest_docs_and_code_contract(tmp_path):
    manifest = tmp_path / "system_review_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "title": "Agentic repo",
                "one_line": "Coordinates agents",
                "systems": [{"system_id": "coordinator", "name": "Coordinator"}],
                "artifacts": [],
                "schemas": [],
                "decision_gates": [],
                "workflows": [],
                "review_questions": ["Which graph should an agent load first?"],
                "known_boundaries": ["Generated docs are not runtime proof."],
            }
        ),
        encoding="utf-8",
    )
    nodes = tmp_path / "nodes.jsonl"
    edges = tmp_path / "edges.jsonl"
    _write_jsonl(nodes, [{"id": "concept:agentic_workflow", "type": "concept"}])
    _write_jsonl(edges, [])
    contract = tmp_path / "code_review_graph_contract.json"
    contract.write_text(
        json.dumps(
            {
                "contract_version": "code-review-graph.agent-contract.v1",
                "summary": {"files": 1, "symbols": 1, "edges": 0},
                "files": [],
                "modules": [],
                "symbols": [],
                "imports": [],
                "edges": [],
                "tests": [],
                "generated_artifacts": [
                    {
                        "id": "artifact:system_review_graph/continuation_plan.json",
                        "path": "system_review_graph/continuation_plan.json",
                        "type": "startup_continuation_plan",
                        "producer": "repo proof or AI Development OS workflow",
                    },
                    {
                        "id": "artifact:system_review_graph/vc_pitch_readiness_report.json",
                        "path": "system_review_graph/vc_pitch_readiness_report.json",
                        "type": "vc_pitch_readiness_report",
                        "producer": "repo proof or AI Development OS workflow",
                    },
                    {
                        "id": "artifact:system_review_graph/board_go_live_readiness_report.json",
                        "path": "system_review_graph/board_go_live_readiness_report.json",
                        "type": "board_go_live_readiness_report",
                        "producer": "repo proof or AI Development OS workflow",
                    },
                    {
                        "id": "artifact:system_review_graph/operator_workflow_report.json",
                        "path": "system_review_graph/operator_workflow_report.json",
                        "type": "operator_workflow_report",
                        "producer": "repo proof or AI Development OS workflow",
                    },
                    {
                        "id": "artifact:system_review_graph/operator_screenshot_manifest.json",
                        "path": "system_review_graph/operator_screenshot_manifest.json",
                        "type": "operator_screenshot_manifest",
                        "producer": "repo proof or AI Development OS workflow",
                    },
                    {
                        "id": (
                            "artifact:system_review_graph/operator_screenshots/"
                            "operator-dashboard.png"
                        ),
                        "path": "system_review_graph/operator_screenshots/operator-dashboard.png",
                        "type": "operator_screenshot",
                        "producer": "operator screenshot proof surface",
                    },
                    {
                        "id": "artifact:docs/STARTUP_LIFECYCLE.md",
                        "path": "docs/STARTUP_LIFECYCLE.md",
                        "type": "startup_lifecycle_surface",
                        "producer": "repo proof or AI Development OS workflow",
                    }
                ],
                "risk_ownership_hints": [],
                "proof_boundary": "structural only",
            }
        ),
        encoding="utf-8",
    )
    workflow = tmp_path / "agentic_execution_manifest.json"
    workflow.write_text(
        json.dumps(
            {
                "name": "ai_development_os_agentic_execution",
                "version": 1,
                "slash_commands": [{"command": "/ados:lane"}],
                "skills": [{"id": "ai-native-delivery"}],
                "background_routines": [{"id": "branch_freshness_check"}],
                "parallel_agent_lanes": [{"id": "workflow-coordinator"}],
                "ci_cd_agent_jobs": [{"id": "workflow_manifest_ci"}],
                "eval_loops": [{"id": "lane_packet_completeness"}],
                "agent_supervision": {"coordinator_rules": []},
                "multi_repo_orchestration": {"repos": [{"id": "ai-development-os"}]},
                "handoff_schema": {"required_fields": ["lane"]},
                "proof_boundaries": ["repo truth remains canonical"],
            }
        ),
        encoding="utf-8",
    )

    bundle = load_repo_context_bundle(
        manifest_path=manifest,
        documentation_nodes_path=nodes,
        documentation_edges_path=edges,
        code_review_graph_path=contract,
        agentic_workflow_path=workflow,
        node_type="concept",
    )

    assert bundle["system_review_graph"]["title"] == "Agentic repo"
    assert bundle["code_review_graph_reference"]["status"] == "ready"
    assert bundle["code_review_graph_reference"]["startup_continuation_plan_present"] is True
    assert (
        "startup_continuation_plan"
        in bundle["code_review_graph_reference"]["generated_artifact_types"]
    )
    assert (
        "vc_pitch_readiness_report"
        in bundle["code_review_graph_reference"]["generated_artifact_types"]
    )
    assert (
        "board_go_live_readiness_report"
        in bundle["code_review_graph_reference"]["generated_artifact_types"]
    )
    assert (
        "operator_workflow_report"
        in bundle["code_review_graph_reference"]["generated_artifact_types"]
    )
    assert (
        "operator_screenshot_manifest"
        in bundle["code_review_graph_reference"]["generated_artifact_types"]
    )
    assert (
        "operator_screenshot"
        in bundle["code_review_graph_reference"]["generated_artifact_types"]
    )
    assert (
        "startup_lifecycle_surface"
        in bundle["code_review_graph_reference"]["generated_artifact_types"]
    )
    assert bundle["agentic_workflow_reference"]["status"] == "ready"
    assert bundle["agentic_workflow_reference"]["summary"]["parallel_agent_lanes"] == 1
    assert bundle["documentation_graph_context"]["summary"]["selected_nodes"] == 1


def test_cli_and_mcp_load_repo_context_bundle(tmp_path, capsys):
    manifest = tmp_path / "system_review_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "title": "Small repo",
                "systems": [],
                "artifacts": [],
                "schemas": [],
                "decision_gates": [],
                "workflows": [],
            }
        ),
        encoding="utf-8",
    )

    workflow = tmp_path / "agentic_execution_manifest.json"
    workflow.write_text(
        json.dumps(
            {
                "slash_commands": [],
                "skills": [],
                "background_routines": [],
                "parallel_agent_lanes": [],
                "ci_cd_agent_jobs": [],
                "eval_loops": [],
                "agent_supervision": {},
                "multi_repo_orchestration": {},
                "handoff_schema": {},
                "proof_boundaries": [],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "load-repo-context-bundle",
            "--manifest",
            str(manifest),
            "--agentic-workflow",
            str(workflow),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Small repo" in captured.out
    assert "missing_input" in captured.out
    assert "agentic_workflow_reference" in captured.out

    tools = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert tools is not None
    names = [tool["name"] for tool in tools["result"]["tools"]]
    assert "srg_load_repo_context_bundle" in names

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "srg_load_repo_context_bundle",
                "arguments": {
                    "manifest_path": str(manifest),
                    "agentic_workflow_path": str(workflow),
                },
            },
        }
    )

    assert response is not None
    text = response["result"]["content"][0]["text"]
    assert "agentic_workflow_reference" in text

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "srg_load_repo_context_bundle",
                "arguments": {"manifest_path": str(manifest)},
            },
        }
    )
    assert response is not None
    assert "Small repo" in response["result"]["content"][0]["text"]
