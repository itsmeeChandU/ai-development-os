# Report-Language Review

Status: `pending_external_review`
Wave: `2`
Severity floor: `P1`
Affected stage: `stronger_trade_claims`

## Scope

Review generated report types, missing-evidence language, buyer/broker packet wording, and customer-safe next moves.

## Primary Artifacts

- `system_review_graph/public_report_types.json`
- `system_review_graph/generated_reports/missing_evidence_packet-frozen-tuna-canada-001.json`
- `system_review_graph/generated_reports/chatgpt_safe_summary_packet-frozen-tuna-canada-001.json`
- `system_review_graph/customer_readiness_report.md`

## Required Decision

Generated PDF/report wording decision for customer-safe language.

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
  "finding_id": "REPORT_LANGUAGE-001",
  "reviewer_role": "Report-Language Review",
  "severity": "P1",
  "affected_stage": "stronger_trade_claims",
  "affected_file_or_artifact": "",
  "issue": "",
  "owner": "report-language reviewer",
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
- next valid move: Send Wave 2 report-language packet before public report language is treated as approved.
