# Production Data Model

Status: `production_data_model_ready_local_schema_proof_external_db_gates_closed`

This is the first production rebuild package for Trade Readiness Copilot.

## Counts

- Tables: 40
- Foreign keys: 73
- Check constraints: 70
- Indexes: 38
- Tenant-scoped RLS tables: 29
- Domain events: 15
- JSON migration maps: 8

## Core Tables

- `organizations` maps `Organization` (global/reference).
- `users` maps `User` (tenant-scoped).
- `roles` maps `Role` (tenant-scoped).
- `user_roles` maps `RoleAssignment` (tenant-scoped).
- `workspaces` maps `Workspace` (tenant-scoped).
- `incoterm_records` maps `IncotermRecord` (global/reference).
- `trade_lanes` maps `TradeLane` (tenant-scoped).
- `trade_readiness_packets` maps `TradeReadinessPacket` (tenant-scoped).
- `packet_events` maps `PacketEvent` (tenant-scoped).
- `product_profiles` maps `ProductProfile` (tenant-scoped).
- `country_packs` maps `CountryPack` (global/reference).
- `source_records` maps `SourceRecord` (global/reference).
- `source_snapshots` maps `SourceSnapshot` (global/reference).
- `research_intakes` maps `ResearchIntake` (tenant-scoped).
- `dataset_connectors` maps `DatasetConnector` (global/reference).
- `country_pack_sources` maps `CountryPackSource` (global/reference).
- `documents` maps `Document` (tenant-scoped).
- `extracted_fields` maps `ExtractedField` (tenant-scoped).
- `field_provenance` maps `FieldProvenance` (tenant-scoped).
- `evidence_items` maps `EvidenceItem` (tenant-scoped).
- `evidence_mappers` maps `EvidenceMapper` (tenant-scoped).
- `market_signals` maps `MarketSignal` (tenant-scoped).
- `market_signal_sources` maps `MarketSignalSource` (global/reference).
- `buyer_profiles` maps `BuyerProfile` (tenant-scoped).
- `buyer_evidence_events` maps `BuyerEvidence` (tenant-scoped).
- `supplier_profiles` maps `SupplierProfile` (tenant-scoped).
- `supplier_evidence_events` maps `SupplierEvidence` (tenant-scoped).
- `responsibility_paths` maps `ResponsibilityPath` (tenant-scoped).
- `blocked_claims` maps `BlockedClaim` (tenant-scoped).
- `claim_gate_mappers` maps `ClaimGateMapper` (global/reference).
- `decision_scores` maps `DecisionScore` (tenant-scoped).
- `reviewer_lanes` maps `ReviewerLane` (global/reference).
- `review_requests` maps `ReviewRequest` (tenant-scoped).
- `review_findings` maps `ReviewFinding` (tenant-scoped).
- `expert_finding_sources` maps `ExpertFindingSource` (global/reference).
- `reports` maps `Report` (tenant-scoped).
- `audit_events` maps `AuditEvent` (tenant-scoped).
- `billing_accounts` maps `BillingAccount` (tenant-scoped).
- `subscriptions` maps `Subscription` (tenant-scoped).
- `usage_records` maps `UsageRecord` (tenant-scoped).

## Domain Events

- `packet_created` -> `packet_events`; external effect: `none`.
- `packet_state_changed` -> `packet_events`; external effect: `none`.
- `product_profile_confirmed` -> `field_provenance`; external effect: `none`.
- `document_uploaded_quarantined` -> `documents`; external effect: `none`.
- `field_extracted_draft` -> `extracted_fields`; external effect: `none`.
- `evidence_attached` -> `evidence_items`; external effect: `none`.
- `source_snapshotted` -> `source_snapshots`; external effect: `none`.
- `market_signal_recorded` -> `market_signals`; external effect: `none`.
- `claim_blocked` -> `blocked_claims`; external effect: `none`.
- `score_calculated` -> `decision_scores`; external effect: `none`.
- `review_requested` -> `review_requests`; external effect: `none`.
- `review_finding_recorded` -> `review_findings`; external effect: `none`.
- `report_exported` -> `reports`; external effect: `none`.
- `billing_usage_reserved` -> `usage_records`; external effect: `no_live_charge`.
- `audit_event_recorded` -> `audit_events`; external effect: `none`.

## JSON Artifact Migration Map

- `system_review_graph/customer_source_packets.json` -> trade_readiness_packets, trade_lanes, product_profiles, blocked_claims, responsibility_paths. One source packet becomes a packet, lane, product profile, responsibility path, and blocked claim rows.
- `system_review_graph/evidence_ledger.json` -> evidence_items, evidence_mappers, documents. Evidence rows keep provenance, freshness, AI-permission metadata, and claim support/block maps.
- `data/official_source_registry.json` -> source_records, country_pack_sources, dataset_connectors. Permanent source registry rows become source records and connector policy rows.
- `system_review_graph/policy_source_snapshots.json` -> source_snapshots. Source hashes and observed dates become source snapshot history.
- `system_review_graph/business_logic_phase_report.json` -> decision_scores, buyer_profiles, supplier_profiles, claim_gate_mappers. Business scores and evidence ladders become durable decision and gate rows.
- `system_review_graph/review_requests.json` -> reviewer_lanes, review_requests, review_findings. Scoped review links and finding templates become review workflow records.
- `system_review_graph/report_exports.json` -> reports, audit_events. Report export records become versioned reports and download audit events.
- `system_review_graph/billing_usage_ledger.json` -> billing_accounts, subscriptions, usage_records. Local reservations become usage records with external_charge_created=false.

## Proof Boundary

This package proves the production domain schema, migration map, and tenant isolation contract locally. It does not prove a hosted managed database, live production migration, backup/restore, external review, public launch, or any customs/trade/payment/legal claim.
