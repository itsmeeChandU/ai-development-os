# Codex Usage For High-Leverage Work

Use Codex as a configured engineering system, not a chat window.

## Practical Surfaces

- `AGENTS.md`: durable repo instructions.
- `.codex/config.toml`: repo-specific settings for trusted projects.
- Skills: reusable workflows with instructions, scripts, and references.
- MCP: live external tools and context providers.
- Worktrees: isolated branches for parallel work.
- Subagents: specialized parallel workers.
- Automations: recurring checks and monitors.
- Hooks: lifecycle enforcement around commands and edits.

## Recommended Use

1. Put stable rules in `AGENTS.md`.
2. Put repeatable workflows in `.agents/skills`.
3. Use MCP for GitHub, docs, browser, Figma, observability, or internal systems.
4. Use worktrees for parallel lanes.
5. Use subagents only when the task can be split by ownership.
6. Keep one coordinator responsible for integration.

## Prompt Shape

```text
Goal:
Context:
Allowed files:
Forbidden files:
Data/artifacts:
Tests/proof commands:
Done when:
Handoff format:
```

## Premium/High-Capacity Usage

Premium capacity is wasted if agents receive vague work. Spend capacity on:

- parallel code/data/test lanes
- long-running proof loops
- browser/UI verification
- source/API research
- code review and adversarial review
- generated artifact refreshes
- CI triage

Do not spend capacity on repeated status summaries without a proof loop.

