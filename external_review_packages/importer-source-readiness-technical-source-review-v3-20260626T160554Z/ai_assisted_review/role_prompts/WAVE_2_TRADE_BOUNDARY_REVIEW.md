# AI-Assisted Trade-Boundary/Customs-Language Review Prompt

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

- reviewer_role: `Trade-Boundary/Customs-Language Review`
- wave: `2`
- severity floor: `P1`
- affected stage: `stronger_trade_claims`
- scope: Review public report and UI language for unsupported customs, tariff, legal, CFIA, and import/export readiness claims.

## Review These Artifacts

- `docs/PUBLIC_TRADE_READINESS.md`
- `system_review_graph/claims_gate_matrix.json`
- `system_review_graph/public_report_types.json`
- `system_review_graph/generated_reports/starter_checklist_packet-frozen-tuna-canada-001.json`

## Suggested Source Anchors

- CBSA importing commercial goods: https://www.cbsa-asfc.gc.ca/import/menu-eng.html
- CFIA importing food, plants, or animals: https://inspection.canada.ca/en/importing-food-plants-animals

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
  "reviewer_role": "Trade-Boundary/Customs-Language Review",
  "model_or_agent_used": "",
  "web_sources_checked": [],
  "verdict": "blocked|needs_fixes|no_p0_p1_found",
  "human_followup_required": true,
  "findings": [
    {
      "finding_id": "TRADE_BOUNDARY_CUSTOMS_LANGUAGE-AI-001",
      "reviewer_role": "Trade-Boundary/Customs-Language Review",
      "severity": "P1",
      "affected_stage": "stronger_trade_claims",
      "affected_file_or_artifact": "",
      "issue": "",
      "owner": "trade compliance reviewer",
      "required_fix": "",
      "retest_command": "python3 scripts/check_product.py",
      "blocks_private_beta": false,
      "blocks_public_launch": true,
      "confidence": "low|medium|high",
      "human_followup_required": true
    }
  ]
}
```
