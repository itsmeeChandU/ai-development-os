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
external_review_findings/EXTERNAL_REVIEW_SUMMARY.json
EXTERNAL_REVIEW_SUMMARY.md
docs/EXTERNAL_REVIEW_PROCESS.md
docs/EXTERNAL_VALIDATION_REQUIREMENTS.md
docs/EXTERNAL_VALIDATION_REVIEWER_BRIEF.md
docs/GO_LIVE_INPUT_REQUESTS.md
output/pdf/external_validation_reviewer_brief.pdf
output/pdf/external_validation_requirements.pdf
output/pdf/go_live_input_requests.pdf
reviewer_packets/*.md
ai_assisted_review/*.md
ai_assisted_review/role_prompts/*.md
ai_assisted_review/simulated_findings/*.json
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
