# Non-Functional Requirements For External Review

Prepared on 2026-06-28 for Trade Readiness Copilot. This document focuses on security, privacy, AI safety, reliability, auditability, payments, and launch controls.

## 2-Minute Summary

The product is a local private-beta candidate with external human gates still closed. It has local controls for roles, audit, deletion tracking, AI-use boundaries, redaction preview, no-AI/manual workflow, claim gates, billing gates, and launch gates.

The product is not ready for unrestricted real files, live payments, public launch, or production claims until external review and hosted-platform proof are complete.

## Security And Access

- Implemented locally: role model, organization boundary model, scoped review links, admin/gate/health surfaces, and audit event records.
- Implemented locally for uploads: generated filenames, PDF signature checks, page limits, quarantine metadata, direct-file-serving blocks, and delete-file actions for uploaded quick-check files.
- Required before hosted beta: real authentication, secure sessions, CSRF where needed, rate limits, malware scanning, private object storage, secret management, and security review signoff.

## Privacy And Data Governance

- Implemented locally: AI-use policy, per-evidence AI permission concept, redaction preview, no-AI/manual fallback, deletion request tracking, and public upload notice.
- Official sample PDFs, synthetic parser QA files, and customer-uploaded evidence are separated so test fixtures are not mistaken for customer proof.
- Required before real user data: privacy notice, terms, retention/deletion approval, breach process, provider inventory, and review of whether any file content may be sent to AI providers.

## Document Handling Boundary

The document engine is ready for local review and parser QA. It is not yet approved for unrestricted real customer files in production.

- Document pipeline status: `production_document_intelligence_engine_ready_local_pipeline_security_gates_closed`.
- Pipeline stages tracked: `16`.
- Official sample PDFs: `3`.
- Synthetic parser QA PDFs: `11`.
- Real file uploads remain blocked until hosted auth, private storage, malware scanning, retention/deletion approval, privacy/legal review, security review, monitoring, and incident response are proven.

## AI Safety

- AI can summarize, structure, and create findings only when permitted.
- AI cannot approve customs, tariff, CFIA, legal, buyer, supplier, payment, launch, or shipment claims.
- Required before real documents: prompt-injection review, provider routing decision, redaction tests on real examples, incident process, and customer-facing AI-language review.

## AI Copilot Controls

- AI copilot status: `production_ai_copilot_engine_ready_no_gate_opening`.
- Output contracts: `8`.
- Prompt-injection checks: `2`.
- Live model calls remain disabled.
- Provider terms review and qualified AI safety review remain incomplete.
- AI output contracts cannot open product gates.

## Expert Review Controls

- Expert review status: `production_expert_review_network_ready_scope_limited_no_external_claims`.
- Reviewer lanes: `10`.
- Credential profiles required: `10`.
- Pending findings: `10`.
- All reviewer profiles require real credentials, identity, conflict, scope, source, and evidence attachments before a finding can be used.
- Draft review requests do not contact reviewers, do not record approval, and do not open claims.

## Report Export Controls

- Reports status: `production_reports_engine_ready_cited_exports_blocked_claims_visible`.
- Report records: `12`.
- Export records: `36`.
- JSON, HTML, and PDF exports are generated locally from packet/evidence/source/review artifacts.
- Reports include blocked claims, citations, version, watermark, and review status.
- Reports cannot hide blocked claims, open external claims, create external effects, enable live payment, or approve public launch.

## Portal Workflow Controls

- Portal workflow status: `production_portal_workflow_engine_ready_routes_gated_business_owner_ux`.
- UX checks: `7`.
- Gate controls: `6`.
- Portal workflows require plain business language, route coverage, mobile review, accessibility review, and blocked-versus-approved confusion testing.
- Portal gate controls keep approval claims, unrestricted uploads, live payments, external effects, and public launch closed.
- Real UX testing, accessibility signoff, mobile approval, hosted proof, and public launch owner approval remain incomplete.

## Enterprise API Controls

- Enterprise API status: `production_enterprise_api_platform_ready_local_contracts_external_gates_closed`.
- API contracts: `17`.
- Permission rows: `17`.
- Usage-limit rows: `6`.
- API contracts require auth, tenant filtering, object-level authorization, claim-gate reuse, rate-limit proof, and closed external effects.
- Live API keys, webhook delivery, unrestricted uploads, hosted auth, enterprise terms, and security review remain incomplete.

## Payment Controls

- Payment status: `production_payment_monetization_engine_ready_live_checkout_closed`.
- Checkout controls: `4`.
- Webhook controls: `6`.
- Payment webhooks require signature verification, idempotency, duplicate handling, delayed handling, and out-of-order handling.
- Live Stripe mode, checkout URLs, external charges, refund/support policy, tax/accounting review, payment security review, and claim-language review remain incomplete.

## Production Trust Control Plane

- Production trust status: `production_security_privacy_reliability_engine_ready_local_controls_external_trust_gates_closed`.
- Trust controls: `15`.
- Blocked trust gates: `16`.
- Unapproved vendor records: `6`.
- Local backup/restore drill: `local_backup_restore_hash_drill_passed`.
- The local backup/restore drill hash-matches existing critical artifacts, but production backup/restore remains unproven.
- Real uploads, hosted customer use, production monitoring, incident response approval, vendor approval, and privacy/security signoff remain incomplete.

## Claim Safety

- Evidence claim-gate status: `production_evidence_claim_gate_engine_ready_claims_fail_closed`.
- Evidence mapper rows: `25`.
- Claim mapper rows: `17`.
- Missing, stale, reference-only, parser-draft, or unreviewed evidence cannot open external claims.
- AI, source routes, uploaded documents, and generated reports cannot approve customs, tariff, CFIA, buyer, supplier, payment, shipment, legal, or launch claims.

## Scoring Safety

- Decision scoring status: `production_decision_scoring_engine_ready_no_global_readiness_score`.
- Score policy count: `6`.
- No single global readiness score is created.
- No combined readiness label is created.
- Approval language remains blocked even when a score is yellow or blue.

## Reliability And Operations

- Implemented locally: repeatable report generation, SQLite workflow store, generated state files, operation log, proof commands, and deployment-readiness artifacts.
- Required before hosted beta: managed database, object storage, backup policy, restore test, monitoring, rollback, incident runbook, and owner assignment.

## Payments And Billing

- Implemented locally: billing controls, usage ledger, payment gate matrix, and live checkout disabled.
- Required before payment activation: pricing decision, refund/support policy, tax/account review, processor setup, webhook handling, payment security review, and approval to activate live checkout.

## Launch And External Claims

- Final go-live status: `local_go_live_contract_complete_public_launch_blocked`.
- Public launch ready remains false.
- External validation gates remain open until real reviewers, users, hosted proof, payment proof, buyer/supplier evidence, and launch-owner approval exist.
- The product must keep `external_effects_created: false` and `claims_opened: false` in local operation proofs.

## Reviewer Decision Requested

Please review whether the non-functional controls are enough for the next controlled private-beta step, and what must change before hosted use or real customer data.

- Decision: approve for your reviewed scope, needs changes, or blocked.
- Security/privacy/AI issues that must be fixed first.
- Any data-retention, deletion, upload, logging, or access-control concern.
- Any reason live payment, real-file beta, hosted beta, or public launch should stay blocked.
