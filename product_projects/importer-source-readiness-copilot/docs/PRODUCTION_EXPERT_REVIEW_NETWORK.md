# Production Expert Review Network

Status: `production_expert_review_network_ready_scope_limited_no_external_claims`

This phase turns human review into a product workflow. It defines reviewer
lanes, credential evidence, scoped review requests, finding templates, claim
gate impact rows, and audit events. It does not record completed human findings.

## Reviewer Lanes

- Customs / Trade Boundary Reviewer: HS candidate, tariff route, importer responsibility, broker-boundary, and customs-language review.
- Food / Regulated Goods Reviewer: Food, seafood, agri, plant, animal, CFIA/AIRS, permit, certificate, and admissibility-language review.
- Freight / Logistics Reviewer: Shipment path, Incoterms responsibility split, importer of record, packing, temperature, insurance, and forwarder questions.
- Market / Buyer Evidence Reviewer: Market signal, buyer lead route, outreach-readiness, and demand-language review.
- Supplier Evidence Reviewer: Supplier evidence checklist, registrations, product documents, certificates, inspections, and supplier-language review.
- Privacy / Legal Reviewer: Privacy notice, consent, retention, deletion, data processing, legal-language, and customer-claim boundary review.
- Security / Upload Reviewer: File upload pipeline, malware scanning, quarantine, storage isolation, auth, audit, and deletion review.
- AI Safety Reviewer: Prompt injection, AI data policy, redaction, no-AI path, provider terms, and model-output label review.
- Report Language Reviewer: Customer-facing report wording, uncertainty labels, blocked-claim section, and non-approval language review.
- Payment / Billing Reviewer: Paid scope, refund/support wording, checkout, webhook, tax/accounting handoff, and live-payment gate review.

## Counts

- Reviewer lanes: 10
- Profile requirements: 10
- Draft review requests: 10
- Finding templates: 10
- Gate impact rows: 19

## Gate Boundary

- Real reviewer signoff recorded: false
- Qualified credentials verified: false
- Scope-limited approval recorded: false
- Claims opened: false
- External effects created: false

The final rule is: no reviewer lane, no claim lane. A reviewer can approve only
the exact scoped wording or workflow they reviewed, and only after credential
evidence, source/evidence attachments, and a dated finding are stored.
