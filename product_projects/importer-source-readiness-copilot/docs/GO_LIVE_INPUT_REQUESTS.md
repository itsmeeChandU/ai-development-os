# Go Live Input Requests

Status: `waiting_for_real_inputs_not_ready_yet`

This is the simple intake plan for real people. Send the short reviewer brief
first. When answers come back, save each answer as a JSON file in
`external_inputs/` using the matching template in
`system_review_graph/go_live_input_templates.json`, then rerun:

```bash
python3 scripts/run_external_validation_requirements.py --input-dir external_inputs
```

## Current Go Live State

- Public launch ready: `False`
- Ready inputs received: `0` of `8`
- Missing inputs: `8`

## Inputs To Collect

## Outside Expert Review

Who to ask: Product, security, privacy/legal, AI safety, operations, trade, and payment reviewers as relevant.

Question: Have the right outside reviewers checked the right scope?

Ready answer: Ready for my area

Minimum input needed:
- reviewer name
- reviewed scope
- decision
- top issues
- missing evidence
- signed date

## Legal, Privacy, And Security

Who to ask: Privacy/legal reviewer plus application security reviewer.

Question: Is customer data handling, security, AI use, retention, deletion, and incident handling acceptable for the launch scope?

Ready answer: Ready for my area

Minimum input needed:
- reviewer name
- data/privacy scope
- security scope
- decision
- missing evidence
- signed date

## Customs And Trade Language

Who to ask: Licensed customs broker or qualified trade/compliance reviewer.

Question: Does the product avoid unsupported customs, tariff, CFIA, sanctions, and trade-readiness claims?

Ready answer: Ready for my area or not applicable for this launch

Minimum input needed:
- reviewer name
- country/product scope
- approved wording
- wording to avoid
- decision
- signed date

## Hosted Staging Or Production

Who to ask: DevOps, SRE, or operations owner.

Question: Is there real hosted evidence for the launch scope, not only localhost?

Ready answer: Ready for my area

Minimum input needed:
- environment URL
- commit/build
- smoke result
- monitoring
- rollback owner
- decision
- signed date

## Payments

Who to ask: Billing/payment owner, tax/accounting advisor if needed, and support owner.

Question: Are live checkout, webhook, tax/refund/support, and billing wording ready, or is payment intentionally off for launch?

Ready answer: Ready for my area or not applicable for this launch

Minimum input needed:
- payment scope
- Stripe mode
- webhook evidence
- refund/support owner
- decision
- signed date

## Real User Feedback

Who to ask: Product/UX owner or user research owner.

Question: Have real target users used the product and understood what is and is not approved?

Ready answer: Ready for my area

Minimum input needed:
- participant count
- segments
- task results
- top issues
- what changed
- decision
- signed date

## Buyer Or Supplier Validation

Who to ask: Founder or commercial validation owner.

Question: Have real buyers, suppliers, importers, exporters, or advisors validated the problem and workflow?

Ready answer: Ready for my area or not applicable for this launch

Minimum input needed:
- counterparty type
- problem validated
- evidence summary
- permission scope
- decision
- signed date

## Final Go Live Decision

Who to ask: Named launch owner.

Question: After all other inputs are in, is this launch approved for the exact stated scope?

Ready answer: Go for public launch

Minimum input needed:
- launch scope
- production URL
- remaining risks
- support owner
- rollback owner
- decision
- signed date


## Once Inputs Are Received

1. Save each response as one JSON file in `external_inputs/`.
2. Rerun the command above.
3. Open `system_review_graph/go_live_input_readiness_report.json`.
4. If status is `go_live_ready_after_real_inputs`, use the exact approved launch scope from the final go-live input.
5. If status is `waiting_for_real_inputs_not_ready_yet`, collect only the missing items shown in that report.
