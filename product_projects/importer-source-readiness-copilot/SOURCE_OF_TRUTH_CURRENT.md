# Source Of Truth - Current State

Date: 2026-06-29

## Current Product State

Trade Readiness Copilot is a local production-slice reference implementation for preparing importer/exporter decision packets. The business logic is locked for the current controlled scope: source routing, evidence organization, blocked-claim handling, packet/report generation, reviewer gates, beginner workflows, market research routes, document triage, and local audit artifacts exist.

This is not public-launch approval. The production platform is partially specified and locally contracted, but not proven as a hosted, secure, legally reviewed, payment-enabled service.

## What Is Implemented Locally

- Trade Readiness Packet as the primary product asset.
- Beginner no-document quick check and starter packet path.
- Country/source registry for Canada import, India origin/export, Vietnam demo, and generic fallback.
- Evidence ledger, provenance, blocked claims, and report exports.
- Six separate decision scores: `market_signal_score`, `evidence_completeness_score`, `source_freshness_score`, `buyer_supplier_evidence_score`, `responsibility_clarity_score`, and `decision_safety_score`.
- Reviewer lanes and review-request artifacts.
- External validation input templates and evidence-room requirements.
- Local proof scripts, tests, and external package audit.

## Canonical Packet Stages

- Starter
- Document
- Decision
- Reviewer-ready
- Beta-ready

## Current Closed Gates

The following remain closed until dated real evidence exists:

- Public launch.
- Hosted private beta with real users.
- Live payment activation.
- Unrestricted real document uploads.
- Customs, tariff, CFIA, legal, sanctions, buyer, supplier, shipment, or market-demand approval language.
- Buyer validation and supplier verification claims.

## Current Development Priority

The immediate product priority is proof reproducibility and production trust:

1. Fresh-clone artifact regeneration before tests.
2. Honest source lifecycle states when refreshes fail or cannot be verified.
3. Production persistence for packet, evidence, source, report, review, and audit state.
4. Claim-gate wiring across every route and report.
5. Hosted trust controls before real file uploads or beta use.
6. Real reviewer and user evidence before external claims open.

## Reviewer Interpretation

Review this product as a decision-preparation platform, not as a broker, customs authority, legal advisor, payment approval, or buyer/supplier certifier. Local artifacts can prove implementation behavior. Only qualified reviewers, hosted infrastructure proof, payment proof, and real user outcomes can open the corresponding external gates.
