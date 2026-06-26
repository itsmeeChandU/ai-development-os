# Requirements Analysis

This document maps the external developer requirements analysis to the current
product implementation. The machine-readable source of truth is
`system_review_graph/requirements_traceability_matrix.json`.

## Implemented Local Product Surface

- identity, seeded organizations, local sessions, RBAC, and scoped expert links
- packet intake, evidence upload, source refresh, blocker grouping, and reports
- organization AI data policies, model-routing contract, per-evidence AI
  permissions, redaction previews, and no-AI/manual fallback
- AI simulated reviewers that can create findings and next moves, but cannot
  open customs, tariff, CFIA, supplier, buyer, legal, financial, or launch gates
- customer, operator, expert-review, admin, support, privacy, terms, AI-use,
  and data-retention routes
- public Trade Readiness Copilot landing, tool selection, no-login PDF quick
  check, import/export selector, public result page, draft PDF downloads, and
  delete-files control
- Export-to-Canada packet mode with Canadian buyer/importer, importer of
  record, Incoterms, exporter-side readiness, importer-side readiness,
  buyer-ready packet, and Canadian broker-review packet
- audit events, deletion requests, health endpoints, Docker/Compose shell, and
  generated SQLite/runtime artifacts

## Requirement Coverage

| ID | Area | Status | Primary Artifacts |
| --- | --- | --- | --- |
| REQ-01 | Identity, organization, permissions | implemented local private beta | `auth_rbac_matrix.json`, `product_runtime_state.json` |
| REQ-02 | Packet intake | implemented | `customer_source_packets.json` |
| REQ-03 | Evidence ledger | implemented | `evidence_ledger.json` |
| REQ-04 | Official source refresh | implemented with refresh boundary | `source_refresh_runs.json` |
| REQ-05 | Claim and blocker engine | implemented fail closed | `claims_gate_matrix.json`, `blockers.jsonl` |
| REQ-06 | AI processing and model routing | implemented policy router | `ai_data_policy.json`, `ai_model_router.json` |
| REQ-07 | AI simulated reviewers | implemented fail closed | `customer_ai_review_runs.json` |
| REQ-08 | Operator UX | implemented local app | `operator_dashboard.html` |
| REQ-09 | Expert review UX | implemented scoped tokens | `review_requests.json` |
| REQ-10 | Reports and exports | implemented safe exports | `report_exports.json` |
| REQ-11 | Customer UX | implemented | `/dashboard`, `/packets/*` |
| REQ-12 | Admin UX | implemented | `/admin/*` |
| REQ-13 | Privacy and data controls | implemented with external gate | `ai_data_policy.json`, `redaction_pipeline.json` |
| REQ-14 | Security | implemented local controls with hosting gates | `auth_rbac_matrix.json` |
| REQ-15 | Audit and observability | implemented | `audit_events.json` |
| REQ-16 | Deployment environments | implemented hostable local stack | `Dockerfile`, `compose.yaml` |
| REQ-17 | Testing and acceptance gates | implemented | `scripts/check_product.py` |
| REQ-PUBLIC-01 | Public quick check | implemented local public surface | `public_trade_readiness_manifest.json`, `/api/public/quick-check` |
| REQ-EXPORT-01 | Export-to-Canada packet | implemented | `customer_readiness_report.json` |
| REQ-EXPORT-02 | Canadian buyer/importer | implemented fail closed | `customer_readiness_report.json` |
| REQ-EXPORT-03 | Incoterms / delivery responsibility | implemented fail closed | `customer_readiness_report.json` |
| REQ-EXPORT-04 | Import responsibility / IOR | implemented fail closed | `customer_readiness_report.json` |
| REQ-EXPORT-05 | Canadian-side readiness blockers | implemented fail closed | `claims_gate_matrix.json` |
| REQ-EXPORT-06 | Exporter-side document readiness | implemented fail closed | `exporter_mode_requirements.json` |
| REQ-EXPORT-07 | Buyer-ready packet | implemented draft PDF | `report_exports.json` |
| REQ-EXPORT-08 | Canadian broker-review packet | implemented draft PDF | `report_exports.json`, `review_requests.json` |
| REQ-EXPORT-09 | Block compliance/tariff/CFIA/buyer/shipment claims | implemented fail closed | `claims_gate_matrix.json` |

## Boundaries

The product is a controlled private-beta candidate with a local public
quick-check dry run. It is not launch-ready, legally approved,
customs/tariff/CFIA approved, supplier approved, buyer validated,
shipment-ready, production-hosted, or commercially ready. Human subject
experts, security/privacy review, infrastructure signoff, and current official
evidence remain explicit gates.
