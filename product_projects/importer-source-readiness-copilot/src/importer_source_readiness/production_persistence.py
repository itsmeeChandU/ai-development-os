"""Executable local production-domain persistence proof.

This module maps today's generated packet artifacts into normalized production
rows and writes a SQLite proof store with the same entity boundaries as the
Postgres migration. The hosted Postgres database remains an external gate; this
proof makes the current local packet state loadable and auditable.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_persistence_ready_local_domain_rows_external_db_gate_closed"
ORG_ID = "org-importer-demo"
WORKSPACE_ID = "workspace-demo-canada"

TABLE_ORDER = (
    "organizations",
    "users",
    "workspaces",
    "trade_lanes",
    "trade_readiness_packets",
    "product_profiles",
    "country_packs",
    "source_records",
    "source_snapshots",
    "evidence_items",
    "blocked_claims",
    "claim_gate_mappers",
    "decision_scores",
    "review_requests",
    "reports",
    "audit_events",
)

ORG_SCOPED_TABLES = {
    "users",
    "workspaces",
    "trade_lanes",
    "trade_readiness_packets",
    "product_profiles",
    "evidence_items",
    "blocked_claims",
    "claim_gate_mappers",
    "decision_scores",
    "review_requests",
    "reports",
    "audit_events",
}

SQLITE_SCHEMAS = {
    "organizations": (
        "organization_id text primary key",
        "name text not null",
        "status text not null",
        "payload_json text not null",
    ),
    "users": (
        "user_id text primary key",
        "organization_id text not null",
        "email text not null",
        "status text not null",
        "payload_json text not null",
    ),
    "workspaces": (
        "workspace_id text primary key",
        "organization_id text not null",
        "name text not null",
        "status text not null",
        "payload_json text not null",
    ),
    "trade_lanes": (
        "trade_lane_id text primary key",
        "organization_id text not null",
        "origin_country text not null",
        "destination_country text not null",
        "direction text not null",
        "payload_json text not null",
    ),
    "trade_readiness_packets": (
        "packet_id text primary key",
        "organization_id text not null",
        "workspace_id text not null",
        "trade_lane_id text not null",
        "state text not null",
        "claim_boundary_status text not null",
        "payload_json text not null",
    ),
    "product_profiles": (
        "product_profile_id text primary key",
        "organization_id text not null",
        "packet_id text not null",
        "name text not null",
        "category text",
        "hs_candidate text",
        "confirmation_status text not null",
        "payload_json text not null",
    ),
    "country_packs": (
        "country_pack_id text primary key",
        "country_code text not null",
        "direction text not null",
        "coverage_level text not null",
        "reviewer_required integer not null",
        "payload_json text not null",
    ),
    "source_records": (
        "source_id text primary key",
        "country_pack_id text",
        "canonical_url text not null",
        "source_type text not null",
        "authority_level text not null",
        "payload_json text not null",
    ),
    "source_snapshots": (
        "snapshot_id text primary key",
        "source_id text not null",
        "packet_id text",
        "source_state text not null",
        "diff_status text not null",
        "fetched_at text",
        "payload_json text not null",
    ),
    "evidence_items": (
        "evidence_id text primary key",
        "organization_id text not null",
        "packet_id text not null",
        "evidence_type text not null",
        "provenance text not null",
        "freshness text not null",
        "review_required integer not null",
        "payload_json text not null",
    ),
    "blocked_claims": (
        "blocked_claim_id text primary key",
        "organization_id text not null",
        "packet_id text not null",
        "claim_type text not null",
        "status text not null",
        "unsafe_to_bypass integer not null",
        "payload_json text not null",
    ),
    "claim_gate_mappers": (
        "claim_gate_mapper_id text primary key",
        "organization_id text not null",
        "packet_id text not null",
        "claim_type text not null",
        "can_show_claim integer not null",
        "required_reviewer_lane text",
        "payload_json text not null",
    ),
    "decision_scores": (
        "decision_score_id text primary key",
        "organization_id text not null",
        "packet_id text not null",
        "score_type text not null",
        "label text not null",
        "value integer not null",
        "cap integer",
        "payload_json text not null",
    ),
    "review_requests": (
        "review_request_id text primary key",
        "organization_id text not null",
        "packet_id text not null",
        "reviewer_lane_id text not null",
        "status text not null",
        "payload_json text not null",
    ),
    "reports": (
        "report_id text primary key",
        "organization_id text not null",
        "packet_id text not null",
        "report_type text not null",
        "status text not null",
        "path text not null",
        "payload_json text not null",
    ),
    "audit_events": (
        "audit_event_id text primary key",
        "organization_id text not null",
        "entity_type text not null",
        "entity_id text not null",
        "event_type text not null",
        "created_at text not null",
        "payload_json text not null",
    ),
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _country_code(value: Any) -> str:
    text = _text(value).upper()
    return {
        "CANADA": "CA",
        "CA": "CA",
        "INDIA": "IN",
        "IN": "IN",
        "VIETNAM": "VN",
        "VIET NAM": "VN",
        "VN": "VN",
    }.get(text, text or "GENERIC")


def _direction(packet: dict[str, Any]) -> str:
    explicit = _text(packet.get("trade_direction") or packet.get("direction")).lower()
    if explicit in {"import", "export", "both", "exploring"}:
        return explicit
    destination = _country_code(packet.get("destination_country"))
    origin = _country_code(packet.get("origin_country"))
    if destination == "CA" and origin != "CA":
        return "export"
    if origin == "CA" and destination != "CA":
        return "export"
    return "exploring"


def _json_safe_payload(row: dict[str, Any], *, redact_keys: set[str] | None = None) -> dict[str, Any]:
    redact = redact_keys or set()
    return {key: ("redacted_for_production_persistence" if key in redact else value) for key, value in row.items()}


def _source_to_pack_map(country_packs: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for pack in country_packs:
        for source_id in pack.get("source_ids", []):
            mapping[_text(source_id)] = _text(pack.get("country_pack_id"))
    return mapping


def _runtime_rows(runtime: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = runtime.get(key, [])
    return rows if isinstance(rows, list) else []


def _packet_runs_by_id(packet_engine: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {_text(run.get("packet_id")): run for run in packet_engine.get("packet_runs", []) if isinstance(run, dict)}


def _organization_rows(runtime: dict[str, Any], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for org in _runtime_rows(runtime, "organizations"):
        org_id = _text(org.get("id") or org.get("organization_id")) or ORG_ID
        rows[org_id] = {
            "organization_id": org_id,
            "name": _text(org.get("name")) or org_id,
            "status": "active",
            "payload": org,
        }
    for packet in packets:
        org_id = _text(packet.get("organization_id")) or ORG_ID
        rows.setdefault(
            org_id,
            {
                "organization_id": org_id,
                "name": org_id,
                "status": "active",
                "payload": {"source": "packet_default"},
            },
        )
    return list(rows.values())


def _user_rows(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for user in _runtime_rows(runtime, "users"):
        user_id = _text(user.get("id") or user.get("user_id"))
        if not user_id:
            continue
        rows.append(
            {
                "user_id": user_id,
                "organization_id": _text(user.get("organization_id")) or ORG_ID,
                "email": _text(user.get("email")) or "unknown@example.local",
                "status": "active",
                "payload": _json_safe_payload(user, redact_keys={"session_token"}),
            }
        )
    return rows


def _workspace_rows(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for packet in packets:
        organization_id = _text(packet.get("organization_id")) or ORG_ID
        workspace_id = _text(packet.get("workspace_id")) or WORKSPACE_ID
        rows[workspace_id] = {
            "workspace_id": workspace_id,
            "organization_id": organization_id,
            "name": "Canada trade readiness workspace",
            "status": "active",
            "payload": {"packet_ids": [packet.get("packet_id")]},
        }
    return list(rows.values())


def _packet_domain_rows(
    packets: list[dict[str, Any]],
    packet_runs: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    lanes: list[dict[str, Any]] = []
    packet_rows: list[dict[str, Any]] = []
    product_profiles: list[dict[str, Any]] = []
    for packet in packets:
        packet_id = _text(packet.get("packet_id"))
        if not packet_id:
            continue
        organization_id = _text(packet.get("organization_id")) or ORG_ID
        workspace_id = _text(packet.get("workspace_id")) or WORKSPACE_ID
        lane_id = f"lane:{packet_id}"
        run = packet_runs.get(packet_id, {})
        lanes.append(
            {
                "trade_lane_id": lane_id,
                "organization_id": organization_id,
                "origin_country": _country_code(packet.get("origin_country")),
                "destination_country": _country_code(packet.get("destination_country")),
                "direction": _direction(packet),
                "payload": {
                    "origin_country_raw": packet.get("origin_country"),
                    "destination_country_raw": packet.get("destination_country"),
                    "direction_provenance": run.get("trade_direction_provenance", "derived_from_packet"),
                },
            }
        )
        packet_rows.append(
            {
                "packet_id": packet_id,
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "trade_lane_id": lane_id,
                "state": _text(run.get("state")) or "reviewer_ready",
                "claim_boundary_status": "external_claims_closed",
                "payload": {
                    "status": packet.get("status"),
                    "blocked_claims": packet.get("blocked_claims", []),
                    "next_valid_move": run.get("next_valid_move") or packet.get("next_valid_move"),
                    "reviewer_ready_not_approved": bool(run.get("reviewer_ready_not_approved", True)),
                },
            }
        )
        product_profiles.append(
            {
                "product_profile_id": f"product:{packet_id}",
                "organization_id": organization_id,
                "packet_id": packet_id,
                "name": _text(packet.get("product_name")) or "Unnamed product",
                "category": _text(packet.get("product_category")),
                "hs_candidate": _text(packet.get("hs_candidate")),
                "confirmation_status": "user_input",
                "payload": {
                    "intended_use": packet.get("intended_use"),
                    "regulated_product_suspicion": packet.get("regulated_product_suspicion", ""),
                },
            }
        )
    return lanes, packet_rows, product_profiles


def _country_pack_rows(country_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "country_pack_id": _text(row.get("country_pack_id")),
            "country_code": _text(row.get("country_code")),
            "direction": _text(row.get("direction")),
            "coverage_level": _text(row.get("coverage_level")),
            "reviewer_required": 1 if row.get("reviewer_required") else 0,
            "payload": row,
        }
        for row in country_payload.get("country_packs", [])
        if _text(row.get("country_pack_id"))
    ]


def _source_record_rows(country_payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_to_pack = _source_to_pack_map(country_payload.get("country_packs", []))
    rows = []
    for row in country_payload.get("source_lifecycle", []):
        source_id = _text(row.get("source_id"))
        if not source_id:
            continue
        rows.append(
            {
                "source_id": source_id,
                "country_pack_id": source_to_pack.get(source_id, ""),
                "canonical_url": _text(row.get("canonical_url")),
                "source_type": _text(row.get("source_type")) or "official_or_primary_reference",
                "authority_level": _text(row.get("authority_level")) or "official_reference",
                "payload": row,
            }
        )
    return rows


def _source_snapshot_rows(country_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in country_payload.get("source_lifecycle", []):
        source_id = _text(row.get("source_id"))
        if not source_id:
            continue
        rows.append(
            {
                "snapshot_id": f"source-snapshot:{source_id}:{_text(row.get('refresh_run_id')) or 'baseline'}",
                "source_id": source_id,
                "packet_id": _text(row.get("refresh_packet_id")),
                "source_state": _text(row.get("source_state")),
                "diff_status": _text(row.get("source_state")),
                "fetched_at": _text(row.get("last_checked_at")),
                "payload": row,
            }
        )
    for row in country_payload.get("source_snapshot_history", []):
        snapshot_id = _text(row.get("snapshot_id"))
        if not snapshot_id:
            continue
        rows.append(
            {
                "snapshot_id": snapshot_id,
                "source_id": _text(row.get("source_id")),
                "packet_id": _text(row.get("packet_id")),
                "source_state": _text(row.get("source_state")),
                "diff_status": _text(row.get("source_state")),
                "fetched_at": _text(row.get("generated_at")),
                "payload": row,
            }
        )
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped[row["snapshot_id"]] = row
    return list(deduped.values())


def _evidence_rows(evidence_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in evidence_ledger.get("rows", []):
        evidence_id = _text(row.get("evidence_id"))
        if not evidence_id:
            continue
        rows.append(
            {
                "evidence_id": evidence_id,
                "organization_id": _text(row.get("organization_id")) or ORG_ID,
                "packet_id": _text(row.get("packet_id")),
                "evidence_type": _text(row.get("evidence_type")) or "unknown",
                "provenance": _text(row.get("provenance") or row.get("quality_status")) or "source_reference",
                "freshness": _text(row.get("freshness_status") or row.get("quality_status")) or "unknown",
                "review_required": 1 if row.get("review_required", True) else 0,
                "payload": row,
            }
        )
    return rows


def _blocked_claim_rows(runtime: dict[str, Any], packet_engine: dict[str, Any], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_org = {_text(packet.get("packet_id")): _text(packet.get("organization_id")) or ORG_ID for packet in packets}
    rows: dict[str, dict[str, Any]] = {}
    for run in packet_engine.get("packet_runs", []):
        packet_id = _text(run.get("packet_id"))
        for blocked in run.get("blocked_claims", []):
            claim = _text(blocked.get("claim"))
            if not packet_id or not claim:
                continue
            row_id = f"blocked-claim:{packet_id}:{claim}"
            rows[row_id] = {
                "blocked_claim_id": row_id,
                "organization_id": packet_org.get(packet_id, ORG_ID),
                "packet_id": packet_id,
                "claim_type": claim,
                "status": _text(blocked.get("status")) or "blocked",
                "unsafe_to_bypass": 1 if blocked.get("unsafe_to_bypass", True) else 0,
                "payload": blocked,
            }
    for claim in _runtime_rows(runtime, "claims"):
        status = _text(claim.get("status"))
        packet_id = _text(claim.get("packet_id"))
        claim_type = _text(claim.get("claim_type"))
        if not packet_id or not claim_type or "blocked" not in status:
            continue
        row_id = f"blocked-runtime-claim:{claim.get('id') or packet_id + ':' + claim_type}"
        rows.setdefault(
            row_id,
            {
                "blocked_claim_id": row_id,
                "organization_id": packet_org.get(packet_id, ORG_ID),
                "packet_id": packet_id,
                "claim_type": claim_type,
                "status": status,
                "unsafe_to_bypass": 1,
                "payload": claim,
            },
        )
    return list(rows.values())


def _claim_gate_rows(claim_payload: dict[str, Any], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_org = {_text(packet.get("packet_id")): _text(packet.get("organization_id")) or ORG_ID for packet in packets}
    rows = []
    for decision in claim_payload.get("decisions", []):
        decision_id = _text(decision.get("claim_gate_decision_id"))
        packet_id = _text(decision.get("packet_id"))
        if not decision_id or not packet_id:
            continue
        rows.append(
            {
                "claim_gate_mapper_id": decision_id,
                "organization_id": packet_org.get(packet_id, ORG_ID),
                "packet_id": packet_id,
                "claim_type": _text(decision.get("claim_type")),
                "can_show_claim": 1 if decision.get("can_show_claim") else 0,
                "required_reviewer_lane": _text(decision.get("required_reviewer_lane")),
                "payload": decision,
            }
        )
    return rows


def _decision_score_rows(score_payload: dict[str, Any], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_org = {_text(packet.get("packet_id")): _text(packet.get("organization_id")) or ORG_ID for packet in packets}
    rows = []
    for score in score_payload.get("records", []):
        score_id = _text(score.get("decision_score_id"))
        packet_id = _text(score.get("packet_id"))
        if not score_id or not packet_id:
            continue
        rows.append(
            {
                "decision_score_id": score_id,
                "organization_id": packet_org.get(packet_id, ORG_ID),
                "packet_id": packet_id,
                "score_type": _text(score.get("score")),
                "label": _text(score.get("label")),
                "value": int(score.get("score_value") or score.get("raw_points") or 0),
                "cap": int(score.get("score_cap") or 0),
                "payload": score,
            }
        )
    return rows


def _review_request_rows(runtime: dict[str, Any], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_org = {_text(packet.get("packet_id")): _text(packet.get("organization_id")) or ORG_ID for packet in packets}
    rows = []
    for request in _runtime_rows(runtime, "review_requests"):
        request_id = _text(request.get("id") or request.get("review_request_id"))
        packet_id = _text(request.get("packet_id"))
        if not request_id or not packet_id:
            continue
        rows.append(
            {
                "review_request_id": request_id,
                "organization_id": packet_org.get(packet_id, ORG_ID),
                "packet_id": packet_id,
                "reviewer_lane_id": _text(request.get("review_type")) or "scoped_review",
                "status": _text(request.get("status")) or "draft",
                "payload": _json_safe_payload(request, redact_keys={"token"}),
            }
        )
    return rows


def _report_rows(runtime: dict[str, Any], report_payload: dict[str, Any], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_org = {_text(packet.get("packet_id")): _text(packet.get("organization_id")) or ORG_ID for packet in packets}
    rows: dict[str, dict[str, Any]] = {}
    for report in _runtime_rows(runtime, "report_exports"):
        report_id = _text(report.get("id"))
        packet_id = _text(report.get("packet_id"))
        if not report_id or not packet_id:
            continue
        rows[report_id] = {
            "report_id": report_id,
            "organization_id": packet_org.get(packet_id, ORG_ID),
            "packet_id": packet_id,
            "report_type": _text(report.get("report_type")) or _text(report.get("id")).split(":")[0],
            "status": _text(report.get("status")) or "export_ready_local",
            "path": _text(report.get("path") or report.get("file_id")),
            "payload": report,
        }
    for report in report_payload.get("export_records", []):
        report_id = _text(report.get("report_id"))
        packet_id = _text(report.get("packet_id"))
        if not report_id or not packet_id:
            continue
        rows[report_id] = {
            "report_id": report_id,
            "organization_id": packet_org.get(packet_id, ORG_ID),
            "packet_id": packet_id,
            "report_type": _text(report.get("report_type")),
            "status": _text(report.get("status")) or "export_ready_local",
            "path": _text(report.get("path")),
            "payload": report,
        }
    return list(rows.values())


def _audit_event_rows(runtime: dict[str, Any], country_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    audit_payload = runtime.get("audit_events", [])
    if isinstance(audit_payload, dict):
        audit_payload = audit_payload.get("events", [])
    for event in audit_payload if isinstance(audit_payload, list) else []:
        event_id = _text(event.get("id") or event.get("audit_event_id"))
        if not event_id:
            continue
        rows[event_id] = {
            "audit_event_id": event_id,
            "organization_id": _text(event.get("organization_id")) or ORG_ID,
            "entity_type": _text(event.get("entity_type")) or "unknown",
            "entity_id": _text(event.get("entity_id")) or event_id,
            "event_type": _text(event.get("event_type")) or "audit_event",
            "created_at": _text(event.get("created_at")) or _now(),
            "payload": event,
        }
    for event in country_payload.get("source_refresh_audit_events", []):
        event_id = _text(event.get("event_id"))
        if not event_id:
            continue
        rows[event_id] = {
            "audit_event_id": event_id,
            "organization_id": ORG_ID,
            "entity_type": "SourceRecord",
            "entity_id": _text(event.get("source_id")) or event_id,
            "event_type": _text(event.get("event_type")) or "source_refresh_attempt_recorded",
            "created_at": _text(event.get("recorded_at")) or _now(),
            "payload": event,
        }
    return list(rows.values())


def _validate_rows(rows: dict[str, list[dict[str, Any]]]) -> list[str]:
    errors: list[str] = []
    orgs = {row["organization_id"] for row in rows["organizations"]}
    packets = {row["packet_id"] for row in rows["trade_readiness_packets"]}
    workspaces = {row["workspace_id"] for row in rows["workspaces"]}
    lanes = {row["trade_lane_id"] for row in rows["trade_lanes"]}
    sources = {row["source_id"] for row in rows["source_records"]}
    for table_name in TABLE_ORDER:
        for index, row in enumerate(rows[table_name], start=1):
            if table_name in ORG_SCOPED_TABLES and row.get("organization_id") not in orgs:
                errors.append(f"{table_name}:{index}: organization_id missing or unknown")
            payload = row.get("payload", {})
            if isinstance(payload, dict) and payload.get("claims_opened") is True:
                errors.append(f"{table_name}:{index}: claims_opened must remain false")
    for row in rows["trade_readiness_packets"]:
        if row["workspace_id"] not in workspaces:
            errors.append(f"packet {row['packet_id']} references unknown workspace {row['workspace_id']}")
        if row["trade_lane_id"] not in lanes:
            errors.append(f"packet {row['packet_id']} references unknown lane {row['trade_lane_id']}")
        if row["claim_boundary_status"] != "external_claims_closed":
            errors.append(f"packet {row['packet_id']} opened external claim boundary")
    for table_name in ("product_profiles", "evidence_items", "blocked_claims", "claim_gate_mappers", "decision_scores", "review_requests", "reports"):
        for row in rows[table_name]:
            if row["packet_id"] not in packets:
                errors.append(f"{table_name}:{row.get(table_name[:-1] + '_id', 'row')}: unknown packet {row['packet_id']}")
    for row in rows["source_snapshots"]:
        if row["source_id"] not in sources:
            errors.append(f"source snapshot {row['snapshot_id']} references unknown source {row['source_id']}")
    return errors


def build_production_persistence_snapshot(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    packets = _load_json(graph / "customer_source_packets.json", [])
    evidence_ledger = _load_json(graph / "evidence_ledger.json", {})
    runtime = _load_json(graph / "product_runtime_state.json", {})
    packet_engine = _load_json(graph / "production_packet_engine_manifest.json", {})
    country_payload = _load_json(graph / "production_country_source_engine_manifest.json", {})
    claim_payload = _load_json(graph / "production_claim_gate_decisions.json", {})
    score_payload = _load_json(graph / "production_decision_score_records.json", {})
    report_payload = _load_json(graph / "production_report_exports.json", {})

    packet_runs = _packet_runs_by_id(packet_engine)
    trade_lanes, packet_rows, product_profiles = _packet_domain_rows(packets, packet_runs)
    rows = {
        "organizations": _organization_rows(runtime, packets),
        "users": _user_rows(runtime),
        "workspaces": _workspace_rows(packets),
        "trade_lanes": trade_lanes,
        "trade_readiness_packets": packet_rows,
        "product_profiles": product_profiles,
        "country_packs": _country_pack_rows(country_payload),
        "source_records": _source_record_rows(country_payload),
        "source_snapshots": _source_snapshot_rows(country_payload),
        "evidence_items": _evidence_rows(evidence_ledger),
        "blocked_claims": _blocked_claim_rows(runtime, packet_engine, packets),
        "claim_gate_mappers": _claim_gate_rows(claim_payload, packets),
        "decision_scores": _decision_score_rows(score_payload, packets),
        "review_requests": _review_request_rows(runtime, packets),
        "reports": _report_rows(runtime, report_payload, packets),
        "audit_events": _audit_event_rows(runtime, country_payload),
    }
    validation_errors = _validate_rows(rows)
    row_counts = {table: len(rows[table]) for table in TABLE_ORDER}
    return {
        "generated_at": _now(),
        "status": STATUS if not validation_errors else "production_persistence_validation_failed",
        "table_order": list(TABLE_ORDER),
        "org_scoped_tables": sorted(ORG_SCOPED_TABLES),
        "row_counts": row_counts,
        "total_row_count": sum(row_counts.values()),
        "rows": rows,
        "validation_errors": validation_errors,
        "validation_error_count": len(validation_errors),
        "postgres_target_migration": "migrations/0002_production_domain_model.sql",
        "sqlite_proof_store": "system_review_graph/production_domain.sqlite",
        "hosted_postgres_ready": False,
        "production_migration_applied": False,
        "external_claims_opened": False,
        "public_launch_ready": False,
        "proof_boundary": (
            "Current packet artifacts are mapped into production-domain rows and written to a local SQLite proof store. "
            "This proves migration shape and referential loading locally; it does not prove hosted Postgres, auth, backups, "
            "real uploads, live payments, customs/legal approval, buyer validation, supplier verification, or public launch."
        ),
    }


def _create_sqlite_tables(conn: sqlite3.Connection) -> None:
    for table in TABLE_ORDER:
        columns = ", ".join(SQLITE_SCHEMAS[table])
        conn.execute(f"create table if not exists {table} ({columns})")


def _insert_sqlite_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    columns = [definition.split(" ", 1)[0] for definition in SQLITE_SCHEMAS[table]]
    placeholders = ", ".join("?" for _ in columns)
    statement = f"insert or replace into {table} ({', '.join(columns)}) values ({placeholders})"
    for row in rows:
        values = []
        for column in columns:
            if column == "payload_json":
                values.append(json.dumps(row.get("payload", {}), sort_keys=True))
            else:
                values.append(row.get(column, ""))
        conn.execute(statement, values)


def write_sqlite_proof_store(snapshot: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.unlink(missing_ok=True)
    with sqlite3.connect(tmp_path) as conn:
        _create_sqlite_tables(conn)
        for table in TABLE_ORDER:
            _insert_sqlite_rows(conn, table, snapshot["rows"][table])
        conn.execute(
            "create table if not exists production_persistence_manifest (key text primary key, value text not null)"
        )
        conn.execute(
            "insert or replace into production_persistence_manifest (key, value) values (?, ?)",
            ("status", snapshot["status"]),
        )
        conn.execute(
            "insert or replace into production_persistence_manifest (key, value) values (?, ?)",
            ("proof_boundary", snapshot["proof_boundary"]),
        )
        conn.commit()
    tmp_path.replace(path)
    return path


def inspect_sqlite_proof_store(path: Path) -> dict[str, Any]:
    with sqlite3.connect(path) as conn:
        table_counts = {
            table: conn.execute(f"select count(*) from {table}").fetchone()[0]
            for table in TABLE_ORDER
        }
        manifest = dict(conn.execute("select key, value from production_persistence_manifest").fetchall())
    return {
        "path": str(path),
        "table_counts": table_counts,
        "manifest": manifest,
    }


def render_production_persistence_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Production Persistence",
        "",
        f"Status: `{snapshot['status']}`",
        "",
        "This artifact maps current packet, evidence, source, score, review, report, and audit state into normalized production-domain rows.",
        "",
        "## Row Counts",
        "",
    ]
    for table in snapshot["table_order"]:
        lines.append(f"- `{table}`: {snapshot['row_counts'][table]}")
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            f"- Hosted Postgres ready: {str(snapshot['hosted_postgres_ready']).lower()}",
            f"- Production migration applied: {str(snapshot['production_migration_applied']).lower()}",
            f"- External claims opened: {str(snapshot['external_claims_opened']).lower()}",
            f"- Public launch ready: {str(snapshot['public_launch_ready']).lower()}",
            "",
            "## Proof Boundary",
            "",
            snapshot["proof_boundary"],
            "",
        ]
    )
    if snapshot["validation_errors"]:
        lines.extend(["## Validation Errors", ""])
        for error in snapshot["validation_errors"]:
            lines.append(f"- {error}")
    return "\n".join(lines)


def write_production_persistence_artifacts(snapshot: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_persistence_snapshot.json"
    row_counts_path = graph / "production_persistence_row_counts.json"
    sqlite_path = graph / "production_domain.sqlite"
    doc_path = docs / "PRODUCTION_PERSISTENCE.md"
    manifest_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row_counts_path.write_text(
        json.dumps(
            {
                "generated_at": snapshot["generated_at"],
                "status": snapshot["status"],
                "row_counts": snapshot["row_counts"],
                "total_row_count": snapshot["total_row_count"],
                "validation_error_count": snapshot["validation_error_count"],
                "external_claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_sqlite_proof_store(snapshot, sqlite_path)
    doc_path.write_text(render_production_persistence_markdown(snapshot), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "row_counts": row_counts_path,
        "sqlite": sqlite_path,
        "doc": doc_path,
    }
