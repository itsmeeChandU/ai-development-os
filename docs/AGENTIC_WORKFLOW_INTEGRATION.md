# Agentic Workflow Integration

AI Development OS coordinates the larger product flow where Venture Studio can
produce a startup or application idea and agents can build it through GitHub,
Ruflo, System Review Graph, code-review graph contracts, worktrees, tests, and
handoffs.

The durable rule is simple: GitHub and repo artifacts are truth. Ruflo is
coordination memory. Web research is evidence. Generated docs are bounded
context surfaces for agents and LLMs, not proof by themselves.

## Workflow Contract

1. Normalize the request into goal, constraints, evidence, gates, scope,
   assumptions, and first action.
2. Classify complexity with `docs/COMPLEXITY_ROUTER.md`.
3. Reconstruct actual state from repo files, generated artifacts, tests,
   runtime proof, and current branch status.
4. Build or load the System Review Graph for system context.
5. Load the code-review graph contract for code-level files, modules, symbols,
   imports, edges, tests, generated artifacts, and risk/ownership hints.
6. Split work only after owned files, forbidden files, proof commands, and
   handoff requirements are clear.
7. Use one branch/worktree per bounded lane when parallel work is useful.
8. Run small proof loops, refresh generated truth artifacts, and push verified
   branches.

## Agent Modes

| Mode | Edits | Use |
|---|---:|---|
| research | no | Fill a repo-proven capability gap with dated evidence. |
| architect | no | Define contracts, graphs, architecture, lanes, and proof. |
| surgeon | yes | Make a bounded change with focused tests and handoff. |
| reviewer | no | Find regressions, missing proof, and forbidden touches. |
| merge | yes | Integrate verified branches and refresh final artifacts. |
| goal | yes | Keep a long-running objective active until done or blocked. |

## GitHub And Worktrees

- Fetch `origin` before lane work.
- Branch from `origin/main` unless a task names another base.
- Use `codex/` branch names by default.
- Do not edit or push `main` unless explicitly requested.
- Keep generated artifact refreshes tied to the final tree being pushed.
- Every pushed branch needs a handoff naming branch, changed files, commands,
  proof results, blockers, unsafe gates, and next valid move.

## Ruflo Boundary

Use Ruflo for:

- swarm and lane records
- memory search/store for coordination summaries
- hook routing events
- branch/worktree ownership notes

Do not use Ruflo as:

- repo truth
- proof that tests passed
- permission to take unsafe or external actions
- storage for secrets or private data rows

## SRG And Code-Review Graph

System Review Graph answers what the system does, trusts, blocks, and should
inspect next. The code-review graph answers what code exists and how it
connects. Use the private `itsmeeChandU/code-review-graph-private` repo as the
working contract implementation; repo-local exporters can emit compatible
contracts for existing systems such as Intelligence Hub. The workflow needs
both:

```text
startup idea -> AI Development OS contract -> SRG context bundle
-> code-review graph contract -> bounded lanes -> proof loops
-> branch push / blocker handoff
```

The machine-readable source of this workflow is
`manifests/agentic_workflow_manifest.json`.
