# Workflow Automation

## Automation

## Trigger

## Goal

## Repo Truth Inputs

- branch:
- system review graph:
- code-review graph contract:
- generated artifacts:
- tests:

## Ruflo Coordination Inputs

- swarm id:
- agent id:
- hook route:
- memory keys:

## Allowed Files

## Forbidden Files

## Steps

1. Fetch and verify branch state.
2. Load AGENTS.md and required repo docs.
3. Load bounded SRG and code-review graph context.
4. Make the smallest scoped change.
5. Run focused proof commands.
6. Refresh generated truth artifacts.
7. Write handoff or blocker rows.
8. Commit and push the branch when proof passes.

## Proof Commands

```bash

```

## Passing Condition

## Failure Condition

## Blocker Rows

| id | module | issue | evidence | owner | gate | next_valid_move | unsafe_to_bypass |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  | closed/open/not_applicable |  | true/false |

## Handoff

- branch/worktree:
- changed files:
- commands run:
- generated artifacts:
- blockers:
- unsafe gates:
- next valid move:
