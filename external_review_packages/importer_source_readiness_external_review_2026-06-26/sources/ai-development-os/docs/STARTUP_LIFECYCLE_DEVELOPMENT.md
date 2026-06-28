# Startup Lifecycle Development

AI Development OS should move like a startup team, not a ticket queue.

The system starts from a thesis, runs research and R&D loops, turns what works
into a product slice, and keeps validation, launch, and learning gates visible.
Agents may simulate first-pass subject expertise, but real users, operators,
buyers, qualified experts, contracts, official sources, and owners remain the
external-world proof layer.

## Lifecycle Stages

| Stage | Purpose | Required Surface |
|---|---|---|
| idea intake | capture the startup thesis, target user, pain, promise, and non-goals | startup brief and instruction contract |
| research routing | decide model-prior, web, official source, dataset, deep research, and expert/user validation needs | research/data plan |
| R&D exploration | run small feasibility experiments, spikes, simulations, source checks, and tool decisions | R&D notes, experiment results, blocker rows |
| product slice | choose the first workflow that can become useful now | architecture overview, work package, lane packet |
| implementation | build code, data, operator surfaces, tests, and generated artifacts | source changes, tests, reports |
| visual/operator evidence | expose screenshots, smoke outputs, logs, and current operator state when experience matters | operator screenshot manifest or proof gallery |
| validation | collect buyer, operator, expert, compliance, data-rights, and contract evidence | continuation plan and evidence lanes |
| VC readiness | prepare private investor conversation without hiding diligence gaps | VC pitch readiness report and investor packet |
| board/private beta | prepare controlled go-live decisioning without claiming public launch | board go-live report, board packet, approval gates |
| launch/operate | open only approved external effects and monitor outcomes | launch approval, runbook, rollback, support, outcome log |
| learning loop | convert outcomes and feedback into the next product loop | estimate-vs-actual, lessons, refined idea |

## R&D Rules

R&D is not a pause before building. It is a bounded learning loop.

Each R&D loop needs:

- hypothesis
- experiment or source check
- artifact path
- pass/fail or continue/kill decision
- cost/time/risk note
- next valid move

Examples:

- technical spike
- data-source feasibility check
- official-rule review
- simulation or fixture prototype
- tool decision record
- buyer workflow interview plan
- manufacturing/procurement blocker
- model or evaluation benchmark

## Proof Boundary

AI can produce the first thesis, implementation, simulations, visual proof, and
operator packets. It cannot by itself prove buyer demand, legal/compliance
approval, financial advice, physical manufacturing readiness, data rights,
signed contracts, public launch approval, or qualified subject-matter truth.

Those become evidence lanes or blocker rows until real people, official
sources, datasets, contracts, or owners close them.

## Operator Evidence

Screenshots and UI smoke outputs belong inside the lifecycle only when they
help a person inspect the product or operator state. They should be generated
artifacts with stable paths and proof boundaries, not decorative assets.
For recurring operator work, the product should also generate a work queue that
combines source rows, evidence gates, continuation lanes, approval gates, proof
commands, and closed claims.

Preferred paths:

```text
system_review_graph/operator_workflow_report.json
system_review_graph/operator_screenshot_manifest.json
system_review_graph/operator_screenshots/
```

The screenshot surface answers:

- what was generated
- when it was captured
- which file proves it exists
- what it does and does not prove
- what remains blocked

## Completion Rule

Do not report a startup as complete just because the first product slice works.

Report the exact lifecycle stage:

- `idea_captured`
- `research_routed`
- `rd_in_progress`
- `prototype_ready`
- `software_loop_complete`
- `operator_ready_internal`
- `startup_in_progress`
- `vc_pitch_ready_with_diligence_gates`
- `board_go_live_candidate_with_human_approval_gates`
- `private_beta_approved`
- `launch_ready`

Only use `launch_ready` after explicit owner approval, current evidence,
qualified review where needed, and final smoke checks.
