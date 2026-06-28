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
- Record product, origin, destination, buyer/importer, supplier, Incoterms, HS-code candidate, source, and evidence details.
- Maintain an evidence ledger and mark evidence as missing, reference-only, stale, or needing review.
- Route users to official-source references without treating those references as approval.
- Generate missing-evidence, starter checklist, buyer packet draft, broker/expert packet, safe summary, and business decision outputs.
- Show grouped unresolved items and the next safe move.
- Record local operation proof with `external_effects_created: false` and `claims_opened: false`.

## Main Workflows

- Quick check: user gives product and country details, optionally adds documents, then receives missing evidence and next safe action.
- Packet workspace: user reviews the packet, evidence, official-source routes, unresolved items, and report outputs.
- Business decision preparation: product runs the decision tree, scores, source freshness check, buyer/supplier evidence ladder, and allowed/blocked action matrix.
- Expert routing: product prepares a scoped packet for a human reviewer; AI cannot approve the lane.
- Local operations: product can refresh source records, generate reports, create work orders, reserve billing internally, and record audit events without external effects.

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
