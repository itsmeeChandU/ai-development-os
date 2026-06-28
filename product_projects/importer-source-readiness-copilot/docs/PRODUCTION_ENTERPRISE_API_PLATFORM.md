# Production Enterprise API Platform

Status: `production_enterprise_api_platform_ready_local_contracts_external_gates_closed`

The enterprise API platform turns the existing organization, workspace, packet,
report, claim-gate, audit, and portal artifacts into scoped API contracts for
brokers, advisors, and enterprise teams.

## Capabilities

- organizations: implemented_local
- workspaces: implemented_local
- roles_rbac: implemented_local
- client_accounts: implemented_local
- multi_packet_dashboard: implemented_local
- team_activity: implemented_local
- review_assignment: implemented_local
- audit_export: implemented_local
- api_keys: local_contract_live_keys_closed
- webhooks: local_contract_delivery_closed
- usage_limits: implemented_local_no_charges
- white_label_reports: local_policy_language_review_required

## API Contracts

- POST `/api/packets`: Create a Trade Readiness Packet. (route_present_gate_checked)
- GET `/api/packets/:id`: Read a packet visible to the caller. (route_present_gate_checked)
- POST `/api/packets/:id/evidence`: Attach evidence metadata to a packet. (route_present_gate_checked)
- POST `/api/documents/upload`: Enterprise document-upload contract; real files remain blocked until production upload gates pass. (route_present_gate_checked)
- POST `/api/sources/refresh`: Refresh packet source routes without proving current law. (route_present_gate_checked)
- GET `/api/packets/:id/scores`: Return separate capped decision scores. (route_present_gate_checked)
- GET `/api/packets/:id/blocked-claims`: Return blocked claims from the evidence claim-gate engine. (route_present_gate_checked)
- POST `/api/reviews`: Draft a scoped review request without contacting a reviewer. (route_present_gate_checked)
- POST `/api/reports`: Generate or list safe packet reports with blocked claims visible. (route_present_gate_checked)
- POST `/api/ai/safe-summary`: Return a safe local packet summary without a live model call. (route_present_gate_checked)
- GET `/api/team-workspace`: Read team workspace and approval-board state. (route_present_gate_checked)
- GET `/api/billing/usage`: Read local usage ledger with no live charges. (route_present_gate_checked)
- GET `/api/audit`: Read scoped audit records. (route_present_gate_checked)
- POST `/api/api-keys`: Record API-key request contract without issuing a live secret. (route_present_gate_checked)
- GET `/api/api-keys`: List local API-key contract fingerprints only. (route_present_gate_checked)
- POST `/api/webhooks`: Record webhook subscription contract with delivery disabled. (route_present_gate_checked)
- GET `/api/webhooks`: List local webhook event contracts. (route_present_gate_checked)

## Gate Boundary

- Hosted enterprise ready: false
- Live API keys issued: false
- Webhook delivery enabled: false
- Unrestricted uploads enabled: false
- White-label claims approved: false
- Claims opened: false

The product can expose reviewable local API contracts, API-key fingerprints,
webhook event shapes, audit export rules, usage limits, and white-label report
rules. It still needs hosted auth, live credential storage, webhook delivery
approval, enterprise terms, security review, and customer validation before
enterprise production gates can open.
