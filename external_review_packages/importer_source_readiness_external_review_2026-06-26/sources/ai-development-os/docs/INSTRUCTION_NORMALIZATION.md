# Instruction Normalization

Users do not need to write perfect prompts. A good AI development operating
system turns messy, urgent, emotional, or evolving instructions into a workable
execution contract.

## What Often Goes Wrong

Large product prompts often mix:

- goal
- frustration
- deadline
- architecture
- task list
- safety preference
- tool preference
- data expectation
- research expectation
- branch/push expectation
- examples and metaphors
- old state that may be stale
- new state that changes priority

If the agent treats all of that as one flat task, it drifts.

## Normalization Buckets

Before broad work, convert the prompt into:

1. Goal: what outcome matters.
2. Current-state claims: what the user says exists now.
3. Constraints: what must be preserved.
4. Non-goals: what should not be done.
5. Safety/external gates: what cannot be opened casually.
6. Scope: files, modules, product surfaces, data sources.
7. Evidence required: tests, reports, artifacts, screenshots, runtime proof.
8. Tools allowed/desired: agents, web, MCP, APIs, worktrees, browser, hardware.
9. Deadline/appetite: how much depth is appropriate now.
10. Clarifications: only questions that truly block safe progress.
11. Default assumptions: what the agent will assume if the user does not answer.
12. Next action: the first concrete move.

## Agent Behavior

The agent should not wait for a perfect prompt.

It should:

- acknowledge the goal
- identify conflicts or impossible parts
- preserve the latest instruction as highest priority
- verify stale claims against repo/runtime truth
- ask only blocking questions
- otherwise proceed with reasonable assumptions
- update the contract when the user changes direction

## Conflict Handling

When instructions conflict, use this order:

1. latest explicit user instruction
2. hard safety/legal/security boundary
3. repo truth and generated artifacts
4. project instructions
5. prior chat or memory
6. inferred preference

Write conflicts as rows:

| Conflict | Chosen Direction | Reason | Next Valid Move |
|---|---|---|---|
|  |  |  |  |

## Better Prompt Shape

Users can help by giving this shape, but the agent must be able to create it
from a messy prompt too.

```text
Goal:
Current state:
Deadline/appetite:
Must preserve:
Can change:
Data/tools available:
Proof required:
Do not do:
Final handoff should include:
```

## Agent Prompt

```text
Normalize these instructions before acting. Extract goal, current-state claims,
constraints, safety/external gates, scope, required evidence, tool preferences,
deadline, conflicts, assumptions, and next action. Ask only blocking questions.
Then execute the first concrete proof loop and update the contract as repo truth
changes.
```

