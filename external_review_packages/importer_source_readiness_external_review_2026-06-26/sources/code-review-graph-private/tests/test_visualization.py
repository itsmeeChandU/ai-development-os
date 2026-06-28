"""Tests for graph visualization export."""

import json

import pytest

from code_review_graph.graph import GraphStore
from code_review_graph.parser import EdgeInfo, NodeInfo


@pytest.fixture
def store_with_data(tmp_path):
    db_path = tmp_path / "test.db"
    store = GraphStore(db_path)
    file_node = NodeInfo(
        kind="File",
        name="auth.py",
        file_path="src/auth.py",
        line_start=1,
        line_end=50,
        language="python",
        parent_name=None,
        params=None,
        return_type=None,
        modifiers=None,
        is_test=False,
        extra={},
    )
    class_node = NodeInfo(
        kind="Class",
        name="AuthService",
        file_path="src/auth.py",
        line_start=5,
        line_end=45,
        language="python",
        parent_name=None,
        params=None,
        return_type=None,
        modifiers=None,
        is_test=False,
        extra={},
    )
    func_node = NodeInfo(
        kind="Function",
        name="login",
        file_path="src/auth.py",
        line_start=10,
        line_end=20,
        language="python",
        parent_name="AuthService",
        params="username, password",
        return_type="bool",
        modifiers=None,
        is_test=False,
        extra={},
    )
    test_file = NodeInfo(
        kind="File",
        name="test_auth.py",
        file_path="tests/test_auth.py",
        line_start=1,
        line_end=10,
        language="python",
        parent_name=None,
        params=None,
        return_type=None,
        modifiers=None,
        is_test=False,
        extra={},
    )
    test_node = NodeInfo(
        kind="Test",
        name="test_login",
        file_path="tests/test_auth.py",
        line_start=1,
        line_end=10,
        language="python",
        parent_name=None,
        params=None,
        return_type=None,
        modifiers=None,
        is_test=True,
        extra={},
    )
    store.upsert_node(file_node)
    store.upsert_node(class_node)
    store.upsert_node(func_node)
    store.upsert_node(test_file)
    store.upsert_node(test_node)
    contains_edge = EdgeInfo(
        kind="CONTAINS",
        source="src/auth.py",
        target="src/auth.py::AuthService",
        file_path="src/auth.py",
        line=5,
        extra={},
    )
    calls_edge = EdgeInfo(
        kind="CALLS",
        source="tests/test_auth.py::test_login",
        target="src/auth.py::AuthService.login",
        file_path="tests/test_auth.py",
        line=5,
        extra={},
    )
    store.upsert_edge(contains_edge)
    store.upsert_edge(calls_edge)
    store.commit()
    return store


def test_export_graph_data(store_with_data):
    from code_review_graph.visualization import export_graph_data

    data = export_graph_data(store_with_data)
    assert "nodes" in data
    assert "edges" in data
    assert "stats" in data
    assert len(data["nodes"]) == 5
    assert len(data["edges"]) == 2
    node_names = {n["name"] for n in data["nodes"]}
    assert "auth.py" in node_names
    assert "AuthService" in node_names
    assert "login" in node_names
    edge_kinds = {e["kind"] for e in data["edges"]}
    assert "CONTAINS" in edge_kinds
    assert "CALLS" in edge_kinds
    json.dumps(data)  # must be serializable


def test_export_agent_contract_contains_required_sections(store_with_data, tmp_path):
    from code_review_graph.exports import CONTRACT_VERSION, export_agent_contract

    artifact_dir = tmp_path / "system_review_graph"
    artifact_dir.mkdir()
    (artifact_dir / "continuation_plan.json").write_text(
        '{"status":"startup_in_progress","must_continue":true}',
        encoding="utf-8",
    )
    (artifact_dir / "readiness_report.json").write_text(
        '{"status":"ready_with_external_gates"}',
        encoding="utf-8",
    )
    (artifact_dir / "vc_pitch_readiness_report.json").write_text(
        '{"status":"vc_pitch_ready_with_diligence_gates"}',
        encoding="utf-8",
    )
    (artifact_dir / "board_go_live_readiness_report.json").write_text(
        '{"status":"board_go_live_candidate_with_human_approval_gates"}',
        encoding="utf-8",
    )
    (artifact_dir / "operator_workflow_report.json").write_text(
        '{"status":"operator_workflow_ready_internal","work_queue_count":31}',
        encoding="utf-8",
    )
    (artifact_dir / "operator_screenshot_manifest.json").write_text(
        '{"status":"screenshots_ready","screenshot_count":1}',
        encoding="utf-8",
    )
    screenshot_dir = artifact_dir / "operator_screenshots"
    screenshot_dir.mkdir()
    (screenshot_dir / "operator-dashboard.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>',
        encoding="utf-8",
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "STARTUP_LIFECYCLE.md").write_text("# Startup Lifecycle\n", encoding="utf-8")
    investor_dir = tmp_path / "investor"
    investor_dir.mkdir()
    (investor_dir / "vc_pitch_deck.md").write_text("# VC Pitch Deck\n", encoding="utf-8")
    board_dir = tmp_path / "board"
    board_dir.mkdir()
    (board_dir / "board_go_live_brief.md").write_text("# Board Go-Live Brief\n", encoding="utf-8")
    output_path = tmp_path / "code_review_graph_contract.json"
    export_agent_contract(store_with_data, output_path, repo_root=tmp_path)

    contract = json.loads(output_path.read_text(encoding="utf-8"))
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["repo"] == str(tmp_path)
    for key in [
        "files",
        "modules",
        "symbols",
        "imports",
        "edges",
        "tests",
        "generated_artifacts",
        "risk_ownership_hints",
    ]:
        assert key in contract
    assert any(row["path"] == "src/auth.py" for row in contract["files"])
    assert any(
        row["qualified_name"] == "tests/test_auth.py::test_login"
        for row in contract["tests"]
    )
    artifact_types = {row["type"] for row in contract["generated_artifacts"]}
    assert "startup_continuation_plan" in artifact_types
    assert "vc_pitch_readiness_report" in artifact_types
    assert "board_go_live_readiness_report" in artifact_types
    assert "operator_workflow_report" in artifact_types
    assert "operator_screenshot_manifest" in artifact_types
    assert "operator_screenshot" in artifact_types
    assert "startup_lifecycle_surface" in artifact_types
    assert "vc_pitch_deck" in artifact_types
    assert "board_go_live_brief" in artifact_types
    assert "product_readiness_report" in artifact_types
    assert "structural code-review context" in contract["proof_boundary"]


def test_generate_html(store_with_data, tmp_path):
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    assert output_path.exists()
    content = output_path.read_text()
    assert "d3js.org" in content or "d3.v7" in content
    assert "auth.py" in content
    assert "AuthService" in content
    assert "<!DOCTYPE html>" in content
    assert "</html>" in content


def test_cpp_include_resolution(tmp_path):
    """IMPORTS_FROM edges with bare C++ include paths should resolve to File nodes
    stored under absolute paths — previously these were dropped, leaving the
    graph almost entirely disconnected for C/C++ projects."""
    from code_review_graph.visualization import export_graph_data

    db_path = tmp_path / "test.db"
    store = GraphStore(db_path)

    def _file(name, path, lang="cpp"):
        return NodeInfo(
            kind="File", name=name, file_path=path,
            line_start=1, line_end=10, language=lang,
            parent_name=None, params=None, return_type=None,
            modifiers=None, is_test=False, extra={},
        )

    store.upsert_node(_file("main.cpp",  "/abs/src/main.cpp"))
    store.upsert_node(_file("Renderer.hpp", "/abs/libs/rendering/Renderer.hpp"))
    store.upsert_node(_file("Utils.hpp",    "/abs/libs/utils/Utils.hpp"))

    # Parser emits bare include paths as targets — exactly what Tree-sitter sees
    store.upsert_edge(EdgeInfo(
        kind="IMPORTS_FROM",
        source="/abs/src/main.cpp",
        target="rendering/Renderer.hpp",   # relative, one directory level
        file_path="/abs/src/main.cpp", line=1, extra={},
    ))
    store.upsert_edge(EdgeInfo(
        kind="IMPORTS_FROM",
        source="/abs/src/main.cpp",
        target="Utils.hpp",                # bare filename only
        file_path="/abs/src/main.cpp", line=2, extra={},
    ))
    store.commit()

    data = export_graph_data(store)
    resolved_targets = {e["target"] for e in data["edges"] if e["kind"] == "IMPORTS_FROM"}

    assert "/abs/libs/rendering/Renderer.hpp" in resolved_targets, (
        "bare relative include 'rendering/Renderer.hpp' was not resolved to its absolute path"
    )
    assert "/abs/libs/utils/Utils.hpp" in resolved_targets, (
        "bare filename include 'Utils.hpp' was not resolved to its absolute path"
    )


def test_generate_html_overwrites(store_with_data, tmp_path):
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    output_path.write_text("old content")
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    assert "old content" not in content
    assert "<!DOCTYPE html>" in content


def test_export_includes_flows(store_with_data):
    """Export data should include a 'flows' key (list, possibly empty)."""
    from code_review_graph.visualization import export_graph_data

    data = export_graph_data(store_with_data)
    assert "flows" in data
    assert isinstance(data["flows"], list)


def test_export_includes_communities(store_with_data):
    """Export data should include a 'communities' key (list, possibly empty)."""
    from code_review_graph.visualization import export_graph_data

    data = export_graph_data(store_with_data)
    assert "communities" in data
    assert isinstance(data["communities"], list)


def test_generate_html_includes_all_edge_types(store_with_data, tmp_path):
    """Generated HTML should define colors and legend entries for all 7 edge types."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    for edge_kind in ["CALLS", "IMPORTS_FROM", "INHERITS", "CONTAINS",
                       "IMPLEMENTS", "TESTED_BY", "DEPENDS_ON"]:
        assert edge_kind in content, f"Edge type {edge_kind} missing from HTML"


def test_generate_html_includes_interactive_features(store_with_data, tmp_path):
    """Generated HTML should include new interactive features."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    # Detail panel
    assert "detail-panel" in content
    # Community coloring button
    assert "btn-community" in content
    # Flow dropdown
    assert "flow-select" in content
    # Filter panel
    assert "filter-panel" in content
    # Search results dropdown
    assert "search-results" in content
    # Accessibility: skip link
    assert "skip-link" in content
    # Accessibility: live region
    assert 'aria-live="polite"' in content
    # Node shapes mapping
    assert "KIND_SHAPE" in content


def test_generate_html_includes_node_shapes(store_with_data, tmp_path):
    """Generated HTML should use d3.symbol() for distinct node shapes."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    assert "d3.symbol()" in content or "symbolCircle" in content
    assert "symbolSquare" in content
    assert "symbolTriangle" in content
    assert "symbolDiamond" in content
    assert "symbolCross" in content


def test_generate_html_includes_help_overlay(store_with_data, tmp_path):
    """Generated HTML should include a help overlay for onboarding."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    assert "help-overlay" in content
    assert "btn-help" in content
    assert "Click a file" in content


def test_generate_html_includes_aria_attributes(store_with_data, tmp_path):
    """Generated HTML should include key ARIA attributes for accessibility."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    assert 'role="tooltip"' in content
    assert 'role="dialog"' in content
    assert 'role="listbox"' in content
    assert 'aria-pressed="false"' in content  # community button
    assert 'aria-modal="false"' in content  # detail panel


def test_generate_html_includes_loading_and_empty_state(store_with_data, tmp_path):
    """Generated HTML should include loading overlay and empty state markup."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    assert "loading-overlay" in content
    assert "empty-state" in content
    assert "No nodes to display" in content


def test_generate_html_includes_focus_visible(store_with_data, tmp_path):
    """Generated HTML should include :focus-visible styles."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "graph.html"
    generate_html(store_with_data, output_path)
    content = output_path.read_text()
    assert ":focus-visible" in content


# ---------------------------------------------------------------------------
# Phase 9: Visualization Aggregation
# ---------------------------------------------------------------------------


@pytest.fixture
def large_store(tmp_path):
    """Store with enough nodes/communities to test aggregation."""
    db_path = tmp_path / "large.db"
    store = GraphStore(db_path)

    # Create nodes across multiple files (simulates a larger codebase)
    files = [f"src/mod{i}.py" for i in range(5)]
    for fp in files:
        file_node = NodeInfo(
            kind="File", name=fp.split("/")[-1], file_path=fp,
            line_start=1, line_end=100, language="python",
            parent_name=None, params=None, return_type=None,
            modifiers=None, is_test=False, extra={},
        )
        store.upsert_node(file_node)
        # Add some functions per file
        for j in range(3):
            func_node = NodeInfo(
                kind="Function", name=f"func_{j}",
                file_path=fp, line_start=10 + j * 10, line_end=20 + j * 10,
                language="python", parent_name=None,
                params="x", return_type="int",
                modifiers=None, is_test=False, extra={},
            )
            store.upsert_node(func_node)
            # CONTAINS edge from file to function
            store.upsert_edge(EdgeInfo(
                kind="CONTAINS", source=fp,
                target=f"{fp}::func_{j}",
                file_path=fp, line=10 + j * 10, extra={},
            ))

    # Add some cross-file CALLS edges
    store.upsert_edge(EdgeInfo(
        kind="CALLS",
        source="src/mod0.py::func_0",
        target="src/mod1.py::func_1",
        file_path="src/mod0.py", line=15, extra={},
    ))
    store.upsert_edge(EdgeInfo(
        kind="CALLS",
        source="src/mod2.py::func_0",
        target="src/mod3.py::func_2",
        file_path="src/mod2.py", line=12, extra={},
    ))
    store.upsert_edge(EdgeInfo(
        kind="CALLS",
        source="src/mod1.py::func_2",
        target="src/mod4.py::func_0",
        file_path="src/mod1.py", line=35, extra={},
    ))

    # Set community_id on nodes (simulate community detection)
    store._conn.execute(
        "UPDATE nodes SET community_id = 0 WHERE file_path IN ('src/mod0.py', 'src/mod1.py')"
    )
    store._conn.execute(
        "UPDATE nodes SET community_id = 1 WHERE file_path IN ('src/mod2.py', 'src/mod3.py')"
    )
    store._conn.execute(
        "UPDATE nodes SET community_id = 2 WHERE file_path = 'src/mod4.py'"
    )

    # Create communities table and insert communities
    store._conn.execute("""
        CREATE TABLE IF NOT EXISTS communities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            level INTEGER DEFAULT 0,
            cohesion REAL DEFAULT 0.0,
            size INTEGER DEFAULT 0,
            dominant_language TEXT DEFAULT '',
            description TEXT DEFAULT ''
        )
    """)
    store._conn.execute("""
        CREATE TABLE IF NOT EXISTS community_members (
            community_id INTEGER, node_id INTEGER,
            FOREIGN KEY (community_id) REFERENCES communities(id)
        )
    """)
    store._conn.execute(
        "INSERT INTO communities (id, name, level, cohesion, size, dominant_language, description) "
        "VALUES (0, 'Core Module', 0, 0.8, 8, 'python', 'Core functionality')"
    )
    store._conn.execute(
        "INSERT INTO communities (id, name, level, cohesion, size, dominant_language, description) "
        "VALUES (1, 'Data Module', 0, 0.7, 8, 'python', 'Data processing')"
    )
    store._conn.execute(
        "INSERT INTO communities (id, name, level, cohesion, size, dominant_language, description) "
        "VALUES (2, 'Utils', 0, 0.5, 4, 'python', 'Utility functions')"
    )
    # Insert community_members so get_communities works
    for row in store._conn.execute(
        "SELECT id, qualified_name, community_id FROM nodes WHERE community_id IS NOT NULL"
    ).fetchall():
        store._conn.execute(
            "INSERT INTO community_members (community_id, node_id) VALUES (?, ?)",
            (row["community_id"], row["id"]),
        )

    store.commit()
    return store


def test_community_mode_fewer_nodes(large_store, tmp_path):
    """Community mode should produce fewer nodes than full mode."""
    from code_review_graph.visualization import (
        _aggregate_community,
        export_graph_data,
    )

    data = export_graph_data(large_store)
    full_node_count = len(data["nodes"])

    agg = _aggregate_community(data)
    community_node_count = len(agg["nodes"])

    assert community_node_count < full_node_count, (
        f"Community mode ({community_node_count} nodes) should have fewer nodes "
        f"than full mode ({full_node_count} nodes)"
    )
    # All aggregated nodes should be of kind "Community"
    for n in agg["nodes"]:
        assert n["kind"] == "Community"
    # Edges should be CROSS_COMMUNITY type
    for e in agg["edges"]:
        assert e["kind"] == "CROSS_COMMUNITY"
    # Should have community_details for drill-down
    assert "community_details" in agg
    assert len(agg["community_details"]) > 0


def test_file_mode_aggregation(large_store, tmp_path):
    """File mode should produce one node per file."""
    from code_review_graph.visualization import (
        _aggregate_file,
        export_graph_data,
    )

    data = export_graph_data(large_store)
    full_node_count = len(data["nodes"])

    agg = _aggregate_file(data)
    file_node_count = len(agg["nodes"])

    assert file_node_count < full_node_count, (
        f"File mode ({file_node_count} nodes) should have fewer nodes "
        f"than full mode ({full_node_count} nodes)"
    )
    # All nodes should be of kind "File"
    for n in agg["nodes"]:
        assert n["kind"] == "File"
    # Edges should be DEPENDS_ON type
    for e in agg["edges"]:
        assert e["kind"] == "DEPENDS_ON"
    # Mode should be set
    assert agg["mode"] == "file"


def test_auto_mode_switches_at_threshold(large_store, tmp_path):
    """Auto mode should switch to community when nodes exceed threshold."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "auto_low.html"
    # Threshold higher than node count -> should use full template
    generate_html(large_store, output_path, mode="auto", max_full_nodes=100000)
    content = output_path.read_text()
    # Full template has btn-community and flow-select
    assert "btn-community" in content
    assert "flow-select" in content

    output_path2 = tmp_path / "auto_high.html"
    # Threshold of 1 -> should switch to community mode
    generate_html(large_store, output_path2, mode="auto", max_full_nodes=1)
    content2 = output_path2.read_text()
    # Aggregated template has btn-back and community_details
    assert "btn-back" in content2
    assert "community_details" in content2


def test_community_mode_html_generation(large_store, tmp_path):
    """Community mode generates valid HTML with aggregated data."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "community.html"
    generate_html(large_store, output_path, mode="community")
    content = output_path.read_text()
    assert "<!DOCTYPE html>" in content
    assert "</html>" in content
    assert "btn-back" in content
    assert "community_details" in content
    assert "drillIntoCommunity" in content


def test_file_mode_html_generation(large_store, tmp_path):
    """File mode generates valid HTML with file-level data."""
    from code_review_graph.visualization import generate_html

    output_path = tmp_path / "file.html"
    generate_html(large_store, output_path, mode="file")
    content = output_path.read_text()
    assert "<!DOCTYPE html>" in content
    assert "</html>" in content
    assert "DEPENDS_ON" in content


def test_full_mode_backward_compatible(store_with_data, tmp_path):
    """Full mode should produce identical output to the original 2-arg call."""
    from code_review_graph.visualization import generate_html

    # Original 2-arg call (backward compat)
    output1 = tmp_path / "compat.html"
    generate_html(store_with_data, output1)
    content1 = output1.read_text()
    assert "btn-community" in content1
    assert "flow-select" in content1

    # Explicit full mode
    output2 = tmp_path / "full.html"
    generate_html(store_with_data, output2, mode="full")
    content2 = output2.read_text()
    assert "btn-community" in content2
    assert "flow-select" in content2


def test_community_detail_data_complete(large_store):
    """Each community's detail data should contain its member nodes."""
    from code_review_graph.visualization import (
        _aggregate_community,
        export_graph_data,
    )

    data = export_graph_data(large_store)
    agg = _aggregate_community(data)

    for cid_str, detail in agg["community_details"].items():
        assert "nodes" in detail
        assert "edges" in detail
        # Detail nodes should exist
        assert isinstance(detail["nodes"], list)
        assert isinstance(detail["edges"], list)

    # All original nodes should appear in exactly one community detail
    all_detail_qns = set()
    for detail in agg["community_details"].values():
        for n in detail["nodes"]:
            all_detail_qns.add(n["qualified_name"])
    original_qns = {n["qualified_name"] for n in data["nodes"]}
    assert original_qns == all_detail_qns, (
        "All original nodes should be accounted for in community details"
    )
