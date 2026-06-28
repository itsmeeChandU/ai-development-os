# Security And Privacy Controls

Importer Source Readiness Copilot is built to fail closed:

- unsafe claims default to blocked
- customer packet access is filtered by organization
- operators and admins can inspect cross-organization queues
- expert reviewers receive scoped review tokens
- AI simulated reviews cannot open gates
- AI processing is controlled by organization policy and per-evidence
  permission
- no-AI/manual workflow is supported
- redaction previews identify sensitive fields before AI processing
- route-specific artifact serving blocks traversal
- public PDFs are stored under generated quarantine names
- public upload paths are not directly served through artifact browsing
- PDF triage records hash, size, page estimate, native-text/OCR status, and
  confirmation requirement
- report exports are audit events
- data deletion is tracked as a request before retention action

Local private-beta controls are implemented in the modular monolith:

- session login/signup endpoints with seeded demo users
- role permission matrix
- organization membership data
- scoped expert review requests
- SQLite product runtime store
- audit event ledger
- evidence type allowlist and metadata size limits
- public upload notice, expiry manifest, delete-files route, and confirmation
  gate
- AI data policy, model router, endpoint contract, and redaction artifacts
- HTML output escaping and script-bearing evidence metadata rejection
- health endpoints for local/container deployments
- production trust control matrix
- vendor/data-processing register
- local backup/restore hash drill for critical artifacts
- incident runbook scenarios for privacy, upload, AI prompt-injection, tenant
  access, restore, payment, source-change, and claim-language issues

Phase 19 proof is stored in:

- `system_review_graph/production_security_privacy_reliability_manifest.json`
- `system_review_graph/production_trust_control_matrix.json`
- `system_review_graph/production_vendor_register.json`
- `system_review_graph/production_backup_restore_drill.json`
- `system_review_graph/production_incident_runbooks.json`

Before real external customer hosting, replace demo session auth with a production identity provider, enforce admin MFA, configure TLS, secrets management, managed database/private object storage, malware scanning, production backup restore, monitoring, incident response, data-residency approval, and qualified privacy/security review.
