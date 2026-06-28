"""External evidence gate evaluation for importer source readiness."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPEN_STATUSES = {"verified", "attached_for_reference"}
BLOCKING_STATUSES = {"missing", "needs_review", "not_verified", "requires_qualified_review"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _blocker(
    *,
    blocker_id: str,
    module: str,
    issue: str,
    evidence: str,
    owner: str,
    next_valid_move: str,
) -> dict[str, Any]:
    return {
        "id": blocker_id,
        "module": module,
        "issue": issue,
        "evidence": evidence,
        "owner": owner,
        "gate": "closed",
        "next_valid_move": next_valid_move,
        "unsafe_to_bypass": True,
    }


def _status_is_open(status: str) -> bool:
    return status in OPEN_STATUSES


def _status_is_blocking(status: str) -> bool:
    return status in BLOCKING_STATUSES or not status


def evaluate_country_matrix(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    fields = [
        ("import_rules_status", "country_import_rules", "qualified import-rules review is missing"),
        ("export_rules_status", "country_export_rules", "qualified export-rules review is missing"),
        ("tariff_status", "tariff_classification", "tariff or HS classification is not qualified"),
        ("food_safety_status", "food_safety", "food safety requirements are not qualified"),
        ("restricted_party_status", "restricted_party_screening", "restricted-party screening is not complete"),
        ("broker_or_expert_review_status", "expert_review", "broker or qualified expert review is missing"),
    ]
    for row in rows:
        row_id = str(row["id"])
        row_blockers: list[dict[str, Any]] = []
        source_count = len(row.get("official_sources") or [])
        if source_count == 0:
            row_blockers.append(
                _blocker(
                    blocker_id=f"{row_id}:official-sources-missing",
                    module="official_source_review",
                    issue="country matrix row has no official source references",
                    evidence=row_id,
                    owner="research",
                    next_valid_move="Attach official source URLs and access dates before using the row.",
                )
            )
        for field, module, issue in fields:
            status = str(row.get(field) or "")
            if _status_is_blocking(status):
                row_blockers.append(
                    _blocker(
                        blocker_id=f"{row_id}:{field}",
                        module=module,
                        issue=issue,
                        evidence=row_id,
                        owner=str(row.get("owner") or "operations"),
                        next_valid_move=str(row.get("next_valid_move") or "Collect qualified review evidence."),
                    )
                )
        blockers.extend(row_blockers)
        summaries.append(
            {
                "id": row_id,
                "country": row.get("country"),
                "product_category": row.get("product_category"),
                "hs_code": row.get("hs_code"),
                "official_source_count": source_count,
                "claims_allowed": bool(row.get("claims_allowed")),
                "gate_state": "open" if bool(row.get("claims_allowed")) and not row_blockers else "closed",
            }
        )
    return summaries, blockers


def evaluate_evidence_packets(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for row in rows:
        gate_id = str(row["id"])
        status = str(row.get("status") or "")
        if _status_is_blocking(status):
            blockers.append(
                _blocker(
                    blocker_id=f"{gate_id}:evidence-missing",
                    module=str(row.get("module") or gate_id),
                    issue=str(row.get("issue") or "required external evidence is missing"),
                    evidence=str(row.get("evidence") or gate_id),
                    owner=str(row.get("owner") or "operator"),
                    next_valid_move=str(row.get("next_valid_move") or "Collect dated evidence and attach it."),
                )
            )
        summaries.append(
            {
                "id": gate_id,
                "module": row.get("module"),
                "status": status,
                "owner": row.get("owner"),
                "gate_state": "open" if _status_is_open(status) else "closed",
            }
        )
    return summaries, blockers


def build_external_gate_report(
    *,
    country_matrix: list[dict[str, Any]],
    evidence_packets: list[dict[str, Any]],
    official_sources: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    country_rows, country_blockers = evaluate_country_matrix(country_matrix)
    evidence_rows, evidence_blockers = evaluate_evidence_packets(evidence_packets)
    blockers = country_blockers + evidence_blockers
    return {
        "generated_at": generated_at or _now(),
        "status": "ready" if not blockers else "ready_with_external_gates",
        "country_matrix_rows": country_rows,
        "evidence_gates": evidence_rows,
        "official_sources": [
            {
                "id": row["id"],
                "name": row["name"],
                "url": row["url"],
                "accessed_at": row["accessed_at"],
                "claim_boundary": row["claim_boundary"],
            }
            for row in official_sources
        ],
        "blocker_count": len(blockers),
        "blockers": blockers,
        "unsafe_gates": {
            "external_sends_run": 0,
            "external_api_calls_run": 0,
            "paid_actions_run": 0,
            "customs_or_tariff_claims_made": 0,
            "import_export_advice_claims_made": 0,
            "supplier_recommendation_claims_made": 0,
        },
        "next_valid_move": (
            "Collect dated official-source refresh evidence, country matrix review, "
            "buyer feedback, contract terms, and qualified compliance review before "
            "external or public claims."
        ),
        "proof_boundary": (
            "This report proves the local product can route external gates. It does "
            "not prove legal, customs, tariff, supplier, buyer, logistics, or launch readiness."
        ),
    }


def write_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
