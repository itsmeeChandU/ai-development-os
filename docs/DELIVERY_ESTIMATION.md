# Delivery Estimation

Agents should estimate before execution and compare after execution.

The goal is not to create false certainty. The goal is to make scope, cost,
timeline, tools, data, risk, and human-vs-agent effort visible.

## Estimate Inputs

- normalized instruction contract
- reconstructed current state
- system review graph
- target product loop
- architecture overview
- required tools and data
- procurement or external dependencies
- safety/compliance gates
- available agents/worktrees

## Estimate Output

Every estimate should include:

- product goal
- final architecture overview
- module/lane breakdown
- worker prompts/specs
- tools/APIs/data needed
- procurement/lab needs
- proof commands
- blockers and assumptions
- AI-agent timeline
- comparable human-team timeline
- cost categories
- confidence range

## Human Timeline Comparison

Use ranges, not fake precision.

| Complexity | AI Agent Path | Human Team Path |
|---|---|---|
| small local app | hours to days | days to weeks |
| data-backed app | days to weeks | weeks to months |
| multi-module SaaS | weeks | months |
| hardware/OS prototype | weeks to months | months to quarters |
| regulated product | months with blockers | quarters to years |

The comparison should say what the AI can accelerate and what it cannot:

- accelerated: code drafting, research, scaffolding, tests, docs, simulations
- not eliminated: real data access, hardware lead time, lab work, certification, user proof, legal review

## Estimate-Vs-Actual Loop

After each proof cycle, write:

- estimated work
- completed work
- changed files
- proofs run
- time spent
- blockers found
- estimate changes
- next valid move

This gives the system a learning loop instead of repeating optimistic planning.

