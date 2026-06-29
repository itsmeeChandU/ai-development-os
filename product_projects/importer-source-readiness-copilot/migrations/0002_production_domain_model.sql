-- Trade Readiness Copilot production domain model.
-- PostgreSQL migration for the first production redevelopment package.
-- Applying this to a hosted database requires the external infrastructure gates.

begin;

create table if not exists organizations (
  organization_id text primary key,
  name text not null,
  status text not null default 'active',
  billing_account_id text,
  retention_policy_id text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organizations_status_check check (status in ('active','suspended','archived'))
);

create table if not exists users (
  user_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  email text not null,
  status text not null default 'active',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint users_status_check check (status in ('invited','active','disabled','archived'))
);
create unique index if not exists users_email_unique on users (lower(email))
alter table users enable row level security;
create policy users_tenant_isolation on users
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists roles (
  role_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  name text not null,
  permissions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
create unique index if not exists roles_org_name_unique on roles (organization_id, name)
alter table roles enable row level security;
create policy roles_tenant_isolation on roles
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists user_roles (
  user_id text not null references users(user_id) on delete cascade,
  role_id text not null references roles(role_id) on delete cascade,
  organization_id text not null references organizations(organization_id) on delete restrict,
  created_at timestamptz not null default now(),
  primary key (user_id, role_id)
);
create index if not exists user_roles_org_idx on user_roles (organization_id)
alter table user_roles enable row level security;
create policy user_roles_tenant_isolation on user_roles
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists workspaces (
  workspace_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  name text not null,
  client_id text,
  status text not null default 'active',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint workspaces_status_check check (status in ('active','archived'))
);
create index if not exists workspaces_org_idx on workspaces (organization_id, status)
alter table workspaces enable row level security;
create policy workspaces_tenant_isolation on workspaces
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists incoterm_records (
  incoterm_id text primary key,
  code text not null,
  responsibility_summary text not null,
  confirmation_status text not null default 'needs_user_confirmation',
  payload jsonb not null default '{}'::jsonb,
  constraint incoterm_code_check check (length(code) between 2 and 10),
  constraint incoterm_confirmation_status_check check (confirmation_status in ('needs_user_confirmation','confirmed','not_applicable'))
);
create unique index if not exists incoterm_records_code_unique on incoterm_records (code)

create table if not exists trade_lanes (
  trade_lane_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  origin_country text not null,
  destination_country text not null,
  direction text not null,
  incoterm_id text references incoterm_records(incoterm_id),
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint trade_lanes_direction_check check (direction in ('import','export','both','exploring'))
);
create index if not exists trade_lanes_route_idx on trade_lanes (organization_id, origin_country, destination_country, direction)
alter table trade_lanes enable row level security;
create policy trade_lanes_tenant_isolation on trade_lanes
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists trade_readiness_packets (
  packet_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  workspace_id text not null references workspaces(workspace_id) on delete restrict,
  trade_lane_id text not null references trade_lanes(trade_lane_id) on delete restrict,
  state text not null,
  claim_boundary_status text not null default 'external_claims_closed',
  version integer not null default 1,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint packet_state_check check (state in ('draft','starter_ready','research_ready','evidence_collecting','document_reviewing','source_checking','decision_preparing','reviewer_ready','expert_reviewing','customer_report_ready','paid_packet_ready','archived')),
  constraint packet_claim_boundary_check check (claim_boundary_status in ('external_claims_closed','reviewer_scope_limited','approved_for_scope'))
);
create index if not exists trade_readiness_packets_workspace_idx on trade_readiness_packets (workspace_id, state)
create index if not exists trade_readiness_packets_org_state_idx on trade_readiness_packets (organization_id, state)
alter table trade_readiness_packets enable row level security;
create policy trade_readiness_packets_tenant_isolation on trade_readiness_packets
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists packet_events (
  event_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  event_type text not null,
  actor_id text references users(user_id),
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists packet_events_packet_idx on packet_events (packet_id, created_at)
alter table packet_events enable row level security;
create policy packet_events_tenant_isolation on packet_events
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists product_profiles (
  product_profile_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  name text not null,
  category text,
  intended_use text,
  hs_candidate text,
  confirmation_status text not null default 'needs_user_confirmation',
  payload jsonb not null default '{}'::jsonb,
  constraint product_confirmation_status_check check (confirmation_status in ('user_input','parser_draft','needs_user_confirmation','source_backed','reviewer_verified'))
);
create index if not exists product_profiles_packet_idx on product_profiles (packet_id)
alter table product_profiles enable row level security;
create policy product_profiles_tenant_isolation on product_profiles
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists country_packs (
  country_pack_id text primary key,
  country_code text not null,
  direction text not null,
  coverage_level text not null,
  reviewer_required boolean not null default true,
  refresh_cadence jsonb not null default '{}'::jsonb,
  claim_boundaries jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint country_packs_direction_check check (direction in ('import','export','both','generic')),
  constraint country_packs_coverage_check check (coverage_level in ('full','partial','reference_only','generic'))
);
create unique index if not exists country_packs_unique on country_packs (country_code, direction)

create table if not exists source_records (
  source_id text primary key,
  country_pack_id text references country_packs(country_pack_id) on delete set null,
  canonical_url text not null,
  source_type text not null,
  authority_level text not null default 'official_reference',
  allowed_use text not null default 'reference_route_only',
  fetch_mode text not null default 'manual_check',
  terms_status text not null default 'not_checked',
  claim_boundary text not null,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint source_records_url_check check (canonical_url like 'https://%'),
  constraint source_records_terms_check check (terms_status in ('not_checked','checked_allowed','manual_only','restricted','unknown'))
);
create index if not exists source_records_type_idx on source_records (source_type, authority_level)

create table if not exists source_snapshots (
  snapshot_id text primary key,
  source_id text not null references source_records(source_id) on delete cascade,
  content_hash text not null,
  fetched_at timestamptz not null,
  diff_status text not null default 'not_checked',
  review_required boolean not null default true,
  payload jsonb not null default '{}'::jsonb,
  constraint source_snapshots_diff_check check (diff_status in ('not_checked','refresh_attempted_not_verified','checked_current_reference_only','changed_minor','changed_material','source_unavailable','stale','review_required'))
);
create index if not exists source_snapshots_source_idx on source_snapshots (source_id, fetched_at desc)

create table if not exists research_intakes (
  research_intake_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text references trade_readiness_packets(packet_id) on delete cascade,
  phase text not null,
  question text not null,
  required_depth text not null,
  owner text not null,
  status text not null default 'open',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint research_intakes_status_check check (status in ('open','in_progress','answered','blocked','archived'))
);
create index if not exists research_intakes_packet_idx on research_intakes (packet_id, status)
alter table research_intakes enable row level security;
create policy research_intakes_tenant_isolation on research_intakes
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists dataset_connectors (
  dataset_connector_id text primary key,
  source_id text not null references source_records(source_id) on delete restrict,
  access_mode text not null,
  license_status text not null default 'not_checked',
  credential_status text not null default 'not_required',
  payload jsonb not null default '{}'::jsonb,
  constraint dataset_connectors_access_check check (access_mode in ('manual_download','api','csv_import','browser_reference','licensed_dataset')),
  constraint dataset_connectors_license_check check (license_status in ('not_checked','allowed','restricted','manual_only','needs_contract'))
);

create table if not exists country_pack_sources (
  country_pack_source_id text primary key,
  country_pack_id text not null references country_packs(country_pack_id) on delete cascade,
  source_id text not null references source_records(source_id) on delete restrict,
  source_area text not null,
  claim_boundary text not null,
  payload jsonb not null default '{}'::jsonb
);
create unique index if not exists country_pack_sources_unique on country_pack_sources (country_pack_id, source_id, source_area)

create table if not exists documents (
  document_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  storage_key text not null,
  quarantine_status text not null default 'quarantined',
  classification text,
  sha256 text,
  uploaded_by text references users(user_id),
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint documents_quarantine_status_check check (quarantine_status in ('quarantined','scan_pending','scan_passed','scan_failed','deleted'))
);
create index if not exists documents_packet_idx on documents (packet_id, quarantine_status)
alter table documents enable row level security;
create policy documents_tenant_isolation on documents
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists extracted_fields (
  field_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  document_id text not null references documents(document_id) on delete cascade,
  field_name text not null,
  value text,
  confidence numeric(5,2) not null default 0,
  confirmation_status text not null default 'parser_draft',
  payload jsonb not null default '{}'::jsonb,
  constraint extracted_fields_confidence_check check (confidence >= 0 and confidence <= 100),
  constraint extracted_fields_confirmation_check check (confirmation_status in ('parser_draft','needs_user_confirmation','user_confirmed','rejected','reviewer_verified'))
);
create index if not exists extracted_fields_document_idx on extracted_fields (document_id, field_name)
alter table extracted_fields enable row level security;
create policy extracted_fields_tenant_isolation on extracted_fields
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists field_provenance (
  field_provenance_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  field_id text not null references extracted_fields(field_id) on delete cascade,
  mode text not null,
  source_reference text,
  reviewer_id text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint field_provenance_mode_check check (mode in ('user_input','parser_draft','official_source_reference','system_derived','reviewer_verified'))
);
create index if not exists field_provenance_field_idx on field_provenance (field_id, mode)
alter table field_provenance enable row level security;
create policy field_provenance_tenant_isolation on field_provenance
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists evidence_items (
  evidence_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  document_id text references documents(document_id) on delete set null,
  source_snapshot_id text references source_snapshots(snapshot_id) on delete set null,
  type text not null,
  provenance text not null,
  confidence text not null default 'low',
  freshness text not null default 'unknown',
  review_required boolean not null default true,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint evidence_items_type_check check (type in ('document','official_source','market_data','buyer_signal','supplier_signal','reviewer_finding','user_input','system_derived')),
  constraint evidence_items_provenance_check check (provenance in ('user_input','parser_draft','official_source_reference','system_derived','reviewer_verified')),
  constraint evidence_items_freshness_check check (freshness in ('current','stale','unknown'))
);
create index if not exists evidence_items_packet_idx on evidence_items (packet_id, type, freshness)
alter table evidence_items enable row level security;
create policy evidence_items_tenant_isolation on evidence_items
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists evidence_mappers (
  evidence_mapper_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  evidence_id text not null references evidence_items(evidence_id) on delete cascade,
  supports_claim text,
  blocks_claim text,
  payload jsonb not null default '{}'::jsonb
);
create index if not exists evidence_mappers_evidence_idx on evidence_mappers (evidence_id)
alter table evidence_mappers enable row level security;
create policy evidence_mappers_tenant_isolation on evidence_mappers
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists market_signals (
  market_signal_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  signal_level text not null,
  confidence text not null,
  source_refs jsonb not null default '[]'::jsonb,
  limitation text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint market_signals_signal_level_check check (signal_level in ('strong_research_signal','moderate_research_signal','weak_research_signal','insufficient_data')),
  constraint market_signals_confidence_check check (confidence in ('no_data','research_plan','source_backed','document_backed','reviewer_verified'))
);
create index if not exists market_signals_packet_idx on market_signals (packet_id, confidence)
alter table market_signals enable row level security;
create policy market_signals_tenant_isolation on market_signals
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists market_signal_sources (
  market_signal_source_id text primary key,
  market_signal_id text not null references market_signals(market_signal_id) on delete cascade,
  source_id text not null references source_records(source_id) on delete restrict,
  metric text not null,
  limitation text not null,
  payload jsonb not null default '{}'::jsonb
);
create index if not exists market_signal_sources_signal_idx on market_signal_sources (market_signal_id, source_id)

create table if not exists buyer_profiles (
  buyer_profile_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  evidence_level text not null default 'lead_discovered',
  claim_status text not null default 'not_validated',
  payload jsonb not null default '{}'::jsonb,
  constraint buyer_profiles_evidence_level_check check (evidence_level in ('lead_discovered','contact_identified','outreach_prepared','contact_attempted','reply_received','meeting_held','sample_requested','loi_received','po_or_paid_order_received')),
  constraint buyer_profiles_claim_status_check check (claim_status in ('not_validated','evidence_collected','review_required'))
);
create index if not exists buyer_profiles_packet_idx on buyer_profiles (packet_id, evidence_level)
alter table buyer_profiles enable row level security;
create policy buyer_profiles_tenant_isolation on buyer_profiles
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists buyer_evidence_events (
  buyer_evidence_event_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  buyer_profile_id text not null references buyer_profiles(buyer_profile_id) on delete cascade,
  evidence_id text references evidence_items(evidence_id) on delete set null,
  event_type text not null,
  event_date date,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists buyer_evidence_events_profile_idx on buyer_evidence_events (buyer_profile_id, event_type)
alter table buyer_evidence_events enable row level security;
create policy buyer_evidence_events_tenant_isolation on buyer_evidence_events
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists supplier_profiles (
  supplier_profile_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  evidence_level text not null default 'supplier_named',
  claim_status text not null default 'not_verified',
  payload jsonb not null default '{}'::jsonb,
  constraint supplier_profiles_evidence_level_check check (evidence_level in ('supplier_named','business_registration_attached','export_registration_or_license_attached','product_spec_attached','certificate_attached','inspection_report_attached','prior_shipment_evidence_attached','commercial_reference_attached','reviewer_assessed')),
  constraint supplier_profiles_claim_status_check check (claim_status in ('not_verified','evidence_collected','review_required'))
);
create index if not exists supplier_profiles_packet_idx on supplier_profiles (packet_id, evidence_level)
alter table supplier_profiles enable row level security;
create policy supplier_profiles_tenant_isolation on supplier_profiles
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists supplier_evidence_events (
  supplier_evidence_event_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  supplier_profile_id text not null references supplier_profiles(supplier_profile_id) on delete cascade,
  evidence_id text references evidence_items(evidence_id) on delete set null,
  event_type text not null,
  event_date date,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists supplier_evidence_events_profile_idx on supplier_evidence_events (supplier_profile_id, event_type)
alter table supplier_evidence_events enable row level security;
create policy supplier_evidence_events_tenant_isolation on supplier_evidence_events
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists responsibility_paths (
  responsibility_path_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  importer_of_record text,
  incoterms text,
  clarity_status text not null default 'unknown',
  warnings jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  constraint responsibility_paths_clarity_check check (clarity_status in ('clear','partial','unknown','blocked'))
);
create index if not exists responsibility_paths_packet_idx on responsibility_paths (packet_id, clarity_status)
alter table responsibility_paths enable row level security;
create policy responsibility_paths_tenant_isolation on responsibility_paths
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists blocked_claims (
  blocked_claim_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  claim text not null,
  reason text not null,
  required_evidence jsonb not null default '[]'::jsonb,
  required_reviewer_lane text,
  status text not null default 'blocked',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint blocked_claims_status_check check (status in ('blocked','needs_changes','approved_for_scope','expired'))
);
create index if not exists blocked_claims_packet_idx on blocked_claims (packet_id, status)
alter table blocked_claims enable row level security;
create policy blocked_claims_tenant_isolation on blocked_claims
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists claim_gate_mappers (
  claim_gate_mapper_id text primary key,
  claim_type text not null,
  required_evidence jsonb not null default '[]'::jsonb,
  required_source_ids jsonb not null default '[]'::jsonb,
  required_reviewer_lane text,
  blocked_language jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb
);
create unique index if not exists claim_gate_mappers_claim_type_unique on claim_gate_mappers (claim_type)

create table if not exists decision_scores (
  score_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  score_name text not null,
  label text not null,
  reason text not null,
  next_action text not null,
  blocking_fields jsonb not null default '[]'::jsonb,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint decision_scores_name_check check (score_name in ('market_signal_score','evidence_completeness_score','source_freshness_score','buyer_supplier_evidence_score','responsibility_clarity_score','decision_safety_score')),
  constraint decision_scores_label_check check (label in ('green','yellow','red','grey'))
);
create index if not exists decision_scores_packet_idx on decision_scores (packet_id, score_name)
alter table decision_scores enable row level security;
create policy decision_scores_tenant_isolation on decision_scores
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists reviewer_lanes (
  reviewer_lane_id text primary key,
  scope text not null,
  required_credentials jsonb not null default '[]'::jsonb,
  gate_can_open text not null,
  payload jsonb not null default '{}'::jsonb
);

create table if not exists review_requests (
  review_request_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  reviewer_lane_id text not null references reviewer_lanes(reviewer_lane_id) on delete restrict,
  status text not null default 'requested',
  scope text not null,
  review_token_hash text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint review_requests_status_check check (status in ('requested','in_review','needs_changes','approved_for_scope','blocked','expired'))
);
create index if not exists review_requests_packet_idx on review_requests (packet_id, status)
alter table review_requests enable row level security;
create policy review_requests_tenant_isolation on review_requests
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists review_findings (
  finding_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  review_request_id text not null references review_requests(review_request_id) on delete cascade,
  severity text not null,
  decision text not null,
  required_changes jsonb not null default '[]'::jsonb,
  evidence_attachment_id text references evidence_items(evidence_id) on delete set null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint review_findings_severity_check check (severity in ('info','low','medium','high','critical')),
  constraint review_findings_decision_check check (decision in ('approved_for_scope','needs_changes','blocked'))
);
create index if not exists review_findings_request_idx on review_findings (review_request_id, decision)
alter table review_findings enable row level security;
create policy review_findings_tenant_isolation on review_findings
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists expert_finding_sources (
  expert_finding_source_id text primary key,
  finding_id text not null references review_findings(finding_id) on delete cascade,
  source_id text references source_records(source_id) on delete set null,
  review_scope text not null,
  payload jsonb not null default '{}'::jsonb
);
create index if not exists expert_finding_sources_finding_idx on expert_finding_sources (finding_id)

create table if not exists reports (
  report_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  packet_id text not null references trade_readiness_packets(packet_id) on delete cascade,
  report_type text not null,
  watermark text not null default 'draft',
  version integer not null default 1,
  storage_key text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint reports_watermark_check check (watermark in ('draft','reviewed','final'))
);
create index if not exists reports_packet_idx on reports (packet_id, report_type, version)
alter table reports enable row level security;
create policy reports_tenant_isolation on reports
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists audit_events (
  audit_event_id text primary key,
  organization_id text references organizations(organization_id) on delete set null,
  actor_id text references users(user_id) on delete set null,
  event_type text not null,
  entity_type text not null,
  entity_id text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists audit_events_org_time_idx on audit_events (organization_id, created_at desc)
alter table audit_events enable row level security;
create policy audit_events_tenant_isolation on audit_events
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists billing_accounts (
  billing_account_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  processor_customer_id text,
  live_mode_enabled boolean not null default false,
  status text not null default 'disabled',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint billing_accounts_status_check check (status in ('disabled','test_mode','review_required','live_enabled'))
);
create unique index if not exists billing_accounts_org_unique on billing_accounts (organization_id)
alter table billing_accounts enable row level security;
create policy billing_accounts_tenant_isolation on billing_accounts
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists subscriptions (
  subscription_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  billing_account_id text not null references billing_accounts(billing_account_id) on delete restrict,
  tier text not null,
  status text not null default 'inactive',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint subscriptions_status_check check (status in ('inactive','trial','active','past_due','cancelled'))
);
create index if not exists subscriptions_billing_idx on subscriptions (billing_account_id, status)
alter table subscriptions enable row level security;
create policy subscriptions_tenant_isolation on subscriptions
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

create table if not exists usage_records (
  usage_record_id text primary key,
  organization_id text not null references organizations(organization_id) on delete restrict,
  billing_account_id text not null references billing_accounts(billing_account_id) on delete restrict,
  meter text not null,
  quantity integer not null default 0,
  external_charge_created boolean not null default false,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint usage_records_quantity_check check (quantity >= 0)
);
create index if not exists usage_records_billing_idx on usage_records (billing_account_id, meter, created_at desc)
alter table usage_records enable row level security;
create policy usage_records_tenant_isolation on usage_records
  using (organization_id = nullif(current_setting('app.current_organization_id', true), ''))
  with check (organization_id = nullif(current_setting('app.current_organization_id', true), ''));

commit;
