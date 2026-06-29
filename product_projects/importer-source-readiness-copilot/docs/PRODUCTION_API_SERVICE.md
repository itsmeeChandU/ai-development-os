# Production API Service

Status: `production_api_service_ready_repository_backed_safe_reads_effects_closed`

The local production API service dispatches reviewed API contracts through the
database-backed production repository. It proves auth checks, organization
scope, safe packet/report reads, blocked-claim visibility, and fail-closed
effectful routes.

## Sample Responses

- `customer_packet_read`: 200 `ok_repository_packet_context`
- `customer_scores_read`: 200 `ok_repository_scores`
- `customer_blocked_claims_read`: 200 `ok_repository_blocked_claims`
- `customer_report_context`: 200 `ok_repository_report_context_no_write`
- `customer_safe_summary`: 200 `ok_safe_summary_no_live_model_call`
- `other_customer_packet_denied`: 403 `access_denied`
- `anonymous_packet_denied`: 401 `authentication_required`
- `upload_effect_closed`: 423 `effect_gate_closed`
- `source_refresh_effect_closed`: 423 `effect_gate_closed`
- `api_key_issue_closed`: 423 `effect_gate_closed`
- `api_key_contract_read`: 200 `ok_api_key_contracts_no_live_secret`

## Gate Boundary

- Hosted API ready: false
- Live API keys issued: false
- Webhook delivery enabled: false
- Real uploads enabled: false
- External effects created: false
- Claims opened: false
- Public launch ready: false
