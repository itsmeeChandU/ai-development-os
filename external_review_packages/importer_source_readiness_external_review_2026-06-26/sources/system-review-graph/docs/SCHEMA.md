# Manifest Schema

System Review Graph uses a JSON manifest. The manifest is deliberately simple so teams can generate it from any language or architecture.

## Top-Level Fields

| Field | Type | Purpose |
|---|---|---|
| `title` | string | Report title. |
| `one_line` | string | One-sentence distinction or summary. |
| `scope` | string | What the report covers. |
| `current_truth` | object | Honest status snapshot. |
| `bigger_picture` | string | Narrative context. |
| `systems` | array | Major subsystems, services, lanes, bounded contexts, or product surfaces. |
| `artifacts` | array | Reports, APIs, tables, files, UI pages, queues, or generated outputs. |
| `schemas` | array | Public, internal, or sanitized contracts. |
| `decision_gates` | array | Rules that advance, block, route, or require review. |
| `workflows` | array | Lifecycle steps. |
| `edges` | array | Optional explicit graph edges. |
| `child_maps` | array | Optional linked subsystem maps for large-repo atlases. |
| `documentation_sources` | array | Optional generated or maintained documentation artifacts used as repo knowledge inputs. |
| `knowledge_nodes` | array | Optional documentation-knowledge nodes such as concepts, files, owner modules, stages, statuses, and cleanup labels. |
| `knowledge_edges` | array | Optional documentation-knowledge relationships between those nodes. |
| `blueprint_sections` | array | Optional source-evidence-backed flows for blueprint-depth reports. |
| `source_links` | array | Public links used for a public-safe report. |
| `architecture_patterns` | array | How different project styles map into this model. |
| `walkthroughs` | array | Human-readable examples. |
| `review_questions` | array | Questions a maintainer, auditor, reviewer, or AI agent should ask. |
| `rebuild_recipe` | array | Commands or steps to reproduce the report. |
| `known_boundaries` | array | What this report does not prove. |

## Systems

Systems can be services, apps, libraries, lanes, workflows, agent roles, data layers, or control surfaces.

Required:

- `system_id`
- `name`
- `purpose`

Useful optional fields:

- `owner`
- `language_stack`
- `architecture_style`
- `lifecycle`
- `code_surfaces`
- `artifacts`
- `decision_gates`
- `truth_boundary`
- `ideal_target`
- `example`

## Artifacts

Artifacts are inspectable things.

Examples:

- API response,
- Markdown report,
- JSONL ledger,
- database table,
- event stream,
- UI page,
- CI job,
- model card,
- deployment manifest.

Fields:

- `artifact_id`
- `name`
- `kind`
- `path`
- `owner`
- `schema`
- `purpose`
- `redaction`

## Schemas

Schemas do not have to expose production data. A private company can publish a safe contract like:

```json
{
  "name": "CustomerTicketContract",
  "kind": "sanitized_event",
  "required_fields": ["ticket_id", "created_at", "status", "priority", "redacted_subject"],
  "privacy_notes": "No customer names, emails, body text, or account ids are included."
}
```

## Decision Gates

Decision gates explain system behavior.

Example:

```json
{
  "gate_id": "human_approval_gate",
  "name": "Human Approval Gate",
  "inputs": ["action_intent", "risk_level"],
  "outputs": ["approved", "blocked", "needs_review"],
  "human_gate": true,
  "rules": [
    { "if": "risk_level == high", "then": "needs_review" },
    { "if": "missing evidence", "then": "blocked" }
  ],
  "risk_boundary": "No external send occurs without approval."
}
```

## Workflow Steps

Workflow steps show movement.

```json
{
  "step_id": "capture_outcome",
  "name": "Capture Outcome",
  "actor": "Outcome Worker",
  "consumes": ["action_intent"],
  "gates": ["human_approval_gate"],
  "produces": ["outcome_ledger"],
  "next_steps": ["learn_from_outcome"],
  "purpose": "Turn action into reality feedback."
}
```

## Source Links

Use `source_links` when a report maps public repos, papers, standards, docs, or
sanitized internal references.

```json
{
  "label": "GitHub repository",
  "url": "https://github.com/example/project",
  "notes": "Primary public source used for paths and architecture surfaces."
}
```

## Child Maps

Use `child_maps` when one flat graph would hide the system. A root atlas can
link child manifests for subsystems, monorepo packages, kernel directories,
microservice families, or product lanes.

```json
{
  "map_id": "drivers",
  "name": "drivers/ subsystem map",
  "path": "subsystems/drivers/system_review_manifest.json",
  "report_path": "../subsystems/drivers/reports/system_review_graph.md",
  "purpose": "Drill-down map generated from this top-level repository directory.",
  "scope": "drivers/",
  "systems": ["c_cpp"],
  "status": "inferred_from_source_tree",
  "review_hint": "Open this child map to refine exact workflows, ownership, tests, and gates."
}
```

The root atlas stays small. The child maps carry local detail. This is useful
when an AI agent, reviewer, or new maintainer needs one uploadable map that
points to the rest of the context.

## Documentation Knowledge Graph

Use `documentation_sources`, `knowledge_nodes`, and `knowledge_edges` when a
repo has its own documentation catalog, file inventory, source-code graph,
cleanup audit, or generated documentation graph. This keeps SRG from flattening
deep repo knowledge into prose only.

```json
{
  "documentation_sources": [
    {
      "artifact": "data/intelligence/global_repository_documentation_rows.jsonl",
      "role": "complete row-per-file documentation catalog",
      "incorporated_information": ["path", "owner", "purpose", "cleanup action"]
    }
  ],
  "knowledge_nodes": [
    {
      "node_id": "concept:stock_selection",
      "type": "concept",
      "label": "Stock selection",
      "attributes": {
        "description": "How source, market, catalyst, and risk proof select candidates."
      }
    }
  ],
  "knowledge_edges": [
    {
      "source": "concept:stock_selection",
      "relation": "USES_OWNER",
      "target": "owner:stock_market_system"
    }
  ]
}
```

For very large documentation graphs, keep the full nodes/edges in JSONL files
and use the MCP/CLI context loader to pull only the slice needed for a review.
These artifacts are designed first for agents and LLMs, so prefer stable IDs,
typed relations, explicit boundaries, query recipes, and compact context slices
over narrative-only documentation.

## Blueprint Sections

Use `blueprint_sections` when a report needs to explain how the system works,
not only where files are.

```json
{
  "section_id": "boot_init_userspace",
  "title": "Boot, Kernel Init, And Userspace Handoff",
  "purpose": "Track the early kernel path into the first userspace process.",
  "subsystems": ["arch", "init", "kernel", "fs"],
  "source_evidence": [
    {
      "path": "init/main.c:1017",
      "symbol": "start_kernel",
      "role": "generic kernel entry",
      "notes": "Generic initialization begins after architecture handoff.",
      "proof_level": "source-confirmed"
    }
  ],
  "flow": [
    {
      "step": "Generic kernel initialization",
      "actor": "start_kernel",
      "consumes": "early boot state",
      "produces": "initialized core services",
      "next": "rest_init",
      "evidence": "init/main.c:1017"
    }
  ],
  "control_points": [
    {
      "gate": "Initcall ordering gate",
      "location": "include/linux/module.h",
      "decision": "early/core/subsys/fs/device/late order",
      "failure_mode": "dependency starts too early or too late",
      "evidence": "module_init/initcall macros"
    }
  ]
}
```

This is the main difference from a code review graph. A code graph may show
that functions reference each other. A blueprint section says what path those
functions represent, what operation moves through them, what gates control the
operation, and what proof level supports the claim.

## Review Questions

Use `review_questions` to turn the report into an audit checklist:

```json
[
  "Which gate blocks unsafe downstream action?",
  "Which artifact proves the action outcome?",
  "What can be reviewed if the database is private?"
]
```

## Privacy Levels

Use `redaction` on artifacts:

- `safe_to_share`
- `public_summary_only`
- `schema_only`
- `counts_only`
- `private_do_not_publish`

## Design Principle

If the database is private, describe the contract and boundary. A reviewer should still understand what the system does.

## Report Depth

The manifest does not need to change when you want more or less detail. Choose
depth at render time:

```bash
system-review-graph build --manifest system_review_manifest.json --out-dir reports --depth overview
system-review-graph build --manifest system_review_manifest.json --out-dir reports --depth standard
system-review-graph build --manifest system_review_manifest.json --out-dir reports --depth deep
system-review-graph build --manifest system_review_manifest.json --out-dir reports --depth blueprint
```

`deep` reports add relationship graphs, schema examples, and per-system
artifact/gate/workflow expansion. `blueprint` reports add source-evidence,
operational-flow, control-point, and known-gap tables for blueprint sections.

## JSON Schema

A machine-readable JSON Schema is available at:

```text
docs/schema/system_review_manifest.schema.json
```

Use it in editors, CI checks, or external tooling.
