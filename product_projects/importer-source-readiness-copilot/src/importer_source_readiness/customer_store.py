"""SQLite persistence artifact for the customer source-packet workflow."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


TABLES = [
    "source_packets",
    "evidence_items",
    "official_sources",
    "blockers",
    "review_runs",
    "gate_decisions",
    "audit_events",
]


def _json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True)


def write_customer_store(workflow: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as conn:
        conn.execute("create table source_packets (packet_id text primary key, status text, payload_json text not null)")
        conn.execute("create table evidence_items (evidence_id text primary key, packet_id text, ledger_status text, payload_json text not null)")
        conn.execute("create table official_sources (source_id text primary key, jurisdiction text, payload_json text not null)")
        conn.execute("create table blockers (blocker_id text primary key, packet_id text, group_id text, status text, payload_json text not null)")
        conn.execute("create table review_runs (run_id text primary key, packet_id text, review_type text, status text, payload_json text not null)")
        conn.execute("create table gate_decisions (decision_id text primary key, packet_id text, gate text, status text, payload_json text not null)")
        conn.execute("create table audit_events (event_id text primary key, packet_id text, event_type text, payload_json text not null)")

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
            conn.execute(
                "insert into audit_events values (?, ?, ?, ?)",
                (
                    f"{packet_id}:workflow-generated",
                    packet_id,
                    "workflow_generated",
                    _json(
                        {
                            "packet_id": packet_id,
                            "event_type": "workflow_generated",
                            "status": packet.get("customer_visible_status"),
                            "display_status": packet.get("display_status"),
                        }
                    ),
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
