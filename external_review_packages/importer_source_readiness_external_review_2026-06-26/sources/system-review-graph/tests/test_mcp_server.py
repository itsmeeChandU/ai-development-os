import json
from pathlib import Path

from system_review_graph.mcp_server import handle_message


def test_mcp_initialize_and_tools_list():
    initialize = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1"},
            },
        }
    )
    tools = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

    assert initialize is not None
    assert initialize["result"]["capabilities"]["tools"]["listChanged"] is False
    assert tools is not None
    names = [tool["name"] for tool in tools["result"]["tools"]]
    assert "srg_scan_repository" in names
    assert "srg_load_atlas_context" in names


def test_mcp_load_atlas_context(tmp_path):
    child = tmp_path / "subsystems" / "drivers" / "system_review_manifest.json"
    child.parent.mkdir(parents=True)
    child.write_text(
        json.dumps(
            {
                "title": "drivers child",
                "systems": [],
                "artifacts": [],
                "schemas": [],
                "decision_gates": [],
                "workflows": [],
            }
        )
    )
    root = tmp_path / "system_review_manifest.json"
    root.write_text(
        json.dumps(
            {
                "title": "Atlas",
                "systems": [],
                "artifacts": [],
                "schemas": [],
                "decision_gates": [],
                "workflows": [],
                "child_maps": [
                    {
                        "map_id": "drivers",
                        "name": "drivers",
                        "path": "subsystems/drivers/system_review_manifest.json",
                    }
                ],
                "blueprint_sections": [
                    {
                        "section_id": "boot",
                        "title": "Boot Flow",
                        "purpose": "Track boot into init.",
                    }
                ],
            }
        )
    )

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "srg_load_atlas_context",
                "arguments": {
                    "manifest_path": str(root),
                    "include_children": True,
                },
            },
        }
    )

    assert response is not None
    text = response["result"]["content"][0]["text"]
    assert "drivers child" in text
    assert "Boot Flow" in text
    assert response["result"]["structuredContent"]["truncated"] is False


def test_mcp_scan_repository_tool(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "hello.py").write_text("print('hello')\n")
    manifest = tmp_path / "manifest.json"

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "srg_scan_repository",
                "arguments": {"repo_path": str(repo), "out": str(manifest)},
            },
        }
    )

    assert response is not None
    assert manifest.exists()
    assert "Python Surface" in Path(manifest).read_text()
