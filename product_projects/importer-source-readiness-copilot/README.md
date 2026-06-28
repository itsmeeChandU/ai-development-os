# Trade Readiness Copilot

Trade Readiness Copilot is a standalone product repo generated from an
Intelligence Hub importer/exporter source-proof lane. The public product is a
PDF-first import/export readiness checker. The internal engine remains Importer
Source Readiness Copilot for source cards, customer source packets, evidence
ledgers, blockers, and operator review.

## Product Goal

Before a user imports or exports, show what is missing. The local product lets
users choose an import/export tool, upload trade PDFs, run a draft quick check,
download a readiness PDF, generate buyer/broker review packets, and delete
uploaded files. Operator and expert-review surfaces remain available for
private-beta review.

This product is intentionally blocked-safe. It does not make customs, tariff,
supplier, buyer, legal, payment, market, launch, or import/export advice
claims.

## Why This Project

The product exists because source-oriented import/export ideas are easy to
overclaim. The completed local loop turns source cards into readiness status,
machine-readable blockers, and a clear next valid move before any external
action is allowed.

The current implementation is a local modular monolith with customer,
operator, expert-review, admin, RBAC, audit, and deployment-readiness surfaces.
It uses generated state plus a SQLite runtime store to prove product control
logic while external data, contracts, compliance review, buyer validation, and
launch claims stay closed.

## Product Surface

The application a user can use today is the local product app:

```bash
python3 scripts/serve_operator_app.py
```

It opens a local browser surface for the public Trade Readiness Copilot
landing page, `/tools`, `/trade-check`, `/tools/import-readiness`,
`/tools/export-readiness`, public result pages, draft PDF downloads,
source-card readiness, customer source packet intake, evidence upload,
AI simulated reviews, AI data policy controls, per-evidence AI permissions,
redaction previews, no-AI/manual fallback, scoped expert-review handoff, audit,
admin controls, the operator work queue, Canada reference tools, blockers,
screenshots, and proof boundaries.
This is hostable for controlled private-beta review after real infrastructure,
security/privacy review, and human approval gates are completed.

## Run Proof

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_readiness.py
python3 scripts/run_external_gates.py
python3 scripts/plan_continuation.py
python3 scripts/build_vc_pitch_packet.py
python3 scripts/build_board_go_live_packet.py
python3 scripts/run_operator_workflow.py
python3 scripts/run_customer_workflow.py
python3 scripts/run_policy_intelligence.py
python3 scripts/export_operator_dashboard.py
python3 scripts/build_external_review_packet.py
python3 scripts/run_external_validation_requirements.py
python3 scripts/run_external_validation_requirements.py --input-dir external_inputs
python3 scripts/run_production_redevelopment.py
python3 scripts/run_production_data_model.py
python3 scripts/run_production_packet_engine.py
python3 scripts/run_production_country_source_engine.py
python3 scripts/run_production_trade_discovery_engine.py
python3 scripts/run_production_market_intelligence_engine.py
python3 scripts/run_production_document_intelligence_engine.py
python3 scripts/run_production_evidence_claim_gate_engine.py
python3 scripts/run_production_decision_scoring_engine.py
python3 scripts/run_production_ai_copilot_engine.py
python3 scripts/run_production_expert_review_network.py
python3 scripts/run_production_reports_engine.py
python3 scripts/run_production_portal_workflow_engine.py
python3 scripts/run_production_enterprise_api_platform.py
python3 scripts/run_production_payment_monetization_engine.py
python3 scripts/run_production_security_privacy_reliability_engine.py
python3 scripts/run_production_launch_control_plane.py
python3 scripts/audit_external_package.py --root .
python3 scripts/check_product.py
```

The product CLI writes:

```text
system_review_graph/readiness_report.json
system_review_graph/external_gate_report.json
system_review_graph/continuation_plan.json
system_review_graph/vc_pitch_readiness_report.json
system_review_graph/board_go_live_readiness_report.json
system_review_graph/operator_workflow_report.json
system_review_graph/operator_screenshot_manifest.json
system_review_graph/customer_readiness_report.json
system_review_graph/customer_source_packets.json
system_review_graph/evidence_ledger.json
system_review_graph/customer_readiness_report.md
system_review_graph/customer_ai_review_runs.json
system_review_graph/customer_workflow.sqlite
system_review_graph/product_runtime_state.json
system_review_graph/auth_rbac_matrix.json
system_review_graph/claims_gate_matrix.json
system_review_graph/review_requests.json
system_review_graph/audit_events.json
system_review_graph/deployment_readiness_report.json
system_review_graph/ai_data_policy.json
system_review_graph/model_endpoints.json
system_review_graph/ai_model_router.json
system_review_graph/redaction_pipeline.json
system_review_graph/manual_no_ai_workflow.json
system_review_graph/requirements_traceability_matrix.json
system_review_graph/public_trade_readiness_manifest.json
system_review_graph/exporter_mode_requirements.json
system_review_graph/public_report_types.json
system_review_graph/public_upload_policy.json
system_review_graph/intelligence_hub_policy_monitor.json
system_review_graph/policy_source_snapshots.json
system_review_graph/policy_change_impact_report.json
system_review_graph/policy_intelligence.sqlite
system_review_graph/expert_review_packet_packet-frozen-tuna-canada-001.md
system_review_graph/external_review_findings_report.json
system_review_graph/external_review_blocker_ledger.jsonl
system_review_graph/ai_assisted_external_review_plan.json
system_review_graph/ai_assisted_external_review_findings_report.json
system_review_graph/external_validation_requirements_report.json
system_review_graph/external_validation_evidence_requirements.json
system_review_graph/go_live_input_templates.json
system_review_graph/go_live_input_readiness_report.json
system_review_graph/production_data_model_manifest.json
system_review_graph/production_data_model_seed.json
system_review_graph/production_packet_engine_manifest.json
system_review_graph/production_packet_events.json
system_review_graph/production_packet_views/packet-frozen-tuna-canada-001/*.json
system_review_graph/production_country_source_engine_manifest.json
system_review_graph/production_country_packs.json
system_review_graph/production_source_lifecycle.json
system_review_graph/production_trade_discovery_manifest.json
system_review_graph/production_trade_discovery_category_map.json
system_review_graph/production_trade_discovery_country_lanes.json
system_review_graph/production_trade_discovery_beginner_flows.json
system_review_graph/production_trade_discovery_source_registry.json
system_review_graph/production_trade_discovery_requirement_audit.json
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
system_review_graph/production_ai_copilot_manifest.json
system_review_graph/production_ai_output_contracts.json
system_review_graph/production_ai_safety_checks.json
system_review_graph/production_expert_review_network_manifest.json
system_review_graph/production_reviewer_profiles.json
system_review_graph/production_review_requests.json
system_review_graph/production_review_finding_contracts.json
system_review_graph/production_reports_engine_manifest.json
system_review_graph/production_report_catalog.json
system_review_graph/production_report_exports.json
system_review_graph/production_report_citations.json
system_review_graph/production_reports/packet-frozen-tuna-canada-001/*.json
system_review_graph/production_reports/packet-frozen-tuna-canada-001/*.html
output/pdf/production_reports/packet-frozen-tuna-canada-001/*.pdf
system_review_graph/production_portal_workflow_manifest.json
system_review_graph/production_portal_route_matrix.json
system_review_graph/production_portal_ux_checks.json
system_review_graph/production_portal_gate_controls.json
system_review_graph/production_enterprise_api_manifest.json
system_review_graph/production_enterprise_api_contracts.json
system_review_graph/production_enterprise_rbac_policy.json
system_review_graph/production_enterprise_workspace_controls.json
system_review_graph/production_enterprise_webhook_policy.json
system_review_graph/production_enterprise_audit_export_policy.json
system_review_graph/production_enterprise_research_references.json
system_review_graph/production_payment_monetization_manifest.json
system_review_graph/production_pricing_tiers.json
system_review_graph/production_paid_scope_policy.json
system_review_graph/production_checkout_gate_controls.json
system_review_graph/production_payment_webhook_controls.json
system_review_graph/production_payment_research_references.json
system_review_graph/production_security_privacy_reliability_manifest.json
system_review_graph/production_trust_control_matrix.json
system_review_graph/production_vendor_register.json
system_review_graph/production_backup_restore_drill.json
system_review_graph/production_incident_runbooks.json
system_review_graph/production_trust_research_references.json
system_review_graph/production_launch_control_plane_manifest.json
system_review_graph/production_launch_gate_states.json
system_review_graph/production_launch_scope_matrix.json
system_review_graph/production_public_launch_decision.json
system_review_graph/production_redevelopment_plan.json
system_review_graph/production_research_anchors.json
data/official_sample_documents/canada/*.pdf
data/parser_qa_documents/*.pdf
external_review_findings/EXTERNAL_REVIEW_SUMMARY.json
EXTERNAL_REVIEW_SUMMARY.md
docs/EXTERNAL_REVIEW_PROCESS.md
docs/EXTERNAL_VALIDATION_REQUIREMENTS.md
docs/EXTERNAL_VALIDATION_REVIEWER_BRIEF.md
docs/GO_LIVE_INPUT_REQUESTS.md
docs/PRODUCTION_DATA_MODEL.md
docs/PRODUCTION_PACKET_ENGINE.md
docs/PRODUCTION_COUNTRY_SOURCE_ENGINE.md
docs/PRODUCTION_DOCUMENT_INTELLIGENCE_ENGINE.md
docs/PRODUCTION_EVIDENCE_CLAIM_GATE_ENGINE.md
docs/PRODUCTION_DECISION_SCORING_ENGINE.md
docs/PRODUCTION_AI_COPILOT_ENGINE.md
docs/PRODUCTION_EXPERT_REVIEW_NETWORK.md
docs/PRODUCTION_REPORTS_ENGINE.md
docs/PRODUCTION_PORTAL_WORKFLOWS.md
docs/PRODUCTION_ENTERPRISE_API_PLATFORM.md
docs/PRODUCTION_PAYMENT_MONETIZATION_ENGINE.md
docs/PRODUCTION_MARKET_INTELLIGENCE_ENGINE.md
docs/PRODUCTION_REDEVELOPMENT.md
output/pdf/external_validation_reviewer_brief.pdf
output/pdf/external_validation_requirements.pdf
output/pdf/go_live_input_requests.pdf
reviewer_packets/*.md
ai_assisted_review/*.md
ai_assisted_review/role_prompts/*.md
ai_assisted_review/simulated_findings/*.json
migrations/0002_production_domain_model.sql
system_review_graph/blockers.jsonl
system_review_graph/operator_dashboard.html
investor/vc_pitch_deck.md
investor/one_pager.md
investor/demo_script.md
investor/diligence_room_index.md
board/board_go_live_brief.md
board/expert_review_packet.md
board/launch_control_checklist.md
board/financial_operating_model.md
```

## Expected State

The expected local product status is:

```text
ready_with_external_gates
```

That means the local product logic works, but final product claims remain
blocked until real external evidence exists.

The expected external-review status is:

```text
external_review_ready_findings_pending
```

The expected production portal workflow status is:

```text
production_portal_workflow_engine_ready_routes_gated_business_owner_ux
```

That means public, exporter, importer, expert reviewer, operator/admin, and
enterprise portal workflows are mapped to real local UI/API routes with a
four-choice business-owner first screen. It does not mean UX testing,
accessibility signoff, mobile review, hosted proof, public launch approval,
unrestricted uploads, or live payments are complete.

The expected production enterprise API status is:

```text
production_enterprise_api_platform_ready_local_contracts_external_gates_closed
```

That means enterprise API contracts, RBAC policy, workspace controls, API-key
fingerprints, webhook contracts, audit export policy, usage limits, and
white-label report rules exist locally and follow the same claim gates. It does
not mean hosted enterprise auth, live API keys, webhook delivery, unrestricted
uploads, enterprise terms, security approval, or public launch are complete.

The expected production payment status is:

```text
production_payment_monetization_engine_ready_live_checkout_closed
```

That means pricing tiers, paid-scope rules, forbidden paid claims, checkout
controls, webhook controls, and payment review gates exist locally. It does not
mean live checkout, live Stripe objects, external charges, tax/accounting
approval, refund/support approval, payment security approval, or public launch
are complete.

The expected production trust status is:

```text
production_security_privacy_reliability_engine_ready_local_controls_external_trust_gates_closed
```

That means managed-auth, MFA, RBAC, session, upload, storage, malware,
audit, deletion, retention, vendor, backup, monitoring, incident, secrets, and
data-residency controls are mapped locally, and a local backup/restore hash
drill has passed. It does not mean real file uploads, hosted private beta,
vendor approval, privacy/security approval, production backup restore,
monitoring approval, incident rehearsal, or public launch are complete.

The expected production launch-control status is:

```text
production_launch_control_plane_ready_exact_scope_public_launch_blocked
```

That means the product has 13 launch gates, a candidate limited public scope,
and a blocked public-scope list. It does not mean activation, hosted private
beta, live payments, real uploads, external claims, final owner approval, or
public launch are complete.

That means reviewer-specific packets, blank findings templates, and external
review blocker rows are ready. It does not mean external review is complete.
Wave 1 reviewer decisions still block hosted private beta, Wave 2 decisions
still block stronger trade/customs/freight/report claims, and Wave 3 decisions
still block monetization or public scale.

For a solo developer, the repo also generates:

```text
ai_assisted_external_review_ready
ai_assisted_wave_1_reviewed_with_blockers
```

That means ChatGPT modes, separate agents, and web-research passes can be used
as simulated reviewers to find and fix issues. Those findings must be labeled
`ai_assisted_simulated_review` and cannot open qualified human approval,
private-beta, public-launch, legal/privacy/security, trade, freight, or payment
gates by themselves. The current Wave 1 simulated pass records five P0 blocker
findings across UX/product, security/public upload, privacy/legal, AI safety,
and DevOps/production readiness; real external review completion remains zero.

`ready_with_external_gates` is never a final startup status. The product check
also writes `system_review_graph/continuation_plan.json`; that plan must say
`startup_in_progress`, `must_continue: true`, and list the next buyer,
compliance, country, data, contract, screening, and launch evidence lanes.

The expected investor-pitch status is:

```text
vc_pitch_ready_with_diligence_gates
```

That means the product has a private VC conversation packet, evidence-backed
claim boundaries, and a demo script. It still does not prove launch readiness,
revenue, product-market fit, buyer validation, supplier readiness, or legal /
customs / tariff readiness.

The expected board/go-live status is:

```text
board_go_live_candidate_with_human_approval_gates
```

That means the Canada-focused implementation is ready for board review and a
controlled-private-beta decision. The AI-built system has simulated product,
Canadian trade compliance, financial, legal/privacy, data, and security/ops
review lanes, plus a Canadian tool registry and launch controls. It still
requires human approval before public launch, production deployment,
legal/financial/customs/tariff/CFIA claims, buyer validation, or spend
commitments.

The expected production redevelopment status is:

```text
production_redevelopment_contract_ready_with_external_build_gates
```

That means the full-scale rebuild has a machine-checkable contract: 14
production layers, phases 0-20, and build/research/source/evidence/gate tracks
for every phase. It still does not prove production deployment, legal/privacy
approval, security approval, customs/trade approval, live payment activation,
real buyer/supplier validation, real user outcomes, or public go/no-go approval.

The expected production data model status is:

```text
production_data_model_ready_local_schema_proof_external_db_gates_closed
```

That means the first rebuild package now has a Postgres-oriented migration,
entity relationships, row-level tenant isolation policies, domain events, a
seed fixture, and a JSON-to-table migration map. It still does not prove a
hosted managed database or production migration application.

The expected production packet engine status is:

```text
production_packet_engine_ready_local_state_machine_claim_gates_closed
```

That means the packet engine now evaluates real local packet, evidence,
source, review, and report artifacts into the 12-state production packet
machine, eight packet views, six scores, packet event proof, blocked claims,
and next valid moves. Reviewer-ready still does not mean approved.

The expected production country/source engine status is:

```text
production_country_source_engine_ready_reference_packs_claim_gates_closed
```

That means Canada import, India export, Vietnam demo-origin, and generic
fallback country packs are generated from the official source registry and
dated source-refresh records. Sources remain reference-only until freshness,
terms/automation, and qualified reviewer gates are proven.

The expected production market intelligence status is:

```text
production_market_intelligence_engine_ready_source_routed_no_demand_claims
```

That means market metrics, source routes, dataset connector states, capped
market signal score, limitations, and blocked demand/profit/buyer claims are
generated from the packet and official source registry. It still does not prove
market size, buyer demand, profitability, or market-entry approval.

The expected production trade discovery status is:

```text
production_trade_discovery_engine_ready_beginner_research_routed_no_opportunity_claims
```

That means beginner users can browse Canada import/export directions, product
families, country lanes into Canada, Canada export lanes, source routes, and
no-document starter flows before they know an HS code or have files. It still
does not recommend products, prove market demand, validate buyers, verify
suppliers, approve customs/CFIA status, or prove shipment readiness.

The expected production document intelligence status is:

```text
production_document_intelligence_engine_ready_local_pipeline_security_gates_closed
```

That means the local product has a document pipeline, downloaded official
CBSA/CFIA sample PDFs, India/Vietnam source routes, filled parser QA samples,
extracted-field provenance, evidence mapping, and redaction previews. It still
does not prove real upload security, malware scanning, private storage,
document authenticity, customs readiness, CFIA clearance, buyer validation, or
supplier verification.

The expected production evidence claim-gate status is:

```text
production_evidence_claim_gate_engine_ready_claims_fail_closed
```

That means the product now evaluates each packet statement through
`can_show_claim(claim_type, packet_id)`. Safe preparation and source-routing
statements can be shown with evidence trails, while tariff confirmation, CFIA
approval, buyer validation, supplier verification, customs readiness, and
shipment approval remain blocked until real official or qualified-review
evidence exists.

The expected production decision scoring status is:

```text
production_decision_scoring_engine_ready_no_global_readiness_score
```

That means the product now writes six separate capped score records with
reasons, blockers, evidence references, claim-gate dependencies, and next
actions. It deliberately does not create one combined readiness score or
approval label.

The expected production AI copilot status is:

```text
production_ai_copilot_engine_ready_no_gate_opening
```

That means AI roles are defined for intake, document extraction, source
summaries, market research, packet drafting, reviewer work orders, redaction,
and QA. Outputs are labeled as draft, source-backed, confirmation-needed,
expert-review-needed, or blocked. AI cannot open product gates, and live model
calls remain disabled.

The expected production expert review status is:

```text
production_expert_review_network_ready_scope_limited_no_external_claims
```

That means reviewer lanes, credential requirements, scoped review requests,
finding templates, gate-impact rows, and audit records are generated locally.
The product does not record completed reviews, does not send review links, and
does not open external claims without real reviewer credentials and dated
scope-limited findings.

The expected production reports status is:

```text
production_reports_engine_ready_cited_exports_blocked_claims_visible
```

That means the 12 required report types are exported as JSON, HTML preview,
and PDF. Each report includes source/evidence citations, version, draft
watermark, review status, and the blocked-claims section. Reports cannot hide
blocked claims or open external gates.

The expected customer source-packet status is:

```text
customer_workflow_ready_internal
```

Customer-facing display language must stay:

```text
Internal logic ready - external claims blocked
```

That means a customer/operator can create or inspect a source packet and get a
safe readiness report, but tariff confirmation, CFIA compliance, supplier
recommendations, buyer validation, import readiness, legal/compliance approval,
and public launch claims remain blocked.

The expected runtime status is:

```text
private_beta_candidate_with_external_human_gates
```

That means the repo now includes local session auth, seeded users and
organizations, organization-scoped packet access, role permissions, scoped
expert-review links, claim/gate matrices, audit events, report exports, data
deletion request tracking, health endpoints, Docker/Compose deployment files,
AI data policy controls, model-route contracts, redaction previews, manual
no-AI fallback, requirement traceability, and security/privacy docs. It does
not prove real public production hosting, qualified legal/privacy/security
signoff, or live customer launch.

The expected public quick-check status is:

```text
public_quick_check_ready_local_with_external_gates
```

That means a no-login user can choose import/export, upload at least one PDF,
accept the AI/data notice, run a draft readiness check, view missing evidence,
download draft/buyer/broker PDFs, see blocked claims, and delete uploaded local
files. It does not mean the product is publicly hosted, legally approved,
customs/tariff/CFIA cleared, shipment-ready, buyer validated, or commercially
ready.

The expected customer stage is:

```text
Customer packet prototype active - real customer use not enabled
```

The current customer workflow supports packet creation, evidence upload,
official-source refresh records, grouped blockers, AI simulated review,
AI data-policy settings, per-evidence AI/no-AI permissions, redaction preview,
expert-review packet export, scoped expert review links, customer-safe
readiness report export, admin source registry, admin gate view, audit,
auth/RBAC, organization isolation, and a local SQLite workflow store. It still
requires real hosted infrastructure and qualified human review before public
customer use.

## External Gates Kept Closed

- buyer validation
- legal/compliance review
- commercial/source contracts
- current data freshness
- official country/import/export requirements
- qualified broker/expert review
- source rights and refresh policy
- public launch claims
- paid actions
- external sends
- customs/tariff/import-export advice
- public go-live or production deployment approval
- Canadian legal/privacy/finance/compliance signoff
- tariff confirmation and CFIA compliance claims
- source-packet supplier, buyer, and import-readiness claims
- export-to-Canada readiness claims
- importer-of-record/DDP/non-resident importer responsibility claims
- trade agreement, MoU, or preference claims
- shipment decision claims

## Next Valid Move

Use `/trade-check` for the public PDF-first quick check and
`system_review_graph/public_trade_readiness_manifest.json` as the
machine-readable public product contract. Use
`system_review_graph/operator_dashboard.html` as the operator surface,
including its generated work queue, customer source-packet workflow, and
screenshot gallery. Use
`system_review_graph/operator_workflow_report.json` as the machine-readable
operator queue: source-card actions, external evidence gates, continuation
lanes, human approval gates, Canadian tool references, and closed claims.
Use `/packets/new` in the local product app or
`system_review_graph/customer_readiness_report.json` as the customer
source-packet proof surface. Use `system_review_graph/evidence_ledger.json`
as the evidence ledger; no evidence means no external claim.
Screenshot artifacts belong in `system_review_graph/operator_screenshots/` and
are indexed in `system_review_graph/operator_screenshot_manifest.json`.
Use `docs/STARTUP_LIFECYCLE.md` as the startup/R&D lifecycle surface.
Use `system_review_graph/continuation_plan.json` as the continuation surface.
Use `investor/vc_pitch_deck.md` and `investor/one_pager.md` for private VC
conversations. Use `board/board_go_live_brief.md` and
`system_review_graph/board_go_live_readiness_report.json` for board review.
Use `system_review_graph/product_runtime_state.json` as the machine-readable
auth/RBAC, review, audit, route, and deployment contract.
Use `system_review_graph/ai_data_policy.json`,
`system_review_graph/ai_model_router.json`,
`system_review_graph/redaction_pipeline.json`, and
`system_review_graph/requirements_traceability_matrix.json` for AI/data-policy
and requirement-coverage review.
The product can now show exactly what is stopping external use and which lane
must move next. To open any external claim gate, attach dated evidence to
`data/evidence_packets.json`, verify country rows in
`data/country_requirements_matrix.json`, and rerun
`python3 scripts/check_product.py`.
