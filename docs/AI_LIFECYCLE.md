# AI Lifecycle

Normal SDLC assumes humans carry context and intent. AI-native delivery assumes
context is fragile unless it is externalized into files, artifacts, and gates.

## Human SDLC

Typical human software lifecycle:

1. requirements
2. design
3. implementation
4. testing
5. release
6. maintenance

This is still useful, but it is not enough for AI agents because agents can:

- move very fast in the wrong direction
- forget implicit constraints
- satisfy tests while missing operational reality
- over-plan instead of ship
- invent readiness when data is missing

## AI-Native Lifecycle

Use this instead:

1. Prompt intake: capture idea, user, promise, constraints, non-goals.
2. Instruction normalization: convert messy input into a stable execution contract.
3. Context grounding: read repo, data, prior artifacts, docs, and current state.
4. System review graph: map code, data, flows, tasks, proof, and resources.
5. Delivery estimate: architecture, lane plan, tool/data needs, cost, and timeline.
6. Product slice selection: choose the smallest useful product loop.
7. Tool/resource loading: connect MCP, APIs, browser, docs, data, or repos only when needed.
8. Agent lane split: assign bounded implementation, data, UI, QA, research lanes.
9. Proof-loop implementation: write code/data/tests/reports/artifacts.
10. Operator surface: produce one truth surface showing usable, blocked, stale, next.
11. Estimate-vs-actual review: compare planned and developed state.
12. Handoff and memory: record changed files, proofs, blockers, next valid move.
13. Reverse analysis: inspect the product that emerged and refine the original idea.

For complex products, add hardware, firmware/OS, simulation, bench validation,
procurement, compliance, and field-operation stages before claiming completion.

## New Definition Of Requirements

For AI, a requirement is weak until it has:

- a file or artifact where it lives
- a command that checks it
- a test/report that can fail
- a next valid move when blocked

## New Definition Of Design

For AI, design is not only architecture. It is:

- file ownership
- state machines
- proof artifacts
- data freshness
- tool permissions
- rollback and handoff paths

## New Definition Of Done

Done means the system can answer:

- what exists
- what works
- what is blocked
- what evidence proves it
- what to do next
- what must not be bypassed
