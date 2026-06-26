# AI Safety/Prompt Injection Review

Status: `pending_external_review`
Wave: `1`
Severity floor: `P0`
Affected stage: `hosted_private_beta`

## Scope

Review model routing, AI permission controls, redaction previews, manual fallback, and prompt-injection boundaries.

## Primary Artifacts

- `docs/AI_DATA_POLICY.md`
- `system_review_graph/ai_model_router.json`
- `system_review_graph/redaction_pipeline.json`
- `system_review_graph/manual_no_ai_workflow.json`
- `tests/test_operator_app.py`

## Required Decision

AI data, prompt-injection, no-AI fallback, and redaction safety decision.

## Finding Row Schema

Every finding must include:

- `finding_id`
- `reviewer_role`
- `severity`
- `affected_stage`
- `affected_file_or_artifact`
- `issue`
- `owner`
- `required_fix`
- `retest_command`
- `blocks_private_beta`
- `blocks_public_launch`

Severity guide:

- `P0`: Unsafe or blocks private beta.
- `P1`: Blocks public launch or stronger trade/payment claims.
- `P2`: Fix before broader beta.
- `P3`: Improvement.

## Findings

No external findings have been submitted yet.

Use this exact row shape when findings are received:

```json
{
  "finding_id": "AI_SAFETY-001",
  "reviewer_role": "AI Safety/Prompt Injection Review",
  "severity": "P0",
  "affected_stage": "hosted_private_beta",
  "affected_file_or_artifact": "",
  "issue": "",
  "owner": "AI safety reviewer",
  "required_fix": "",
  "retest_command": "python3 -m unittest tests/test_operator_app.py tests/test_product_runtime.py",
  "blocks_private_beta": true,
  "blocks_public_launch": true
}
```

## Gate

- blocks private beta: `true`
- blocks public launch: `true`
- gate state until actual review is recorded: `closed`
- next valid move: Send Wave 1 AI safety packet, collect structured findings, fix every P0 before private beta.
