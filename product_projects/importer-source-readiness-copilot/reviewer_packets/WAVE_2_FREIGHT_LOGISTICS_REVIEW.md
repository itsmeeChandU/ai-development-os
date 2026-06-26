# Freight/Logistics Review Packet

Status: `ready_to_send_to_external_reviewer`
Wave: `2`

## Review Boundary

The attached product is locally implemented with external gates. Your decision
must not be treated as legal, customs, tariff, freight, security, privacy,
payment, buyer, production, or public-launch approval unless your role
explicitly covers that claim and your findings say so.

## Ask

Review transport readiness rows, broker/forwarder packets, Incoterms-style questions, and shipment-readiness boundaries.

Required decision: Forwarder packet, transport questions, and shipment-readiness boundary decision.

## Review These Artifacts

- `system_review_graph/transport_readiness_report.json`
- `system_review_graph/generated_reports/broker_packet_packet-frozen-tuna-canada-001.json`
- `system_review_graph/public_report_types.json`

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
- next valid move: Send Wave 2 freight/logistics packet before shipment or forwarder-readiness claims are strengthened.
