# Product Status

## Current State

The first local software loop is complete and the operator-gate plus customer
source-packet layer is now implemented. The startup/product is still
`startup_in_progress` because external evidence lanes remain open. The product
reads source cards, accepts customer source packets, builds an evidence ledger,
evaluates readiness gates, writes
`system_review_graph/readiness_report.json`, writes
`system_review_graph/external_gate_report.json`, writes
`system_review_graph/continuation_plan.json`, writes
`system_review_graph/vc_pitch_readiness_report.json`, writes
`system_review_graph/board_go_live_readiness_report.json`, writes
`system_review_graph/customer_readiness_report.json`, writes
`system_review_graph/evidence_ledger.json`, writes
`system_review_graph/blockers.jsonl`, exports
`system_review_graph/operator_dashboard.html`, writes
`system_review_graph/operator_screenshot_manifest.json`, writes investor pitch
artifacts, writes Canada-focused board artifacts, and passes the local proof
gate. It also writes AI/data policy, model-router, redaction, no-AI/manual
workflow, public trade readiness, exporter-mode, report-type, upload-policy,
and requirements traceability artifacts.

The current usable application is the local private-beta product app served by:

```bash
python3 scripts/serve_operator_app.py
```

This is the surface a customer, operator, expert reviewer, or admin can use in
local private-beta review. It includes `/`, `/tools`, `/trade-check`,
`/tools/import-readiness`, `/tools/export-readiness`,
`/public/packets/:id/result`, public PDF report downloads, `/dashboard`,
`/packets/new`,
`/packets/:id/evidence`, `/packets/:id/blockers`, `/packets/:id/readiness`,
`/packets/:id/ai-reviews`, `/packets/:id/reviews`, `/packets/:id/reports`,
`/settings/ai-data-policy`, scoped `/review/:token` pages,
`/operator/queue`, `/operator/packets/:id`, `/admin/sources`,
`/admin/gates`, `/admin/audit`, and
`/admin/system-health`. It is hostable after real infrastructure and qualified
security/privacy/human review gates are completed.

## Ready Now

- local source-card readiness evaluation
- unsafe external counter detection
- blocker ledger emission
- deterministic readiness report
- official-source registry
- country requirements matrix
- buyer/expert/contract/source-rights evidence packets
- external-gate report
- startup continuation plan
- VC pitch readiness report
- investor pitch deck, one-pager, demo script, and diligence-room index
- Canada official tool registry
- simulated expert review packet
- board go-live readiness report
- launch-control checklist
- financial operating model boundary
- generated operator work queue
- customer source-packet intake
- public Trade Readiness Copilot landing and tool selection
- no-login import/export quick check with PDF upload
- Export-to-Canada packet mode for foreign exporters
- buyer-ready and Canadian broker-review packet PDFs
- public upload notice, expiry manifest, and delete-files route
- evidence ledger with proof boundaries
- blocked-safe customer readiness report
- source-packet export routes
- grouped customer blockers
- official-source refresh records
- AI simulated review runs
- AI data policy and model router
- per-evidence AI/no-AI permissions
- redaction preview contract
- manual no-AI workflow
- requirement traceability matrix
- expert-review packet export
- scoped expert-review links and finding ingestion
- local SQLite workflow store
- auth/RBAC runtime contract
- organization-scoped packet access
- audit events and deletion-request tracking
- report export registry
- health endpoints and Docker/Compose deployment shell
- admin source registry and private-beta gates
- local operator app server
- static operator dashboard
- generated operator screenshot manifest and dashboard gallery
- standalone product check
- CI workflow for the proof gate

## Not Ready For External Claims

- customs, tariff, or import/export advice
- supplier recommendations
- buyer demand or PMF claims
- commercial/source contract claims
- legal/compliance readiness
- public launch claims
- tariff confirmation or CFIA compliance claims
- customer-visible source-packet approval claims

## Ready For Private VC Pitch

- pitch packet status: `vc_pitch_ready_with_diligence_gates`
- demo proof: `python3 scripts/check_product.py`
- pitch deck: `investor/vc_pitch_deck.md`
- one-pager: `investor/one_pager.md`
- demo script: `investor/demo_script.md`
- diligence index: `investor/diligence_room_index.md`

This is a private investor conversation state, not a public launch state.

## Ready For Board Go-Live Review

- board status: `board_go_live_candidate_with_human_approval_gates`
- primary market: Canada
- board brief: `board/board_go_live_brief.md`
- expert review packet: `board/expert_review_packet.md`
- launch checklist: `board/launch_control_checklist.md`
- financial operating model: `board/financial_operating_model.md`
- machine report: `system_review_graph/board_go_live_readiness_report.json`

This is the board-review stage for a controlled private beta. It is not public
launch approval, production deployment approval, legal advice, financial advice,
customs/tariff advice, CFIA compliance approval, buyer validation, or revenue
proof. The AI-built system has completed simulated expert review lanes and
keeps real human approvals explicit.

## Ready For Internal Source-Packet Review

- customer workflow status: `customer_workflow_ready_internal`
- display status: `Internal logic ready - external claims blocked`
- customer stage: `Customer packet prototype active - real customer use not enabled`
- source packet route: `/packets/new`
- safe report route: `/packets/:id/readiness`
- evidence route: `/packets/:id/evidence`
- blocker route: `/packets/:id/blockers`
- expert-review packet route: `/packets/:id/expert-review-packet`
- scoped expert-review route: `/review/:token`
- machine report: `system_review_graph/customer_readiness_report.json`
- evidence ledger: `system_review_graph/evidence_ledger.json`
- AI review runs: `system_review_graph/customer_ai_review_runs.json`
- AI policy: `system_review_graph/ai_data_policy.json`
- model router: `system_review_graph/ai_model_router.json`
- redaction pipeline: `system_review_graph/redaction_pipeline.json`
- no-AI workflow: `system_review_graph/manual_no_ai_workflow.json`
- requirements matrix: `system_review_graph/requirements_traceability_matrix.json`
- runtime contract: `system_review_graph/product_runtime_state.json`
- RBAC matrix: `system_review_graph/auth_rbac_matrix.json`
- audit events: `system_review_graph/audit_events.json`
- deployment readiness: `system_review_graph/deployment_readiness_report.json`
- local store: `system_review_graph/customer_workflow.sqlite`

This lets a customer/operator packet enter the product and get a safe readiness
report, upload evidence, refresh official-source records, view grouped blockers,
run AI simulated review, generate expert-review packets, and export a
customer-safe report. It also exposes local auth/RBAC, organization isolation,
AI data-policy controls, per-evidence AI permissions, redaction previews,
manual no-AI fallback, scoped expert review, admin audit, and deployment health
surfaces. It still blocks tariff confirmation, CFIA compliance, supplier
recommendation, buyer validation, import readiness, legal/compliance approval,
and public launch claims.

## Ready For Public Quick-Check Dry Run

- public product: `Trade Readiness Copilot`
- internal engine: `Importer Source Readiness Copilot`
- public surface status: `public_quick_check_ready_local_with_external_gates`
- tool routes: `/tools`, `/trade-check`, `/tools/import-readiness`,
  `/tools/export-readiness`, `/tools/buyer-broker-packet`
- result route: `/public/packets/:id/result`
- API route: `/api/public/quick-check`
- report downloads: draft trade readiness, buyer-ready, broker review,
  missing evidence, operator review, expert review
- machine contract: `system_review_graph/public_trade_readiness_manifest.json`
- exporter contract: `system_review_graph/exporter_mode_requirements.json`
- upload policy: `system_review_graph/public_upload_policy.json`

This is a local dry run of the public product flow. It supports PDF upload,
AI/data notice acceptance, readiness preview, blocked claims, draft PDF
download, and delete-files. It is not public hosting, approval, tariff
confirmation, CFIA clearance, customs/legal advice, buyer validation, shipment
readiness, or commercial readiness.

## Next Valid Move

The product now tells operators what is stopping external use. Remaining work
requires real evidence: dated buyer/operator feedback, written contracts,
source-rights approval, repeatable Canadian official-source refresh proof,
qualified Canadian import/export or food compliance review, exporter-side
country evidence where needed, legal/privacy approval, finance approval, and
operator/security signoff.

Do not report the product as fully operational or launch ready while
`system_review_graph/continuation_plan.json` says `must_continue: true`.
