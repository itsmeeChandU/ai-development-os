# AI-Assisted Billing/Payment Review Prompt

Status: `ready_for_solo_ai_review`

Use this in a separate ChatGPT mode, agent, or model context. Treat yourself as
an independent reviewer, not as the product builder. Be skeptical, concrete, and
file-specific.

## Boundary

This is an AI-assisted simulated review. Your output can create fixes or
blockers. It cannot approve hosted private beta, public launch, legal/privacy
readiness, security readiness, customs/tariff readiness, freight readiness, or
payment readiness.

## Product Context

The product is a blocked-safe import/export readiness checker. The expected
state is local readiness with external gates closed.

## Review Role

- reviewer_role: `Billing/Payment Review`
- wave: `3`
- severity floor: `P1`
- affected stage: `monetization_or_public_scale`
- scope: Review billing controls, usage ledger, pricing page, live-checkout disabled state, refund/tax/invoice gaps, and payment-flow blockers.

## Review These Artifacts

- `system_review_graph/billing_credit_controls.json`
- `system_review_graph/billing_usage_ledger.json`
- `system_review_graph/product_operations_report.json`
- `README.md`

## Suggested Source Anchors

- Stripe go-live checklist: https://docs.stripe.com/get-started/checklist/go-live

## Task

1. Inspect the artifacts for this role.
2. If web research is useful, use current sources and list exact URLs.
3. Find unsafe claims, missing controls, confusing UX, missing blocker rows, or
   untested behavior.
4. Return only structured findings plus a short verdict.

## Required Output

```json
{
  "review_origin": "ai_assisted_simulated_review",
  "reviewer_role": "Billing/Payment Review",
  "model_or_agent_used": "",
  "web_sources_checked": [],
  "verdict": "blocked|needs_fixes|no_p0_p1_found",
  "human_followup_required": true,
  "findings": [
    {
      "finding_id": "BILLING_PAYMENT-AI-001",
      "reviewer_role": "Billing/Payment Review",
      "severity": "P1",
      "affected_stage": "monetization_or_public_scale",
      "affected_file_or_artifact": "",
      "issue": "",
      "owner": "billing/payment reviewer",
      "required_fix": "",
      "retest_command": "python3 -m unittest tests/test_product_runtime.py tests/test_completion_platform.py",
      "blocks_private_beta": false,
      "blocks_public_launch": true,
      "confidence": "low|medium|high",
      "human_followup_required": true
    }
  ]
}
```
