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

## Boundaries

The product is a controlled private-beta candidate. It is not launch-ready,
legally approved, customs/tariff/CFIA approved, supplier approved, buyer
validated, production-hosted, or commercially ready. Human subject experts,
security/privacy review, infrastructure signoff, and current official evidence
remain explicit gates.
