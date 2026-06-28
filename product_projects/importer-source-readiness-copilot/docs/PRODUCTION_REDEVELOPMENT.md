# Production Redevelopment Contract

Status: `production_redevelopment_contract_ready_with_external_build_gates`

Trade Readiness Copilot keeps the current business-rule engine and rebuilds the production platform around it.

## Current Decision

- Product: Trade Readiness Copilot
- Architecture: modular_monolith_first
- Current repo role: business-rule reference implementation and proof engine.
- External claims opened: false.
- Public launch ready: false.

## Counts

- Production layers: 14
- Redevelopment phases: 21 including phase 0
- Domain entities: 39
- Service boundaries: 12
- Dated research anchors: 18
- First rebuild work packages: 5

## Fourteen Production Layers

- 1. Product doctrine: Lock what the product is and is not.
- 2. Domain model: Make all product behavior map to durable entities.
- 3. Data platform: Move JSON/SQLite proof into governed production persistence.
- 4. Workflow engine: Run packets through explicit lifecycle states and review gates.
- 5. Country-pack engine: Scale country-specific routing and claim boundaries.
- 6. Source intelligence engine: Track official-source permissions, freshness, diffs, and packet impact.
- 7. Market intelligence engine: Produce source-backed research signals without demand claims.
- 8. Evidence and document intelligence engine: Extract, confirm, and govern evidence from files.
- 9. Decision and rules engine: Explain capped scores and blocked claims.
- 10. AI copilot layer: Use AI for assistance, never approval.
- 11. Expert review network: Turn human review into product workflow.
- 12. User portals: Give each user type a complete workflow.
- 13. Enterprise platform: Support firms, teams, clients, APIs, audit, and retention controls.
- 14. Production operations and go-live system: Operate only approved scopes with observable controls.

## Redevelopment Phases

### Phase 0: Product doctrine and claim boundary

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: ClaimPolicy module contract, allowed/blocked claims list, report-language rules, source-citation rules.
- Research track: customs broker boundary, importer responsibility, CFIA reference-only language, tariff classification limits, sanctions routing limits, AI output limits.
- Source track: cbsa-import-commercial-goods, cbsa-licensed-customs-brokers, cbsa-customs-tariff-2026, cfia-airs, gac-sanctions, wco-harmonized-system.
- Evidence track: claim policy row with required evidence, reviewer lane assignment, user-facing explanation.
- Claims still closed: approved, compliant, ready_to_ship, tariff_confirmed, cfia_approved, buyer_validated, supplier_verified.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 1: Production domain model

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: production entity schema, domain event list, entity lifecycle rules, JSON to Postgres migration map.
- Research track: WCO HS structure, Incoterms responsibility fields, Canada import data requirements, India IEC/export fields, source metadata requirements.
- Source track: wco-harmonized-system, icc-incoterms-2020, cbsa-import-commercial-goods, india-dgft-foreign-trade-policy.
- Evidence track: field provenance, source snapshot references, audit event for every business action.
- Claims still closed: field_presence_is_not_proof, parser_draft_is_not_confirmation.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 2: Trade Readiness Packet engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: packet state machine, starter/market/buyer/supplier/broker/operator/executive/blocked-claim packet views.
- Research track: required fields by direction, required fields by product class, regulated-product question set.
- Source track: cbsa-import-commercial-goods, cfia-airs, gac-import-controls.
- Evidence track: packet state transition log, packet view export, blocked-claims packet.
- Claims still closed: reviewer_ready_not_approved, packet_complete_not_trade_ready.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 3: No-document beginner intelligence

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: explore/import/export intake, starter packet, market checklist, source map, buyer/supplier/broker questions.
- Research track: market data availability, HS candidate lookup methods, country-pack coverage, common beginner mistakes.
- Source track: ised-trade-data-online, wco-harmonized-system, itc-market-access-map, cbsa-import-commercial-goods.
- Evidence track: no-document starter packet, research plan, blocked claims, next safe move.
- Claims still closed: research_plan_not_market_conclusion, no_documents_no_external_claims.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 4: Market intelligence engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: HS candidate route, destination import value, 3-5 year trend, top origin countries, unit value, market access barriers, lead routes.
- Research track: ISED TDO, Canadian Importers Database, WITS, ITC Trade Map, Market Access Map, UN Comtrade if API access is needed, dataset licensing and terms.
- Source track: ised-trade-data-online, canada-cid, world-bank-wits, itc-trade-map, itc-market-access-map.
- Evidence track: MarketSignal record per metric, source period, confidence, limitation, next validation.
- Claims still closed: no_profitable_market_claim, no_guaranteed_demand_claim, buyer_validation_required.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 5: Country-pack platform

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: country pack schema, Canada destination pack, India origin pack, Vietnam sample pack, Generic fallback, US/UK/EU/UAE queue.
- Research track: Canada import sources, India export sources, Vietnam proof sources, expansion-country source availability.
- Source track: cbsa-import-commercial-goods, cbsa-customs-tariff-2026, cfia-airs, gac-sanctions, india-dgft-foreign-trade-policy.
- Evidence track: coverage level, claim boundary, last checked, reviewer required, unsupported areas.
- Claims still closed: unsupported_country_generic_research_only, country_claim_requires_full_coverage_and_review.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 6: Official-source intelligence and monitoring

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: source lifecycle, robots/terms/license fields, source states, diff classification, packet impact calculation.
- Research track: robots status, terms, data license, update cadence, source owner, allowed automation, manual-only restrictions.
- Source track: official_source_registry.
- Evidence track: SourceRecord, SourceSnapshot, content hash, diff classification, packet stale event.
- Claims still closed: source_route_not_current_law, material_change_requires_reviewer.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 7: Import/export workflow engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: ExportPathEngine, ImportPathEngine, ResponsibilityPathEngine, broker/expert routing.
- Research track: Canada import process, India export process, Incoterms, broker responsibility, regulated goods, origin export controls.
- Source track: cbsa-import-commercial-goods, india-dgft-foreign-trade-policy, icc-incoterms-2020, cbsa-licensed-customs-brokers, cfia-airs.
- Evidence track: responsibility path, import/export unresolved questions, review route.
- Claims still closed: cannot_say_you_can_import, cannot_say_you_can_export.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 8: Buyer discovery and buyer-evidence engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: buyer evidence ladder, possible importer list, buyer questions, outreach preparation, buyer packet, validation gap.
- Research track: Canadian Importers Database, public importer directories, trade fairs, industry associations, anti-spam rules.
- Source track: canada-cid.
- Evidence track: lead source, contact evidence, reply evidence, meeting notes, LOI/PO/paid order evidence.
- Claims still closed: database_record_is_lead_not_validation, never_say_buyer_validated_without_threshold_evidence.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 9: Supplier evidence engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: supplier evidence ladder, supplier document request, risk questions, missing evidence, reviewer packet.
- Research track: company registries, export licenses, product certificates, food/agri/seafood certifications, inspection body standards, fraud indicators.
- Source track: india-dgft-foreign-trade-policy, cfia-airs.
- Evidence track: registration, export ability, product docs, certificates, inspection, prior shipment, commercial reference, reviewer assessment.
- Claims still closed: supplier_evidence_collected_not_supplier_verified.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 10: Document intelligence platform

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: upload, malware scan, file signature check, quarantine, OCR/text extraction, classification, field extraction, redaction preview.
- Research track: trade document templates, commercial invoice, packing list, certificate of origin, bill of lading, PO/contract, inspection report, upload security.
- Source track: owasp-file-upload.
- Evidence track: document id, page/section, extracted value, confidence, provenance, confirmation status, claim boundary.
- Claims still closed: parser_extraction_is_draft_evidence, real_uploads_blocked_until_security_privacy_controls.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

- Implementation status: `local_document_pipeline_sample_library_ready_security_gates_closed`
- Implementation artifacts: data/official_sample_documents/, data/parser_qa_documents/, system_review_graph/production_document_intelligence_manifest.json, system_review_graph/production_document_pipeline.json, system_review_graph/production_document_extracted_fields.json, docs/PRODUCTION_DOCUMENT_INTELLIGENCE_ENGINE.md.
- Implementation proof: Production document intelligence now maps declared document gaps, downloaded official sample forms, source-route-only country samples, synthetic filled parser QA documents, extracted-field provenance, redaction previews, and evidence records while keeping real upload/security/AI/document claims closed.

### Phase 11: Evidence ledger and claim-gate engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: EvidenceItem schema, can_show_claim(claim_type, packet_id), supports/blocks claim map, stale evidence blocking.
- Research track: evidence requirements by claim type, HS candidate, tariff route, CFIA relevance, buyer/supplier evidence, origin claim, Incoterms, market signal.
- Source track: cbsa-customs-tariff-2026, cfia-airs, wco-harmonized-system, icc-incoterms-2020, ised-trade-data-online.
- Evidence track: claim reason, evidence trail, source snapshot, reviewer requirement.
- Claims still closed: no_evidence_no_claim, stale_evidence_blocks_claim.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

- Implementation status: `local_evidence_claim_gate_engine_ready_claims_fail_closed`
- Implementation artifacts: system_review_graph/production_evidence_claim_gate_manifest.json, system_review_graph/production_claim_gate_decisions.json, system_review_graph/production_evidence_claim_mappers.json, docs/PRODUCTION_EVIDENCE_CLAIM_GATE_ENGINE.md.
- Implementation proof: can_show_claim decisions, evidence trails, required evidence types, stale/reference-only evidence blockers, and claim/evidence mapper rows are generated from local packet, source, market, document, and review artifacts by scripts/run_production_evidence_claim_gate_engine.py while external claims remain closed.

### Phase 12: Decision and scoring engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: six permanent scores, score reason, blocking fields, next action, cap policy.
- Research track: thresholds by packet stage, country coverage, product category, evidence strength, source freshness, reviewer status.
- Source track: official_source_registry.
- Evidence track: score output record, cap reason, next action.
- Claims still closed: no_single_global_readiness_score, no_approval_language.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

- Implementation status: `local_decision_scoring_engine_ready_no_global_readiness_score`
- Implementation artifacts: system_review_graph/production_decision_scoring_manifest.json, system_review_graph/production_decision_score_records.json, system_review_graph/production_score_cap_policy.json, docs/PRODUCTION_DECISION_SCORING_ENGINE.md.
- Implementation proof: Six separate score records, threshold bands, cap policies, claim-gate dependencies, evidence references, blocker fields, reasons, and next actions are generated from local packet, business, market, document, and claim-gate artifacts by scripts/run_production_decision_scoring_engine.py without creating a single readiness score or approval language.

### Phase 13: AI copilot layer

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: intake assistant, document assistant, source summarizer, market research assistant, packet writer, review work-order drafter, redaction assistant, QA assistant.
- Research track: AI provider data-use terms, retention settings, no-training guarantees, redaction tests, prompt-injection tests, model routing, human review.
- Source track: owasp-llm01-prompt-injection, nist-ai-rmf.
- Evidence track: AI output label, permission record, prompt-injection test result, redaction result.
- Claims still closed: ai_cannot_open_any_external_gate.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 14: Expert review network

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: reviewer profile, credentials, scope, packet review link, finding form, severity, decision values, audit trail.
- Research track: customs broker qualifications, trade consultant categories, freight expert scope, privacy/legal/security/AI/payment reviewer criteria.
- Source track: cbsa-licensed-customs-brokers.
- Evidence track: review finding, required changes, approved scope, evidence attachment.
- Claims still closed: no_reviewer_lane_no_claim_lane, scope_limited_approval_only.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 15: Reports and deliverables engine

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: starter packet, market brief, buyer-ready packet, supplier request, broker packet, missing evidence, blocked claims, country source map, source freshness, expert summary, executive report, audit export.
- Research track: beginner exporter needs, experienced exporter needs, Canadian importer needs, broker/supplier/buyer/operator/reviewer report needs.
- Source track: official_source_registry.
- Evidence track: HTML preview, PDF export, JSON export, citations, version history, watermark, review status.
- Claims still closed: reports_must_keep_blocked_claims_visible.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 16: User portals and workflows

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: public portal, exporter portal, importer portal, reviewer portal, admin/operator portal, enterprise portal.
- Research track: exporter/importer UX testing, accessibility, terminology, mobile review, blocked vs approved confusion testing.
- Source track: user_research_required.
- Evidence track: workflow smoke result, terminology feedback, accessibility result.
- Claims still closed: public_no_unrestricted_uploads, public_no_live_payment, public_no_strong_claims.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 17: Enterprise SaaS and API platform

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: organizations, workspaces, RBAC, client accounts, multi-packet dashboard, comments, review assignment, audit export, API keys, webhooks, usage limits, white-label reports.
- Research track: broker/advisor workflow, enterprise retention, API use cases, audit requirements, multi-client permissions, white-label needs.
- Source track: enterprise_user_validation_required.
- Evidence track: API contract, RBAC test, audit export, retention policy.
- Claims still closed: api_outputs_follow_same_claim_gate_engine.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 18: Payments and monetization

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: free quick check, starter packet, pro workspace, expert review add-on, broker/advisor workspace, enterprise, API/data access.
- Research track: Stripe live-mode requirements, refund/support policy, tax/accounting review, price testing, willingness to pay, payment wording.
- Source track: stripe-go-live.
- Evidence track: pricing approval, refund/support policy, tax review, webhook test, payment security review, claim-language review.
- Claims still closed: charge_for_preparation_not_approval, live_checkout_disabled_until_review.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 19: Security, privacy, reliability, and production trust

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: managed auth, admin MFA, org RBAC, secure sessions, CSRF, rate limits, private object storage, malware scanning, audit logs, deletion, retention, vendor register, backup/restore, monitoring, incident runbooks.
- Research track: PIPEDA, data residency, AI vendor terms, upload threat model, retention periods, breach process, security findings.
- Source track: opc-pipeda-principles, owasp-file-upload, owasp-llm01-prompt-injection, nist-ai-rmf.
- Evidence track: auth proof, upload security proof, privacy review, vendor inventory, backup restore test, incident runbook.
- Claims still closed: real_file_uploads_blocked_until_controls_proven.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.

### Phase 20: Launch control plane

- Local status: `phase_research_build_source_evidence_gate_tracks_ready`
- Build track: business logic gate, country-pack gate, source freshness gate, market-data gate, security gate, privacy gate, AI safety gate, trade-language gate, expert-review gate, payment gate, real-user evidence gate, production infrastructure gate, final owner gate.
- Research track: public copy review, source refresh proof, reviewer signoffs, user outcomes, hosted proof, payment proof.
- Source track: official_source_registry, reviewer_findings, user_validation_records.
- Evidence track: gate state, approved scope, expiry, owner approval.
- Claims still closed: launch_only_for_exact_approved_scope.
- Next valid move: Build the production implementation for this phase and attach the listed evidence before any gated claim can open.


## Permanent Research Intelligence Entities

- SourceSnapshot: snapshot_id, source_id, content_hash, fetched_at, diff_status.
- ResearchIntake: research_intake_id, phase, question, required_depth, owner.
- SourceRegistry: source_registry_id, source_id, source_area, authority_level, allowed_use.
- DatasetConnector: dataset_connector_id, source_id, access_mode, license_status, credential_status.
- CountryPackSource: country_pack_source_id, country_pack_id, source_id, source_area, claim_boundary.
- MarketSignalSource: market_signal_source_id, market_signal_id, source_id, metric, limitation.
- LegalBoundarySource: legal_boundary_source_id, claim, source_id, required_reviewer_lane.
- ExpertFindingSource: expert_finding_source_id, finding_id, source_id, review_scope.
- EvidenceMapper: evidence_mapper_id, evidence_id, supports_claim, blocks_claim.
- ClaimGateMapper: claim_gate_mapper_id, claim_type, required_evidence, required_source_ids, required_reviewer_lane.

## First Five Rebuild Packages

- production_data_model: TradeReadinessPacket, EvidenceItem, SourceRecord, CountryPack, DecisionScore, BlockedClaim, ReviewRequest, Report.
- packet_engine: create packet, update packet, score packet, block claims, generate packet views, export packet.
- country_source_engine: Canada pack, India origin pack, source registry, source snapshots, source freshness, stale packet logic.
- market_intelligence_engine: product/HS discovery, trade data signal, competitor countries, market access comparison, buyer/importer lead routes, confidence labels.
- report_engine: starter packet, market brief, buyer-ready packet, broker packet, missing evidence report, blocked claims report, executive decision report.

## Research Anchors

- ISED Trade Data Online: https://ised-isde.canada.ca/site/trade-data-online/en/overview
- International Trade Centre Market Access Map: https://www.macmap.org/
- Canada Border Services Agency commercial import guidance: https://www.cbsa-asfc.gc.ca/import/menu-eng.html
- CFIA Automated Import Reference System: https://inspection.canada.ca/en/importing-food-plants-animals/airs
- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- Stripe go-live checklist: https://docs.stripe.com/get-started/checklist/go-live
- Office of the Privacy Commissioner of Canada PIPEDA principles: https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/
- CBSA Canadian Customs Tariff 2026: https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/2026/menu-eng.html
- CBSA Licensed Customs Brokers: https://www.cbsa-asfc.gc.ca/services/cb-cd/cb-cd-eng.html
- Global Affairs Canada sanctions: https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/index.aspx?lang=eng
- Canadian Importers Database: https://ised-isde.canada.ca/site/ised/en/research-and-business-intelligence/canadian-importers-database
- India Directorate General of Foreign Trade: https://www.dgft.gov.in/
- World Bank World Integrated Trade Solution: https://wits.worldbank.org/
- International Trade Centre Trade Map: https://www.trademap.org/
- World Customs Organization Harmonized System: https://www.wcoomd.org/en/topics/nomenclature/overview/what-is-the-harmonized-system.aspx
- ICC Incoterms 2020: https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/
- OWASP GenAI prompt injection guidance: https://genai.owasp.org/llmrisk/llm01-prompt-injection/

## Proof Boundary

This artifact completes the local production redevelopment contract. It does not prove production deployment, legal/privacy/security approval, qualified customs/trade review, buyer/supplier validation, live payments, real user outcomes, or public go/no-go approval.
