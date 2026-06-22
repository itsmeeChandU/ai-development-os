# System Review Graph

The system review graph is the pattern that prevents agents from wandering.
It is a linked map of what exists, what data powers it, what flow it belongs to,
what blocks it, and what proves it.

## Graph Layers

1. Code graph: files, functions, entrypoints, tests, generated artifacts.
2. Data graph: sources, loaders, freshness, rights, schemas, lineage.
3. Flow graph: user journeys, runtime states, background jobs, external calls.
4. Decision graph: decisions, gates, permissions, ownership, expiry.
5. Proof graph: tests, reports, smoke checks, screenshots, logs, artifacts.
6. Task graph: blockers, next valid moves, assigned lanes, handoffs.
7. Resource graph: docs, API references, open-source repos, licenses.

## Required Output

Every non-trivial project should have a generated or maintained graph summary:

```text
system_review_graph/
  code_graph.md
  data_graph.md
  flow_graph.md
  proof_graph.md
  task_graph.md
  resource_graph.md
  blockers.jsonl
```

## Blocker Row Schema

```json
{
  "id": "module:blocker-name",
  "module": "Module name",
  "issue": "What is wrong",
  "evidence": "File/report/test/source proving it",
  "owner": "lane or person",
  "gate": "closed/open/not_applicable",
  "next_valid_move": "Smallest action that can move it",
  "unsafe_to_bypass": true
}
```

## Agent Prompt

```text
Build a system review graph before editing. Inspect code, data, flows, proof
artifacts, blockers, and external resources. Then implement the smallest slice
that moves the highest-impact blocker. Produce changed files, commands run,
artifact paths, and next_valid_move rows.
```

