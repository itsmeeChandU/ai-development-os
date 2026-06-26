# Policy Monitoring

Policy monitoring integrates Intelligence Hub style source tracking into the product without treating the source cache as truth.

## Flow

1. Official/reference sources are registered with IDs, tags, claim boundaries, and refresh modes.
2. Snapshot records store hashes and source metadata.
3. Change classifications identify whether packet recheck is required.
4. Packet impact rows mark stale-source risk and next valid moves.
5. Human or qualified expert review remains required before external claims.

## Generated Artifacts

- `system_review_graph/intelligence_hub_policy_monitor.json`
- `system_review_graph/policy_source_snapshots.json`
- `system_review_graph/policy_change_impact_report.json`
- `system_review_graph/policy_intelligence.sqlite`

Proof boundary: monitoring detects stale packet risk. It does not prove current law, tariff, CFIA, import permit, sanctions, buyer, supplier, legal, customs, or commercial readiness.
