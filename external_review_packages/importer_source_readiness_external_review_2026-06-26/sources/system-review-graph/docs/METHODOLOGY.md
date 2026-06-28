# Methodology

System Review Graph does not claim that code structure alone proves system
behavior. Code shows what can happen. A system review asks what actually moves,
what controls it, what evidence supports it, and what outcomes it creates.

## Code Map Versus System Map

| Layer | Main Question | Typical Evidence |
|---|---|---|
| Code map | What files, modules, functions, imports, and calls exist? | source tree, call graph, imports, symbols |
| System map | What does the system do from input to decision to output? | APIs, configs, docs, tests, schemas, queues, databases, reports, UI, runbooks |
| Documentation knowledge map | How do repo docs, files, concepts, stages, owners, and cleanup states connect? | file catalog rows, documentation graph nodes/edges, module inventory, reference audit |
| Operating map | What is trusted, blocked, reviewed, or acted on? | decision gates, permissions, logs, outcomes, incidents, human review |

System Review Graph starts from a manifest because the system boundary often
cannot be recovered perfectly from code alone.

## The Core Method

Use this sequence:

```text
sources -> artifacts -> schemas -> systems -> workflows -> gates -> outcomes -> review questions
```

1. Identify external and internal sources.
2. List inspectable artifacts: files, APIs, tables, queues, dashboards, reports, logs, configs.
3. Describe schemas or contracts for each artifact.
4. Group artifacts into systems or bounded contexts.
5. Describe workflows: what consumes, gates, produces, and routes to the next step.
6. Add decision gates: what advances, waits, blocks, or needs human review.
7. Add current truth and boundaries: what is proven, unproven, private, or unsafe to publish.
8. Generate registers: coverage, evidence, gaps, and actions.
9. Add review questions so humans and agents know where to inspect next.

## Report Registers

The generated report includes four registers so it can be reviewed like an
open-source audit packet rather than only read like narrative documentation.

| Register | Purpose |
|---|---|
| Coverage Register | Counts the systems, artifacts, schemas, gates, workflows, graph edges, child maps, blueprint sections, evidence rows, source links, boundaries, review questions, and rebuild phases. |
| Evidence Register | Lists the source links, artifact paths, schema contracts, and blueprint evidence rows used to support the report. |
| Gap Register | Lists known boundaries, unproven runtime claims, missing gates, missing workflows, missing evidence, and optional deepening areas. |
| Action Register | Turns review questions, known boundaries, blueprint gaps, and rebuild phases into a next-action queue. |

These registers do not make a report true by themselves. They make the truth
surface inspectable: a maintainer can see what was mapped, what supports it,
what remains open, and what should happen next.

## Documentation Knowledge Graphs

Some repositories maintain deeper generated documentation than a normal README:
file-by-file catalogs, module relevance inventories, source-code graphs,
reference audits, and nodes/edges that connect concepts to files and cleanup
states. SRG can carry that information as documentation sources, knowledge
nodes, and knowledge edges.

The intended stack is:

```text
documentation sources -> knowledge nodes/edges -> SRG report registers
                      -> MCP context slices for agents
```

For a very large graph, do not paste every node into a manifest. Keep the full
JSONL graph artifacts in the target repo and load bounded slices through the
MCP tool or CLI context command.

These generated artifacts are primarily agent/LLM operating surfaces. Optimize
them for stable IDs, compact summaries, query recipes, proof boundaries,
machine-readable `next_moves`, and bounded context loading. Human-readable prose
still matters, but it should sit beside the machine-readable graph instead of
being the only way to understand the repository.

## How It Works With Only Code

If only source code is available, create a provisional system map from:

- top-level package directories,
- CLI entry points,
- web/API route files,
- config files,
- database migrations,
- tests,
- examples,
- docs,
- package metadata,
- generated outputs.

Then mark uncertainty explicitly. For example:

```json
{
  "truth_boundary": "Inferred from public source paths and tests; production deployment is not reviewed."
}
```

## How It Works With Private Systems

Private companies often cannot expose raw databases or records. In that case,
publish:

- logical service names,
- API contracts,
- schema-only artifacts,
- counts instead of records,
- fake examples,
- redaction rules,
- decision gates,
- known boundaries.

The report should teach the architecture without leaking the organization.

## Why This Is Different From A Call Graph

A call graph can say `function A calls function B`. It usually cannot tell you:

- whether an external action is allowed,
- whether a human gate is required,
- whether a dataset is stale,
- whether an artifact is safe to publish,
- whether an output becomes an operational decision,
- whether the outcome is captured and learned from.

System Review Graph treats function calls as one source of evidence, not the
whole truth.

## Quality Bar

A good report lets a reviewer answer:

- What enters the system?
- What transforms it?
- What rules control it?
- What artifacts prove each stage exists?
- What leaves the system?
- What is blocked?
- What is not proven?
- Where should I inspect next?
