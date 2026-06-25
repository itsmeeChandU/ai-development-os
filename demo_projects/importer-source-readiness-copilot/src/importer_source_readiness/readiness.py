"""Source readiness evaluator for the importer/exporter demo project.

The evaluator is intentionally conservative. It turns fixture and official
source rows into operator readiness reports, but it does not make customs,
tariff, supplier, buyer, legal, or launch claims.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UNSAFE_COUNTERS = [
    "external_sends_run",
    "external_api_calls_run",
    "paid_actions_run",
    "customs_or_tariff_claims_made",
    "import_export_advice_claims_made",
    "supplier_recommendation_claims_made",
]


@dataclass(frozen=True)
class Blocker:
    id: str
    module: str
    issue: str
    evidence: str
    owner: str
    gate: str
    next_valid_move: str
    unsafe_to_bypass: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "module": self.module,
            "issue": self.issue,
            "evidence": self.evidence,
            "owner": self.owner,
            "gate": self.gate,
            "next_valid_move": self.next_valid_move,
            "unsafe_to_bypass": self.unsafe_to_bypass,
        }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_cards(path: Path) -> list[dict[str, Any]]:
    """Load source-card fixtures from JSON."""

    return json.loads(path.read_text(encoding="utf-8"))


def _blocker_id(card: dict[str, Any], suffix: str) -> str:
    slug = str(card.get("product_slug") or "unknown").replace("_", "-")
    return f"{slug}:{suffix}"


def _evaluate_card(card: dict[str, Any]) -> dict[str, Any]:
    blockers: list[Blocker] = []
    evidence = str(card.get("source_name") or card.get("product_slug") or "source card")

    for counter in UNSAFE_COUNTERS:
        if int(card.get(counter) or 0) != 0:
            blockers.append(
                Blocker(
                    id=_blocker_id(card, f"unsafe-{counter}"),
                    module="unsafe_external_gate",
                    issue=f"{counter} must remain zero in this demo",
                    evidence=evidence,
                    owner="operator",
                    gate="closed",
                    next_valid_move="Reset the counter to zero and remove any unsupported external-effect claim.",
                )
            )

    if bool(card.get("buyer_validation_claimed")):
        blockers.append(
            Blocker(
                id=_blocker_id(card, "unsupported-buyer-claim"),
                module="buyer_validation",
                issue="buyer validation is claimed without dated buyer evidence",
                evidence=evidence,
                owner="product",
                gate="closed",
                next_valid_move="Collect dated buyer/no-fit/payment/no-budget evidence or remove the claim.",
            )
        )

    if not card.get("source_url") or card.get("source_type") != "official":
        blockers.append(
            Blocker(
                id=_blocker_id(card, "official-source-missing"),
                module="official_source_review",
                issue="official source URL is missing or the row is fixture-only",
                evidence=evidence,
                owner="research",
                gate="closed",
                next_valid_move="Attach a current official source URL and access date before source claims.",
            )
        )

    if str(card.get("data_freshness_status") or "") != "current":
        blockers.append(
            Blocker(
                id=_blocker_id(card, "freshness-not-proven"),
                module="data_freshness",
                issue="data freshness is not proven for product claims",
                evidence=evidence,
                owner="data",
                gate="closed",
                next_valid_move="Run a dated refresh or mark the row as fixture-only.",
            )
        )

    if str(card.get("buyer_validation_status") or "") != "validated":
        blockers.append(
            Blocker(
                id=_blocker_id(card, "buyer-validation-missing"),
                module="buyer_validation",
                issue="buyer validation is missing",
                evidence=evidence,
                owner="product",
                gate="closed",
                next_valid_move="Collect dated buyer feedback or no-fit evidence before commercial claims.",
            )
        )

    if str(card.get("legal_review_status") or "") != "reviewed":
        blockers.append(
            Blocker(
                id=_blocker_id(card, "legal-review-missing"),
                module="legal_compliance",
                issue="legal/compliance review is missing",
                evidence=evidence,
                owner="compliance",
                gate="closed",
                next_valid_move="Get qualified review before legal, customs, import/export, or public claims.",
            )
        )

    if str(card.get("contract_status") or "") != "signed":
        blockers.append(
            Blocker(
                id=_blocker_id(card, "contract-missing"),
                module="commercial_contract",
                issue="commercial/source contract is missing",
                evidence=evidence,
                owner="operations",
                gate="closed",
                next_valid_move="Attach written source, supplier, buyer, or commercial terms before readiness claims.",
            )
        )

    unsafe_blockers = [row for row in blockers if row.module == "unsafe_external_gate"]
    status = "blocked_unsafe" if unsafe_blockers else "ready_with_external_gates"
    if not blockers:
        status = "ready"

    return {
        "product_slug": card.get("product_slug"),
        "queue_id": card.get("queue_id"),
        "source_name": card.get("source_name"),
        "country": card.get("country"),
        "hs_code": card.get("hs_code"),
        "status": status,
        "official_source_attached": bool(card.get("source_url") and card.get("source_type") == "official"),
        "unsafe_counters": {counter: int(card.get(counter) or 0) for counter in UNSAFE_COUNTERS},
        "blockers": [blocker.to_dict() for blocker in blockers],
        "next_valid_move": (
            "Resolve unsafe external counters before any product work."
            if unsafe_blockers
            else "Use this row for internal operator readiness only; collect external evidence before claims."
        ),
    }


def evaluate_cards(cards: list[dict[str, Any]], *, generated_at: str | None = None) -> dict[str, Any]:
    rows = [_evaluate_card(card) for card in cards]
    blockers = [blocker for row in rows for blocker in row["blockers"]]
    unsafe_rows = [row for row in rows if row["status"] == "blocked_unsafe"]
    ready_rows = [row for row in rows if row["status"] == "ready"]
    return {
        "generated_at": generated_at or _now(),
        "status": "blocked_unsafe" if unsafe_rows else "ready_with_external_gates",
        "row_count": len(rows),
        "ready_rows": len(ready_rows),
        "ready_with_external_gates_rows": len(
            [row for row in rows if row["status"] == "ready_with_external_gates"]
        ),
        "blocked_unsafe_rows": len(unsafe_rows),
        "blocker_count": len(blockers),
        "rows": rows,
        "blockers": blockers,
        "proof_boundary": (
            "This report proves local fixture evaluation only. It does not prove "
            "customs, tariff, supplier, buyer, legal, payment, launch, or market readiness."
        ),
    }


def write_report(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
