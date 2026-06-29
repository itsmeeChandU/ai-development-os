"""Production data model package for Trade Readiness Copilot.

This module turns the first rebuild package into executable schema evidence:
a PostgreSQL migration, a seed fixture, a JSON-artifact migration map, and a
machine-readable manifest. It is still a local schema proof; applying it to a
hosted managed database remains an external infrastructure gate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_data_model_ready_local_schema_proof_external_db_gates_closed"


@dataclass(frozen=True)
class TableSpec:
    name: str
    entity: str
    columns: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    indexes: tuple[str, ...] = ()
    organization_scoped: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        "organizations",
        "Organization",
        (
            "organization_id text primary key",
            "name text not null",
            "status text not null default 'active'",
            "billing_account_id text",
            "retention_policy_id text",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
            "updated_at timestamptz not null default now()",
        ),
        ("constraint organizations_status_check check (status in ('active','suspended','archived'))",),
    ),
    TableSpec(
        "users",
        "User",
        (
            "user_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "email text not null",
            "status text not null default 'active'",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
            "updated_at timestamptz not null default now()",
        ),
        ("constraint users_status_check check (status in ('invited','active','disabled','archived'))",),
        ("create unique index if not exists users_email_unique on users (lower(email))",),
        True,
    ),
    TableSpec(
        "roles",
        "Role",
        (
            "role_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "name text not null",
            "permissions jsonb not null default '[]'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (),
        ("create unique index if not exists roles_org_name_unique on roles (organization_id, name)",),
        True,
    ),
    TableSpec(
        "user_roles",
        "RoleAssignment",
        (
            "user_id text not null references users(user_id) on delete cascade",
            "role_id text not null references roles(role_id) on delete cascade",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "created_at timestamptz not null default now()",
            "primary key (user_id, role_id)",
        ),
        (),
        ("create index if not exists user_roles_org_idx on user_roles (organization_id)",),
        True,
    ),
    TableSpec(
        "workspaces",
        "Workspace",
        (
            "workspace_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "name text not null",
            "client_id text",
            "status text not null default 'active'",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
            "updated_at timestamptz not null default now()",
        ),
        ("constraint workspaces_status_check check (status in ('active','archived'))",),
        ("create index if not exists workspaces_org_idx on workspaces (organization_id, status)",),
        True,
    ),
    TableSpec(
        "incoterm_records",
        "IncotermRecord",
        (
            "incoterm_id text primary key",
            "code text not null",
            "responsibility_summary text not null",
            "confirmation_status text not null default 'needs_user_confirmation'",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (
            "constraint incoterm_code_check check (length(code) between 2 and 10)",
            "constraint incoterm_confirmation_status_check check (confirmation_status in ('needs_user_confirmation','confirmed','not_applicable'))",
        ),
        ("create unique index if not exists incoterm_records_code_unique on incoterm_records (code)",),
    ),
    TableSpec(
        "trade_lanes",
        "TradeLane",
        (
            "trade_lane_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "origin_country text not null",
            "destination_country text not null",
            "direction text not null",
            "incoterm_id text references incoterm_records(incoterm_id)",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint trade_lanes_direction_check check (direction in ('import','export','both','exploring'))",),
        ("create index if not exists trade_lanes_route_idx on trade_lanes (organization_id, origin_country, destination_country, direction)",),
        True,
    ),
    TableSpec(
        "trade_readiness_packets",
        "TradeReadinessPacket",
        (
            "packet_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "workspace_id text not null references workspaces(workspace_id) on delete restrict",
            "trade_lane_id text not null references trade_lanes(trade_lane_id) on delete restrict",
            "state text not null",
            "claim_boundary_status text not null default 'external_claims_closed'",
            "version integer not null default 1",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
            "updated_at timestamptz not null default now()",
        ),
        (
            "constraint packet_state_check check (state in ('draft','starter_ready','research_ready','evidence_collecting','document_reviewing','source_checking','decision_preparing','reviewer_ready','expert_reviewing','customer_report_ready','paid_packet_ready','archived'))",
            "constraint packet_claim_boundary_check check (claim_boundary_status in ('external_claims_closed','reviewer_scope_limited','approved_for_scope'))",
        ),
        (
            "create index if not exists trade_readiness_packets_workspace_idx on trade_readiness_packets (workspace_id, state)",
            "create index if not exists trade_readiness_packets_org_state_idx on trade_readiness_packets (organization_id, state)",
        ),
        True,
    ),
    TableSpec(
        "packet_events",
        "PacketEvent",
        (
            "event_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "event_type text not null",
            "actor_id text references users(user_id)",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (),
        ("create index if not exists packet_events_packet_idx on packet_events (packet_id, created_at)",),
        True,
    ),
    TableSpec(
        "product_profiles",
        "ProductProfile",
        (
            "product_profile_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "name text not null",
            "category text",
            "intended_use text",
            "hs_candidate text",
            "confirmation_status text not null default 'needs_user_confirmation'",
            "payload jsonb not null default '{}'::jsonb",
        ),
        ("constraint product_confirmation_status_check check (confirmation_status in ('user_input','parser_draft','needs_user_confirmation','source_backed','reviewer_verified'))",),
        ("create index if not exists product_profiles_packet_idx on product_profiles (packet_id)",),
        True,
    ),
    TableSpec(
        "country_packs",
        "CountryPack",
        (
            "country_pack_id text primary key",
            "country_code text not null",
            "direction text not null",
            "coverage_level text not null",
            "reviewer_required boolean not null default true",
            "refresh_cadence jsonb not null default '{}'::jsonb",
            "claim_boundaries jsonb not null default '[]'::jsonb",
            "payload jsonb not null default '{}'::jsonb",
            "updated_at timestamptz not null default now()",
        ),
        (
            "constraint country_packs_direction_check check (direction in ('import','export','both','generic'))",
            "constraint country_packs_coverage_check check (coverage_level in ('full','partial','reference_only','generic'))",
        ),
        ("create unique index if not exists country_packs_unique on country_packs (country_code, direction)",),
    ),
    TableSpec(
        "source_records",
        "SourceRecord",
        (
            "source_id text primary key",
            "country_pack_id text references country_packs(country_pack_id) on delete set null",
            "canonical_url text not null",
            "source_type text not null",
            "authority_level text not null default 'official_reference'",
            "allowed_use text not null default 'reference_route_only'",
            "fetch_mode text not null default 'manual_check'",
            "terms_status text not null default 'not_checked'",
            "claim_boundary text not null",
            "payload jsonb not null default '{}'::jsonb",
            "updated_at timestamptz not null default now()",
        ),
        (
            "constraint source_records_url_check check (canonical_url like 'https://%')",
            "constraint source_records_terms_check check (terms_status in ('not_checked','checked_allowed','manual_only','restricted','unknown'))",
        ),
        ("create index if not exists source_records_type_idx on source_records (source_type, authority_level)",),
    ),
    TableSpec(
        "source_snapshots",
        "SourceSnapshot",
        (
            "snapshot_id text primary key",
            "source_id text not null references source_records(source_id) on delete cascade",
            "content_hash text not null",
            "fetched_at timestamptz not null",
            "diff_status text not null default 'not_checked'",
            "review_required boolean not null default true",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (
            "constraint source_snapshots_diff_check check "
            "(diff_status in ('not_checked','refresh_attempted_not_verified','checked_current_reference_only','changed_minor','changed_material','source_unavailable','stale','review_required'))",
        ),
        ("create index if not exists source_snapshots_source_idx on source_snapshots (source_id, fetched_at desc)",),
    ),
    TableSpec(
        "research_intakes",
        "ResearchIntake",
        (
            "research_intake_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text references trade_readiness_packets(packet_id) on delete cascade",
            "phase text not null",
            "question text not null",
            "required_depth text not null",
            "owner text not null",
            "status text not null default 'open'",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint research_intakes_status_check check (status in ('open','in_progress','answered','blocked','archived'))",),
        ("create index if not exists research_intakes_packet_idx on research_intakes (packet_id, status)",),
        True,
    ),
    TableSpec(
        "dataset_connectors",
        "DatasetConnector",
        (
            "dataset_connector_id text primary key",
            "source_id text not null references source_records(source_id) on delete restrict",
            "access_mode text not null",
            "license_status text not null default 'not_checked'",
            "credential_status text not null default 'not_required'",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (
            "constraint dataset_connectors_access_check check (access_mode in ('manual_download','api','csv_import','browser_reference','licensed_dataset'))",
            "constraint dataset_connectors_license_check check (license_status in ('not_checked','allowed','restricted','manual_only','needs_contract'))",
        ),
    ),
    TableSpec(
        "country_pack_sources",
        "CountryPackSource",
        (
            "country_pack_source_id text primary key",
            "country_pack_id text not null references country_packs(country_pack_id) on delete cascade",
            "source_id text not null references source_records(source_id) on delete restrict",
            "source_area text not null",
            "claim_boundary text not null",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (),
        ("create unique index if not exists country_pack_sources_unique on country_pack_sources (country_pack_id, source_id, source_area)",),
    ),
    TableSpec(
        "documents",
        "Document",
        (
            "document_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "storage_key text not null",
            "quarantine_status text not null default 'quarantined'",
            "classification text",
            "sha256 text",
            "uploaded_by text references users(user_id)",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint documents_quarantine_status_check check (quarantine_status in ('quarantined','scan_pending','scan_passed','scan_failed','deleted'))",),
        ("create index if not exists documents_packet_idx on documents (packet_id, quarantine_status)",),
        True,
    ),
    TableSpec(
        "extracted_fields",
        "ExtractedField",
        (
            "field_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "document_id text not null references documents(document_id) on delete cascade",
            "field_name text not null",
            "value text",
            "confidence numeric(5,2) not null default 0",
            "confirmation_status text not null default 'parser_draft'",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (
            "constraint extracted_fields_confidence_check check (confidence >= 0 and confidence <= 100)",
            "constraint extracted_fields_confirmation_check check (confirmation_status in ('parser_draft','needs_user_confirmation','user_confirmed','rejected','reviewer_verified'))",
        ),
        ("create index if not exists extracted_fields_document_idx on extracted_fields (document_id, field_name)",),
        True,
    ),
    TableSpec(
        "field_provenance",
        "FieldProvenance",
        (
            "field_provenance_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "field_id text not null references extracted_fields(field_id) on delete cascade",
            "mode text not null",
            "source_reference text",
            "reviewer_id text",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint field_provenance_mode_check check (mode in ('user_input','parser_draft','official_source_reference','system_derived','reviewer_verified'))",),
        ("create index if not exists field_provenance_field_idx on field_provenance (field_id, mode)",),
        True,
    ),
    TableSpec(
        "evidence_items",
        "EvidenceItem",
        (
            "evidence_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "document_id text references documents(document_id) on delete set null",
            "source_snapshot_id text references source_snapshots(snapshot_id) on delete set null",
            "type text not null",
            "provenance text not null",
            "confidence text not null default 'low'",
            "freshness text not null default 'unknown'",
            "review_required boolean not null default true",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (
            "constraint evidence_items_type_check check (type in ('document','official_source','market_data','buyer_signal','supplier_signal','reviewer_finding','user_input','system_derived'))",
            "constraint evidence_items_provenance_check check (provenance in ('user_input','parser_draft','official_source_reference','system_derived','reviewer_verified'))",
            "constraint evidence_items_freshness_check check (freshness in ('current','stale','unknown'))",
        ),
        ("create index if not exists evidence_items_packet_idx on evidence_items (packet_id, type, freshness)",),
        True,
    ),
    TableSpec(
        "evidence_mappers",
        "EvidenceMapper",
        (
            "evidence_mapper_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "evidence_id text not null references evidence_items(evidence_id) on delete cascade",
            "supports_claim text",
            "blocks_claim text",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (),
        ("create index if not exists evidence_mappers_evidence_idx on evidence_mappers (evidence_id)",),
        True,
    ),
    TableSpec(
        "market_signals",
        "MarketSignal",
        (
            "market_signal_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "signal_level text not null",
            "confidence text not null",
            "source_refs jsonb not null default '[]'::jsonb",
            "limitation text not null",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (
            "constraint market_signals_signal_level_check check (signal_level in ('strong_research_signal','moderate_research_signal','weak_research_signal','insufficient_data'))",
            "constraint market_signals_confidence_check check (confidence in ('no_data','research_plan','source_backed','document_backed','reviewer_verified'))",
        ),
        ("create index if not exists market_signals_packet_idx on market_signals (packet_id, confidence)",),
        True,
    ),
    TableSpec(
        "market_signal_sources",
        "MarketSignalSource",
        (
            "market_signal_source_id text primary key",
            "market_signal_id text not null references market_signals(market_signal_id) on delete cascade",
            "source_id text not null references source_records(source_id) on delete restrict",
            "metric text not null",
            "limitation text not null",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (),
        ("create index if not exists market_signal_sources_signal_idx on market_signal_sources (market_signal_id, source_id)",),
    ),
    TableSpec(
        "buyer_profiles",
        "BuyerProfile",
        (
            "buyer_profile_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "evidence_level text not null default 'lead_discovered'",
            "claim_status text not null default 'not_validated'",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (
            "constraint buyer_profiles_evidence_level_check check (evidence_level in ('lead_discovered','contact_identified','outreach_prepared','contact_attempted','reply_received','meeting_held','sample_requested','loi_received','po_or_paid_order_received'))",
            "constraint buyer_profiles_claim_status_check check (claim_status in ('not_validated','evidence_collected','review_required'))",
        ),
        ("create index if not exists buyer_profiles_packet_idx on buyer_profiles (packet_id, evidence_level)",),
        True,
    ),
    TableSpec(
        "buyer_evidence_events",
        "BuyerEvidence",
        (
            "buyer_evidence_event_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "buyer_profile_id text not null references buyer_profiles(buyer_profile_id) on delete cascade",
            "evidence_id text references evidence_items(evidence_id) on delete set null",
            "event_type text not null",
            "event_date date",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (),
        ("create index if not exists buyer_evidence_events_profile_idx on buyer_evidence_events (buyer_profile_id, event_type)",),
        True,
    ),
    TableSpec(
        "supplier_profiles",
        "SupplierProfile",
        (
            "supplier_profile_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "evidence_level text not null default 'supplier_named'",
            "claim_status text not null default 'not_verified'",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (
            "constraint supplier_profiles_evidence_level_check check (evidence_level in ('supplier_named','business_registration_attached','export_registration_or_license_attached','product_spec_attached','certificate_attached','inspection_report_attached','prior_shipment_evidence_attached','commercial_reference_attached','reviewer_assessed'))",
            "constraint supplier_profiles_claim_status_check check (claim_status in ('not_verified','evidence_collected','review_required'))",
        ),
        ("create index if not exists supplier_profiles_packet_idx on supplier_profiles (packet_id, evidence_level)",),
        True,
    ),
    TableSpec(
        "supplier_evidence_events",
        "SupplierEvidence",
        (
            "supplier_evidence_event_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "supplier_profile_id text not null references supplier_profiles(supplier_profile_id) on delete cascade",
            "evidence_id text references evidence_items(evidence_id) on delete set null",
            "event_type text not null",
            "event_date date",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (),
        ("create index if not exists supplier_evidence_events_profile_idx on supplier_evidence_events (supplier_profile_id, event_type)",),
        True,
    ),
    TableSpec(
        "responsibility_paths",
        "ResponsibilityPath",
        (
            "responsibility_path_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "importer_of_record text",
            "incoterms text",
            "clarity_status text not null default 'unknown'",
            "warnings jsonb not null default '[]'::jsonb",
            "payload jsonb not null default '{}'::jsonb",
        ),
        ("constraint responsibility_paths_clarity_check check (clarity_status in ('clear','partial','unknown','blocked'))",),
        ("create index if not exists responsibility_paths_packet_idx on responsibility_paths (packet_id, clarity_status)",),
        True,
    ),
    TableSpec(
        "blocked_claims",
        "BlockedClaim",
        (
            "blocked_claim_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "claim text not null",
            "reason text not null",
            "required_evidence jsonb not null default '[]'::jsonb",
            "required_reviewer_lane text",
            "status text not null default 'blocked'",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint blocked_claims_status_check check (status in ('blocked','needs_changes','approved_for_scope','expired'))",),
        ("create index if not exists blocked_claims_packet_idx on blocked_claims (packet_id, status)",),
        True,
    ),
    TableSpec(
        "claim_gate_mappers",
        "ClaimGateMapper",
        (
            "claim_gate_mapper_id text primary key",
            "claim_type text not null",
            "required_evidence jsonb not null default '[]'::jsonb",
            "required_source_ids jsonb not null default '[]'::jsonb",
            "required_reviewer_lane text",
            "blocked_language jsonb not null default '[]'::jsonb",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (),
        ("create unique index if not exists claim_gate_mappers_claim_type_unique on claim_gate_mappers (claim_type)",),
    ),
    TableSpec(
        "decision_scores",
        "DecisionScore",
        (
            "score_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "score_name text not null",
            "label text not null",
            "reason text not null",
            "next_action text not null",
            "blocking_fields jsonb not null default '[]'::jsonb",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (
            "constraint decision_scores_name_check check (score_name in ('market_signal_score','evidence_completeness_score','source_freshness_score','buyer_supplier_evidence_score','responsibility_clarity_score','decision_safety_score'))",
            "constraint decision_scores_label_check check (label in ('green','yellow','red','grey'))",
        ),
        ("create index if not exists decision_scores_packet_idx on decision_scores (packet_id, score_name)",),
        True,
    ),
    TableSpec(
        "reviewer_lanes",
        "ReviewerLane",
        (
            "reviewer_lane_id text primary key",
            "scope text not null",
            "required_credentials jsonb not null default '[]'::jsonb",
            "gate_can_open text not null",
            "payload jsonb not null default '{}'::jsonb",
        ),
    ),
    TableSpec(
        "review_requests",
        "ReviewRequest",
        (
            "review_request_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "reviewer_lane_id text not null references reviewer_lanes(reviewer_lane_id) on delete restrict",
            "status text not null default 'requested'",
            "scope text not null",
            "review_token_hash text",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint review_requests_status_check check (status in ('requested','in_review','needs_changes','approved_for_scope','blocked','expired'))",),
        ("create index if not exists review_requests_packet_idx on review_requests (packet_id, status)",),
        True,
    ),
    TableSpec(
        "review_findings",
        "ReviewFinding",
        (
            "finding_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "review_request_id text not null references review_requests(review_request_id) on delete cascade",
            "severity text not null",
            "decision text not null",
            "required_changes jsonb not null default '[]'::jsonb",
            "evidence_attachment_id text references evidence_items(evidence_id) on delete set null",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (
            "constraint review_findings_severity_check check (severity in ('info','low','medium','high','critical'))",
            "constraint review_findings_decision_check check (decision in ('approved_for_scope','needs_changes','blocked'))",
        ),
        ("create index if not exists review_findings_request_idx on review_findings (review_request_id, decision)",),
        True,
    ),
    TableSpec(
        "expert_finding_sources",
        "ExpertFindingSource",
        (
            "expert_finding_source_id text primary key",
            "finding_id text not null references review_findings(finding_id) on delete cascade",
            "source_id text references source_records(source_id) on delete set null",
            "review_scope text not null",
            "payload jsonb not null default '{}'::jsonb",
        ),
        (),
        ("create index if not exists expert_finding_sources_finding_idx on expert_finding_sources (finding_id)",),
    ),
    TableSpec(
        "reports",
        "Report",
        (
            "report_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "packet_id text not null references trade_readiness_packets(packet_id) on delete cascade",
            "report_type text not null",
            "watermark text not null default 'draft'",
            "version integer not null default 1",
            "storage_key text",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint reports_watermark_check check (watermark in ('draft','reviewed','final'))",),
        ("create index if not exists reports_packet_idx on reports (packet_id, report_type, version)",),
        True,
    ),
    TableSpec(
        "audit_events",
        "AuditEvent",
        (
            "audit_event_id text primary key",
            "organization_id text references organizations(organization_id) on delete set null",
            "actor_id text references users(user_id) on delete set null",
            "event_type text not null",
            "entity_type text not null",
            "entity_id text",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        (),
        ("create index if not exists audit_events_org_time_idx on audit_events (organization_id, created_at desc)",),
        True,
    ),
    TableSpec(
        "billing_accounts",
        "BillingAccount",
        (
            "billing_account_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "processor_customer_id text",
            "live_mode_enabled boolean not null default false",
            "status text not null default 'disabled'",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint billing_accounts_status_check check (status in ('disabled','test_mode','review_required','live_enabled'))",),
        ("create unique index if not exists billing_accounts_org_unique on billing_accounts (organization_id)",),
        True,
    ),
    TableSpec(
        "subscriptions",
        "Subscription",
        (
            "subscription_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "billing_account_id text not null references billing_accounts(billing_account_id) on delete restrict",
            "tier text not null",
            "status text not null default 'inactive'",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint subscriptions_status_check check (status in ('inactive','trial','active','past_due','cancelled'))",),
        ("create index if not exists subscriptions_billing_idx on subscriptions (billing_account_id, status)",),
        True,
    ),
    TableSpec(
        "usage_records",
        "UsageRecord",
        (
            "usage_record_id text primary key",
            "organization_id text not null references organizations(organization_id) on delete restrict",
            "billing_account_id text not null references billing_accounts(billing_account_id) on delete restrict",
            "meter text not null",
            "quantity integer not null default 0",
            "external_charge_created boolean not null default false",
            "payload jsonb not null default '{}'::jsonb",
            "created_at timestamptz not null default now()",
        ),
        ("constraint usage_records_quantity_check check (quantity >= 0)",),
        ("create index if not exists usage_records_billing_idx on usage_records (billing_account_id, meter, created_at desc)",),
        True,
    ),
)


DOMAIN_EVENTS: tuple[dict[str, str], ...] = (
    {"event": "packet_created", "table": "packet_events", "external_effect": "none"},
    {"event": "packet_state_changed", "table": "packet_events", "external_effect": "none"},
    {"event": "product_profile_confirmed", "table": "field_provenance", "external_effect": "none"},
    {"event": "document_uploaded_quarantined", "table": "documents", "external_effect": "none"},
    {"event": "field_extracted_draft", "table": "extracted_fields", "external_effect": "none"},
    {"event": "evidence_attached", "table": "evidence_items", "external_effect": "none"},
    {"event": "source_snapshotted", "table": "source_snapshots", "external_effect": "none"},
    {"event": "market_signal_recorded", "table": "market_signals", "external_effect": "none"},
    {"event": "claim_blocked", "table": "blocked_claims", "external_effect": "none"},
    {"event": "score_calculated", "table": "decision_scores", "external_effect": "none"},
    {"event": "review_requested", "table": "review_requests", "external_effect": "none"},
    {"event": "review_finding_recorded", "table": "review_findings", "external_effect": "none"},
    {"event": "report_exported", "table": "reports", "external_effect": "none"},
    {"event": "billing_usage_reserved", "table": "usage_records", "external_effect": "no_live_charge"},
    {"event": "audit_event_recorded", "table": "audit_events", "external_effect": "none"},
)


JSON_MIGRATION_MAP: tuple[dict[str, Any], ...] = (
    {
        "artifact": "system_review_graph/customer_source_packets.json",
        "target_tables": ["trade_readiness_packets", "trade_lanes", "product_profiles", "blocked_claims", "responsibility_paths"],
        "migration_rule": "One source packet becomes a packet, lane, product profile, responsibility path, and blocked claim rows.",
    },
    {
        "artifact": "system_review_graph/evidence_ledger.json",
        "target_tables": ["evidence_items", "evidence_mappers", "documents"],
        "migration_rule": "Evidence rows keep provenance, freshness, AI-permission metadata, and claim support/block maps.",
    },
    {
        "artifact": "data/official_source_registry.json",
        "target_tables": ["source_records", "country_pack_sources", "dataset_connectors"],
        "migration_rule": "Permanent source registry rows become source records and connector policy rows.",
    },
    {
        "artifact": "system_review_graph/policy_source_snapshots.json",
        "target_tables": ["source_snapshots"],
        "migration_rule": "Source hashes and observed dates become source snapshot history.",
    },
    {
        "artifact": "system_review_graph/business_logic_phase_report.json",
        "target_tables": ["decision_scores", "buyer_profiles", "supplier_profiles", "claim_gate_mappers"],
        "migration_rule": "Business scores and evidence ladders become durable decision and gate rows.",
    },
    {
        "artifact": "system_review_graph/review_requests.json",
        "target_tables": ["reviewer_lanes", "review_requests", "review_findings"],
        "migration_rule": "Scoped review links and finding templates become review workflow records.",
    },
    {
        "artifact": "system_review_graph/report_exports.json",
        "target_tables": ["reports", "audit_events"],
        "migration_rule": "Report export records become versioned reports and download audit events.",
    },
    {
        "artifact": "system_review_graph/billing_usage_ledger.json",
        "target_tables": ["billing_accounts", "subscriptions", "usage_records"],
        "migration_rule": "Local reservations become usage records with external_charge_created=false.",
    },
)


POSTGRES_DESIGN_SOURCES = [
    {
        "name": "PostgreSQL constraints documentation",
        "url": "https://www.postgresql.org/docs/current/ddl-constraints.html",
        "used_for": "foreign keys, check constraints, primary keys, and data-integrity rules",
    },
    {
        "name": "PostgreSQL row security documentation",
        "url": "https://www.postgresql.org/docs/current/ddl-rowsecurity.html",
        "used_for": "tenant row-level security policy shape",
    },
    {
        "name": "PostgreSQL indexes documentation",
        "url": "https://www.postgresql.org/docs/current/indexes-intro.html",
        "used_for": "query-path index requirements for packet, evidence, source, review, and audit tables",
    },
]


def _table_sql(table: TableSpec) -> str:
    lines = [*table.columns, *table.constraints]
    rendered = ",\n  ".join(lines)
    return f"create table if not exists {table.name} (\n  {rendered}\n);"


def _rls_sql(table: TableSpec) -> list[str]:
    if not table.organization_scoped:
        return []
    policy_name = f"{table.name}_tenant_isolation"
    predicate = "organization_id = nullif(current_setting('app.current_organization_id', true), '')"
    return [
        f"alter table {table.name} enable row level security;",
        (
            f"create policy {policy_name} on {table.name}\n"
            f"  using ({predicate})\n"
            f"  with check ({predicate});"
        ),
    ]


def render_postgres_schema() -> str:
    sections = [
        "-- Trade Readiness Copilot production domain model.",
        "-- PostgreSQL migration for the first production redevelopment package.",
        "-- Applying this to a hosted database requires the external infrastructure gates.",
        "",
        "begin;",
        "",
    ]
    for table in TABLES:
        sections.append(_table_sql(table))
        sections.extend(table.indexes)
        sections.extend(_rls_sql(table))
        sections.append("")
    sections.extend(["commit;", ""])
    return "\n".join(sections)


def build_seed_fixture() -> dict[str, Any]:
    return {
        "status": "production_data_model_seed_ready_no_external_effects",
        "organization": {"organization_id": "org-importer-demo", "name": "Importer Demo Co."},
        "workspace": {"workspace_id": "workspace-demo-canada", "organization_id": "org-importer-demo"},
        "trade_lane": {
            "trade_lane_id": "lane-vn-ca-food-001",
            "origin_country": "VN",
            "destination_country": "CA",
            "direction": "export",
        },
        "packet": {
            "packet_id": "packet-frozen-tuna-canada-001",
            "state": "document_reviewing",
            "claim_boundary_status": "external_claims_closed",
        },
        "decision_scores": [
            "market_signal_score",
            "evidence_completeness_score",
            "source_freshness_score",
            "buyer_supplier_evidence_score",
            "responsibility_clarity_score",
            "decision_safety_score",
        ],
        "blocked_claims": [
            "tariff_confirmed",
            "cfia_approved",
            "buyer_validated",
            "supplier_verified",
            "ready_to_ship",
        ],
        "proof_boundary": "Seed data proves schema shape only; it does not create real buyer, supplier, customs, payment, or launch evidence.",
    }


def build_production_data_model() -> dict[str, Any]:
    sql = render_postgres_schema()
    foreign_key_count = sql.count(" references ")
    check_constraint_count = sql.count(" check ")
    index_count = sql.count("create index") + sql.count("create unique index")
    rls_tables = [table.name for table in TABLES if table.organization_scoped]
    return {
        "generated_at": _now(),
        "status": STATUS,
        "package_id": "production_data_model",
        "migration_path": "migrations/0002_production_domain_model.sql",
        "table_count": len(TABLES),
        "foreign_key_count": foreign_key_count,
        "check_constraint_count": check_constraint_count,
        "index_count": index_count,
        "row_level_security_table_count": len(rls_tables),
        "domain_event_count": len(DOMAIN_EVENTS),
        "json_migration_map_count": len(JSON_MIGRATION_MAP),
        "tables": [
            {
                "table": table.name,
                "entity": table.entity,
                "organization_scoped": table.organization_scoped,
                "column_count": len(table.columns),
                "constraint_count": len(table.constraints),
                "index_count": len(table.indexes),
            }
            for table in TABLES
        ],
        "row_level_security_tables": rls_tables,
        "domain_events": list(DOMAIN_EVENTS),
        "json_artifact_migration_map": list(JSON_MIGRATION_MAP),
        "seed_fixture": build_seed_fixture(),
        "postgres_design_sources": POSTGRES_DESIGN_SOURCES,
        "hosted_database_ready": False,
        "production_migration_applied": False,
        "external_claims_opened": False,
        "public_launch_ready": False,
        "proof_boundary": (
            "This package proves the production domain schema, migration map, and tenant isolation contract locally. "
            "It does not prove a hosted managed database, live production migration, backup/restore, external review, "
            "public launch, or any customs/trade/payment/legal claim."
        ),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Data Model",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This is the first production rebuild package for Trade Readiness Copilot.",
        "",
        "## Counts",
        "",
        f"- Tables: {payload['table_count']}",
        f"- Foreign keys: {payload['foreign_key_count']}",
        f"- Check constraints: {payload['check_constraint_count']}",
        f"- Indexes: {payload['index_count']}",
        f"- Tenant-scoped RLS tables: {payload['row_level_security_table_count']}",
        f"- Domain events: {payload['domain_event_count']}",
        f"- JSON migration maps: {payload['json_migration_map_count']}",
        "",
        "## Core Tables",
        "",
    ]
    for table in payload["tables"]:
        scoped = "tenant-scoped" if table["organization_scoped"] else "global/reference"
        lines.append(f"- `{table['table']}` maps `{table['entity']}` ({scoped}).")
    lines.extend(["", "## Domain Events", ""])
    for event in payload["domain_events"]:
        lines.append(f"- `{event['event']}` -> `{event['table']}`; external effect: `{event['external_effect']}`.")
    lines.extend(["", "## JSON Artifact Migration Map", ""])
    for row in payload["json_artifact_migration_map"]:
        lines.append(f"- `{row['artifact']}` -> {', '.join(row['target_tables'])}. {row['migration_rule']}")
    lines.extend(
        [
            "",
            "## Proof Boundary",
            "",
            payload["proof_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def write_production_data_model_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    migrations = repo_root / "migrations"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    migrations.mkdir(parents=True, exist_ok=True)

    migration_path = migrations / "0002_production_domain_model.sql"
    manifest_path = graph / "production_data_model_manifest.json"
    seed_path = graph / "production_data_model_seed.json"
    doc_path = docs / "PRODUCTION_DATA_MODEL.md"

    migration_path.write_text(render_postgres_schema(), encoding="utf-8")
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    seed_path.write_text(json.dumps(payload["seed_fixture"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    doc_path.write_text(render_markdown(payload), encoding="utf-8")

    return {
        "migration": migration_path,
        "manifest": manifest_path,
        "seed": seed_path,
        "doc": doc_path,
    }
