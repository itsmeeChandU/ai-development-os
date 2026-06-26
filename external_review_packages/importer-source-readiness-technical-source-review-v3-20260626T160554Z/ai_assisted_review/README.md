# AI-Assisted External Review

Status: `ai_assisted_external_review_ready`
Wave 1 simulated review status: `ai_assisted_wave_1_reviewed_with_blockers`

This folder is for a solo developer using ChatGPT modes, separate agents, and
web research to approximate external review pressure before real qualified
review is available.

AI-assisted review can find P0/P1 issues and improve the product. It cannot
open private beta, public launch, legal/privacy/security, customs, freight, or
payment gates by itself.

## Workflow

1. Run each prompt in `role_prompts/` in a separate model mode or agent.
2. For source-sensitive roles, record web sources in `WEB_RESEARCH_SOURCE_LOG.md`.
3. Save outputs in `simulated_findings/` with `review_origin:
   ai_assisted_simulated_review`.
4. Convert actionable rows into fixes or blocker rows.
5. Rerun `python3 scripts/check_product.py`.

## Current Simulated Review Evidence

- simulated review count: `5`
- simulated finding count: `5`
- simulated findings report: `system_review_graph/ai_assisted_external_review_findings_report.json`

## Gate Boundary

- human-equivalent approval: `false`
- can open private beta gate: `false`
- can open public launch gate: `false`
- can reduce findings before real review: `true`
