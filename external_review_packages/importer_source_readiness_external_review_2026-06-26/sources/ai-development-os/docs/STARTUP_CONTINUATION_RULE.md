# Startup Continuation Rule

## Rule

`ready_with_external_gates` is not a final product or startup status.

It means the local software loop is useful for internal operator work, but the
startup is still `startup_in_progress` until external evidence lanes close.
Agents must not report a product as fully operational, launch ready,
commercially ready, legally ready, buyer validated, customs/tariff ready, or
supplier ready while any generated continuation plan says
`must_continue: true`.

## Required Artifact

Externally gated product repos must write:

```text
system_review_graph/continuation_plan.json
```

The artifact must include:

- `status`
- `software_loop_status`
- `local_operator_status`
- `readiness_status`
- `external_gate_status`
- `must_continue`
- `lane_count`
- `blocker_count`
- `lanes`
- `not_done_reasons`
- `next_valid_move`
- `proof_boundary`
- `closed_claims`

When readiness or external-gate status is `ready_with_external_gates`, the
continuation plan must say:

```json
{
  "status": "startup_in_progress",
  "must_continue": true
}
```

## Lane Expectations

The continuation plan should turn blockers into bounded evidence lanes such as:

- buyer/operator validation
- qualified compliance review
- country import/export requirements
- source rights and data freshness
- commercial/source contracts
- restricted-party screening
- launch and public-claim approval

Each lane needs an owner, required evidence, blocker references,
`next_valid_move`, proof command, and bypass boundary.

## Completion Semantics

Use these meanings consistently:

| Status | Meaning |
|---|---|
| `software_loop_complete` | code, tests, local artifacts, and internal operator surface work |
| `operator_ready_internal` | useful for internal review while unsafe and external gates stay closed |
| `startup_in_progress` | external evidence, contracts, users, qualified review, or launch approval remain open |
| `externally_operational_candidate` | local and external blocker reports are clear, pending final launch review |
| `launch_ready` | only after explicit operator approval, evidence artifacts, compliance/review proof, and final smoke checks |

## Proof Boundary

AI model subject synthesis can produce the first hypothesis and local product
logic can move fast. Current rules, official sources, datasets, contracts,
country import/export needs, buyer truth, and final subject direction still
require dated evidence, qualified people, or blocker rows.
