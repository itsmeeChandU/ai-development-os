# Business Logic Document For External Review

Prepared on 2026-06-28 for Trade Readiness Copilot. This document explains how the product makes local preparation decisions while keeping real-world claims closed.

## 2-Minute Summary

The product's business logic is now implemented for the local repo-controlled scope. It can prepare a packet, compute safe statuses, score the packet, show evidence gaps, and decide which local actions are allowed.

The logic deliberately does not approve trade action. It blocks stronger claims until real source freshness, buyer/supplier evidence, qualified review, security/privacy review, payment review, and public go/no-go approval exist.

## Business Position

- Product name: Trade Readiness Copilot.
- First wedge: foreign exporters preparing to sell into Canada.
- First categories: food, seafood, agri, and general goods.
- First persona: beginner-to-intermediate exporter.
- Country path: Canada destination, Vietnam demo origin, India strategic next origin, Generic fallback.
- Core object: Trade Readiness Packet.

## Implemented Business Rules

- 12-question decision tree: trade direction, product, origin, destination, HS code, buyer/importer, importer of record, Incoterms, documents, regulated-product risk, official sources, and next safe move.
- Starter flow: checks minimum inputs and allows a starter packet when product, country, direction, intended use, and source routes exist.
- Market signal: computes a bounded local signal from source routes and evidence, capped before real demand proof.
- Country packs: checks whether required import, tariff, regulated-product, restricted-party, and market/buyer source routes exist.
- Source freshness: evaluates attached evidence for freshness, last verification, content hash, and review status.
- Buyer/supplier evidence: uses evidence ladders and blocks buyer-validated and supplier-verified language.
- Business gate decision: allows local drafts and reports while blocking outreach, payment, approvals, and shipment decisions.
- Phase coverage: exposes 13 business phase surfaces, while phase 0 remains the business identity lock.

## Document Logic Implemented Now

Document logic is now part of the packet decision system. The product accepts no-document intake as a valid beginner path and accepts PDFs as draft evidence only when upload checks pass.

- No-document intake creates a missing-evidence packet and does not show extracted-field confirmation or delete-uploaded-files actions.
- Uploaded-document intake creates quarantine metadata, draft extraction rows, user-confirmation status, and deletion actions.
- Expected document classes covered locally: `11`.
- Official sample PDFs stored for parser orientation: `3`.
- Synthetic filled parser QA PDFs stored for local parser testing: `11`.
- Official samples and synthetic QA files do not count as customer proof.
- Every extracted field has provenance, confidence, user-confirmation status, claim boundary, supported claims, and blocked claims.

## Claim Gate Logic Implemented Now

The product now checks packet statements through a claim gate before showing them. This prevents a source route, user input, parser draft, or missing-document placeholder from being presented as real approval.

- Claim decisions generated: `17`.
- Safe preparation/source-routing statements: `7`.
- Blocked statements: `10`.
- HS candidate, tariff route, CFIA route, market signal, and buyer lead-route statements can be shown only as preparation language.
- Origin evidence, supplier evidence, Incoterms responsibility, and document extraction stay blocked when the required proof is missing.
- Tariff confirmed, CFIA approved, buyer validated, supplier verified, customs ready, and shipment approved remain forbidden external claims.

## Current Sample Packet Result

- Packet reviewed: `packet-frozen-tuna-canada-001`.
- Business logic status: `business_logic_implemented_with_external_evidence_gates`.
- Business phase surfaces: `13`.
- Market signal score: `55` out of `59` before external evidence.
- Buyer evidence level: `no_evidence`.
- Supplier evidence level: `supplier_named`.
- Source freshness: `source_freshness_blocked_until_refresh_and_review`.
- Customer-visible decision: `draft_packet_allowed_external_claims_blocked`.

## Actions Allowed Locally

- approve trade action: False
- generate broker or expert packet: True
- generate buyer packet draft: True
- generate missing evidence report: True
- generate starter packet: True
- refresh sources record: True
- send outreach: False
- take payment: False

## Claims Still Blocked

- customs or tariff advice
- cfia or regulated product clearance
- buyer validation claim
- supplier verification or recommendation
- shipment or export ready claim
- live payment checkout
- public launch approval

## Evidence Needed Before Stronger Claims

- Dated official-source refresh and qualified review.
- Qualified customs/trade review for country, tariff, CFIA, import controls, and claim language.
- Dated buyer reply, call note, LOI, PO, or paid-order evidence before buyer-demand claims.
- Supplier registration, export ability, product documents, inspection/certificate, and prior-shipment evidence before supplier confidence claims.
- Security, privacy, AI-safety, DevOps, billing/payment, report-language, and launch-owner approval before hosted/private/public rollout.

## Reviewer Decision Requested

Please review whether the business rules make sense for a safe trade-readiness preparation product.

- Are any rules too weak or too strict for a controlled private-beta candidate?
- Do any labels overclaim approval, compliance, buyer validation, supplier verification, or market demand?
- Are the buyer and supplier evidence ladders reasonable?
- What must change before this can be shown to real users?
