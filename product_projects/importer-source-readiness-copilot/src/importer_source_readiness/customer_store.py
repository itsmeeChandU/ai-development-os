"""SQLite persistence artifact for the customer source-packet workflow."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from .product_runtime import build_runtime_state

TABLES = [
    "users",
    "organizations",
    "memberships",
    "source_packets",
    "evidence_items",
    "official_sources",
    "claims",
    "blockers",
    "review_runs",
    "review_requests",
    "human_review_findings",
    "gate_decisions",
    "report_exports",
    "data_deletion_requests",
    "audit_events",
]


def _json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True)


def _execute_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        "create table users (user_id text primary key, email text not null, role text not null, organization_id text not null, payload_json text not null)"
    )
    conn.execute(
        "create table organizations (organization_id text primary key, name text not null, payload_json text not null)"
    )
    conn.execute(
        "create table memberships (user_id text not null, organization_id text not null, role text not null, payload_json text not null, primary key (user_id, organization_id))"
    )
    conn.execute("create table source_packets (packet_id text primary key, status text, payload_json text not null)")
    conn.execute(
        "create table evidence_items (evidence_id text primary key, packet_id text, ledger_status text, payload_json text not null)"
    )
    conn.execute(
        "create table official_sources (source_id text primary key, jurisdiction text, payload_json text not null)"
    )
    conn.execute(
        "create table claims (claim_id text primary key, packet_id text, claim_type text, status text, payload_json text not null)"
    )
    conn.execute(
        "create table blockers (blocker_id text primary key, packet_id text, group_id text, status text, payload_json text not null)"
    )
    conn.execute(
        "create table review_runs (run_id text primary key, packet_id text, review_type text, status text, payload_json text not null)"
    )
    conn.execute(
        "create table review_requests (review_request_id text primary key, packet_id text, review_type text, status text, token text, payload_json text not null)"
    )
    conn.execute(
        "create table human_review_findings (finding_id text primary key, review_request_id text, packet_id text, decision text, payload_json text not null)"
    )
    conn.execute(
        "create table gate_decisions (decision_id text primary key, packet_id text, gate text, status text, payload_json text not null)"
    )
    conn.execute(
        "create table report_exports (report_id text primary key, packet_id text, report_type text, format text, status text, payload_json text not null)"
    )
    conn.execute(
        "create table data_deletion_requests (request_id text primary key, organization_id text, status text, payload_json text not null)"
    )
    conn.execute(
        "create table audit_events (event_id text primary key, organization_id text, entity_id text, event_type text, payload_json text not null)"
    )


def _insert_runtime(conn: sqlite3.Connection, runtime: dict[str, Any]) -> None:
    for user in runtime.get("users", []):
        conn.execute(
            "insert into users values (?, ?, ?, ?, ?)",
            (user["id"], user["email"], user["role"], user["organization_id"], _json(user)),
        )
    for org in runtime.get("organizations", []):
        conn.execute(
            "insert into organizations values (?, ?, ?)",
            (org["id"], org["name"], _json(org)),
        )
    for membership in runtime.get("memberships", []):
        conn.execute(
            "insert into memberships values (?, ?, ?, ?)",
            (
                membership["user_id"],
                membership["organization_id"],
                membership["role"],
                _json(membership),
            ),
        )
    for claim in runtime.get("claims", []):
        conn.execute(
            "insert into claims values (?, ?, ?, ?, ?)",
            (
                claim["id"],
                claim["packet_id"],
                claim["claim_type"],
                claim["status"],
                _json(claim),
            ),
        )
    for request in runtime.get("review_requests", []):
        conn.execute(
            "insert into review_requests values (?, ?, ?, ?, ?, ?)",
            (
                request["id"],
                request["packet_id"],
                request["review_type"],
                request["status"],
                request["token"],
                _json(request),
            ),
        )
    for finding in runtime.get("human_review_findings", []):
        conn.execute(
            "insert into human_review_findings values (?, ?, ?, ?, ?)",
            (
                finding.get("id"),
                finding.get("review_request_id"),
                finding.get("packet_id"),
                finding.get("decision"),
                _json(finding),
            ),
        )
    for report in runtime.get("report_exports", []):
        conn.execute(
            "insert into report_exports values (?, ?, ?, ?, ?, ?)",
            (
                report["id"],
                report["packet_id"],
                report["report_type"],
                report["format"],
                report["status"],
                _json(report),
            ),
        )
    for request in runtime.get("data_deletion_requests", []):
        conn.execute(
            "insert into data_deletion_requests values (?, ?, ?, ?)",
            (
                request.get("id"),
                request.get("organization_id"),
                request.get("status"),
                _json(request),
            ),
        )
    for event in runtime.get("audit_events", []):
        conn.execute(
            "insert or replace into audit_events values (?, ?, ?, ?, ?)",
            (
                event["id"],
                event["organization_id"],
                event["entity_id"],
                event["event_type"],
                _json(event),
            ),
        )


def _insert_workflow(conn: sqlite3.Connection, workflow: dict[str, Any]) -> None:
    for packet in workflow.get("packets", []):
        packet_id = str(packet.get("packet_id"))
        conn.execute(
            "insert into source_packets values (?, ?, ?)",
            (packet_id, packet.get("customer_visible_status"), _json(packet)),
        )
        for blocker in packet.get("blockers", []):
            conn.execute(
                "insert into blockers values (?, ?, ?, ?, ?)",
                (
                    blocker.get("id"),
                    packet_id,
                    blocker.get("group"),
                    blocker.get("status"),
                    _json(blocker),
                ),
            )
        for claim in packet.get("blocked_claims", []):
            decision = {
                "decision_id": f"{packet_id}:{claim}",
                "packet_id": packet_id,
                "gate": claim,
                "status": "closed",
                "reason": "External claim remains blocked until scoped evidence and human review exist.",
            }
            conn.execute(
                "insert into gate_decisions values (?, ?, ?, ?, ?)",
                (
                    decision["decision_id"],
                    packet_id,
                    decision["gate"],
                    decision["status"],
                    _json(decision),
                ),
            )

    for evidence in workflow.get("evidence_ledger", {}).get("rows", []):
        conn.execute(
            "insert into evidence_items values (?, ?, ?, ?)",
            (
                evidence.get("evidence_id"),
                evidence.get("packet_id"),
                evidence.get("ledger_status"),
                _json(evidence),
            ),
        )

    for source in workflow.get("official_sources", []):
        conn.execute(
            "insert into official_sources values (?, ?, ?)",
            (source.get("id"), source.get("jurisdiction"), _json(source)),
        )

    for run in workflow.get("ai_review_runs", []):
        conn.execute(
            "insert into review_runs values (?, ?, ?, ?, ?)",
            (
                run.get("run_id"),
                run.get("packet_id"),
                run.get("review_type"),
                run.get("status"),
                _json(run),
            ),
        )


def write_customer_store(workflow: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_handle = tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    tmp_path = Path(tmp_handle.name)
    tmp_handle.close()
    try:
        with sqlite3.connect(tmp_path) as conn:
            runtime = build_runtime_state(workflow)
            _execute_schema(conn)
            _insert_runtime(conn, runtime)
            _insert_workflow(conn, workflow)
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return path


def inspect_customer_store(path: Path) -> dict[str, Any]:
    with sqlite3.connect(path) as conn:
        counts = {
            table: conn.execute(f"select count(*) from {table}").fetchone()[0]
            for table in TABLES
        }
    return {
        "status": "customer_store_ready",
        "path": str(path),
        "tables": TABLES,
        "counts": counts,
    }
