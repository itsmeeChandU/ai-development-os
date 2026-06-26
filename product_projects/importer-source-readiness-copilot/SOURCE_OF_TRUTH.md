# Source Of Truth

Repo files, generated reports, tests, and git history are the source of truth.

## Canonical Product Reports

- `system_review_graph/readiness_report.json`
- `system_review_graph/external_gate_report.json`
- `system_review_graph/continuation_plan.json`
- `system_review_graph/customer_readiness_report.json`
- `system_review_graph/evidence_ledger.json`
- `system_review_graph/operator_workflow_report.json`
- `system_review_graph/operator_dashboard.html`
- `system_review_graph/operator_screenshot_manifest.json`
- `system_review_graph/vc_pitch_readiness_report.json`
- `system_review_graph/board_go_live_readiness_report.json`
- `system_review_graph/intelligence_hub_policy_monitor.json`
- `system_review_graph/completion_platform_manifest.json`
- `system_review_graph/opportunity_scanner_report.json`
- `system_review_graph/country_coverage_report.json`
- `system_review_graph/transport_readiness_report.json`
- `system_review_graph/billing_credit_controls.json`
- `system_review_graph/agent_api_manifest.json`
- `system_review_graph/product_operations_report.json`
- `system_review_graph/public_upload_policy.json`
- `PRODUCT_REVIEW_REPORT.md`
- `THOROUGH_COMPLETION_AUDIT.md`
- `system_review_graph/thorough_completion_audit.json`

## Canonical Product Doctrine

- `PRODUCT_DOCTRINE.md`
- `CUSTOMER_SOURCE_PACKET_SPEC.md`
- `REVIEW_USE_TERMS.md`

## Proof Commands

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_product.py
python3 scripts/audit_external_package.py --root .
```

Chat summaries, package descriptions, screenshots, and review comments are
claims until they are backed by one of the artifacts above.
