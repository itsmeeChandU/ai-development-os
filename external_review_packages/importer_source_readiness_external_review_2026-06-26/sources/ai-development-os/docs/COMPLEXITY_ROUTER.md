# Complexity Router

AI Development OS should scale down and up.

A calculator app should not get the same process as a hardware operating
system or chip design. The agent must choose the lightest process that can
prove the product.

## Complexity Levels

| Level | Example | Process |
|---|---|---|
| S0 tiny | calculator, static page, small script | quick task contract, implement, run, smoke test |
| S1 small app | CRUD app, local tool, simple game | state check, focused implementation, UI/test proof |
| S2 data/API app | app with external APIs, auth, data freshness | source/data audit, credentials, fixtures, integration tests |
| S3 multi-module product | SaaS, marketplace, trading tool, internal platform | system review graph, architecture, lane split, generated artifacts |
| S4 complex physical/system product | hardware, OS, firmware, robotics, chip design | complex product playbook, tool breeding ground, simulation/bench/compliance |
| S5 regulated/field product | medical, finance execution, public legal claims, safety-critical field ops | qualified review, compliance gates, staged launch, no unsupported claims |

## Routing Rules

Use the lowest level that proves the outcome.

- If it can be built and verified locally in one file or one small app, use S0/S1.
- If real data, credentials, APIs, or paid sources matter, use S2.
- If multiple modules, agents, worktrees, or launch surfaces matter, use S3.
- If hardware, firmware, OS, chip, lab, procurement, or physical safety matter, use S4.
- If legal, medical, financial execution, safety-critical, or external claims matter, use S5.

## Small Product Prompt

```text
Classify this product complexity first. If it is S0 or S1, do not create heavy
architecture. Build the smallest working product, run it, test the main flow,
and provide changed files and proof. Escalate only if real blockers appear.
```

## Complex Product Prompt

```text
Classify this product complexity first. If it is S4 or S5, use instruction
normalization, state reconstruction, system review graph, delivery estimate,
tool breeding ground, complex product playbook, simulation/bench/compliance
proof, and blocker rows before claiming operational completion.
```

