# Trade-Boundary/Customs-Language Review Packet

Status: `ready_to_send_to_external_reviewer`
Wave: `2`

## Review Boundary

The attached product is locally implemented with external gates. Your decision
must not be treated as legal, customs, tariff, freight, security, privacy,
payment, buyer, production, or public-launch approval unless your role
explicitly covers that claim and your findings say so.

## Ask

Review public report and UI language for unsupported customs, tariff, legal, CFIA, and import/export readiness claims.

Required decision: Customs, tariff, CFIA, import/export wording and claim-boundary decision.

## Review These Artifacts

- `docs/PUBLIC_TRADE_READINESS.md`
- `system_review_graph/claims_gate_matrix.json`
- `system_review_graph/public_report_types.json`
- `system_review_graph/generated_reports/starter_checklist_packet-frozen-tuna-canada-001.json`

## Finding Format

Return every issue with:

`finding_id`, `reviewer_role`, `severity`, `affected_stage`,
`affected_file_or_artifact`, `issue`, `owner`, `required_fix`,
`retest_command`, `blocks_private_beta`, `blocks_public_launch`.

Severity: `P0` unsafe or blocks private beta, `P1` blocks public launch,
`P2` fix before broader beta, `P3` improvement.

## Retest Command

```bash
python3 scripts/check_product.py
```

## Gate

- blocks private beta: `false`
- blocks public launch: `true`
- next valid move: Send Wave 2 trade-boundary packet before any stronger trade/customs wording is used publicly.
