# External Review Process

Status: `external_review_ready_findings_pending`

The product has an external-review-ready package and a technical source-review
workflow. This is not external review completion. Real reviewer decisions must
be collected in `external_review_findings/` before any gate opens.

Solo-developer AI-assisted review is supported in `ai_assisted_review/`. Those
reviews can discover and fix issues, but they remain simulated and cannot open
qualified approval gates by themselves.

## Package Variants

- Executive/expert audit package: high-level artifacts for product, trade, legal,
  privacy, security, operations, and launch reviewers.
- Technical source review package: source code, tests, scripts, Docker/Compose,
  environment example, migrations, docs, and generated review artifacts.

## Review Waves

- Wave 1 before hosted private beta: UX/Product Usability Review, Security/Public Upload Review, Privacy/Legal Review, AI Safety/Prompt Injection Review, DevOps/Production Readiness Review.
- Wave 2 before stronger trade/customs/freight/report claims: Trade-Boundary/Customs-Language Review, Freight/Logistics Review, Report-Language Review.
- Wave 3 before monetization or public scale: Billing/Payment Review.

## Required Finding Fields

Every external finding row must include:

- `finding_id`
- `reviewer_role`
- `severity`
- `affected_stage`
- `affected_file_or_artifact`
- `issue`
- `owner`
- `required_fix`
- `retest_command`
- `blocks_private_beta`
- `blocks_public_launch`

## Current Gate

- completed external reviews: `0`
- required external reviews: `9`
- hosted private beta ready: `false`
- public launch ready: `false`
- unsafe gates closed: `true`
- solo AI-assisted review supported: `true`

## Next Valid Move

Send Wave 1 reviewer packets, collect structured findings, fix P0/P1 rows, rerun proof, build v2 packages, then run five-user private-beta usability smoke only after real Wave 1 signoff exists.
