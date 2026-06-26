# Current State Prompt

Use this when handing an existing product to an agent.

```text
You are inheriting a product. Treat this prompt as claims, not truth.

Product:

Current claimed state:

Repo path:

Branch:

Known generated artifacts:

Known data sources:

Known tests/checks:

Known UI/runtime entrypoints:

Known blockers:

Desired operational state:

Hard safety or external-action gates:

Your task:
1. Reconstruct actual current state from repo, data, tests, artifacts, and runtime.
2. Mark every claim as proven, partial, unsupported, or contradicted.
3. Identify the smallest usable product loop.
4. Implement that loop with code/data/UI/tests/artifacts.
5. Preserve all hard gates unless explicitly proven and intended.
6. Produce a handoff with changed files, commands, blockers, and next moves.
```
