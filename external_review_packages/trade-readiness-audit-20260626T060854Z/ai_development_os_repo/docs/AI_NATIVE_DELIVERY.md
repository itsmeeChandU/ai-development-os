# AI-Native Delivery

Human development often works through tacit context, judgment, and informal
memory. AI development needs explicit external structure.

## The Best Process

1. Start from a product outcome, not a task list.
2. Create an executable contract: requirements, artifacts, tests, blockers.
3. Build a system review graph.
4. Split work into lanes only after ownership boundaries are clear.
5. Run focused proof cycles.
6. Merge only verified slices.
7. Regenerate truth artifacts from the final tree.
8. Keep a single operator/readiness surface.

## When Minimal Instructions Are Enough

Use a short prompt when:

- the change is local
- tests already describe desired behavior
- files are obvious
- no data, credentials, legal, payment, or external side effects are involved

## When More Instructions Are Required

Demand a task spec when:

- the idea is vague
- multiple modules are involved
- data freshness matters
- external APIs or paid tools are involved
- agent parallelism is requested
- launch claims or customer-facing claims are involved
- safety, money, privacy, or legal risk exists

## The Useful Failure Pattern

If a task drifts:

1. Stop broad implementation.
2. Run the system review graph.
3. Name the exact failing predicate.
4. Write the blocker and next valid move.
5. Make one code/data/report/test change that moves that predicate.

## Full-Capacity Agent Pattern

Use one coordinator and many bounded workers:

- coordinator owns main integration and final truth
- worker owns one lane and one branch/worktree
- worker cannot redefine done
- worker must produce code, tests, artifacts, blockers, and handoff
- coordinator merges only passing slices

## What Not To Do

- Do not let agents run broad audits forever.
- Do not accept "implemented with blockers" as operational.
- Do not create private readiness or permission paths.
- Do not use tests without generated truth artifacts.
- Do not let stale worktrees become authoritative.
- Do not add tools because they are fashionable.

