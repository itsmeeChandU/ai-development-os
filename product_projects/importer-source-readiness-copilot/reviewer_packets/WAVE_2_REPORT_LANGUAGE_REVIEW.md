# Report-Language Review Packet

Status: `ready_to_send_to_external_reviewer`
Wave: `2`

## Review Boundary

The attached product is locally implemented with external gates. Your decision
must not be treated as legal, customs, tariff, freight, security, privacy,
payment, buyer, production, or public-launch approval unless your role
explicitly covers that claim and your findings say so.

## Ask

Review generated report types, missing-evidence language, buyer/broker packet wording, and customer-safe next moves.

Required decision: Generated PDF/report wording decision for customer-safe language.

## Review These Artifacts

- `system_review_graph/public_report_types.json`
- `system_review_graph/generated_reports/missing_evidence_packet-frozen-tuna-canada-001.json`
- `system_review_graph/generated_reports/chatgpt_safe_summary_packet-frozen-tuna-canada-001.json`
- `system_review_graph/customer_readiness_report.md`

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
- next valid move: Send Wave 2 report-language packet before public report language is treated as approved.
