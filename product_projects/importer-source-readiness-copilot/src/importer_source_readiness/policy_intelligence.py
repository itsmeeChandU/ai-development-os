"""Database-style source monitoring contract for Intelligence Hub integration."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


POLICY_MONITOR_STATUS = "intelligence_hub_policy_monitor_ready_with_external_refresh_gates"
STORE_TABLES = [
    "monitored_sources",
    "source_snapshots",
    "source_change_classifications",
    "packet_source_impacts",
    "stale_source_blockers",
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True)


def _hash(payload: Any) -> str:
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()


def _source_tags(source: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(source.get(key) or "")
        for key in ("id", "name", "evidence_role", "claim_boundary", "url", "source_url")
    ).lower()
    tags: set[str] = {"official_reference"}
    if "tariff" in text or "hs" in text:
        tags.add("tariff")
    if "cfia" in text or "food" in text or "airs" in text:
        tags.add("food_import")
    if "permit" in text or "control" in text:
        tags.add("import_controls")
    if "sanction" in text or "restricted" in text:
        tags.add("restricted_party_screening")
    if "broker" in text:
        tags.add("expert_review")
    if "importer" in text or "buyer" in text:
        tags.add("buyer_importer_discovery")
    if "data" in text:
        tags.add("trade_data")
    return sorted(tags)


def _source_url(source: dict[str, Any]) -> str:
    return str(source.get("url") or source.get("source_url") or "")


def _packet_tags(packet: dict[str, Any]) -> set[str]:
    category = str(packet.get("product_category") or "").lower()
    tags = {"official_reference", "tariff", "import_controls", "restricted_party_screening", "expert_review"}
    if any(keyword in category for keyword in ("food", "health", "plant", "animal", "seafood", "agri")):
        tags.add("food_import")
    if str(packet.get("destination_country") or "").strip().lower() in {"canada", "ca"}:
        tags.add("buyer_importer_discovery")
    return tags


def build_policy_monitor(
    *,
    official_sources: list[dict[str, Any]],
    workflow: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a local contract for Intelligence Hub-style source monitoring."""

    generated = generated_at or _now()
    monitored_sources: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    classifications: list[dict[str, Any]] = []
    for source in official_sources:
        source_id = str(source.get("id") or source.get("name"))
        url = _source_url(source)
        tags = _source_tags(source)
        normalized = {
            "source_id": source_id,
            "name": source.get("name") or source_id,
            "jurisdiction": source.get("jurisdiction") or "unknown",
            "url": url,
            "evidence_role": source.get("evidence_role") or source.get("board_use") or "",
            "tags": tags,
            "accessed_at": source.get("accessed_at") or "",
            "claim_boundary": source.get("claim_boundary") or "",
            "loader": "intelligence_hub.official_source_registry",
            "refresh_mode": "external_refresh_required_before_claims",
        }
        snapshot_hash = _hash(normalized)
        monitored_sources.append(normalized)
        snapshots.append(
            {
                "snapshot_id": f"snapshot:{source_id}:{snapshot_hash[:12]}",
                "source_id": source_id,
                "url": url,
                "snapshot_hash": snapshot_hash,
                "observed_at": generated,
                "content_mode": "registry_metadata_only",
                "live_fetch_performed": False,
                "rights_status": "official_reference_url_only",
                "freshness_status": "monitoring_contract_ready_requires_live_refresh",
                "proof_boundary": "Registry metadata proves which source to monitor, not current legal or compliance truth.",
            }
        )
        classifications.append(
            {
                "classification_id": f"classification:{source_id}:{snapshot_hash[:12]}",
                "source_id": source_id,
                "change_type": "baseline_registered",
                "severity": "watch",
                "affected_tags": tags,
                "requires_packet_recheck": True,
                "human_review_required": True,
                "next_valid_move": "Run the live source loader, compare hashes, classify the diff, and route affected packets for qualified review.",
            }
        )

    impacts: list[dict[str, Any]] = []
    stale_blockers: list[dict[str, Any]] = []
    source_by_tag = {
        tag: [source for source in monitored_sources if tag in source.get("tags", [])]
        for tag in sorted({tag for source in monitored_sources for tag in source.get("tags", [])})
    }
    for packet in workflow.get("packets", []):
        packet_id = str(packet.get("packet_id"))
        packet_tags = _packet_tags(packet)
        matched_sources = {
            source["source_id"]
            for tag in packet_tags
            for source in source_by_tag.get(tag, [])
            if source.get("jurisdiction") in {"CA", "Canada", "unknown"}
        }
        impact = {
            "packet_id": packet_id,
            "product_name": packet.get("product_name"),
            "origin_country": packet.get("origin_country"),
            "destination_country": packet.get("destination_country"),
            "trade_direction": packet.get("trade_direction"),
            "matched_source_ids": sorted(matched_sources),
            "matched_tag_ids": sorted(packet_tags),
            "impact_status": "packet_recheck_required_on_source_change",
            "next_valid_move": "If any matched source hash changes, mark this packet stale and rerun the readiness/expert-review lane.",
        }
        impacts.append(impact)
        if matched_sources:
            stale_blockers.append(
                {
                    "id": f"{packet_id}:policy-source-monitoring-live-refresh",
                    "packet_id": packet_id,
                    "module": "policy_source_monitoring",
                    "issue": "Official-source monitoring contract exists, but live source refresh/diff proof is not attached.",
                    "owner": "research",
                    "evidence": "system_review_graph/intelligence_hub_policy_monitor.json",
                    "gate": "closed",
                    "status": "open",
                    "unsafe_to_bypass": True,
                    "source_ids": sorted(matched_sources),
                    "claim_blocked": "current official-source correctness",
                    "next_valid_move": "Run Intelligence Hub source snapshots, diff classifiers, and qualified packet review before claiming current import/export correctness.",
                }
            )

    return {
        "generated_at": generated,
        "status": POLICY_MONITOR_STATUS,
        "integration_mode": "database_style_local_contract",
        "intelligence_hub_role": [
            "official source registry",
            "source snapshot store",
            "hash and diff classifier",
            "country/product/HS mapping",
            "packet stale-source blocker routing",
        ],
        "external_effects": {
            "live_fetch_performed": False,
            "paid_calls_made": False,
            "external_claims_opened": False,
        },
        "monitored_source_count": len(monitored_sources),
        "packet_impact_count": len(impacts),
        "stale_source_blocker_count": len(stale_blockers),
        "monitored_sources": monitored_sources,
        "source_snapshots": snapshots,
        "source_change_classifications": classifications,
        "packet_source_impacts": impacts,
        "stale_source_blockers": stale_blockers,
        "proof_boundary": (
            "This artifact defines how Intelligence Hub should monitor official sources and stale packets. "
            "It does not prove current tariff, CFIA, import permit, sanctions, buyer, supplier, legal, or commercial readiness."
        ),
    }


def write_policy_store(monitor: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_handle = tempfile.NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False)
    tmp_path = Path(tmp_handle.name)
    tmp_handle.close()
    try:
        with sqlite3.connect(tmp_path) as conn:
            conn.execute("create table monitored_sources (source_id text primary key, jurisdiction text, url text, payload_json text not null)")
            conn.execute("create table source_snapshots (snapshot_id text primary key, source_id text, snapshot_hash text, observed_at text, payload_json text not null)")
            conn.execute("create table source_change_classifications (classification_id text primary key, source_id text, change_type text, severity text, payload_json text not null)")
            conn.execute("create table packet_source_impacts (packet_id text primary key, impact_status text, payload_json text not null)")
            conn.execute("create table stale_source_blockers (blocker_id text primary key, packet_id text, status text, payload_json text not null)")
            for source in monitor.get("monitored_sources", []):
                conn.execute(
                    "insert into monitored_sources values (?, ?, ?, ?)",
                    (source["source_id"], source.get("jurisdiction"), source.get("url"), _json(source)),
                )
            for snapshot in monitor.get("source_snapshots", []):
                conn.execute(
                    "insert into source_snapshots values (?, ?, ?, ?, ?)",
                    (
                        snapshot["snapshot_id"],
                        snapshot["source_id"],
                        snapshot["snapshot_hash"],
                        snapshot["observed_at"],
                        _json(snapshot),
                    ),
                )
            for row in monitor.get("source_change_classifications", []):
                conn.execute(
                    "insert into source_change_classifications values (?, ?, ?, ?, ?)",
                    (row["classification_id"], row["source_id"], row["change_type"], row["severity"], _json(row)),
                )
            for impact in monitor.get("packet_source_impacts", []):
                conn.execute(
                    "insert into packet_source_impacts values (?, ?, ?)",
                    (impact["packet_id"], impact["impact_status"], _json(impact)),
                )
            for blocker in monitor.get("stale_source_blockers", []):
                conn.execute(
                    "insert into stale_source_blockers values (?, ?, ?, ?)",
                    (blocker["id"], blocker["packet_id"], blocker["status"], _json(blocker)),
                )
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return path


def inspect_policy_store(path: Path) -> dict[str, Any]:
    with sqlite3.connect(path) as conn:
        tables = {
            row[0]: conn.execute(f"select count(*) from {row[0]}").fetchone()[0]
            for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
        }
    return {"path": str(path), "tables": tables, "required_tables": STORE_TABLES}


def write_policy_monitor_artifacts(monitor: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    graph = repo_root / "system_review_graph"
    graph.mkdir(parents=True, exist_ok=True)
    (graph / "intelligence_hub_policy_monitor.json").write_text(
        json.dumps(monitor, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (graph / "policy_source_snapshots.json").write_text(
        json.dumps(
            {
                "status": "policy_source_snapshots_ready",
                "source_snapshots": monitor["source_snapshots"],
                "monitored_sources": monitor["monitored_sources"],
                "proof_boundary": monitor["proof_boundary"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (graph / "policy_change_impact_report.json").write_text(
        json.dumps(
            {
                "status": "policy_change_impact_report_ready",
                "source_change_classifications": monitor["source_change_classifications"],
                "packet_source_impacts": monitor["packet_source_impacts"],
                "stale_source_blockers": monitor["stale_source_blockers"],
                "proof_boundary": monitor["proof_boundary"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    store_path = write_policy_store(monitor, graph / "policy_intelligence.sqlite")
    return {**monitor, "store": inspect_policy_store(store_path)}
