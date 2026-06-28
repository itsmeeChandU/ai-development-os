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
- AI data policy, model router, endpoint contract, and redaction artifacts
- HTML output escaping and script-bearing evidence metadata rejection
- health endpoints for local/container deployments

Before real external customer hosting, replace demo session auth with a production identity provider, configure TLS, secrets management, managed database/object storage, malware scanning, backup restore tests, and qualified privacy/security review.
