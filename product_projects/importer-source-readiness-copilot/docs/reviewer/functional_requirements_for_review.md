# Functional Requirements For External Review

Prepared on 2026-06-28 for Trade Readiness Copilot. This is a current-state review document for the locally implemented product, not a public-launch claim.

## 2-Minute Summary

Trade Readiness Copilot helps an exporter or trade operator prepare a Trade Readiness Packet before taking external action. The product accepts product, country, party, and evidence details; then it shows what is known, what is missing, what source routes should be checked, and what the next safe action is.

The current product is usable for local review and controlled preparation. It does not approve imports or exports, confirm tariff or CFIA status, verify suppliers, validate buyers, send messages, collect payments, or approve public launch.

## Users

- Public visitor: can start a quick check and receive a safe result.
- Exporter or customer operator: can create packets, add evidence, review missing inputs, and export safe reports.
- Internal operator: can review queues, source routes, evidence, and generated next steps.
- Expert reviewer: can review a scoped packet and return findings for that exact scope.
- Admin or support: can inspect audit, gates, health, and operational state.

## Core Functions Implemented Now

- Create or inspect a Trade Readiness Packet.
- Support a beginner flow with little or no documentation.
- Support a no-document quick check that creates a missing-evidence packet without showing upload-only actions.
- Support uploaded PDF triage with quarantine metadata, draft field extraction, user confirmation, delete-file action, and blocked-claim boundaries.
- Record product, origin, destination, buyer/importer, supplier, Incoterms, HS-code candidate, source, and evidence details.
- Maintain an evidence ledger and mark evidence as missing, reference-only, stale, or needing review.
- Route users to official-source references without treating those references as approval.
- Generate missing-evidence, starter checklist, buyer packet draft, broker/expert packet, safe summary, and business decision outputs.
- Show grouped unresolved items and the next safe move.
- Record local operation proof with `external_effects_created: false` and `claims_opened: false`.

## Main Workflows

- Quick check: user gives product and country details, optionally adds documents, then receives missing evidence and next safe action.
- Packet workspace: user reviews the packet, evidence, official-source routes, unresolved items, and report outputs.
- Document intelligence: product separates official samples, synthetic parser QA fixtures, no-document intake, and customer-uploaded evidence.
- Business decision preparation: product runs the decision tree, scores, source freshness check, buyer/supplier evidence ladder, and allowed/blocked action matrix.
- Expert routing: product prepares a scoped packet for a human reviewer; AI cannot approve the lane.
- Local operations: product can refresh source records, generate reports, create work orders, reserve billing internally, and record audit events without external effects.

## Document Intelligence Implemented

- Pipeline status: `production_document_intelligence_engine_ready_local_pipeline_security_gates_closed`.
- Expected document classes: `11`.
- Official sample PDFs downloaded: `3`.
- Synthetic parser QA PDFs generated: `11`.
- Parser output is draft evidence only and requires user confirmation before sharing.
- No document parser output opens customs, tariff, CFIA, buyer, supplier, shipment, payment, legal, or launch gates.

## Claim Gate Implemented

- Claim-gate status: `production_evidence_claim_gate_engine_ready_claims_fail_closed`.
- Packet statements evaluated: `17`.
- Safe preparation statements currently showable: `7`.
- Blocked packet statements: `10`.
- The product can show source-routing and preparation language with an evidence trail.
- It still blocks tariff confirmed, CFIA approved, buyer validated, supplier verified, customs ready, and shipment approved.

## Decision Scoring Implemented

- Scoring status: `production_decision_scoring_engine_ready_no_global_readiness_score`.
- Separate score records: `6`.
- Scores remain separate for market signal, evidence completeness, source freshness, buyer/supplier evidence, responsibility clarity, and decision safety.
- The product does not create one combined readiness score or approval label.
- Every score includes a reason, cap, blocker fields, claim-gate dependency, and next action.

## AI Copilot Implemented

- AI copilot status: `production_ai_copilot_engine_ready_no_gate_opening`.
- AI roles: `8`.
- AI can help draft, extract, summarize, prepare reviewer work orders, and flag wording risks.
- AI outputs are labeled as draft, source-backed, needs user confirmation, needs expert review, or blocked.
- Live model calls are disabled and AI cannot open product gates.

## Expert Review Network Implemented

- Expert review status: `production_expert_review_network_ready_scope_limited_no_external_claims`.
- Reviewer lanes: `10`.
- Draft scoped review requests: `10`.
- Finding templates: `10`.
- The product records what a reviewer may review, which credentials are required, what evidence must be attached, and which claims remain out of scope.
- No real reviewer signoff is recorded yet; review links are draft-only and no external claims are opened.

## Reports And Deliverables Implemented

- Reports status: `production_reports_engine_ready_cited_exports_blocked_claims_visible`.
- Report types: `12`.
- Report exports: `36`.
- Citation records: `132`.
- Each report is exported as JSON, HTML preview, and PDF.
- Every report keeps blocked claims visible, includes evidence/source citations, has a draft watermark, and remains not reviewed locally.

## Portal Workflows Implemented

- Portal workflow status: `production_portal_workflow_engine_ready_routes_gated_business_owner_ux`.
- Portal workflows: `6`.
- Default first-screen choices: `4`.
- All required local routes present: `True`.
- Public, exporter, importer, expert reviewer, operator/admin, and enterprise workflows are mapped to existing local UI/API routes.
- UX testing, accessibility signoff, mobile review, hosted proof, unrestricted uploads, live payments, and public launch approval remain external gates.

## Enterprise API Platform Implemented

- Enterprise API status: `production_enterprise_api_platform_ready_local_contracts_external_gates_closed`.
- API contracts: `17`.
- All required API routes present: `True`.
- Workspace controls: `3`.
- The product exposes local contracts for packets, evidence, documents, source refresh, scores, blocked claims, reviews, reports, AI safe summaries, audit, API keys, and webhooks.
- Live API secrets, webhook delivery, unrestricted uploads, hosted enterprise auth, enterprise terms, security approval, and public launch remain closed.

## Payment Monetization Implemented

- Payment status: `production_payment_monetization_engine_ready_live_checkout_closed`.
- Pricing tiers: `7`.
- Payment gates: `10`.
- Paid scope is preparation, evidence organization, reports, source monitoring, review workflow, workspace, and API usage.
- Forbidden paid scope includes customs approval, tariff confirmation, legal advice, CFIA approval, buyer validation, supplier verification, shipment approval, and public launch approval.
- Live checkout, external charges, webhook delivery, tax/accounting approval, refund/support approval, payment security approval, and claim-language approval remain closed.

## Enterprise And Advisor Use Cases

- Broker or trade advisor can manage multiple client packets and export missing-evidence or broker-review packets.
- Enterprise sourcing team can compare lanes while seeing which country/source paths are full, partial, reference-only, or generic.
- Compliance or legal reviewer can inspect blocked claims, source routes, evidence provenance, and the exact scope of requested review.
- Security or privacy reviewer can inspect upload, AI, deletion, audit, and retention controls before real-user data is accepted.
- Finance or billing reviewer can confirm that paid scope is preparation only and live checkout remains disabled until payment gates pass.

## Current Product Proof

- Business logic status: `business_logic_implemented_with_external_evidence_gates`.
- Operation status: `local_product_operations_executed`.
- Operation count in latest product run: `12`.
- Sample packet: `packet-frozen-tuna-canada-001`.
- Product proof commands currently pass: product tests, product check, root product check, completion integrity audit, and AI Dev OS check.

## Current Boundaries

- No customs, tariff, CFIA, legal, buyer, supplier, shipment, payment, or launch approval claim is opened.
- No automatic buyer/supplier outreach is sent.
- Live checkout is disabled.
- Hosted private beta and public launch remain blocked until real external review and platform proof exist.
- Official-source references are source routes only; they are not current-law proof or professional advice.

## Reviewer Decision Requested

Please review whether the implemented workflows are understandable, useful, and safe for a controlled private-beta candidate. A useful response can be short.

- Decision: approve for your reviewed scope, needs changes, or blocked.
- Top issues that must change before private beta.
- Any wording that sounds like approval, legal advice, customs advice, supplier verification, buyer validation, or launch readiness.
- Any workflow gap that would stop a real exporter or reviewer from using the product.
