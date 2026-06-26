"""Customer source-packet workflow for the importer readiness product."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CUSTOMER_STATUS_LABELS = {
    "draft",
    "submitted",
    "needs_more_evidence",
    "needs_operator_review",
    "needs_expert_review",
    "blocked_missing_evidence",
    "blocked_stale_source",
    "blocked_reference_only",
    "ready_for_internal_review",
    "ready_for_expert_review",
    "ready_for_private_beta_review",
    "closed",
}

BLOCKED_CLAIMS = [
    "tariff_confirmed",
    "cfia_compliant",
    "supplier_recommended",
    "buyer_validated",
    "ready_to_import",
    "public_launch_ready",
    "customs_or_tariff_advice_ready",
    "legal_or_compliance_approved",
]

SAFE_DISPLAY_STATUS = "Internal operator ready - external claims blocked"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slug(text: str) -> str:
    chars = [char if char.isalnum() else "-" for char in text.strip().lower()]
    compact = "-".join(part for part in "".join(chars).split("-") if part)
    return compact[:80] or "source-packet"


def _packet_id(packet: dict[str, Any]) -> str:
    existing = str(packet.get("packet_id") or packet.get("id") or "").strip()
    if existing:
        return existing
    name = str(packet.get("packet_name") or packet.get("product_name") or "source-packet")
    return f"packet-{_slug(name)}"


def _evidence_for_packet(packet_id: str, evidence_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in evidence_items if str(row.get("packet_id")) == packet_id]


def _status_for_evidence(row: dict[str, Any]) -> str:
    if str(row.get("rights_status") or "") in {"blocked", "unknown", "fixture_only"}:
        return "blocked_reference_only"
    if str(row.get("freshness_status") or "") in {"stale", "expired", "needs_current_refresh_before_claims"}:
        return "blocked_stale_source"
    if row.get("review_required") and str(row.get("human_review_status") or "") != "reviewed":
        return "needs_expert_review"
    return "ready_for_internal_review"


def build_evidence_ledger(
    evidence_items: list[dict[str, Any]], *, generated_at: str | None = None
) -> dict[str, Any]:
    rows = []
    counts: dict[str, int] = {}
    for raw in evidence_items:
        row = dict(raw)
        row.setdefault("evidence_id", row.get("id") or f"evidence-{len(rows) + 1}")
        row.setdefault("review_required", True)
        row.setdefault("human_review_status", "not_reviewed")
        row["ledger_status"] = _status_for_evidence(row)
        counts[row["ledger_status"]] = counts.get(row["ledger_status"], 0) + 1
        rows.append(row)
    return {
        "generated_at": generated_at or _now(),
        "kind": "evidence_ledger",
        "status": "evidence_ledger_ready_internal",
        "evidence_count": len(rows),
        "counts_by_status": counts,
        "rows": rows,
        "rule": "No evidence, no claim. Stale or reference-only evidence blocks customer-visible claims.",
        "proof_boundary": (
            "This ledger organizes evidence for internal review. It does not prove customs, tariff, "
            "CFIA, supplier, buyer, legal, or launch readiness."
        ),
    }


def _packet_blockers(packet: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_id = _packet_id(packet)
    blockers: list[dict[str, Any]] = []

    def add(suffix: str, module: str, issue: str, owner: str, next_valid_move: str, severity: str) -> None:
        blockers.append(
            {
                "id": f"{packet_id}:{suffix}",
                "packet_id": packet_id,
                "module": module,
                "severity": severity,
                "issue": issue,
                "owner": owner,
                "gate": "closed",
                "unsafe_to_bypass": True,
                "evidence": f"source packet {packet_id}",
                "next_valid_move": next_valid_move,
                "created_at": _now(),
                "resolved_at": "",
                "resolution_evidence_id": "",
            }
        )

    if not str(packet.get("source_url") or "").strip():
        add(
            "missing-source-url",
            "source_packet_intake",
            "source URL is missing",
            "customer",
            "Add a source URL or mark the packet as offline evidence-only.",
            "P1_blocks_external_claim",
        )
    if not evidence_rows:
        add(
            "missing-evidence",
            "evidence_ledger",
            "no evidence items are attached to this packet",
            "customer",
            "Attach at least one evidence item before readiness review.",
            "P1_blocks_external_claim",
        )
    for evidence in evidence_rows:
        ledger_status = str(evidence.get("ledger_status") or _status_for_evidence(evidence))
        if ledger_status == "blocked_reference_only":
            add(
                f"{evidence.get('evidence_id')}:reference-only",
                "evidence_ledger",
                "evidence is reference-only or has blocked/unknown rights",
                "operator",
                "Collect rights/freshness evidence or keep this claim reference-only.",
                "P1_blocks_external_claim",
            )
        if ledger_status == "blocked_stale_source":
            add(
                f"{evidence.get('evidence_id')}:stale",
                "official_source_refresh",
                "evidence freshness is stale or not proven",
                "research",
                "Refresh the official source and record accessed_at, last_verified_at, and content hash.",
                "P1_blocks_external_claim",
            )
        if ledger_status == "needs_expert_review":
            add(
                f"{evidence.get('evidence_id')}:expert-review",
                "expert_review",
                "evidence requires qualified human review",
                "compliance",
                "Create a reviewer packet and collect a scoped reviewer decision.",
                "P2_blocks_private_beta",
            )
    for field, module, owner, message in (
        ("restricted_party_screening_status", "restricted_party_screening", "operations", "Complete restricted-party screening."),
        ("qualified_review_status", "expert_review", "compliance", "Request qualified import/compliance review."),
        ("buyer_validation_status", "buyer_validation", "product", "Collect dated buyer/operator feedback."),
        ("contract_status", "commercial_contract", "operations", "Attach source-rights or commercial terms."),
    ):
        if str(packet.get(field) or "missing") not in {"complete", "reviewed", "signed", "validated"}:
            add(
                field.replace("_status", "-missing"),
                module,
                f"{field} is missing or incomplete",
                owner,
                message,
                "P1_blocks_external_claim",
            )
    return blockers


def _customer_status(blockers: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> str:
    modules = {str(row.get("module")) for row in blockers}
    if "evidence_ledger" in modules or not evidence_rows:
        return "blocked_missing_evidence"
    if "official_source_refresh" in modules:
        return "blocked_stale_source"
    if "expert_review" in modules:
        return "needs_expert_review"
    if blockers:
        return "needs_operator_review"
    return "ready_for_internal_review"


def _safe_report_summary(status: str) -> str:
    if status == "ready_for_internal_review":
        return (
            "This packet has enough structured information for internal operator review. "
            "External claims remain blocked until qualified review, source freshness, "
            "buyer validation, contracts, and launch gates are closed."
        )
    return (
        "This packet is not ready for external action. It needs more evidence, "
        "operator review, or qualified expert review before any customs, tariff, "
        "supplier, buyer, CFIA, legal, or launch claim can be made."
    )


def build_customer_workflow(
    *,
    source_packets: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    official_sources: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or _now()
    ledger = build_evidence_ledger(evidence_items, generated_at=generated)
    evidence_rows = ledger["rows"]
    packets = []
    all_blockers = []
    for raw_packet in source_packets:
        packet = dict(raw_packet)
        packet_id = _packet_id(packet)
        packet["packet_id"] = packet_id
        packet.setdefault("status", "submitted")
        linked_evidence = _evidence_for_packet(packet_id, evidence_rows)
        blockers = _packet_blockers(packet, linked_evidence)
        all_blockers.extend(blockers)
        customer_status = _customer_status(blockers, linked_evidence)
        if customer_status not in CUSTOMER_STATUS_LABELS:
            customer_status = "needs_operator_review"
        packets.append(
            {
                "packet_id": packet_id,
                "packet_name": packet.get("packet_name") or packet.get("product_name"),
                "product_name": packet.get("product_name"),
                "product_category": packet.get("product_category"),
                "origin_country": packet.get("origin_country"),
                "destination_country": packet.get("destination_country"),
                "supplier_name": packet.get("supplier_name"),
                "supplier_country": packet.get("supplier_country"),
                "hs_code_known": bool(packet.get("hs_code_known")),
                "hs_code_value": packet.get("hs_code_value"),
                "source_url": packet.get("source_url"),
                "intended_use": packet.get("intended_use"),
                "customer_visible_status": customer_status,
                "display_status": SAFE_DISPLAY_STATUS,
                "evidence_count": len(linked_evidence),
                "blocker_count": len(blockers),
                "blocked_claims": BLOCKED_CLAIMS,
                "blockers": blockers,
                "evidence_items": linked_evidence,
                "official_reference_count": len(official_sources),
                "safe_summary": _safe_report_summary(customer_status),
                "next_valid_move": (
                    blockers[0]["next_valid_move"]
                    if blockers
                    else "Proceed to internal operator review; external claims stay closed."
                ),
            }
        )
    return {
        "generated_at": generated,
        "kind": "customer_source_packet_workflow",
        "status": "customer_workflow_ready_internal",
        "display_status": SAFE_DISPLAY_STATUS,
        "packet_count": len(packets),
        "evidence_count": ledger["evidence_count"],
        "blocker_count": len(all_blockers),
        "packets": packets,
        "evidence_ledger": ledger,
        "blocked_claims": BLOCKED_CLAIMS,
        "official_sources": official_sources,
        "next_valid_move": "Use this workflow for internal/customer beta review only; collect missing evidence before external claims.",
        "proof_boundary": (
            "Customer source-packet workflow is local-first and fixture-backed. It produces safe readiness "
            "reports and blockers, not import approval, tariff confirmation, CFIA clearance, supplier "
            "recommendations, buyer validation, legal advice, or launch approval."
        ),
    }


def packet_from_submission(fields: dict[str, Any]) -> dict[str, Any]:
    product_name = str(fields.get("product_name") or fields.get("packet_name") or "Untitled source packet")
    packet_id = str(fields.get("packet_id") or f"packet-{_slug(product_name)}")
    return {
        "packet_id": packet_id,
        "packet_name": fields.get("packet_name") or product_name,
        "customer_id": fields.get("customer_id") or "local-customer",
        "organization_id": fields.get("organization_id") or "local-organization",
        "product_name": product_name,
        "product_category": fields.get("product_category") or "",
        "hs_code_known": bool(fields.get("hs_code_value") or fields.get("hs_code_known")),
        "hs_code_value": fields.get("hs_code_value") or "",
        "origin_country": fields.get("origin_country") or "",
        "destination_country": fields.get("destination_country") or "Canada",
        "supplier_name": fields.get("supplier_name") or "",
        "supplier_country": fields.get("supplier_country") or "",
        "source_url": fields.get("source_url") or "",
        "source_type": fields.get("source_type") or "customer_submitted",
        "intended_use": fields.get("intended_use") or "",
        "documents": fields.get("documents") or [],
        "notes": fields.get("notes") or "",
        "restricted_party_screening_status": "missing",
        "qualified_review_status": "missing",
        "buyer_validation_status": "missing",
        "contract_status": "missing",
        "created_at": _now(),
    }


def evidence_from_submission(packet: dict[str, Any]) -> dict[str, Any]:
    source_url = str(packet.get("source_url") or "")
    return {
        "evidence_id": f"evidence-{packet['packet_id']}-source",
        "packet_id": packet["packet_id"],
        "evidence_type": "source_url",
        "source_url": source_url,
        "file_path": "",
        "source_owner": packet.get("supplier_name") or "customer",
        "uploaded_by": packet.get("customer_id") or "local-customer",
        "created_at": _now(),
        "accessed_at": "",
        "last_verified_at": "",
        "expires_at": "",
        "rights_status": "unknown" if source_url else "blocked",
        "freshness_status": "needs_current_refresh_before_claims",
        "claim_supported": "source reference exists" if source_url else "",
        "claim_boundary": "Customer-submitted reference only until refreshed and reviewed.",
        "review_required": True,
        "human_review_status": "not_reviewed",
        "reviewed_by": "",
        "reviewed_at": "",
    }


def load_json_list(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(payload: dict[str, Any] | list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def markdown_report(workflow: dict[str, Any], packet_id: str) -> str:
    packets = {str(packet["packet_id"]): packet for packet in workflow.get("packets", [])}
    packet = packets[packet_id]
    blocker_lines = "\n".join(
        f"- {row['issue']}: {row['next_valid_move']}" for row in packet.get("blockers", [])
    ) or "- No blockers for internal review; external claims remain closed."
    claims = "\n".join(f"- {claim}" for claim in packet.get("blocked_claims", []))
    return "\n".join(
        [
            "# Importer Source Readiness Report",
            "",
            f"Packet: {packet['packet_name']}",
            f"Status: {packet['display_status']}",
            f"Customer-visible status: {packet['customer_visible_status']}",
            "",
            "## Summary",
            "",
            packet["safe_summary"],
            "",
            "## Blockers",
            "",
            blocker_lines,
            "",
            "## Blocked Claims",
            "",
            claims,
            "",
            "## Next Valid Move",
            "",
            str(packet["next_valid_move"]),
            "",
            "## Boundary",
            "",
            workflow["proof_boundary"],
            "",
        ]
    )


def contains_local_path(text: str) -> bool:
    return bool(
        re.search("/" + "Users" + r"/[^\s'\"<>\x60]+", text)
        or re.search("file:///" + "Users" + r"/[^\s'\"<>\x60]+", text)
    )
