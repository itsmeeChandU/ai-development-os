"""Database-backed repository/service layer for local production proof.

The persistence layer proves rows can be written. This module proves the
application can read those rows through one service boundary instead of
reaching back into scattered generated JSON artifacts.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .production_persistence import TABLE_ORDER


STATUS = "production_repository_service_ready_database_backed_packet_context_claim_gates_closed"
DEFAULT_PACKET_ID = "packet-frozen-tuna-canada-001"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _decode_payload(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    value = row["payload_json"] if isinstance(row, sqlite3.Row) else row.get("payload_json")
    if not value:
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {"value": decoded}


def _public_row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    payload = _decode_payload(row)
    data.pop("payload_json", None)
    data["payload"] = payload
    return data


class ProductionRepository:
    """Read-only repository over the local production-domain proof store."""

    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def table_counts(self) -> dict[str, int]:
        with self._connect() as conn:
            return {
                table: int(conn.execute(f"select count(*) from {table}").fetchone()[0])
                for table in TABLE_ORDER
            }

    def packet_ids(self, organization_id: str | None = None) -> list[str]:
        with self._connect() as conn:
            if organization_id:
                rows = conn.execute(
                    "select packet_id from trade_readiness_packets where organization_id = ? order by packet_id",
                    (organization_id,),
                ).fetchall()
            else:
                rows = conn.execute("select packet_id from trade_readiness_packets order by packet_id").fetchall()
        return [str(row["packet_id"]) for row in rows]

    def _packet(self, conn: sqlite3.Connection, packet_id: str) -> dict[str, Any] | None:
        row = conn.execute(
            "select * from trade_readiness_packets where packet_id = ?",
            (packet_id,),
        ).fetchone()
        return _public_row(row) if row else None

    def _one_by_key(self, conn: sqlite3.Connection, table: str, key: str, value: str) -> dict[str, Any] | None:
        row = conn.execute(f"select * from {table} where {key} = ?", (value,)).fetchone()
        return _public_row(row) if row else None

    def _many_for_packet(self, conn: sqlite3.Connection, table: str, packet_id: str, order_by: str) -> list[dict[str, Any]]:
        rows = conn.execute(f"select * from {table} where packet_id = ? order by {order_by}", (packet_id,)).fetchall()
        return [_public_row(row) for row in rows]

    def packet_context(self, packet_id: str, *, organization_id: str | None = None) -> dict[str, Any]:
        with self._connect() as conn:
            packet = self._packet(conn, packet_id)
            if not packet:
                return {
                    "status": "packet_not_found",
                    "packet_id": packet_id,
                    "can_access": False,
                    "external_claims_opened": False,
                    "next_valid_move": "Create or load the packet before building a production context.",
                }
            if organization_id and packet["organization_id"] != organization_id:
                return {
                    "status": "access_denied",
                    "packet_id": packet_id,
                    "requested_organization_id": organization_id,
                    "can_access": False,
                    "external_claims_opened": False,
                    "next_valid_move": "Use an organization-scoped packet id or request access through RBAC.",
                }
            lane = self._one_by_key(conn, "trade_lanes", "trade_lane_id", packet["trade_lane_id"])
            workspace = self._one_by_key(conn, "workspaces", "workspace_id", packet["workspace_id"])
            product_rows = self._many_for_packet(conn, "product_profiles", packet_id, "product_profile_id")
            evidence_rows = self._many_for_packet(conn, "evidence_items", packet_id, "evidence_id")
            blocked_claims = self._many_for_packet(conn, "blocked_claims", packet_id, "claim_type")
            claim_decisions = self._many_for_packet(conn, "claim_gate_mappers", packet_id, "claim_type")
            scores = self._many_for_packet(conn, "decision_scores", packet_id, "score_type")
            review_requests = self._many_for_packet(conn, "review_requests", packet_id, "review_request_id")
            reports = self._many_for_packet(conn, "reports", packet_id, "report_type")
            audit_events = conn.execute(
                "select * from audit_events where organization_id = ? order by created_at, audit_event_id",
                (packet["organization_id"],),
            ).fetchall()
            source_snapshot_states = {
                row["source_state"]: row["count"]
                for row in conn.execute(
                    "select source_state, count(*) as count from source_snapshots group by source_state"
                ).fetchall()
            }

        safe_claims = [row for row in claim_decisions if int(row["can_show_claim"]) == 1]
        blocked_claim_decisions = [row for row in claim_decisions if int(row["can_show_claim"]) != 1]
        return {
            "status": "packet_context_ready_from_production_repository",
            "generated_at": _now(),
            "packet_id": packet_id,
            "organization_id": packet["organization_id"],
            "can_access": True,
            "packet": packet,
            "workspace": workspace,
            "trade_lane": lane,
            "product_profiles": product_rows,
            "evidence_items": evidence_rows,
            "blocked_claims": blocked_claims,
            "claim_gate_decisions": claim_decisions,
            "decision_scores": scores,
            "review_requests": review_requests,
            "reports": reports,
            "audit_events": [_public_row(row) for row in audit_events],
            "source_snapshot_state_counts": source_snapshot_states,
            "safe_claim_count": len(safe_claims),
            "blocked_claim_decision_count": len(blocked_claim_decisions),
            "external_claims_opened": False,
            "public_launch_ready": False,
            "hosted_postgres_ready": False,
            "proof_boundary": (
                "This context is read from the local production-domain proof store. It is preparation evidence only "
                "and does not prove hosted infrastructure, qualified review, legal/customs approval, payments, buyer "
                "validation, supplier verification, or public launch readiness."
            ),
        }

    def can_show_claim(self, packet_id: str, claim_type: str, *, organization_id: str | None = None) -> dict[str, Any]:
        context = self.packet_context(packet_id, organization_id=organization_id)
        if context.get("status") != "packet_context_ready_from_production_repository":
            return {
                "claim_type": claim_type,
                "packet_id": packet_id,
                "can_show_claim": False,
                "reason": context.get("status"),
                "allowed_language": "",
                "blocked_language": "Claim cannot be shown because the packet context is unavailable or inaccessible.",
                "next_valid_move": context.get("next_valid_move", "Load an accessible packet context first."),
                "external_claims_opened": False,
            }
        for decision in context["claim_gate_decisions"]:
            if decision["claim_type"] == claim_type:
                payload = decision["payload"]
                return {
                    "claim_gate_mapper_id": decision["claim_gate_mapper_id"],
                    "claim_type": claim_type,
                    "packet_id": packet_id,
                    "can_show_claim": bool(decision["can_show_claim"]),
                    "allowed_language": payload.get("allowed_wording", ""),
                    "blocked_language": payload.get("blocked_wording", ""),
                    "required_reviewer_lane": decision.get("required_reviewer_lane", ""),
                    "required_evidence": payload.get("required_evidence_types", []),
                    "reason": payload.get("reason", ""),
                    "next_valid_move": payload.get("next_valid_move", ""),
                    "external_claims_opened": False,
                }
        return {
            "claim_type": claim_type,
            "packet_id": packet_id,
            "can_show_claim": False,
            "reason": "claim_gate_mapper_missing",
            "allowed_language": "",
            "blocked_language": "No claim gate exists for this claim type, so the claim fails closed.",
            "next_valid_move": "Add an explicit claim-gate mapper with evidence requirements before showing this claim.",
            "external_claims_opened": False,
        }

    def report_context(self, packet_id: str, *, organization_id: str | None = None) -> dict[str, Any]:
        context = self.packet_context(packet_id, organization_id=organization_id)
        if context.get("status") != "packet_context_ready_from_production_repository":
            return context
        visible_claims = [
            self.can_show_claim(packet_id, row["claim_type"], organization_id=organization_id)
            for row in context["claim_gate_decisions"]
            if int(row["can_show_claim"]) == 1
        ]
        blocked_claims = [
            self.can_show_claim(packet_id, row["claim_type"], organization_id=organization_id)
            for row in context["claim_gate_decisions"]
            if int(row["can_show_claim"]) != 1
        ]
        return {
            "status": "database_backed_report_context_ready",
            "generated_at": _now(),
            "packet_id": packet_id,
            "organization_id": context["organization_id"],
            "packet_state": context["packet"]["state"],
            "product_name": context["product_profiles"][0]["name"] if context["product_profiles"] else "",
            "trade_lane": context["trade_lane"],
            "score_summary": [
                {
                    "score_type": row["score_type"],
                    "label": row["label"],
                    "value": row["value"],
                    "cap": row["cap"],
                    "next_action": row["payload"].get("next_action", ""),
                }
                for row in context["decision_scores"]
            ],
            "visible_claims": visible_claims,
            "blocked_claims": blocked_claims,
            "evidence_count": len(context["evidence_items"]),
            "report_exports": context["reports"],
            "watermark": "DRAFT - NOT APPROVAL",
            "external_claims_opened": False,
            "public_launch_ready": False,
            "proof_boundary": context["proof_boundary"],
        }


def build_production_repository_service(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    sqlite_path = root / "system_review_graph" / "production_domain.sqlite"
    repository = ProductionRepository(sqlite_path)
    packet_ids = repository.packet_ids()
    packet_id = packet_ids[0] if packet_ids else DEFAULT_PACKET_ID
    context = repository.packet_context(packet_id)
    report_context = repository.report_context(packet_id)
    sample_claims = [
        repository.can_show_claim(packet_id, "product_context_recorded"),
        repository.can_show_claim(packet_id, "tariff_confirmed"),
        repository.can_show_claim(packet_id, "unknown_future_claim"),
    ]
    return {
        "generated_at": _now(),
        "status": STATUS,
        "sqlite_proof_store": str(sqlite_path.relative_to(root)),
        "table_counts": repository.table_counts(),
        "packet_ids": packet_ids,
        "packet_context_status": context.get("status"),
        "report_context_status": report_context.get("status"),
        "sample_claim_decisions": sample_claims,
        "safe_claim_count": context.get("safe_claim_count", 0),
        "blocked_claim_decision_count": context.get("blocked_claim_decision_count", 0),
        "report_export_count": len(context.get("reports", [])),
        "tenant_access_control": {
            "same_org_status": repository.packet_context(packet_id, organization_id=context.get("organization_id", "")).get("status"),
            "wrong_org_status": repository.packet_context(packet_id, organization_id="org-not-authorized").get("status"),
        },
        "external_claims_opened": False,
        "hosted_postgres_ready": False,
        "public_launch_ready": False,
        "proof_boundary": (
            "The repository service reads the local production-domain store and fails closed for missing or inaccessible claims. "
            "It does not open any external legal, customs, payment, buyer, supplier, hosted, or launch gate."
        ),
    }


def render_repository_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Repository Service",
        "",
        f"Status: `{payload['status']}`",
        "",
        "The repository service is the application boundary over the normalized production-domain proof store.",
        "",
        "## Proof",
        "",
        f"- Store: `{payload['sqlite_proof_store']}`",
        f"- Packets: `{len(payload['packet_ids'])}`",
        f"- Safe preparation claims: `{payload['safe_claim_count']}`",
        f"- Blocked claim decisions: `{payload['blocked_claim_decision_count']}`",
        f"- Report exports: `{payload['report_export_count']}`",
        f"- Wrong-organization access: `{payload['tenant_access_control']['wrong_org_status']}`",
        "",
        "## Sample Claim Decisions",
        "",
    ]
    for decision in payload["sample_claim_decisions"]:
        lines.append(f"- `{decision['claim_type']}`: can show `{str(decision['can_show_claim']).lower()}`; reason `{decision['reason']}`.")
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            f"- External claims opened: {str(payload['external_claims_opened']).lower()}",
            f"- Hosted Postgres ready: {str(payload['hosted_postgres_ready']).lower()}",
            f"- Public launch ready: {str(payload['public_launch_ready']).lower()}",
            "",
            "## Proof Boundary",
            "",
            payload["proof_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def write_production_repository_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    repository = ProductionRepository(repo_root / payload["sqlite_proof_store"])
    packet_id = payload["packet_ids"][0] if payload["packet_ids"] else DEFAULT_PACKET_ID
    manifest_path = graph / "production_repository_service_manifest.json"
    context_path = graph / f"production_repository_packet_context_{packet_id}.json"
    report_context_path = graph / f"production_repository_report_context_{packet_id}.json"
    doc_path = docs / "PRODUCTION_REPOSITORY_SERVICE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    context_path.write_text(
        json.dumps(repository.packet_context(packet_id), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_context_path.write_text(
        json.dumps(repository.report_context(packet_id), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_repository_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "packet_context": context_path,
        "report_context": report_context_path,
        "doc": doc_path,
    }
