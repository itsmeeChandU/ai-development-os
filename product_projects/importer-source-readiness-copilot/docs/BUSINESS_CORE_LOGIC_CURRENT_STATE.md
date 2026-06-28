# Business Core Logic Current State

Date: 2026-06-28

Current status: `business_logic_phases_ready_with_evidence_gates`

Operation status: `business_logic_operational_local_with_evidence_gates`

## Product Position

The product is a trade decision preparation system. It helps a user understand what is known, what is missing, which official sources should be checked, which claims are blocked, and what the next safe move is.

It is not an import approval system, customs adviser, tariff confirmer, buyer validator, supplier verifier, shipment approver, or legal/compliance adviser.

Current first wedge: foreign exporters selling into Canada, especially food, agri, seafood, and general goods.

Current proof packet: `packet-frozen-tuna-canada-001`

Current example flow: Vietnam origin to Canada destination for a food import packet.

## Core Business Object

The core business object is the Trade Readiness Packet.

The packet carries:

- product identity and category
- trade direction
- origin country
- destination country
- intended use
- HS code candidate when available
- exporter, importer, buyer, supplier, and manufacturer details when known
- importer of record and Incoterms or delivery responsibility when known
- documents and evidence rows
- official source references
- responsibility path
- blocked claims
- next valid move
- field-level provenance

Each important field is marked as one of:

- `user_input`
- `parser_extracted_draft`
- `official_source_reference`
- `system_derived`
- `reviewer_verified`

This matters because field presence alone is not proof. A packet can know a product name or source URL while still blocking stronger claims.

## Packet Stages

The current logic supports three stages:

| Stage | Meaning | Required Before Moving Forward |
| --- | --- | --- |
| Starter | User may have little or no evidence yet | product, direction, origin or destination, intended use |
| Document | User has some evidence or source material | evidence item or offline flag, source or file reference, confirmation path |
| Decision | User is preparing a trade decision packet | importer of record, Incoterms or delivery responsibility, buyer/importer identity or broker-ready rationale, source freshness, category review status |

The current example packet is at document stage because it has evidence, but importer of record and Incoterms are still missing.

## Implemented Logic Phases

| Phase | Current Implementation |
| --- | --- |
| Decision tree before more features | implemented as 12 packet questions with answered, research, review, and blocked states |
| Market intelligence module | implemented as a research plan, not a demand claim |
| Country-pack architecture | implemented for destination, origin, and generic fallback packs |
| Source monitoring contract | implemented as source registry rows with cadence, terms/robots checks, hash/diff strategy, and stale-source routing |
| Commercial packet outputs | implemented as beginner, exporter, importer, operator, supplier, buyer/broker, and expert-facing packet sections |

## Decision Tree

The current decision tree asks 12 questions:

1. Are you importing, exporting, or exploring?
2. What product or category is involved?
3. What is the origin country?
4. What is the destination country?
5. Do you know the HS code?
6. Do you have a buyer or importer?
7. Who is importer of record?
8. What Incoterms or delivery responsibility applies?
9. Do you have documents?
10. Is the product likely regulated?
11. What official sources must be checked?
12. What is the next safe move?

The current packet blocks or routes to review on HS code, buyer/importer, importer of record, Incoterms, regulated product review, and official source review.

## Business Scores

The product now uses five separate scores, not one generic readiness score.

| Score | Current Meaning | Current Boundary |
| --- | --- | --- |
| Market signal score, `market_signal_score` | whether there is enough market data to treat the opportunity as worth deeper validation | capped until official trade data, market-access comparison, and buyer evidence are attached |
| Evidence completeness score, `evidence_completeness_score` | whether the packet has enough supporting evidence for the current stage | capped when core fields or evidence are missing |
| Source freshness score, `source_freshness_score` | whether official/reference sources are fresh enough for the packet | blocked when critical source refresh or change review is pending |
| Responsibility clarity score, `responsibility_clarity_score` | whether importer of record, Incoterms, and role split are clear | capped while importer of record or Incoterms are unknown |
| Decision safety score, `decision_safety_score` | whether it is safe to move beyond internal review | capped while blocker rows or external claim gates remain open |

Allowed score labels are internal and conservative:

- red: blocked
- yellow: research or qualified review needed
- grey: unknown or no data
- green: internally usable only for a fully supported local scope

Forbidden labels remain blocked:

- approved
- compliant
- ready to ship
- tariff confirmed
- buyer validated
- supplier verified

## Country Packs

The current packet has three country packs:

| Pack | Role | Current Status |
| --- | --- | --- |
| Canada | destination import pack | reference-only source routes available |
| Vietnam | origin export pack | country pack required for deeper source coverage |
| Generic | fallback pack | used when country-specific source coverage is not enough |

The Canada pack routes to sources for commercial import process, tariff orientation, regulated product checks, import controls, sanctions/restricted-party screening, trade data, importer discovery, and broker discovery.

The India source registry entries are present for future India-origin flows, but the current example packet is Vietnam to Canada.

## Source Monitoring

The source monitoring contract now records the fields expected for each important source:

- source ID
- jurisdiction
- source type
- canonical URL
- fetch mode
- refresh cadence
- robots status
- terms status
- auth requirement
- parser type
- content hash
- diff strategy
- claim boundary
- packet tags

Current behavior is conservative. Sources are registered and routed. They do not prove current law, tariff treatment, permit status, or compliance until refresh and review evidence exists.

## Packet Outputs

The business logic prepares these output groups:

- beginner starter output
- exporter output
- importer output
- operator/expert output
- supplier document request
- buyer/importer questions
- broker/expert questions
- missing evidence list
- blocked claims list
- next valid move

These outputs are for review preparation only. They do not send messages, create external effects, approve a packet, or open claim gates.

## Reviewer Signoff Rule

Final rule: `no reviewer lane, no claim lane`

Current reviewer lanes:

- UX/Product
- Security/Public Upload
- Privacy/Legal
- AI Safety/Prompt Injection
- DevOps/Production
- Trade-Boundary/Customs Language
- Freight/Logistics
- Report Language
- Billing/Payment

AI can prepare review packets. AI cannot approve a reviewer lane.

## Hosted Beta And Payment Boundary

Hosted private beta remains blocked until real platform proof exists.

Minimum hosted beta controls include:

- real authentication
- secure sessions
- safe upload handling
- data governance
- AI routing controls
- audit logs
- backup and restore proof
- observability

Payments remain downstream. Live checkout stays disabled until scope, support, refund, tax, webhook, and claim-boundary reviews pass.

## Implementation Evidence

| Evidence | Current Proof |
| --- | --- |
| Business engine | `src/importer_source_readiness/business_logic.py` |
| Completion platform wiring | `src/importer_source_readiness/completion_platform.py` |
| Local operation wiring | `src/importer_source_readiness/product_operations.py` |
| Business phase report | `system_review_graph/business_logic_phase_report.json` |
| Business decision report | `system_review_graph/generated_reports/business_decision_packet-frozen-tuna-canada-001.json` |
| Tests | `tests/test_business_logic.py`, `tests/test_completion_platform.py` |
| Product proof | `python3 scripts/check_product.py` |
| Root proof | `python3 scripts/product_project_check.py` |
| Delivery policy proof | root delivery policy audit command |

## What Is Implemented Now

- five business phases
- 12-question decision tree
- canonical Trade Readiness Packet contract
- field-level provenance
- Canada/Vietnam/Generic country-pack rows
- source-monitor contract with source metadata and stale-source behavior
- five separate business scores
- beginner, exporter, importer, operator, supplier, buyer/broker, and expert-facing output sections
- reviewer lane framework
- hosted beta control boundary
- live payment disabled boundary
- agent tool for business phase report
- agent tool for business decision report
- generated business decision packet

## Still Blocked

The following are not complete and must stay blocked until real evidence comes back:

- public launch approval
- hosted staging or production proof
- live payment activation
- legal/privacy/security approval
- qualified customs/trade review
- buyer validation
- supplier verification
- real user or private beta outcomes
- public go/no-go approval
- product-specific tariff or CFIA confirmation
- current official-source freshness proof for stronger claims

## Questions To Close Before We Lock This Logic

1. Should the first commercial wedge remain "foreign exporters selling into Canada", or should we narrow it further to one category such as food, seafood, or agri?
2. For Canada-first flows, should India be the next origin country to make fully explicit, or should Vietnam remain the example because the current packet uses Vietnam?
3. Which customer should the first version speak to first: beginner exporter, experienced exporter, Canadian importer, broker/operator, or internal reviewer?
4. What evidence should count as real buyer validation for this product: email reply, signed LOI, paid order, call note, or something else?
5. What evidence should count as supplier verification: business registration, export license, product certificate, third-party inspection, prior shipment, or something else?
6. What source freshness cadence should we promise in the product language: per packet, weekly, monthly, or only before paid review?
7. Should the product generate outreach drafts for buyers/suppliers, or should it only generate questions until external messaging is approved?
8. Should the product name used with reviewers be `Trade Readiness Copilot`, `Importer Source Readiness Copilot`, or a new simpler buyer-facing name?
