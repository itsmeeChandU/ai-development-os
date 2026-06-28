# Product And Operator Review Brief

## Review Goal

Review whether the current internal operator application is useful for a
founder, sourcing operator, compliance reviewer, or board/private-beta owner.

## What The App Does

The operator app shows:

- source-card readiness status
- external evidence gates
- blocker rows
- next valid moves
- Canadian official/reference tools
- continuation lanes
- human approval gates
- board/private-beta readiness
- screenshot evidence

The app is served from:

```bash
cd sources/importer-source-readiness-copilot
python3 scripts/serve_operator_app.py
```

## Questions

1. Can an operator understand what to do next?
2. Are blockers phrased clearly enough?
3. Does the work queue help prioritize action?
4. Is the dashboard too technical, too legalistic, or useful as-is?
5. What would a real importer, broker, or founder need on the first screen?
6. What workflow is missing before controlled private beta?
7. What workflow is missing before a customer-facing product?
8. What evidence should be captured after a real operator review?

## Key Artifacts

- `evidence/operator_artifacts/operator_dashboard.html`
- `evidence/operator_artifacts/operator_workflow_report.json`
- `evidence/product_reports/readiness_report.json`
- `evidence/product_reports/external_gate_report.json`
- `evidence/product_reports/continuation_plan.json`

## Known Product Boundary

This is an internal operator product. It is not yet the product a paying
external importer would use directly.

Please recommend what the customer-facing app should become.
