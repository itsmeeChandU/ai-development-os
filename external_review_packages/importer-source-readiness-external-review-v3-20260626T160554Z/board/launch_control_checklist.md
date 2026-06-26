# Launch Control Checklist

## Controls

- `scope-private-controlled-beta` [implemented] owner=operator: Only private controlled beta or board review is allowed; public launch remains closed. Next: Board approves or rejects private beta scope.
- `external-effects-closed` [implemented] owner=operator: External sends, paid actions, advice claims, and supplier recommendations remain zero. Next: Keep counters at zero unless a future approved launch gate opens them.
- `canadian-official-tools-attached` [implemented] owner=research: Canadian official tools and references are attached with claim boundaries. Next: Refresh dates before each board or launch review.
- `qualified-compliance-signoff` [approval_required] owner=compliance: Canadian customs/trade/food compliance signoff is required before external claims. Next: Route the generated packet to a licensed Canadian customs broker or qualified reviewer.
- `legal-privacy-signoff` [approval_required] owner=legal: Canadian legal/privacy review is required before public copy, data collection, or fundraising documents are sent as official materials. Next: Have counsel/privacy reviewer approve terms, privacy posture, liability boundary, and claims.
- `finance-signoff` [approval_required] owner=founder: Funding ask, pricing, runway, and spend plan require founder/accountant/finance review. Next: Approve a 12-month operating plan and first 90-day budget before commitments.
- `data-rights-refresh-signoff` [approval_required] owner=data: Source rights, refresh cadence, lineage, and API credentials must be approved before external source claims. Next: Add a no-write refresh proof and source-rights approval.
- `security-ops-signoff` [approval_required] owner=security: Deployment environment, access, logging, backup, incident response, support, and rollback require operator/security approval. Next: Approve private beta deployment controls before external users.

## Closed Claims

- public_launch_ready
- production_deploy_approved
- customs_or_tariff_advice_ready
- CFIA_compliance_ready
- legal_advice_ready
- financial_advice_ready
- buyer_validated
- revenue_proven
- product_market_fit_proven
- supplier_recommendation_ready
