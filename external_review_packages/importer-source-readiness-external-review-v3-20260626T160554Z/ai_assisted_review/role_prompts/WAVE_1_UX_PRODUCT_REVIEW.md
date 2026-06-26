# AI-Assisted UX/Product Usability Review Prompt

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

- reviewer_role: `UX/Product Usability Review`
- wave: `1`
- severity floor: `P0`
- affected stage: `hosted_private_beta`
- scope: Can a target importer/exporter understand the flow, blockers, generated reports, and next valid move without unsafe advice?

## Review These Artifacts

- `README.md`
- `docs/GO_LIVE_READINESS.md`
- `system_review_graph/operator_dashboard.html`
- `system_review_graph/customer_readiness_report.md`
- `system_review_graph/public_trade_readiness_manifest.json`

## Suggested Source Anchors

- Add current sources if you search the web for this role.

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
  "reviewer_role": "UX/Product Usability Review",
  "model_or_agent_used": "",
  "web_sources_checked": [],
  "verdict": "blocked|needs_fixes|no_p0_p1_found",
  "human_followup_required": true,
  "findings": [
    {
      "finding_id": "UX_PRODUCT-AI-001",
      "reviewer_role": "UX/Product Usability Review",
      "severity": "P0",
      "affected_stage": "hosted_private_beta",
      "affected_file_or_artifact": "",
      "issue": "",
      "owner": "product/UX reviewer",
      "required_fix": "",
      "retest_command": "python3 scripts/check_product.py",
      "blocks_private_beta": true,
      "blocks_public_launch": true,
      "confidence": "low|medium|high",
      "human_followup_required": true
    }
  ]
}
```
