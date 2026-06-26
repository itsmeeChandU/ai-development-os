# Trade-Boundary/Customs-Language Review

Status: `pending_external_review`
Wave: `2`
Severity floor: `P1`
Affected stage: `stronger_trade_claims`

## Scope

Review public report and UI language for unsupported customs, tariff, legal, CFIA, and import/export readiness claims.

## Primary Artifacts

- `docs/PUBLIC_TRADE_READINESS.md`
- `system_review_graph/claims_gate_matrix.json`
- `system_review_graph/public_report_types.json`
- `system_review_graph/generated_reports/starter_checklist_packet-frozen-tuna-canada-001.json`

## Required Decision

Customs, tariff, CFIA, import/export wording and claim-boundary decision.

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
  "finding_id": "TRADE_BOUNDARY_CUSTOMS_LANGUAGE-001",
  "reviewer_role": "Trade-Boundary/Customs-Language Review",
  "severity": "P1",
  "affected_stage": "stronger_trade_claims",
  "affected_file_or_artifact": "",
  "issue": "",
  "owner": "trade compliance reviewer",
  "required_fix": "",
  "retest_command": "python3 scripts/check_product.py",
  "blocks_private_beta": false,
  "blocks_public_launch": true
}
```

## Gate

- blocks private beta: `false`
- blocks public launch: `true`
- gate state until actual review is recorded: `closed`
- next valid move: Send Wave 2 trade-boundary packet before any stronger trade/customs wording is used publicly.
