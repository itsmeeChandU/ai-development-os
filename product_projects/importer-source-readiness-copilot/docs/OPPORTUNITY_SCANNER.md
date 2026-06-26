# Opportunity Scanner

The opportunity scanner turns existing packet context into possible opportunity signals and research prompts. It does not recommend products or claim demand, profit, supplier quality, buyer validation, or shipment readiness.

## What It Uses

- Packet product category
- Trade direction
- Origin and destination countries
- Country coverage tier
- Evidence and blocker context

## What It Produces

- Possible opportunity signal rows
- Demand/supply/trend fields marked as `unknown_requires_external_research` until evidence exists
- Requirements and transport complexity prompts
- Next valid moves into packet, buyer, expert, and logistics review

## Generated Artifacts

- `system_review_graph/opportunity_scanner_report.json`
- `system_review_graph/country_coverage_report.json`
- `system_review_graph/completion_platform_manifest.json`

Proof boundary: opportunity rows are research prompts only. Real market demand, margins, buyers, suppliers, routes, contracts, and legal/compliance needs require current evidence and qualified review.
