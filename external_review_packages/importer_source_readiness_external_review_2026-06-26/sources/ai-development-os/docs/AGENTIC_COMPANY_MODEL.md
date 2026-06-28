# Agentic Company Model

AI Development OS should behave like an AI-native company in a box.

The user supplies vision, constraints, taste, and decisions. The system turns
that into a coordinated product organization with agents acting as departments,
each producing evidence instead of vague progress.

## Company Functions

| Function | Agent Responsibility | Output |
|---|---|---|
| CEO / product owner | clarify outcome, deadline, appetite, final calls | product intent and decision log |
| Chief of staff | normalize instructions, maintain task graph | instruction contract |
| Product management | users, workflows, scope, release slices | startup brief and product loop |
| Research | market, APIs, hardware, open-source, standards | research records |
| Architecture | modules, interfaces, data/control flows | architecture overview |
| Engineering | implementation across backend, frontend, data, firmware | code and tests |
| Design / UX | operator experience and product flows | UI plan and screenshots |
| Data office | sources, loaders, freshness, lineage, rights | data/source graph |
| QA / verification | tests, smoke checks, reports, generated artifacts | proof gate |
| Security | secrets, threat model, supply chain | security checklist |
| Legal / licensing | license, attribution, responsibility, compliance | licensing records |
| Finance / delivery control | estimates, cost, timeline, variance | estimate and actuals report |
| Operations | launch, monitoring, runbooks, support | operator surface and runbook |

## Operating Cadence

1. Intake: normalize prompt and reconstruct state.
2. Estimate: produce architecture, lane plan, tool/data/procurement needs, and timeline.
3. Commit: choose the first usable product loop.
4. Build: run lane-owned proof cycles.
5. Integrate: coordinator merges verified slices only.
6. Review: compare estimated vs actual output.
7. Operate: launch, monitor, and record next valid moves.

## Agent Department Rules

- Every department produces files, not just opinions.
- Every estimate names uncertainty and assumptions.
- Every lane has owned files, forbidden files, proof commands, and a handoff.
- Every external dependency has a fallback or blocker.
- Every product claim has evidence or a blocker.
- Every launch has an operator surface and rollback path.

## Company Prompt

```text
Run this as an AI-native company. Create an instruction contract, reconstruct
current state, produce a delivery estimate, draft the final architecture,
split the work into departments/lanes, write the exact worker prompts, execute
the first proof cycle, and report estimate-vs-actual output.
```

