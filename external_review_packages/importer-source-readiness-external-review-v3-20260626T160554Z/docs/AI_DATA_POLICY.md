# AI Data Policy

Trade Readiness Copilot treats AI as an optional evidence-organization layer, not as an authority for customs, tariff, legal, supplier, buyer, shipment, or launch claims.

## Modes

- `no_ai`: manual review only.
- `metadata_only`: AI can see packet metadata, not uploaded document contents.
- `redacted`: AI can receive redacted evidence summaries.
- `business_api`: hosted model route, blocked for restricted evidence unless policy allows it.
- `private_hosted_llm`, `customer_managed_llm`, `on_prem_manual`: private or customer-controlled routes for sensitive workflows.

## Rules

- Organization policy decides the default mode and allowed modes.
- Evidence can lower permission to `no_ai` or `metadata_only`.
- Restricted or regulated evidence requires private/no-AI handling.
- AI simulated reviewers can suggest findings and next moves only.
- AI output cannot open external claim gates.

## Generated Artifacts

- `system_review_graph/ai_data_policy.json`
- `system_review_graph/ai_model_router.json`
- `system_review_graph/redaction_pipeline.json`
- `system_review_graph/manual_no_ai_workflow.json`

Proof boundary: this policy is a product control. Hosted use still needs qualified privacy, legal, security, and customer data review.
