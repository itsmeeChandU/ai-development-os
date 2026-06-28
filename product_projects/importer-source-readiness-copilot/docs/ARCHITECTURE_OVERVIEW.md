# Architecture Overview

## System Shape

```text
data/sample_source_cards.json
data/country_requirements_matrix.json
data/evidence_packets.json
data/official_source_registry.json
data/canada_tool_registry.json
data/expert_review_simulations.json
data/launch_controls.json
        |
        v
src/importer_source_readiness/readiness.py
src/importer_source_readiness/external_gates.py
src/importer_source_readiness/continuation.py
src/importer_source_readiness/investor_readiness.py
src/importer_source_readiness/board_readiness.py
src/importer_source_readiness/operator_workflow.py
src/importer_source_readiness/operator_report.py
src/importer_source_readiness/operator_screenshots.py
src/importer_source_readiness/document_processing.py
src/importer_source_readiness/policy_intelligence.py
src/importer_source_readiness/completion_platform.py
src/importer_source_readiness/production_country_source_engine.py
src/importer_source_readiness/production_data_model.py
src/importer_source_readiness/production_decision_scoring_engine.py
src/importer_source_readiness/production_document_intelligence_engine.py
src/importer_source_readiness/production_evidence_claim_gate_engine.py
src/importer_source_readiness/production_market_intelligence_engine.py
src/importer_source_readiness/production_packet_engine.py
src/importer_source_readiness/production_redevelopment.py
        |
        v
system_review_graph/readiness_report.json
system_review_graph/external_gate_report.json
system_review_graph/continuation_plan.json
system_review_graph/vc_pitch_readiness_report.json
system_review_graph/board_go_live_readiness_report.json
system_review_graph/operator_workflow_report.json
system_review_graph/operator_screenshot_manifest.json
system_review_graph/operator_dashboard.html
system_review_graph/operator_screenshots/*.png
system_review_graph/intelligence_hub_policy_monitor.json
system_review_graph/policy_source_snapshots.json
system_review_graph/policy_change_impact_report.json
system_review_graph/policy_intelligence.sqlite
system_review_graph/completion_platform_manifest.json
system_review_graph/opportunity_scanner_report.json
system_review_graph/country_coverage_report.json
system_review_graph/transport_readiness_report.json
system_review_graph/billing_credit_controls.json
system_review_graph/agent_api_manifest.json
system_review_graph/traffic_pages_manifest.json
system_review_graph/production_data_model_manifest.json
system_review_graph/production_data_model_seed.json
system_review_graph/production_packet_engine_manifest.json
system_review_graph/production_packet_events.json
system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/*.json
system_review_graph/production_country_source_engine_manifest.json
system_review_graph/production_country_packs.json
system_review_graph/production_source_lifecycle.json
system_review_graph/production_market_intelligence_manifest.json
system_review_graph/production_market_signals.json
system_review_graph/production_market_dataset_connectors.json
system_review_graph/production_document_intelligence_manifest.json
system_review_graph/production_document_pipeline.json
system_review_graph/production_document_extracted_fields.json
system_review_graph/production_evidence_claim_gate_manifest.json
system_review_graph/production_claim_gate_decisions.json
system_review_graph/production_evidence_claim_mappers.json
system_review_graph/production_decision_scoring_manifest.json
system_review_graph/production_decision_score_records.json
system_review_graph/production_score_cap_policy.json
system_review_graph/production_redevelopment_plan.json
system_review_graph/production_research_anchors.json
data/official_sample_documents/canada/*.pdf
data/parser_qa_documents/*.pdf
docs/PRODUCTION_DATA_MODEL.md
docs/PRODUCTION_PACKET_ENGINE.md
docs/PRODUCTION_COUNTRY_SOURCE_ENGINE.md
docs/PRODUCTION_DOCUMENT_INTELLIGENCE_ENGINE.md
docs/PRODUCTION_EVIDENCE_CLAIM_GATE_ENGINE.md
docs/PRODUCTION_DECISION_SCORING_ENGINE.md
docs/PRODUCTION_MARKET_INTELLIGENCE_ENGINE.md
docs/PRODUCTION_REDEVELOPMENT.md
migrations/0002_production_domain_model.sql
investor/*.md
board/*.md
```

## Modules

| Module | Responsibility |
|---|---|
| `data/sample_source_cards.json` | fixture source and gate rows |
| `data/country_requirements_matrix.json` | country-specific requirement review rows |
| `data/evidence_packets.json` | buyer, expert, contract, source-rights, and launch evidence gates |
| `data/official_source_registry.json` | official source references and claim boundaries |
| `data/canada_tool_registry.json` | Canadian official tools for board/go-live review |
| `data/expert_review_simulations.json` | AI-simulated expert review lanes with human approval gates |
| `data/launch_controls.json` | controlled private beta and go-live approval controls |
| `src/importer_source_readiness/readiness.py` | evaluate source cards and produce blocker rows |
| `src/importer_source_readiness/external_gates.py` | evaluate country and evidence gates |
| `src/importer_source_readiness/continuation.py` | convert external blockers into required continuation lanes |
| `src/importer_source_readiness/investor_readiness.py` | build VC pitch readiness and diligence gates |
| `src/importer_source_readiness/board_readiness.py` | build Canada-focused board/go-live candidate readiness |
| `src/importer_source_readiness/operator_workflow.py` | compose source rows, evidence gates, continuation lanes, human approvals, and Canadian tool references into an operator queue |
| `src/importer_source_readiness/operator_report.py` | render static operator dashboard |
| `src/importer_source_readiness/operator_screenshots.py` | index operator-generated screenshot artifacts for dashboard review |
| `src/importer_source_readiness/document_processing.py` | triage public PDF uploads, native text extraction, OCR decision, hashes, and confirmation requirement |
| `src/importer_source_readiness/policy_intelligence.py` | database-style Intelligence Hub source monitoring contract, source snapshots, packet impacts, and stale-source blockers |
| `src/importer_source_readiness/completion_platform.py` | completion-stage contracts for opportunities, country coverage, transport readiness, billing, agent/API, and traffic pages |
| `src/importer_source_readiness/production_country_source_engine.py` | production country/source engine for country packs, source lifecycle states, source refresh evidence, packet impacts, and closed claim gates |
| `src/importer_source_readiness/production_data_model.py` | first production rebuild package: PostgreSQL migration, domain-event list, tenant RLS contract, seed fixture, and JSON-to-table migration map |
| `src/importer_source_readiness/production_decision_scoring_engine.py` | production decision scoring engine for six separate capped scores, reasons, blocker fields, evidence references, and no global readiness score |
| `src/importer_source_readiness/production_document_intelligence_engine.py` | production document intelligence engine for official sample forms, synthetic parser QA samples, document records, extracted-field provenance, evidence mapping, redaction previews, and closed upload/security/document gates |
| `src/importer_source_readiness/production_evidence_claim_gate_engine.py` | production evidence claim-gate engine for `can_show_claim`, required evidence types, evidence trails, mapper rows, and closed external claims |
| `src/importer_source_readiness/production_market_intelligence_engine.py` | production market intelligence engine for metric records, source routes, dataset connector states, score caps, and blocked demand/profit claims |
| `src/importer_source_readiness/production_packet_engine.py` | production packet engine for 12 packet states, packet event proof, eight packet views, six scores, blocked claims, and next valid moves |
| `src/importer_source_readiness/production_redevelopment.py` | full-scale production redevelopment contract with 14 layers, phases 0-20, research/source/evidence/gate tracks, permanent research entities, and closed external gates |
| `scripts/run_readiness.py` | CLI entrypoint and report writer |
| `scripts/run_external_gates.py` | external-gate report writer |
| `scripts/export_operator_dashboard.py` | dashboard exporter |
| `scripts/plan_continuation.py` | continuation plan writer |
| `scripts/build_vc_pitch_packet.py` | investor packet and pitch readiness writer |
| `scripts/build_board_go_live_packet.py` | board packet and go-live candidate writer |
| `scripts/run_operator_workflow.py` | operator work queue writer |
| `scripts/run_policy_intelligence.py` | Intelligence Hub policy/source monitor artifact writer |
| `scripts/run_completion_platform.py` | completion-stage artifact writer |
| `scripts/run_production_country_source_engine.py` | production country/source engine manifest and source lifecycle writer |
| `scripts/run_production_data_model.py` | production data model migration and manifest writer |
| `scripts/run_production_decision_scoring_engine.py` | production decision score records and cap-policy writer |
| `scripts/run_production_document_intelligence_engine.py` | production document intelligence sample library, pipeline, and extracted-field writer |
| `scripts/run_production_evidence_claim_gate_engine.py` | production evidence claim-gate decision, mapper, and review doc writer |
| `scripts/run_production_market_intelligence_engine.py` | production market intelligence signal and dataset connector writer |
| `scripts/run_production_packet_engine.py` | production packet engine manifest, event, and packet-view writer |
| `scripts/run_production_redevelopment.py` | production redevelopment contract and research-anchor writer |
| `tests/test_readiness.py` | proof for blocked-safe behavior |
| `tests/test_external_gates.py` | proof for external-gate and dashboard behavior |
| `tests/test_continuation.py` | proof that externally gated status keeps work in progress |
| `tests/test_investor_readiness.py` | proof that pitch status keeps diligence and claim gates visible |
| `tests/test_board_go_live.py` | proof that Canada board/go-live candidate status keeps human approval gates visible |
| `tests/test_operator_workflow.py` | proof that the product has an operator work queue with Canadian tool references and closed claims |
| `tests/test_operator_screenshots.py` | proof that screenshot artifacts are indexed and rendered without replacing generated truth |
| `tests/test_production_data_model.py` | proof that the first rebuild package has production tables, relationships, RLS policies, domain events, and closed external gates |
| `tests/test_production_packet_engine.py` | proof that the packet engine evaluates real local packet artifacts into states, views, scores, events, blockers, and closed external gates |
| `tests/test_production_country_source_engine.py` | proof that country packs, source lifecycle rows, and packet source impacts are generated from the official source registry and refresh records |
| `tests/test_production_decision_scoring_engine.py` | proof that the six score records stay separate, capped, reasoned, and closed to approval language |
| `tests/test_production_document_intelligence_engine.py` | proof that official samples, country source routes, parser QA fixtures, field provenance, and closed document/security gates are generated |
| `tests/test_production_evidence_claim_gate_engine.py` | proof that can_show_claim separates safe preparation statements from blocked external claims with evidence mappers |
| `tests/test_production_market_intelligence_engine.py` | proof that market metrics are source-routed without invented values, demand claims, profitability claims, or buyer validation |
| `tests/test_production_redevelopment.py` | proof that every redevelopment phase has build, research, source, evidence, and gate tracks backed by known source IDs |
| `system_review_graph/` | generated packets, reports, blockers, handoff evidence |

## Data Flow

1. Load source-card fixtures.
2. Evaluate unsafe counters.
3. Check official-source, freshness, buyer, legal, and contract gates.
4. Emit row-level status.
5. Flatten blockers into a report.
6. Write report to `system_review_graph/readiness_report.json`.
7. Evaluate country, buyer, expert, contract, source-rights, and launch gates.
8. Write `system_review_graph/external_gate_report.json`.
9. Convert blockers into `system_review_graph/continuation_plan.json`.
10. Convert pitch evidence into `system_review_graph/vc_pitch_readiness_report.json`.
11. Write investor pitch, one-pager, demo, and diligence artifacts.
12. Convert Canadian tools, expert simulations, and launch controls into
    `system_review_graph/board_go_live_readiness_report.json`.
13. Write board go-live brief, expert review packet, launch checklist, and
    financial operating model.
14. Compose `system_review_graph/operator_workflow_report.json` from source
    cards, external gates, continuation lanes, human approval gates, Canadian
    tools, closed claims, and proof commands.
15. Index operator screenshots in
    `system_review_graph/operator_screenshot_manifest.json`.
16. Render `system_review_graph/operator_dashboard.html` with the operator
    work queue, screenshot gallery, and generated proof boundary.
17. Generate Intelligence Hub-style source monitor artifacts with source
    hashes, diff-classifier placeholders, packet impact rows, stale-source
    blockers, and a SQLite policy intelligence store.
18. Generate completion-stage platform artifacts for opportunity signals,
    country coverage, transport questions, billing/credit gates, agent/API
    rules, and traffic-first pages.
19. Generate the production data model package: PostgreSQL migration, tenant
    row-level security contract, domain events, seed fixture, and JSON artifact
    migration map for the first rebuild package.
20. Generate the production packet engine package: 12-state packet lifecycle,
    packet events, eight packet views, six scores, blocked claims, and next
    valid moves from actual local packet/evidence/source/review/report data.
21. Generate the production country/source engine package: Canada import,
    India export, Vietnam demo-origin, and generic fallback country packs,
    source lifecycle states, source-refresh evidence, and packet source-impact
    rows.
22. Generate the production market intelligence engine package: source-routed
    metric records, dataset connector states, capped market signal score, and
    blocked demand/profit/buyer claims.
23. Generate the production document intelligence package: downloaded official
    sample forms, India/Vietnam source-route rows, synthetic filled parser QA
    samples, upload pipeline controls, document/evidence records, extracted
    fields, redaction previews, and closed upload/security/document claims.
24. Generate the production redevelopment contract and research anchors for
    the full-scale build: 14 production layers, phases 0-20, permanent source
    registry links, evidence requirements, and launch gates that remain closed.

## Status Rules

| Status | Meaning |
|---|---|
| `ready` | all local and external gates proven |
| `ready_with_external_gates` | local logic works but external evidence is still missing |
| `blocked_unsafe` | an unsafe external counter or unsupported claim opened |

The expected local product status is `ready_with_external_gates`.
That is not a final startup status. If either gate report is
`ready_with_external_gates`, the continuation plan must say
`startup_in_progress` and `must_continue: true`.

The expected investor status is `vc_pitch_ready_with_diligence_gates`. It
means a private VC pitch is supported by a demo, sources, and diligence lanes;
it does not mean the product is launch ready or externally operational.

The expected board status is
`board_go_live_candidate_with_human_approval_gates`. It means the Canada-focused
implementation can be placed in front of a board for controlled-private-beta
decisioning. It does not mean public launch, production deployment, customs,
tariff, CFIA, legal, financial, buyer, revenue, or PMF proof.

The expected production redevelopment status is
`production_redevelopment_contract_ready_with_external_build_gates`. It means
the next full-scale build contract exists and every phase has build, research,
source, evidence, and gate tracks. It does not mean production deployment,
legal/privacy/security approval, customs/trade approval, live payments, real
buyer/supplier validation, or public go/no-go approval.

The expected production data model status is
`production_data_model_ready_local_schema_proof_external_db_gates_closed`. It
means the first rebuild package now has a Postgres-oriented migration, entity
relationships, tenant isolation policies, domain events, and JSON migration
mapping. It does not mean the migration has been applied to a hosted managed
database.

The expected production packet engine status is
`production_packet_engine_ready_local_state_machine_claim_gates_closed`. It
means local packet state, packet views, scores, events, blockers, and next
moves are executable from current artifacts. It does not mean reviewer-ready
equals approved.

The expected production country/source engine status is
`production_country_source_engine_ready_reference_packs_claim_gates_closed`.
It means source-backed country packs and source lifecycle rows exist locally.
It does not mean source routes prove current law, tariff treatment, CFIA
approval, sanctions clearance, buyer validation, supplier verification, or
public launch readiness.

The expected production market intelligence status is
`production_market_intelligence_engine_ready_source_routed_no_demand_claims`.
It means market metric rows and dataset connector states exist locally. It
does not mean market size, buyer demand, profitability, tariff advantage, or
market-entry approval is proven.

The expected production document intelligence status is
`production_document_intelligence_engine_ready_local_pipeline_security_gates_closed`.
It means local document pipeline proof, official sample-form references,
parser QA samples, extracted-field provenance, evidence mapping, and redaction
previews exist locally. It does not mean real uploads, malware scanning,
private object storage, AI provider safety, document authenticity, customs
readiness, CFIA clearance, buyer validation, or supplier verification are
approved.

The expected production evidence claim-gate status is
`production_evidence_claim_gate_engine_ready_claims_fail_closed`. It means
`can_show_claim` decisions, evidence trails, claim-gate mappers, and
evidence mappers exist locally. It does not mean tariff, CFIA, customs, buyer,
supplier, shipment, payment, legal, or launch gates are approved.

The expected production decision scoring status is
`production_decision_scoring_engine_ready_no_global_readiness_score`. It means
six separate capped score records and cap policies exist locally. It does not
mean the packet is approved, globally ready, commercially ready, or safe for
shipment.

## Proof Boundary

The architecture proves local fixture evaluation only. It does not prove
customs, tariff, supplier, buyer, legal, payment, launch, or market readiness.
