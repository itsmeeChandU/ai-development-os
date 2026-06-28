# Functional Requirements Current State

Date: 2026-06-28

Current product status: `ready_with_external_gates`

Current runtime status: `private_beta_candidate_with_external_human_gates`

## Purpose

This document describes what the product can do now. It is written as a current-state functional requirement document, not as a future roadmap.

The product helps users prepare trade readiness packets, organize evidence, review official-source routes, see blockers, generate safe reports, and route work to human review.

## Users And Roles

| Role | Current Capabilities |
| --- | --- |
| Public visitor | can start a no-login quick check, select import/export context, upload or describe documents, and see a safe result page |
| Customer/operator | can create packets, review evidence, see blockers, refresh source records, view readiness, and generate safe reports |
| Expert reviewer | can use scoped review links and record findings for an exact packet scope |
| Admin/support | can review source registry, gates, audit events, health state, and operational queues |
| Agent/local operator | can run safe local tools that create internal reports without external effects |

## Core Functional Requirements

| ID | Requirement | Current State | Evidence |
| --- | --- | --- | --- |
| FR-01 | Capture trade packet information | Implemented locally | `customer_source_packets.json`, packet routes |
| FR-02 | Support beginner/no-document flow | Implemented locally | starter checklist output |
| FR-03 | Support no-file quick checks, document upload, and PDF triage | Implemented locally with confirmation gates | `document_processing.py`, public upload policy, `production_document_intelligence_manifest.json` |
| FR-04 | Maintain evidence ledger | Implemented locally | `evidence_ledger.json` |
| FR-05 | Maintain official source registry | Implemented locally as reference routes | `official_source_registry.json` |
| FR-06 | Refresh source records safely | Implemented locally with freshness boundaries | `source_refresh_runs.json` |
| FR-07 | Create blocker rows and grouped blockers | Implemented fail closed | `blockers.jsonl`, `customer_readiness_report.json` |
| FR-08 | Generate customer-safe readiness report | Implemented locally | report exports and generated reports |
| FR-09 | Generate business decision report | Implemented locally | `business_decision_packet-frozen-tuna-canada-001.json` |
| FR-10 | Run business core logic phases | Implemented locally | `business_logic_phase_report.json` |
| FR-11 | Provide country coverage routing | Implemented locally with claim gates | `country_coverage_report.json` |
| FR-12 | Provide opportunity signal prompts | Implemented as signal-only research prompts | `opportunity_scanner_report.json` |
| FR-13 | Provide transport readiness questions | Implemented with forwarder/reviewer gates | `transport_readiness_report.json` |
| FR-14 | Provide expert review work orders | Implemented locally | `expert_review_work_orders.json` |
| FR-15 | Provide scoped expert review links | Implemented locally | `review_requests.json` |
| FR-16 | Record AI-assisted review findings safely | Implemented fail closed | `customer_ai_review_runs.json` |
| FR-17 | Provide AI data policy and redaction controls | Implemented locally | `ai_data_policy.json`, `redaction_pipeline.json` |
| FR-18 | Provide no-AI/manual path | Implemented locally | `manual_no_ai_workflow.json` |
| FR-19 | Provide audit events and deletion request records | Implemented locally | `audit_events.json`, `deletion_requests.json` |
| FR-20 | Provide local app routes for customer, operator, expert, admin, and public pages | Implemented locally | `product_runtime_state.json` |
| FR-21 | Provide agent/API tool manifest | Implemented locally | `agent_api_manifest.json` |
| FR-22 | Execute safe local agent tools | Implemented locally with no external effects | `product_operations_report.json` |
| FR-23 | Keep live checkout disabled | Implemented as blocked billing controls | `billing_credit_controls.json` |
| FR-24 | Keep launch controls and go-live blockers visible | Implemented locally | `launch_operations_report.json`, `final_go_live_decision_report.json` |
| FR-25 | Maintain production document intelligence pipeline | Implemented locally with official sample documents and parser QA fixtures | `production_document_pipeline.json`, `production_document_extracted_fields.json` |
| FR-26 | Keep uploaded-document actions separate from no-document packets | Implemented locally | no-document quick-check regression test and public result route |
| FR-27 | Decide which packet statements can be shown | Implemented locally with evidence trails and closed external claims | `production_evidence_claim_gate_manifest.json`, `production_claim_gate_decisions.json` |
| FR-28 | Explain packet decisions with separate capped scores | Implemented locally without a single readiness score | `production_decision_scoring_manifest.json`, `production_decision_score_records.json` |
| FR-29 | Provide AI assistance without authority | Implemented locally with role/output contracts and safety checks | `production_ai_copilot_manifest.json`, `production_ai_output_contracts.json` |
| FR-30 | Route scoped expert reviews without recorded approval | Implemented locally with reviewer lanes, credential requirements, draft requests, finding templates, and gate impacts | `production_expert_review_network_manifest.json`, `production_review_requests.json` |
| FR-31 | Export cited packet reports | Implemented locally with 12 report types, JSON/HTML/PDF exports, source/evidence citations, and blocked-claim sections | `production_reports_engine_manifest.json`, `production_report_exports.json` |
| FR-32 | Provide route-covered portal workflows for public, exporter, importer, reviewer, operator/admin, and enterprise users | Implemented locally with route coverage, UX review hooks, and closed external gates | `production_portal_workflow_manifest.json`, `production_portal_route_matrix.json` |
| FR-33 | Provide enterprise SaaS/API contracts for broker, advisor, and team workflows | Implemented locally with API contracts, RBAC policy, workspace controls, API-key fingerprints, webhook contracts, audit export, usage limits, and white-label report rules | `production_enterprise_api_manifest.json`, `production_enterprise_api_contracts.json` |
| FR-34 | Provide payment monetization contract without live checkout | Implemented locally with pricing tiers, paid-scope boundaries, checkout controls, webhook controls, and payment gates | `production_payment_monetization_manifest.json`, `production_checkout_gate_controls.json` |
| FR-35 | Provide production trust control plane without accepting real files | Implemented locally with trust controls, vendor register, incident runbooks, local backup/restore hash drill, and closed hosted/real-file gates | `production_security_privacy_reliability_manifest.json`, `production_trust_control_matrix.json` |
| FR-36 | Provide exact-scope launch control plane without activation | Implemented locally with 13 launch gates, candidate public scope, blocked public scope, and public launch approval false | `production_launch_control_plane_manifest.json`, `production_launch_scope_matrix.json` |
| FR-37 | Provide beginner trade discovery before packet creation | Implemented locally with Canada import/export browsing, category families, diverse country lanes, source routes, and no-document flows; recommendations and opportunity claims remain blocked | `production_trade_discovery_manifest.json`, `production_trade_discovery_category_map.json`, `production_trade_discovery_country_lanes.json` |

## Current Main Workflows

## Locked Functional Answers

| Question | Current Answer |
| --- | --- |
| Default first screen | What are you trying to do? |
| First-screen choices | Explore a market, Prepare buyer packet, Check my documents, Prepare for broker/expert review |
| Primary deliverable | Trade Readiness Packet |
| Other packet views | Starter checklist, buyer-ready packet, broker-review packet, business decision report |
| Buyer/supplier outreach | Questions and preparation checklist only in private beta |
| First-class countries | Canada destination, India origin, Vietnam demo/sample, Generic fallback |
| Private beta upload scope | Metadata-only packets plus optional redacted/sample documents until upload review passes |
| Business scores | Six separate scores, including `buyer_supplier_evidence_score`; no single global readiness score |
| Business questions | Resolved for local scope; remaining work is external evidence, hosted proof, reviewer approval, and real user validation |

### Public Quick Check

1. User starts a quick check.
2. User selects import/export context.
3. User provides product and country details.
4. User may upload a PDF or continue without documents.
5. Product creates a draft packet and safe summary.
6. Product returns missing evidence, source routes, blockers, and next valid move.
7. Strong claims stay blocked.

If the user continues without documents, the packet records a no-document
intake evidence row and shows missing-evidence, starter, buyer, and broker
outputs. It does not show extracted-field confirmation or delete-uploaded-files
actions because no upload exists.

If the user uploads PDFs, the packet creates quarantine metadata, draft extracted
fields, document-intelligence rows, user-confirmation actions, and delete-file
actions. Parser output remains draft evidence until the user confirms and a
qualified reviewer checks the relevant scope.

### Customer Packet Workspace

1. Customer creates or opens a packet.
2. Customer reviews evidence and source records.
3. Product groups blockers.
4. Product generates readiness and missing-evidence reports.
5. Product can generate a broker/expert packet.
6. Product routes unresolved items to reviewer or operator queues.

### Business Decision Preparation

1. Product builds a canonical Trade Readiness Packet.
2. Product runs the 12-question decision tree.
3. Product generates market research requirements.
4. Product builds destination, origin, and generic country packs.
5. Product builds source-monitor rows.
6. Product calculates six separate business scores.
7. Product generates a business decision report.
8. Product keeps approval, tariff, buyer, supplier, shipment, and launch claims blocked.

### Beginner Trade Discovery

1. User can browse Canada import and export directions before knowing an HS code.
2. Product shows source-routed product families such as food/agri/seafood,
   textiles, machinery, electronics, cosmetics, chemicals, building materials,
   and general consumer goods.
3. Product shows diverse origin-to-Canada lanes and Canada export lanes as
   reference-only research paths.
4. Product shows regulated-product warnings and source routes for CFIA, CBSA,
   sanctions, trade data, market access, and importer-lead research.
5. Product can turn a selected category and lane into a starter packet with
   missing evidence and next safe moves.
6. Product does not recommend products, prove demand, prove profit, validate
   buyers, verify suppliers, approve customs/CFIA status, or prove shipment
   readiness.

### Production Document Intelligence

1. Product recognizes expected trade document classes: commercial invoice,
   packing list, certificate of origin, bill of lading, airway bill, product
   specification, lab certificate, phytosanitary/health certificate, purchase
   order, contract, and inspection report.
2. Product separates official sample documents from synthetic parser QA
   fixtures and from customer-uploaded evidence.
3. Product records file-signature checks, generated filenames, quarantine
   status, extraction confidence, user-confirmation status, and claim boundary.
4. Product maps every extracted field to document ID, page or section,
   provenance, confidence, user-confirmation status, supported claims, and
   blocked claims.
5. Product blocks authenticity, tariff, CFIA, customs, buyer, supplier,
   shipment, and launch claims from parser output.

### Enterprise / Advisor Use Cases

1. Broker or trade advisor can manage multiple client packets and export
   missing-evidence or broker-review packets.
2. Enterprise sourcing team can compare lanes while seeing which country/source
   paths are full, partial, reference-only, or generic.
3. Compliance or legal reviewer can inspect blocked claims, source routes,
   evidence provenance, and the exact scope of requested review.
4. Security or privacy reviewer can inspect upload, AI, deletion, audit, and
   retention controls before real-user data is accepted.
5. Finance or billing reviewer can confirm that paid scope is preparation only
   and live checkout remains disabled until payment gates pass.

### Production Portal Workflows

1. Public portal: business owner can start safe exploration, quick check, sample
   report review, and security/AI boundary review.
2. Exporter portal: foreign exporter can create a packet, attach evidence,
   download cited reports, and prepare buyer or broker questions.
3. Importer portal: Canadian importer can review missing import evidence,
   refresh source routes, and prepare a broker review packet.
4. Expert reviewer portal: scoped reviewer can inspect assigned evidence,
   answer scoped questions, and submit a finding for the exact scope.
5. Operator/admin portal: internal user can inspect blockers, refresh
   artifacts, route reviews, and check audit/health state.
6. Enterprise portal: broker, advisor, or team can manage workspaces, inspect
   usage, use scoped local API contracts, and export audit-ready reports.

Every portal workflow maps to existing local UI/API routes. The workflow engine
keeps approval, ready-to-ship, tariff-confirmed, buyer-validated,
supplier-verified, public-launch, unrestricted-upload, and live-payment actions
blocked.

### Enterprise API Platform

1. Broker, advisor, or enterprise user can review a local API contract for
   packets, evidence, documents, sources, scores, blocked claims, reviews,
   reports, AI safe summaries, team workspace, billing usage, audit, API keys,
   and webhooks.
2. Product maps every API contract to an existing local route.
3. Product requires authentication, tenant filtering, object-level
   authorization, claim-gate reuse, and rate-limit proof before hosted use.
4. Product records API-key fingerprints only; it does not issue live secrets.
5. Product records webhook event contracts only; it does not deliver webhooks.
6. Product keeps white-label reports from removing blocked claims, citations,
   draft watermark, or claim-gate language.
7. Hosted enterprise auth, live keys, webhook delivery, unrestricted uploads,
   enterprise terms, security review, and public launch remain blocked.

### Payment Monetization

1. Product defines seven pricing tiers: free quick check, starter packet, pro
   packet workspace, expert review add-on, broker/advisor workspace,
   enterprise, and API/data access.
2. Product can charge only for preparation, evidence organization, source
   monitoring, reports, review workflow, workspace, and API usage.
3. Product cannot charge for customs approval, tariff confirmation, legal
   advice, CFIA approval, buyer validation, supplier verification, shipment
   approval, or public launch approval.
4. Checkout controls keep live mode, checkout URLs, external charges,
   refund/support approval, and tax/accounting approval closed.
5. Webhook controls require signature verification, idempotency, duplicate
   event handling, delayed event handling, and out-of-order event handling.
6. Live checkout remains disabled until pricing, refund/support, tax/accounting,
   webhook, payment security, and claim-language reviews pass.

### Production Trust Controls

1. Product maps 15 production trust controls: managed auth, admin MFA, RBAC,
   secure sessions/CSRF, rate limits, private storage, malware scanning, audit,
   deletion, retention, vendor register, backup/restore, monitoring, incident
   runbooks, secrets, and data residency.
2. Product stores vendor review records for hosting/storage, OpenAI API,
   Stripe, malware/CDR, monitoring, and support/email candidates.
3. Product performs a local backup/restore hash drill over critical repo
   artifacts and stores the result.
4. Product keeps every production trust gate blocked until hosted proof and
   qualified privacy/security review exist.
5. Product does not allow unrestricted real files, hosted private beta, or
   public launch from local trust artifacts alone.

### Launch Control Plane

1. Product defines 13 launch gates: business logic, country pack, source
   freshness, market data, security, privacy, AI safety, trade language, expert
   review, payment, real-user evidence, production infrastructure, and final
   owner approval.
2. Product defines the candidate public scope as landing page, public quick
   check, no-document starter packet, source routing, sample reports, and
   waitlist/demo booking.
3. Product keeps unrestricted real uploads, live payments, automated outreach,
   approval language, buyer validated, supplier verified, shipment approval,
   and public legal/compliance advice out of scope.
4. Product keeps activation, exact public-scope approval, and public launch
   approval false until real evidence and owner approval exist.

### Expert Review

1. Product creates a scoped review request.
2. Reviewer sees only the packet scope.
3. Reviewer records findings for that scope.
4. Findings update blocker and next-move surfaces.
5. Review does not open unrelated claims.

### Local Operations

1. Local operator runs product operation flow.
2. Product records intake, research/source refresh, reports, expert work orders, billing reservation, team activity, launch event, and agent tool execution.
3. Product writes `product_operations_report.json`.
4. Product confirms `external_effects_created: false` and `claims_opened: false`.

## Current Routes And APIs

The runtime contract currently includes:

- 50 customer UI routes
- 56 API routes
- scoped expert review route
- admin/source/gate/audit/health routes
- public start, tool, result, confirmation, and report routes
- agent tool routes for country coverage, business logic report, business decision report, packet status, starter checklist, missing evidence, safe summary, broker packet, and billing quote

The route source of truth is `system_review_graph/product_runtime_state.json`.

## Functional Acceptance Criteria

The functional state is acceptable only when these commands pass:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_product.py
python3 scripts/product_project_check.py
python3 scripts/ai_dev_os_check.py
python3 scripts/self_test_flow.py
```

The product must also keep:

- public launch ready: false
- hosted private beta ready: false until real hosting/security/privacy proof exists
- live payment ready: false
- external effects created: false in local operation proofs
- claims opened: false in local operation proofs

## Functional Boundaries

The product does not currently:

- approve imports or exports
- confirm tariffs
- confirm CFIA or regulated-product compliance
- provide legal advice
- verify suppliers
- validate buyers
- send external emails or messages
- submit government forms
- collect payment
- book freight
- ship goods
- claim production hosting proof
- claim public launch approval

## Local Functional Questions

There are no open local business-logic questions for the current controlled scope. The remaining questions require external evidence or approval: hosted staging proof, qualified customs/trade review, privacy/legal/security review, buyer/supplier evidence, real-user outcomes, payment approval, and named public go/no-go approval.
