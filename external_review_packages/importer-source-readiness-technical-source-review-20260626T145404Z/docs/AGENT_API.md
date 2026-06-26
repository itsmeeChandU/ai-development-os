# Agent API

The Agent/API layer is a local contract for automation tools and external agents. Agents can create packets and reports through backend rules, but cannot bypass claim/blocker gates.

## Allowed Pattern

- Get supported countries and coverage tiers.
- Create a trade packet.
- Generate starter, missing-evidence, buyer, broker, and safe-summary outputs.
- Read packet status and blocker state.
- Request metered work only after plan and credit authorization.

## Forbidden Pattern

- Approve import/export.
- Confirm tariff or CFIA status.
- Verify suppliers.
- Validate buyers.
- Ship goods or declare shipment readiness.
- Send reports externally without user confirmation.

## Generated Artifacts

- `system_review_graph/agent_api_manifest.json`
- `system_review_graph/billing_credit_controls.json`
- `system_review_graph/traffic_pages_manifest.json`

Proof boundary: this is a local API/MCP contract. It does not expose a live public gateway, payment system, or claim-opening authority.
