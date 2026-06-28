# Production Reports Engine

Status: `production_reports_engine_ready_cited_exports_blocked_claims_visible`

The reports engine exports every Trade Readiness Packet as cited JSON, HTML,
and PDF deliverables. Each report keeps blocked claims visible, carries a
draft watermark, and records review status.

## Report Types

- Starter Trade Readiness Packet: Show the known product/lane context, missing fields, official source routes, and next safe move.
- Market Opportunity Brief: Summarize source-routed market signals without demand, profitability, or buyer-validation claims.
- Buyer-Ready Packet: Prepare buyer-facing context, questions, evidence level, and blocked buyer-validation language.
- Supplier Document Request: List supplier evidence requested and separate collected evidence from supplier verification.
- Broker Review Packet: Package customs, tariff, CFIA, responsibility, and unresolved review questions for scoped human review.
- Missing Evidence Report: Show missing documents, missing confirmations, stale source evidence, and next collection steps.
- Blocked Claims Report: List each blocked claim, why it is blocked, and what evidence or review is required.
- Country Source Map: Show country-pack coverage, source routes, refresh state, and claim boundaries.
- Source Freshness Report: Show source snapshot freshness, source lifecycle state, and packet stale-review needs.
- Expert Review Summary: Summarize scoped reviewer lanes, pending findings, credential needs, and review gate impacts.
- Executive Decision Report: Summarize scores, blockers, source/evidence state, external gates, and the next safe decision.
- Audit Export: Export report generation inputs, evidence citations, source citations, review status, and audit rows.

## Counts

- Packets: 1
- Report types: 12
- Report records: 12
- Export records: 36
- Citation records: 132

Report records are generated as report types per packet. In a multi-packet
workspace, export counts increase without opening new claims.

## Gate Boundary

- Blocked-claim sections required: true
- Claims opened: false
- External effects created: false
- Public launch ready: false

Reports organize evidence for decisions and expert review. They do not approve
trade action or remove unresolved claims.
