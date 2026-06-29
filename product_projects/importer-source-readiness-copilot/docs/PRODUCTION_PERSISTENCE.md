# Production Persistence

Status: `production_persistence_ready_local_domain_rows_external_db_gate_closed`

This artifact maps current packet, evidence, source, score, review, report, and audit state into normalized production-domain rows.

## Row Counts

- `organizations`: 3
- `users`: 4
- `workspaces`: 1
- `trade_lanes`: 1
- `trade_readiness_packets`: 1
- `product_profiles`: 1
- `country_packs`: 4
- `source_records`: 32
- `source_snapshots`: 35
- `evidence_items`: 3
- `blocked_claims`: 25
- `claim_gate_mappers`: 17
- `decision_scores`: 6
- `review_requests`: 1
- `reports`: 24
- `audit_events`: 6

## Closed Gates

- Hosted Postgres ready: false
- Production migration applied: false
- External claims opened: false
- Public launch ready: false

## Proof Boundary

Current packet artifacts are mapped into production-domain rows and written to a local SQLite proof store. This proves migration shape and referential loading locally; it does not prove hosted Postgres, auth, backups, real uploads, live payments, customs/legal approval, buyer validation, supplier verification, or public launch.
