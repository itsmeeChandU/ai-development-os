# MCP Server

System Review Graph includes a lightweight stdio MCP server:

```bash
system-review-graph-mcp
```

It lets MCP-capable agents call SRG directly instead of shelling out manually.
The server uses newline-delimited JSON-RPC over stdin/stdout and exposes tools
for scanning, building, validating, doctoring, and loading atlas context.

## Client Config

Example MCP client configuration:

```json
{
  "mcpServers": {
    "system-review-graph": {
      "command": "system-review-graph-mcp"
    }
  }
}
```

For local development from a checkout:

```json
{
  "mcpServers": {
    "system-review-graph": {
      "command": "python",
      "args": ["-m", "system_review_graph.mcp_server"]
    }
  }
}
```

## Tools

| Tool | Purpose |
|---|---|
| `srg_validate_manifest` | Validate manifest structure and unresolved references. |
| `srg_doctor_manifest` | Report audit-readiness warnings and missing review surfaces. |
| `srg_build_report` | Build Markdown/JSON reports, with optional HTML and DOT. |
| `srg_scan_repository` | Generate a starter manifest or large-repo atlas from a local repo. |
| `srg_load_atlas_context` | Load a compact context bundle from a root atlas, blueprint sections, and optional child maps. |
| `srg_load_documentation_graph_context` | Load a compact slice from documentation knowledge graph nodes/edges JSONL files. |
| `srg_load_repo_context_bundle` | Load bounded SRG, documentation graph, and code-review graph context for agents. |

## Why MCP Matters For Atlases

For a huge repository, the static report is useful for humans, but the MCP tool
surface is useful for agents:

```text
agent -> srg_load_atlas_context(root manifest)
      -> choose changed/risky child map
      -> choose source-backed blueprint section
      -> load child context
      -> validate/doctor/build updated reports
```

That makes the atlas a live context object. A reviewer can attach one root map,
and an agent can discover the linked subsystem maps without reading the entire
repo at once.

The same applies to documentation knowledge graphs. Generated docs should be
loaded as bounded, machine-readable context for agents and LLMs: start from a
stable concept or file node, follow typed edges, inspect summaries and
`next_moves`, then open source artifacts only when the task needs proof.

## Example Tool Calls

Validate:

```json
{
  "name": "srg_validate_manifest",
  "arguments": {
    "manifest_path": "examples/fictional_ai_ops/system_review_manifest.json"
  }
}
```

Generate an atlas and reports:

```json
{
  "name": "srg_scan_repository",
  "arguments": {
    "repo_path": "/path/to/repo",
    "out": "reports/system-review-atlas",
    "atlas": true,
    "max_subsystems": 24,
    "build_reports": true,
    "depth": "overview"
  }
}
```

Load an atlas for an agent:

```json
{
  "name": "srg_load_atlas_context",
  "arguments": {
    "manifest_path": "reports/system-review-atlas/system_review_manifest.json",
    "include_children": true,
    "max_child_maps": 8,
    "max_blueprint_sections": 8
  }
}
```

Load a documentation graph slice for an agent:

```json
{
  "name": "srg_load_documentation_graph_context",
  "arguments": {
    "nodes_path": "/path/to/documentation_knowledge_graph_nodes.jsonl",
    "edges_path": "/path/to/documentation_knowledge_graph_edges.jsonl",
    "start_node": "concept:stock_selection",
    "max_nodes": 80,
    "max_edges": 160
  }
}
```

Load a repo context bundle for an AI Development OS lane:

```json
{
  "name": "srg_load_repo_context_bundle",
  "arguments": {
    "manifest_path": "reports/system-review-atlas/system_review_manifest.json",
    "documentation_nodes_path": "/path/to/documentation_knowledge_graph_nodes.jsonl",
    "documentation_edges_path": "/path/to/documentation_knowledge_graph_edges.jsonl",
    "code_review_graph_path": "/path/to/code_review_graph_contract.json",
    "start_node": "concept:agentic_workflow",
    "max_nodes": 80,
    "max_edges": 160
  }
}
```

## Boundaries

- The MCP server does not execute arbitrary shell commands.
- It reads and writes only the paths supplied by the MCP client.
- Atlas scans are source-surface maps, not proof of runtime behavior.
- Documentation graph context is a bounded slice; use narrower node/relation
  filters or load the source artifact when more detail is needed.
- Repo context bundles are agent handoff packets, not runtime proof or
  permission to bypass review, safety, legal, or release gates.
- Keep private data, secrets, and production records out of manifests.
