# UX/Product Usability Review

Status: `pending_external_review`
Wave: `1`
Severity floor: `P0`
Affected stage: `hosted_private_beta`

## Scope

Can a target importer/exporter understand the flow, blockers, generated reports, and next valid move without unsafe advice?

## Primary Artifacts

- `README.md`
- `docs/GO_LIVE_READINESS.md`
- `system_review_graph/operator_dashboard.html`
- `system_review_graph/customer_readiness_report.md`
- `system_review_graph/public_trade_readiness_manifest.json`

## Required Decision

Private-beta usability decision with P0/P1 findings listed.

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
  "finding_id": "UX_PRODUCT-001",
  "reviewer_role": "UX/Product Usability Review",
  "severity": "P0",
  "affected_stage": "hosted_private_beta",
  "affected_file_or_artifact": "",
  "issue": "",
  "owner": "product/UX reviewer",
  "required_fix": "",
  "retest_command": "python3 scripts/check_product.py",
  "blocks_private_beta": true,
  "blocks_public_launch": true
}
```

## Gate

- blocks private beta: `true`
- blocks public launch: `true`
- gate state until actual review is recorded: `closed`
- next valid move: Send Wave 1 UX/product packet, collect structured findings, fix every P0 before private beta.
