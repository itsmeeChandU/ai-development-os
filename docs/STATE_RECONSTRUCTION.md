# State Reconstruction

The most important agent skill is not writing code from a prompt. It is
recovering the actual state of a product from mixed evidence.

Use this workflow whenever the user gives a prompt like:

```text
Here is the current state of the product. Tell me where we actually are and
finish it.
```

## Principle

Chat is a lead. Repo truth is evidence.

The agent must separate:

- what the user says is true
- what files prove is true
- what data proves is true
- what tests prove is true
- what runtime/screenshot/log evidence proves is true
- what external research proves is true
- what remains unsupported

## Reconstruction Inputs

Collect these before broad edits:

1. user prompt and claimed product state
2. repository status, branch, dirty files, latest commits
3. project instructions such as `AGENTS.md`, `README.md`, and architecture docs
4. generated artifacts and reports
5. test results and CI status
6. loaded data, fixtures, databases, schemas, freshness, and rights
7. UI routes, screenshots, browser smoke checks, or CLI outputs
8. external APIs, credentials presence, entitlements, and rate limits
9. deployment/runtime status
10. open tasks, blockers, worktrees, branches, and handoffs

## Output Model

Write a current-state artifact with this shape:

```json
{
  "as_of": "2026-06-22T00:00:00Z",
  "repo": {
    "branch": "main",
    "head": "commit",
    "dirty": false
  },
  "product": {
    "claim": "What the product is supposed to be",
    "actual_state": "What is implemented and verified",
    "usable_now": false
  },
  "modules": [
    {
      "name": "module",
      "implemented": true,
      "evidence": ["file", "test", "report"],
      "blockers": ["blocker id"],
      "next_valid_move": "smallest safe action"
    }
  ],
  "unsafe_or_external_gates": [
    {
      "name": "payment/live-send/legal-public/etc",
      "state": "closed",
      "evidence": "why"
    }
  ]
}
```

## Reconstruction Loop

1. Parse the prompt into claims.
2. For each claim, find repo or external evidence.
3. Mark each claim as `proven`, `partially_proven`, `unsupported`, or `contradicted`.
4. Map proven claims into modules and user flows.
5. Map unsupported claims into blocker rows.
6. Find the smallest end-to-end flow that can become usable.
7. Split only that flow into implementation lanes.
8. Run focused proof commands.
9. Refresh generated artifacts from the final source tree.
10. Produce a handoff that another agent can resume.

## Prompt

```text
Reconstruct actual product state from this prompt and repo. Treat the prompt as
claims, not truth. Verify against files, generated artifacts, data, tests,
runtime behavior, and cited external sources. Produce a state table, blockers,
next_valid_move rows, unsafe/external gates, and the smallest product loop that
can be completed now. Then implement that loop with tests and artifacts.
```

## Failure Mode To Avoid

Do not turn the user's product-state prompt into a plan without verification.
The agent should be able to say:

```text
The prompt says X. The repo proves Y. The product can currently do Z. The next
valid move is A.
```

