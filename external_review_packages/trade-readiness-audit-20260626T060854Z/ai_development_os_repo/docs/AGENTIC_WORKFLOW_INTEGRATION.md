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
7. If an optional external harness such as Everything Claude Code is useful,
   generate an external harness integration packet before installing or relying
   on it.
8. Use one branch/worktree per bounded lane when parallel work is useful.
9. Run small proof loops, refresh generated truth artifacts, and push verified
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

## External Agent Harnesses

External harnesses can speed up AI-native delivery when they are treated as
optional accelerators. Everything Claude Code (ECC) is currently recorded as an
optional MIT-licensed harness pattern source for thin vertical-slice MVP work,
managed loops, verification loops, model routing, harness audits, AgentShield
security scans, skills, commands, and hooks.

Before using an external harness, generate:

```bash
python3 scripts/agentic_workflow_orchestrator.py harness-intake \
  --harness ecc \
  --install-mode observe \
  --target-repo ai-development-os \
  --goal "Evaluate optional same-day product harness patterns" \
  --out-dir system_review_graph
```

Use `observe` as the default mode. Installing project-local or global harness
surfaces needs explicit operator approval, source/license recording, duplicate
hook/plugin checks, and a config/security scan where relevant. The harness can
help agents move faster, but it cannot replace source inspection, tests,
generated artifacts, GitHub branch state, blocker rows, continuation plans, or
qualified human approval gates.

## Execution Surface

The runnable execution contract lives in
`manifests/agentic_execution_manifest.json`. It defines:

- slash commands such as `/ados:normalize`, `/ados:repo-intake`,
  `/ados:research-plan`, `/ados:strategy-plan`, `/ados:lane`,
  `/ados:proof`, `/ados:merge`, and `/ados:goal`
- skills and their proof boundaries
- background routines for branch freshness, context refresh, stale blockers,
  overnight eval loops, and CI failure triage
- parallel agent lane packets with allowed files, forbidden files, proof
  commands, and handoff requirements
- CI/CD jobs, eval loops, supervision rules, and multi-repo integration rules

Validate and emit an execution plan with:

```bash
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py automation-check
python3 scripts/agentic_workflow_orchestrator.py emit \
  --goal "Build the first verified product loop" \
  --out-dir system_review_graph
```

The plan can be handed to agents or LLMs as bounded context. It is still only a
coordination surface; completion requires changed files, focused checks,
generated artifacts, GitHub branch state, and a handoff or blocker row.

## Research And Strategy Routing

Prompt-to-product is not one development path. The coordinator must choose the
minimum useful external context and the right agent mix for the product field:

- `manifests/internal_repo_registry.json` declares which internal/helper repos
  can originate ideas, coordinate work, provide context, export code-review
  graph contracts, or hold product implementation.
- `manifests/research_data_router.json` separates model-prior synthesis,
  normal web scans, official-source review, structured data/API needs, deep
  research, and real user or subject-expert validation.
- `manifests/development_strategy_router.json` chooses field modes for local
  software, data/API products, AI/ML products, regulated/high-stakes work,
  hardware/manufacturing, cross-border supply chains, and contract-dependent
  products.

AI model subject knowledge is acceptable for first-pass hypotheses and product
drafting. It is not proof for current facts, buyer demand, country rules,
tariffs, certifications, supplier availability, contracts, safety, medical,
legal, financial, or launch claims. Those require dated source records,
official-source evidence, datasets/API contracts, qualified experts, or blocker
rows with `next_valid_move`.

For manufacturing, import/export, and contract-heavy ideas, the expected flow
is:

```text
idea packet -> repo intake -> research/data plan -> development strategy plan
-> country requirements matrix / supplier data / contract blockers
-> implementation lanes -> proof loops -> expert/user correction loop
```

The coordinator should move quickly where software proof is enough and slow
down only at external gates. External inputs are not chat blockers; they become
machine-readable blocker rows with owner, evidence, gate, and next valid move.

## Startup Continuation Rule

`ready_with_external_gates` is a useful internal software state, not final
startup completion. When any product readiness or external-gate report has that
status, the product repo must generate:

```text
system_review_graph/continuation_plan.json
```

That plan must keep the product `startup_in_progress`, set
`must_continue: true`, list the next evidence lanes, and close premature claims
such as `fully_operational`, `launch_ready`, and `commercially_ready`.

The difference is important: AI agents can build the local product loop quickly,
but current country rules, source rights, buyer demand, contracts, qualified
review, screening, and public launch approval still require evidence or blocker
rows. A coordinator must not mark the long-running goal complete until those
lanes are closed or the goal was explicitly scoped as local-only.

## Prompt-To-Product Runtime

The local runtime now materializes the operating flow into files:

```bash
python3 scripts/agentic_workflow_orchestrator.py repo-intake \
  --idea-source intelligence-hub \
  --target-repo future-product-repo \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py research-plan \
  --problem "Manufacturing product requiring supplier data, country import/export requirements, contracts, and expert validation" \
  --domain manufacturing \
  --data-need "supplier data, official country rules, tariffs, certifications, contract terms" \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py strategy-plan \
  --idea "Manufacturing product requiring supplier discovery, country import/export checks, contracts, and logistics" \
  --field manufacturing \
  --country US \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py harness-intake \
  --harness ecc \
  --install-mode observe \
  --target-repo future-product-repo \
  --goal "Evaluate optional same-day product harness patterns" \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py prompt-to-product \
  --name "my-startup" \
  --idea "Build a product with proof gates" \
  --field software \
  --idea-source intelligence-hub \
  --target-repo future-product-repo \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py emit-slash-commands \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py lane-packet \
  --lane workflow-coordinator \
  --goal "Own the first proof loop" \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py routine-report \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py scheduler-plan \
  --out-dir system_review_graph
python3 scripts/agentic_workflow_orchestrator.py ci-fix \
  --check-name workflow_manifest_ci \
  --out-dir handoffs
```

This gives agents runnable packets for slash commands, lane work, safe
background routines, scheduler wiring, CI repair, research/data routing, and
field-specific development strategy. The runtime intentionally defaults to
dry-run packet generation so external effects remain behind explicit proof
gates.
