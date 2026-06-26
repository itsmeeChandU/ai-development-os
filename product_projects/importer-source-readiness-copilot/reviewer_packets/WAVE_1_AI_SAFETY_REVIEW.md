# AI Safety/Prompt Injection Review Packet

Status: `ready_to_send_to_external_reviewer`
Wave: `1`

## Review Boundary

The attached product is locally implemented with external gates. Your decision
must not be treated as legal, customs, tariff, freight, security, privacy,
payment, buyer, production, or public-launch approval unless your role
explicitly covers that claim and your findings say so.

## Ask

Review model routing, AI permission controls, redaction previews, manual fallback, and prompt-injection boundaries.

Required decision: AI data, prompt-injection, no-AI fallback, and redaction safety decision.

## Review These Artifacts

- `docs/AI_DATA_POLICY.md`
- `system_review_graph/ai_model_router.json`
- `system_review_graph/redaction_pipeline.json`
- `system_review_graph/manual_no_ai_workflow.json`
- `tests/test_operator_app.py`

## Finding Format

Return every issue with:

`finding_id`, `reviewer_role`, `severity`, `affected_stage`,
`affected_file_or_artifact`, `issue`, `owner`, `required_fix`,
`retest_command`, `blocks_private_beta`, `blocks_public_launch`.

Severity: `P0` unsafe or blocks private beta, `P1` blocks public launch,
`P2` fix before broader beta, `P3` improvement.

## Retest Command

```bash
python3 -m unittest tests/test_operator_app.py tests/test_product_runtime.py
```

## Gate

- blocks private beta: `true`
- blocks public launch: `true`
- next valid move: Send Wave 1 AI safety packet, collect structured findings, fix every P0 before private beta.
