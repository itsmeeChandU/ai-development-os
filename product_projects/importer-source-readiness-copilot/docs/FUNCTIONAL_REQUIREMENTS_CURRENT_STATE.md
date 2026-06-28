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
| FR-03 | Support document upload and PDF triage | Implemented locally with confirmation gates | `document_processing.py`, public upload policy |
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

## Current Main Workflows

## Locked Functional Answers

| Question | Current Answer |
| --- | --- |
| Default first screen | Exporter quick start |
| First-screen choices | Explore a market, Prepare buyer packet, Check my documents |
| Primary deliverable | Trade Readiness Packet |
| Other packet views | Starter checklist, buyer-ready packet, broker-review packet, business decision report |
| Buyer/supplier outreach | Questions and preparation checklist only in private beta |
| First-class countries | Canada destination, India origin, Vietnam demo/sample, Generic fallback |
| Private beta upload scope | Metadata-only packets plus optional redacted/sample documents until upload review passes |

### Public Quick Check

1. User starts a quick check.
2. User selects import/export context.
3. User provides product and country details.
4. User may upload a PDF or continue without documents.
5. Product creates a draft packet and safe summary.
6. Product returns missing evidence, source routes, blockers, and next valid move.
7. Strong claims stay blocked.

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
6. Product calculates five business scores.
7. Product generates a business decision report.
8. Product keeps approval, tariff, buyer, supplier, shipment, and launch claims blocked.

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

- 49 customer UI routes
- 55 API routes
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

## Functional Questions To Resolve

1. Which user role should be the default first screen: public beginner, exporter, importer, broker/operator, or internal reviewer?
2. Which report should be the primary customer deliverable: starter checklist, trade readiness packet, buyer-ready packet, broker-review packet, or business decision report?
3. Should buyer/supplier outreach stay as questions only, or should the product prepare draft messages after review?
4. Which countries must be first-class at launch beyond Canada?
5. Should the private beta include real file uploads, or start with metadata-only packet entry?
