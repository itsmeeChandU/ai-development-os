-- Importer Source Readiness Copilot product runtime schema.
-- SQLite-compatible development schema; PostgreSQL production migration should
-- preserve the same entity names and ownership constraints.

create table if not exists users (
  user_id text primary key,
  email text not null,
  role text not null,
  organization_id text not null,
  payload_json text not null
);

create table if not exists organizations (
  organization_id text primary key,
  name text not null,
  payload_json text not null
);

create table if not exists memberships (
  user_id text not null,
  organization_id text not null,
  role text not null,
  payload_json text not null,
  primary key (user_id, organization_id)
);

create table if not exists source_packets (
  packet_id text primary key,
  status text,
  payload_json text not null
);

create table if not exists evidence_items (
  evidence_id text primary key,
  packet_id text,
  ledger_status text,
  payload_json text not null
);

create table if not exists official_sources (
  source_id text primary key,
  jurisdiction text,
  payload_json text not null
);

create table if not exists claims (
  claim_id text primary key,
  packet_id text,
  claim_type text,
  status text,
  payload_json text not null
);

create table if not exists blockers (
  blocker_id text primary key,
  packet_id text,
  group_id text,
  status text,
  payload_json text not null
);

create table if not exists review_runs (
  run_id text primary key,
  packet_id text,
  review_type text,
  status text,
  payload_json text not null
);

create table if not exists review_requests (
  review_request_id text primary key,
  packet_id text,
  review_type text,
  status text,
  token text,
  payload_json text not null
);

create table if not exists human_review_findings (
  finding_id text primary key,
  review_request_id text,
  packet_id text,
  decision text,
  payload_json text not null
);

create table if not exists gate_decisions (
  decision_id text primary key,
  packet_id text,
  gate text,
  status text,
  payload_json text not null
);

create table if not exists report_exports (
  report_id text primary key,
  packet_id text,
  report_type text,
  format text,
  status text,
  payload_json text not null
);

create table if not exists data_deletion_requests (
  request_id text primary key,
  organization_id text,
  status text,
  payload_json text not null
);

create table if not exists audit_events (
  event_id text primary key,
  organization_id text,
  entity_id text,
  event_type text,
  payload_json text not null
);
