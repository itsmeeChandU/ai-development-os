# Non-Functional Requirements Current State

Date: 2026-06-28

Current product status: `ready_with_external_gates`

Current safety posture: local private-beta candidate, external human gates still closed.

## Purpose

This document describes the current non-functional requirements and boundaries for security, privacy, reliability, AI safety, operations, auditability, payment safety, and launch readiness.

## Current Non-Functional Requirements

| ID | Requirement | Current State | Evidence |
| --- | --- | --- | --- |
| NFR-01 | Keep external effects closed by default | Implemented locally | `product_operations_report.json` |
| NFR-02 | Keep unsafe claims blocked by default | Implemented locally | `claims_gate_matrix.json` |
| NFR-03 | Require auth/RBAC for private workspace surfaces | Implemented as runtime contract | `auth_rbac_matrix.json` |
| NFR-04 | Keep organization-scoped access boundaries | Implemented as runtime contract | `product_runtime_state.json` |
| NFR-05 | Record audit events | Implemented locally | `audit_events.json` |
| NFR-06 | Support deletion request tracking | Implemented locally | `deletion_requests.json` |
| NFR-07 | Keep public upload handling gated | Implemented locally with hosting review still required | `public_upload_policy.json` |
| NFR-08 | Provide AI data-use controls | Implemented locally | `ai_data_policy.json` |
| NFR-09 | Provide redaction preview before AI use | Implemented locally | `redaction_pipeline.json` |
| NFR-10 | Provide no-AI/manual path | Implemented locally | `manual_no_ai_workflow.json` |
| NFR-11 | Keep model routing explicit | Implemented locally | `ai_model_router.json` |
| NFR-12 | Preserve source freshness and stale-source blockers | Implemented locally | `intelligence_hub_policy_monitor.json`, `policy_change_impact_report.json` |
| NFR-13 | Keep payments disabled until approved | Implemented locally | `billing_credit_controls.json` |
| NFR-14 | Keep launch controls explicit | Implemented locally | `launch_operations_report.json` |
| NFR-15 | Provide deployment shell without claiming hosted proof | Implemented locally | `Dockerfile`, `compose.yaml`, `deployment_readiness_report.json` |
| NFR-16 | Provide proof commands and generated reports | Implemented locally | `check_product.py`, root check scripts |

## Security

Current security controls are local contracts and proof artifacts.

Implemented now:

- role and organization boundary model
- scoped expert review token concept
- public upload policy
- direct serving block for upload quarantine paths
- audit event records
- deletion request records
- admin health and gate surfaces

Still required before hosted private beta:

- real authentication provider or hardened passwordless authentication
- secure session configuration
- CSRF protection where applicable
- rate limits
- malware scanning for uploads
- object storage isolation
- secret management
- production logging policy
- security review signoff

## Privacy And Data Governance

Implemented now:

- AI data-use policy
- per-evidence AI permission concept
- redaction preview contract
- no-AI/manual fallback
- data deletion request tracking
- public upload notice and expiry policy

Still required before hosted private beta:

- privacy notice review
- terms review
- retention policy approval
- breach process
- processor/vendor inventory
- review of whether uploaded files may be sent to any AI provider
- human approval for real user data handling

## AI Safety

Implemented now:

- AI cannot open approval gates
- AI cannot approve customs, tariff, CFIA, legal, buyer, supplier, payment, or launch claims
- AI-assisted review can create findings, blockers, and next moves
- no-AI/manual workflow exists
- ChatGPT-safe summaries avoid private file-content sharing by default

Still required:

- prompt-injection review for uploaded documents
- production model/provider routing decision
- redaction behavior verification on real examples
- incident process for unsafe AI output
- reviewer approval of customer-facing AI language

## Reliability And Recovery

Implemented now:

- deterministic local report generation
- local SQLite workflow store
- generated JSON reports for state reconstruction
- local health and deployment readiness artifacts
- repeatable proof commands

Still required before hosted private beta:

- managed database decision
- backup policy
- restore test
- environment-specific configuration
- uptime/error monitoring
- rollback process
- production incident runbook

## Observability And Auditability

Implemented now:

- product operations log
- product operations report
- audit events
- source refresh runs
- policy change impact report
- generated readiness and blocker reports
- proof commands in product and root checks

Still required:

- hosted logs
- alerting
- error aggregation
- security event monitoring
- real user activity review
- operational owner assignment

## Performance And Scale

Current expected scale is local review and controlled private beta preparation.

Implemented now:

- local JSON and SQLite artifacts
- deterministic local report generation
- local app route contract

Still required before production:

- file-size limits for uploads
- request-size limits
- load testing for report generation
- storage growth policy
- background job policy for OCR or heavy processing
- cost controls for AI/model usage

## Accessibility And Usability

Implemented now:

- generated operator dashboard
- customer route contract
- public quick-check route contract
- plain-language blockers and next valid moves

Still required:

- real usability review
- accessibility review
- mobile review
- copy review for non-expert users
- confirmation that users understand "blocked" versus "approved"

## Compliance And Professional Boundaries

Implemented now:

- reference-only official source routing
- blocked legal/customs/tariff/CFIA/supplier/buyer claims
- reviewer lanes for trade-boundary, legal/privacy/security, report language, freight/logistics, and billing/payment
- final rule: no reviewer lane, no claim lane

Still required:

- qualified customs/trade review
- legal/privacy/security review
- report-language review
- freight/logistics review
- public launch owner approval

## Payment And Billing Safety

Implemented now:

- billing and credit controls
- local usage ledger
- live checkout disabled
- no charges created by local operations

Still required:

- pricing decision
- refund/support policy
- tax/account review
- payment processor setup
- webhook handling
- payment security review
- written approval to activate live checkout

## Non-Functional Acceptance Criteria

The non-functional state is acceptable for local/private-review work only when:

- `external_effects_created` remains false
- `claims_opened` remains false
- public launch ready remains false
- hosted private beta ready remains false until real hosting/security/privacy proof exists
- live payment ready remains false
- delivery policy audit passes
- product and root checks pass

Required proof commands:

```bash
python3 scripts/check_product.py
python3 scripts/product_project_check.py
python3 scripts/ai_dev_os_check.py
python3 scripts/self_test_flow.py
```

## Non-Functional Questions To Resolve

1. Will private beta use real uploaded files, metadata-only packets, or both?
2. Which authentication option do we want for hosted beta?
3. Which database and object storage should be used for hosted beta?
4. Which AI provider policy is acceptable for real customer data?
5. Who will review security, privacy, legal, customs/trade, and report language?
6. What is the maximum file size and retention period for uploaded documents?
7. Should payments stay fully disabled through private beta?
