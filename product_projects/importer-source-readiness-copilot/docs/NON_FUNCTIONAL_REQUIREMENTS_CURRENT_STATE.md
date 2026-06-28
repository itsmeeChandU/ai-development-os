# Non-Functional Requirements Current State

Date: 2026-06-28

Current product status: `ready_with_external_gates`

Current safety posture: local private-beta candidate, external human gates still closed.

## Purpose

This document describes the current non-functional requirements and boundaries for security, privacy, reliability, AI safety, operations, auditability, payment safety, and launch readiness.

## Current Non-Functional Requirements

## Locked Non-Functional Answers

| Question | Current Answer |
| --- | --- |
| Private beta data mode | Phase 1 metadata-only; Phase 2 supervised real-file beta after controls pass |
| Authentication | Managed auth provider or hardened passwordless login required before hosted beta |
| Database and object storage | Managed Postgres for packet state; private object storage for files |
| AI provider policy | Default no-AI/manual unless user explicitly permits AI use for evidence |
| Required reviewers | UX/Product, Security/Public Upload, Privacy/Legal, AI Safety, DevOps, Trade-Boundary/Customs, Freight/Logistics, Report Language, Billing/Payment |
| File handling | Small PDFs only, generated filenames, file-signature checks, quarantine metadata, explicit expiry, deletion support, no indefinite retention until reviewed |
| Payments | Disabled through private beta unless payment gates and reviews pass |

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
| NFR-17 | Keep production document intelligence gated | Implemented locally; real-file production use blocked | `production_document_intelligence_manifest.json`, `production_document_pipeline.json` |
| NFR-18 | Separate official samples, synthetic QA fixtures, and customer evidence | Implemented locally | `official_sample_documents/`, `parser_qa_documents/` |
| NFR-19 | Keep evidence-based claims fail closed | Implemented locally; unsupported external claims remain blocked | `production_evidence_claim_gate_manifest.json`, `production_evidence_claim_mappers.json` |
| NFR-20 | Avoid misleading readiness aggregation | Implemented locally; no single global readiness score is created | `production_decision_scoring_manifest.json`, `production_score_cap_policy.json` |
| NFR-21 | Keep AI assistance fail closed | Implemented locally; live calls and gate opening remain blocked | `production_ai_copilot_manifest.json`, `production_ai_safety_checks.json` |
| NFR-22 | Require real credentials and evidence before reviewer findings affect claims | Implemented locally; reviewer signoff and scope-limited approval remain blocked until real evidence is attached | `production_reviewer_profiles.json`, `production_review_finding_contracts.json` |
| NFR-23 | Keep report exports review-safe | Implemented locally; reports include citations, version, draft watermark, review status, and cannot hide blocked claims | `production_report_exports.json`, `production_report_citations.json` |
| NFR-24 | Keep portal workflows plain, route-covered, and gate-closed | Implemented locally; UX/accessibility/mobile testing and public launch approval remain external gates | `production_portal_workflow_manifest.json`, `production_portal_ux_checks.json`, `production_portal_gate_controls.json` |
| NFR-25 | Keep enterprise APIs tenant-scoped, rate-limit-ready, and live-effect closed | Implemented locally; hosted auth, live API keys, webhook delivery, enterprise terms, and security review remain external gates | `production_enterprise_api_manifest.json`, `production_enterprise_rbac_policy.json`, `production_enterprise_webhook_policy.json` |
| NFR-26 | Keep payment monetization preparation-only and live-checkout closed | Implemented locally; live Stripe mode, external charges, webhook delivery, refund/support approval, tax review, and payment security signoff remain external gates | `production_payment_monetization_manifest.json`, `production_payment_webhook_controls.json` |
| NFR-27 | Keep production trust controls evidence-based and real-file gates closed | Implemented locally; managed auth, MFA, private storage, malware scanning, vendor approval, monitoring, incident rehearsal, and production backup restore remain external gates | `production_security_privacy_reliability_manifest.json`, `production_backup_restore_drill.json` |
| NFR-28 | Keep launch activation exact-scope and owner-gated | Implemented locally; public launch, activation, hosted private beta, real-user evidence, payment activation, and final owner approval remain false | `production_launch_control_plane_manifest.json`, `production_public_launch_decision.json` |
| NFR-29 | Keep beginner trade discovery source-routed and non-recommendatory | Implemented locally; product/category/country browsing remains research-only and cannot claim demand, profit, buyer validation, supplier verification, customs/CFIA approval, or shipment readiness | `production_trade_discovery_manifest.json`, `production_trade_discovery_requirement_audit.json` |
| NFR-30 | Keep trade-data browsing value-gated and auditable | Implemented locally; browse cards and query work orders can show required inputs and source routes, but numeric values require dated dataset rows and no market conclusion is allowed without evidence | `production_trade_data_catalog_manifest.json`, `production_trade_data_ingestion_policy.json` |

## Security

Current security controls are local contracts and proof artifacts.

Implemented now:

- role and organization boundary model
- scoped expert review token concept
- public upload policy
- direct serving block for upload quarantine paths
- generated filenames and local quarantine metadata for public quick-check uploads
- PDF signature and page-limit checks for local upload intake
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
- clear separation between official sample PDFs, synthetic parser QA files, and customer-submitted evidence

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
- real-file parser safety review before AI-assisted document analysis is enabled for hosted users
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
- enterprise audit export policy for packets, evidence, reports, claim-gate
  decisions, score records, review requests, audit events, and source refreshes

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
- local enterprise usage-limit contracts for API requests, packets, report
  exports, AI safe summaries, webhook deliveries, and real-file upload bytes

Still required before production:

- file-size limits for uploads
- request-size limits
- enforced hosted API rate limits and abuse monitoring
- load testing for report generation
- storage growth policy
- background job policy for OCR or heavy processing
- cost controls for AI/model usage

## Enterprise API Security

Implemented now:

- 17 enterprise API contracts mapped to local routes
- RBAC permission matrix
- tenant filtering and object-level authorization requirements
- API-key fingerprints only, with no raw secret returned
- webhook event contracts with delivery disabled
- white-label report policy that forbids removing blocked claims, citations,
  draft watermark, and claim-gate language

Still required before enterprise hosted use:

- managed authentication and SSO/MFA decisions
- secure API-token issuance, storage, rotation, and revocation
- enforced rate limits and abuse monitoring
- customer-approved webhook endpoints, signing secrets, retries, and monitoring
- enterprise terms, support policy, retention policy, and security review

## Accessibility And Usability

Implemented now:

- generated operator dashboard
- customer route contract
- public quick-check route contract
- polished public landing and document-intake screens with clear next actions
- separate no-document and uploaded-document result actions
- plain-language blockers and next valid moves
- production portal workflow route matrix for public, exporter, importer,
  expert reviewer, operator/admin, and enterprise users
- four plain first-screen choices: Explore a market, Prepare a buyer packet,
  Check my documents, and Prepare for broker/expert review

Still required:

- real usability review
- accessibility review
- mobile review
- copy review for non-expert users
- confirmation that users understand "blocked" versus "approved"
- confirmation that portal buttons, labels, reports, and next actions are
  clear enough for non-technical business owners

## Compliance And Professional Boundaries

Implemented now:

- reference-only official source routing
- blocked legal/customs/tariff/CFIA/supplier/buyer claims
- reviewer lanes for trade-boundary, legal/privacy/security, report language, freight/logistics, and billing/payment
- final rule: no reviewer lane, no claim lane
- parser extraction is draft evidence only and cannot open approval gates

Still required:

- qualified customs/trade review
- legal/privacy/security review
- report-language review
- freight/logistics review
- public launch owner approval

## Document Handling Boundary

Current document handling is acceptable for local review and parser QA only.
The product has official sample PDFs, source-route-only rows, and synthetic
filled parser fixtures so parser behavior can be tested without pretending that
customer proof exists.

Real customer file handling remains blocked until these are proven in the
hosted environment:

- managed authentication and organization access control
- private object storage outside the webroot
- malware scanning or sandbox review
- file type validation beyond browser-provided Content-Type
- retention/deletion policy approval
- privacy/legal/security review of upload and AI-use language
- monitoring, incident handling, and backup/restore proof

## Payment And Billing Safety

Implemented now:

- billing and credit controls
- local usage ledger
- live checkout disabled
- no charges created by local operations
- production payment monetization contract with seven pricing tiers
- paid-scope policy that allows preparation work only
- forbidden paid-scope policy for approval/advice/validation/verification claims
- checkout controls with live checkout, checkout URL creation, and external
  charges disabled
- webhook controls that require signature verification, idempotency, duplicate
  event handling, delayed event handling, and out-of-order event handling

Still required:

- pricing decision
- refund/support policy
- tax/account review
- payment processor setup
- webhook handling
- payment security review
- written approval to activate live checkout
- claim-language review for all paid copy, checkout copy, invoices, and reports

## Production Trust Controls

Implemented now:

- production trust control matrix with 15 security, privacy, reliability, and
  operational controls
- vendor register for hosting/storage, AI, payment, malware/CDR, monitoring,
  and support/email review
- local backup/restore hash drill over critical artifacts
- incident runbook scenarios for privacy breach, malicious upload, prompt
  injection, tenant access issue, restore incident, payment incident, source
  change, and public claim-language issue
- explicit closed gates for real file uploads, hosted private beta, production
  trust approval, and public launch

Still required:

- managed hosted auth and admin MFA proof
- private object storage and malware scanning
- approved retention/deletion policy and privacy/security review
- vendor DPA/security/privacy review and data-residency decision
- production backup/restore test, monitoring alerts, incident rehearsal, and
  secrets manager proof

## Launch Control

Implemented now:

- 13 launch gates with evidence artifacts and required external evidence
- candidate public scope matrix for landing page, quick check, no-document
  starter packet, source routing, sample reports, and waitlist/demo booking
- blocked public-scope list for real uploads, live payments, automated
  outreach, approval language, buyer validation, supplier verification,
  shipment approval, and public legal/compliance advice
- public launch decision record with activation false

Still required:

- real external review and source refresh proof
- hosted infrastructure proof, privacy/security approval, and private-beta
  user evidence
- payment proof if monetized
- dated final owner approval for the exact public scope

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

## External Non-Functional Inputs Still Required

The local non-functional answers are locked for the current controlled scope:
metadata-first private beta, managed auth before hosted beta, managed Postgres
for packet state, private object storage for files, explicit AI consent, and
payments disabled until review. Production still needs dated external inputs:
security/privacy/legal/trade/report-language reviewers, hosted infrastructure
proof, upload size and retention approval, vendor/processor review, backup and
restore proof, and payment/tax/refund/support approval before any wider launch
or real file/payment scope can open.
