# Business Core Logic Current State

Date: 2026-06-28

Current status: `business_logic_implemented_with_external_evidence_gates`

Operation status: `business_logic_operational_local_with_evidence_gates`

Phase completion status: `local_business_logic_implemented_external_gates_preserved`

## Product Position

The product is a trade decision preparation system. It helps a user understand what is known, what is missing, which official sources should be checked, which claims are blocked, and what the next safe move is.

It is not an import approval system, customs adviser, tariff confirmer, buyer validator, supplier verifier, shipment approver, or legal/compliance adviser.

Current first wedge: foreign exporters selling into Canada, especially food, agri, seafood, and general goods.

Current proof packet: `packet-frozen-tuna-canada-001`

Current example flow: Vietnam origin to Canada destination for a food import packet.

## Locked Business Answers

| Decision | Locked Current Answer |
| --- | --- |
| First commercial wedge | Foreign exporters preparing to sell into Canada |
| First category scope | Food, seafood, agri, plus general goods |
| First customer persona | Beginner-to-intermediate exporter |
| Secondary users | Canadian importers, internal reviewers, brokers, and experts |
| Product name | Trade Readiness Copilot for external/user-facing language |
| Internal engine name | Importer Source Readiness Copilot |
| First destination pack | Canada |
| Next explicit origin pack | India |
| Demo/proof origin | Vietnam |
| Generic country handling | Generic fallback remains research-only until source coverage is added |
| Buyer evidence language | Use evidence levels; do not say buyer validated |
| Supplier evidence language | Use evidence collected; do not say supplier verified |
| Source freshness promise | Checked before packet generation or paid review, not continuous legal freshness |
| Outreach policy | Questions only for initial controlled scope; no automatic sending |

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

The current logic supports five stages:

| Stage | Meaning | Required Before Moving Forward |
| --- | --- | --- |
| Starter | User may have little or no evidence yet | product, direction, origin or destination, intended use |
| Document | User has some evidence or source material | evidence item or offline flag, source or file reference, confirmation path |
| Decision | User is preparing a trade decision packet | importer of record, Incoterms or delivery responsibility, buyer/importer identity or broker-ready rationale, source freshness, category review status |
| Reviewer-ready | Packet has enough structure to route to a scoped reviewer | broker/expert packet, blocked-claims report, review scope, source snapshot or stale-source blocker |
| Beta-ready | Packet is usable in a controlled beta context | reviewer-ready fields, scoped reviewer findings, metadata-only beta controls, hosted/local review boundary |

The current example packet is at document stage because it has evidence, but importer of record and Incoterms are still missing.

## Implemented Logic Phases

| Phase | Current Implementation |
| --- | --- |
| 1. Business logic runtime | implemented as 12 packet questions, canonical packet stage, provenance, six scores, blocked claims, and allowed/blocked local actions |
| 2. No-document beginner flow | implemented as executable starter input checks, source routes, starter outputs, buyer packet draft, and questions-only outreach policy |
| 3. Market intelligence | implemented as bounded local signal scoring, importer/buyer discovery routes, and demand-claim blocks |
| 4. Country packs | implemented for destination, origin, strategic India, and generic fallback packs with required route checks |
| 5. Source monitoring | implemented as source registry rows, refresh cadence, stale-source impact rules, and packet evidence freshness evaluation |
| 6. Packet outputs | implemented as beginner, exporter, importer, operator, supplier, buyer/broker, expert, missing-evidence, and blocked-claim output sections |
| 7. Human review gates | implemented as reviewer lanes, scope templates, decision values, required evidence fields, and no-reviewer-no-claim rule |
| 8. Metadata-only beta | implemented as beta scope, outcome capture requirements, and real-user evidence gate |
| 9. Hosted beta infrastructure | implemented as hosted control checklist for auth, database, storage, logs, backups, AI routing, observability, and payment gates |
| 10. Controlled real-file beta | implemented as real-file beta scope, upload consent, AI-use consent, redaction, deletion, and audit requirements |
| 11. Buyer/supplier evidence | implemented as executable buyer and supplier evidence ladders that block validation and verification claims |
| 12. Payments | implemented as paid scope, forbidden paid scope, review prerequisites, and live-checkout-disabled gate |
| 13. Public launch | implemented as safe initial public scope, blocked public scope, approval prerequisites, and public-launch-ready false |

## Document Intelligence Business Logic

Document handling is now part of the business core, not a loose upload utility.
The product supports two valid public quick-check paths:

- no-document intake: creates a packet from product, country, party, and
  responsibility context; records a no-document evidence row; produces missing
  evidence, starter checklist, buyer packet, broker packet, safe summary, and
  blocked claims.
- uploaded-document intake: creates quarantine metadata, draft extracted
  fields, document-intelligence rows, user-confirmation actions, deletion
  actions, and report outputs.

The production document engine recognizes these expected document classes:

- commercial invoice
- packing list
- certificate of origin
- bill of lading
- airway bill
- product specification
- lab certificate
- phytosanitary or health certificate
- purchase order
- contract
- inspection report

Official sample documents and synthetic parser QA files are used only for parser
orientation and local QA. They are not customer proof, government approval, or
evidence that a shipment is ready.

Every extracted field must carry document ID, page or section, extracted value,
confidence, provenance, user-confirmation status, claim boundary, supported
claims, and blocked claims.

Parser output is always `parser_extracted_draft`. It can help the user review
documents faster, but it cannot open customs, tariff, CFIA, origin, buyer,
supplier, shipment, payment, legal, or launch gates.

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

The product now uses six separate scores, not one generic readiness score.

| Score | Current Meaning | Current Boundary |
| --- | --- | --- |
| Market signal score, `market_signal_score` | whether there is enough market data to treat the opportunity as worth deeper validation | capped until official trade data, market-access comparison, and buyer evidence are attached |
| Evidence completeness score, `evidence_completeness_score` | whether the packet has enough supporting evidence for the current stage | capped when core fields or evidence are missing |
| Source freshness score, `source_freshness_score` | whether official/reference sources are fresh enough for the packet | blocked when critical source refresh or change review is pending |
| Buyer/supplier evidence score, `buyer_supplier_evidence_score` | whether buyer and supplier evidence levels are present enough for internal review | capped because evidence levels do not equal buyer validation or supplier verification |
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

The source monitor also carries:

- freshness status
- diff classifier
- packet impact logic
- source changed flow
- stale-source blocker behavior

If a critical source changes, affected packet outputs become stale until refreshed evidence and reviewer review are attached.

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

## Portal Workflow Business Logic

The production portal workflow engine now maps the business logic to six
user-facing workflow contracts:

- public portal for business owners exploring a trade lane
- exporter portal for foreign exporters preparing a Canada-facing packet
- importer portal for Canadian importers checking source, supplier, and
  responsibility questions
- expert reviewer portal for scoped external reviewers
- operator and admin portal for internal queue, source, audit, and health work
- enterprise portal for brokers, advisors, and teams managing multiple packets

The default first screen is intentionally plain:

1. Explore a market
2. Prepare a buyer packet
3. Check my documents
4. Prepare for broker/expert review

The engine verifies that each workflow maps to existing local UI/API routes in
`system_review_graph/product_runtime_state.json`. It also blocks unsafe button
labels such as approve, ready to ship, confirm tariff, validate buyer, and
verify supplier.

Portal workflow proof is stored in:

- `system_review_graph/production_portal_workflow_manifest.json`
- `system_review_graph/production_portal_route_matrix.json`
- `system_review_graph/production_portal_ux_checks.json`
- `system_review_graph/production_portal_gate_controls.json`

Portal workflow completion is local route and gate coverage only. It does not
record real UX testing, accessibility signoff, mobile review, hosted proof,
unrestricted uploads, live payment activation, or public launch approval.

## Enterprise API Business Logic

The production enterprise API platform now turns the same packet, evidence,
claim-gate, report, audit, workspace, and RBAC rules into 17 local enterprise
API contracts.

The API contracts cover:

- packet creation and packet read
- evidence attachment
- document upload contract with real-file gates closed
- official-source refresh
- separate packet scores
- blocked claims
- scoped review request drafting
- report generation/listing
- AI safe summary with no live model call
- team workspace, billing usage, and audit export
- API-key and webhook contracts with live delivery closed

Every enterprise API contract requires authentication, tenant filtering,
object-level authorization, claim-gate reuse, and rate-limit proof before
hosting. API outputs cannot bypass blocked claims, hide report uncertainty,
issue live API secrets, send webhooks, approve white-label claims, accept
unrestricted files, or open external effects.

Enterprise proof is stored in:

- `system_review_graph/production_enterprise_api_manifest.json`
- `system_review_graph/production_enterprise_api_contracts.json`
- `system_review_graph/production_enterprise_rbac_policy.json`
- `system_review_graph/production_enterprise_workspace_controls.json`
- `system_review_graph/production_enterprise_webhook_policy.json`
- `system_review_graph/production_enterprise_audit_export_policy.json`
- `system_review_graph/production_enterprise_research_references.json`

This is a local enterprise/API contract. It does not record hosted enterprise
auth, live API-key issuance, webhook delivery, enterprise customer terms,
security approval, or public launch approval.

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

Each real review lane must return:

- reviewer name
- review date
- scope reviewed
- finding
- required changes
- decision: approved_for_scope, needs_changes, or blocked
- evidence attachment

Without those records, the lane stays blocked.

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

## Phase Completion Matrix

| Phase | Name | Current Status | What Is Complete Now | What Still Needs Real Evidence |
| ---: | --- | --- | --- | --- |
| 0 | Business identity lock | local complete, claims blocked | wedge, persona, promise, name, forbidden claims | none for local scope |
| 1 | Business logic runtime | local executable, claims blocked | 12 questions, five stages, provenance, six scores, cap reasons, gate decision | real reviewer verification before stronger claims |
| 2 | No-document beginner flow | local executable, claims blocked | starter input checks, source routes, questions, missing evidence, no-send policy | real user feedback |
| 3 | Market intelligence | local signal scoring complete, datasets required | signal components, confidence levels, source/date/limitation rules | official dataset rows, buyer/operator validation |
| 4 | Country packs | local executable route checks, reference boundaries | Canada, India, Vietnam, Generic pack logic and required source route checks | current source refresh and qualified country review |
| 5 | Source monitoring | local executable freshness evaluation, no live freshness claim | freshness status, diff classifier, packet impact logic, attached evidence freshness state | permitted refresh evidence and reviewer review |
| 6 | Packet outputs | local complete, claims blocked | Trade Readiness Packet views and supporting reports | user value validation |
| 7 | Human review gates | local review-lane contract ready, external evidence required | reviewer lanes, decision templates, and required evidence fields | real reviewer records |
| 8 | Metadata-only beta | metadata-only beta contract ready, real users required | beta scope and outcome capture requirements | 5-10 real user outcomes |
| 9 | Hosted beta infrastructure | hosted control contract ready, hosted proof required | auth, DB, storage, logs, backups, AI routing, observability, and payment-gate checklist | hosted platform proof |
| 10 | Controlled real-file beta | local document-intelligence pipeline ready, hosted review required | consent, redaction, deletion, audit, AI-use requirements, sample library, parser QA fixtures, and draft extraction provenance | supervised real-file beta results plus upload security/privacy proof |
| 11 | Buyer/supplier evidence | local executable ladders, real evidence required | buyer/supplier evidence levels and language boundaries | dated buyer and supplier evidence for stronger claims |
| 12 | Payments | local contract complete, live checkout disabled | paid scope and required reviews | pricing, tax, support, webhook, payment review |
| 13 | Public launch | launch contract ready, public launch blocked | safe initial launch scope and blocked launch scope | named launch owner approval and all external gates |

## Implementation Evidence

| Evidence | Current Proof |
| --- | --- |
| Business engine | `src/importer_source_readiness/business_logic.py` |
| Completion platform wiring | `src/importer_source_readiness/completion_platform.py` |
| Local operation wiring | `src/importer_source_readiness/product_operations.py` |
| Business phase report | `system_review_graph/business_logic_phase_report.json` |
| Business decision report | `system_review_graph/generated_reports/business_decision_packet-frozen-tuna-canada-001.json` |
| Production document intelligence | `system_review_graph/production_document_intelligence_manifest.json` |
| Production document pipeline | `system_review_graph/production_document_pipeline.json` |
| Extracted-field proof | `system_review_graph/production_document_extracted_fields.json` |
| Production evidence claim gate | `system_review_graph/production_evidence_claim_gate_manifest.json` |
| Claim decision proof | `system_review_graph/production_claim_gate_decisions.json` |
| Evidence/claim mapper proof | `system_review_graph/production_evidence_claim_mappers.json` |
| Production decision scoring | `system_review_graph/production_decision_scoring_manifest.json` |
| Decision score records | `system_review_graph/production_decision_score_records.json` |
| Score cap policy | `system_review_graph/production_score_cap_policy.json` |
| Production AI copilot | `system_review_graph/production_ai_copilot_manifest.json` |
| AI output contracts | `system_review_graph/production_ai_output_contracts.json` |
| AI safety checks | `system_review_graph/production_ai_safety_checks.json` |
| Production expert review network | `system_review_graph/production_expert_review_network_manifest.json` |
| Reviewer profile requirements | `system_review_graph/production_reviewer_profiles.json` |
| Scoped review requests | `system_review_graph/production_review_requests.json` |
| Review finding contracts | `system_review_graph/production_review_finding_contracts.json` |
| Production reports engine | `system_review_graph/production_reports_engine_manifest.json` |
| Production report exports | `system_review_graph/production_report_exports.json` |
| Production report citations | `system_review_graph/production_report_citations.json` |
| Tests | `tests/test_business_logic.py`, `tests/test_completion_platform.py` |
| Product proof | `python3 scripts/check_product.py` |
| Root proof | `python3 scripts/product_project_check.py` |
| Delivery policy proof | root delivery policy audit command |

## What Is Implemented Now

- 13 business phase surfaces, plus phase 0 business identity lock
- 12-question decision tree
- canonical Trade Readiness Packet contract
- field-level provenance
- executable starter flow
- no-document quick-check packet path
- production document-intelligence pipeline for expected trade document classes
- production evidence claim-gate engine for `can_show_claim` decisions
- explicit separation between safe preparation/source-routing statements and blocked external claims
- production decision scoring engine with six separate capped scores and no single readiness score
- production AI copilot engine with label-bound outputs and no gate-opening authority
- production expert review network with credential-required reviewer lanes, scoped requests, finding templates, and no completed signoff recorded
- production reports engine with cited JSON/HTML/PDF packet views and blocked claims preserved
- official sample document library and synthetic parser QA fixtures for local parser validation
- Canada/Vietnam/India/Generic country-pack rows with route checks
- source-monitor contract with source metadata and executable evidence freshness evaluation
- buyer/supplier evidence ladders
- six separate business scores
- business_gate_decision allowed/blocked action matrix
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

## No Open Local Business-Logic Questions

The local business logic is locked for the current implementation scope:

- wedge: foreign exporters preparing to sell into Canada
- first categories: food, seafood, agri, and general goods
- first persona: beginner-to-intermediate exporter
- country path: Canada destination, Vietnam demo origin, India strategic next origin, Generic fallback
- buyer evidence: ladder only; no buyer-validated claim
- supplier evidence: ladder only; no supplier-verified claim
- source freshness: checked before packet generation or paid review; no continuous legal freshness claim
- outreach: questions only; no automatic sending

Remaining incomplete work is external evidence, not an unanswered local business-logic decision.
