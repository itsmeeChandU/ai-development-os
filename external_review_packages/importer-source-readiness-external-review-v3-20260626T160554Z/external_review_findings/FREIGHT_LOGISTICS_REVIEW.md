# Freight/Logistics Review

Status: `pending_external_review`
Wave: `2`
Severity floor: `P1`
Affected stage: `stronger_trade_claims`

## Scope

Review transport readiness rows, broker/forwarder packets, Incoterms-style questions, and shipment-readiness boundaries.

## Primary Artifacts

- `system_review_graph/transport_readiness_report.json`
- `system_review_graph/generated_reports/broker_packet_packet-frozen-tuna-canada-001.json`
- `system_review_graph/public_report_types.json`

## Required Decision

Forwarder packet, transport questions, and shipment-readiness boundary decision.

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
  "finding_id": "FREIGHT_LOGISTICS-001",
  "reviewer_role": "Freight/Logistics Review",
  "severity": "P1",
  "affected_stage": "stronger_trade_claims",
  "affected_file_or_artifact": "",
  "issue": "",
  "owner": "freight/logistics reviewer",
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
- next valid move: Send Wave 2 freight/logistics packet before shipment or forwarder-readiness claims are strengthened.
