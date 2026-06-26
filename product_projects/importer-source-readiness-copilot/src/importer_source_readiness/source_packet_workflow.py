"""Customer source-packet workflow for the importer readiness product."""

from __future__ import annotations

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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
    "source_refreshed_pending_review",
    "source_fresh_reference_only",
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

SAFE_DISPLAY_STATUS = "Internal logic ready - external claims blocked"
OPERATOR_WORKBENCH_STATUS = "Operator workbench usable for internal review"
CUSTOMER_PROTOTYPE_STATUS = "Customer packet prototype active - real customer use not enabled"
PRIVATE_BETA_STATUS = "Private beta blocked"

CUSTOMER_STATUS_COPY = {
    "blocked_missing_evidence": "Blocked - evidence missing",
    "blocked_stale_source": "Blocked - source freshness missing",
    "blocked_reference_only": "Blocked - reference-only evidence",
    "needs_expert_review": "Blocked - qualified review missing",
    "needs_operator_review": "Blocked - operator review required",
    "ready_for_internal_review": "Internal review ready - external claims blocked",
    "source_refreshed_pending_review": "Source refreshed - qualified review still required",
    "source_fresh_reference_only": "Fresh reference attached - external claims blocked",
}

BLOCKED_CLAIM_COPY = {
    "tariff_confirmed": "Tariff/HS classification",
    "cfia_compliant": "CFIA/food import compliance",
    "supplier_recommended": "Supplier/source confidence",
    "buyer_validated": "Buyer validation",
    "ready_to_import": "Import readiness",
    "public_launch_ready": "Commercial launch readiness",
    "customs_or_tariff_advice_ready": "Customs or tariff advice",
    "legal_or_compliance_approved": "Legal/compliance approval",
}

BLOCKER_GROUP_RULES = {
    "official_source_refresh": {
        "id": "source_freshness",
        "title": "Source Freshness",
        "stage": "P0 - Must fix before customer/private beta",
        "owner_role": "Research",
        "evidence_required": "Fresh official-source refresh record with accessed_at, last_verified_at, content_hash, HTTP status, and reviewer boundary.",
        "next_valid_move": "Refresh official sources and keep claims reference-only until qualified review.",
    },
    "evidence_ledger": {
        "id": "source_freshness",
        "title": "Source Freshness",
        "stage": "P0 - Must fix before customer/private beta",
        "owner_role": "Research",
        "evidence_required": "Traceable evidence item with freshness and rights metadata.",
        "next_valid_move": "Attach evidence and record freshness/rights metadata.",
    },
    "expert_review": {
        "id": "compliance_review",
        "title": "Compliance Review",
        "stage": "P0 - Must fix before customer/private beta",
        "owner_role": "Compliance",
        "evidence_required": "Scoped Canadian import/export, food, customs, or broker review finding.",
        "next_valid_move": "Generate a compliance review packet and request qualified review.",
    },
    "restricted_party_screening": {
        "id": "compliance_review",
        "title": "Compliance Review",
        "stage": "P0 - Must fix before customer/private beta",
        "owner_role": "Operations",
        "evidence_required": "Dated restricted-party screening record with source and reviewer boundary.",
        "next_valid_move": "Run restricted-party screening and attach the dated search record.",
    },
    "commercial_contract": {
        "id": "source_rights_contract",
        "title": "Source Rights / Contract",
        "stage": "P0 - Must fix before customer/private beta",
        "owner_role": "Operations",
        "evidence_required": "Signed source-rights, data-rights, or commercial terms record.",
        "next_valid_move": "Attach source-rights or commercial terms before external use.",
    },
    "buyer_validation": {
        "id": "buyer_validation",
        "title": "Buyer Validation",
        "stage": "P0 - Must fix before customer/private beta",
        "owner_role": "Product",
        "evidence_required": "Dated buyer/operator feedback tied to the packet and intended use.",
        "next_valid_move": "Collect buyer/operator validation before demand or PMF claims.",
    },
    "source_packet_intake": {
        "id": "source_freshness",
        "title": "Source Freshness",
        "stage": "P0 - Must fix before customer/private beta",
        "owner_role": "Customer",
        "evidence_required": "A source URL or offline evidence reference.",
        "next_valid_move": "Add a source URL or mark the packet as offline evidence-only.",
    },
}

PRIVATE_BETA_BLOCKERS = [
    {
        "id": "security_private_beta_controls",
        "title": "Security / Private Beta",
        "stage": "P0 - Must fix before customer/private beta",
        "status": "blocked",
        "next_valid_move": "Add auth, organizations, roles, audit logs, upload controls, backup, and incident-response procedures.",
    },
    {
        "id": "legal_privacy_terms",
        "title": "Legal / Privacy",
        "stage": "P0 - Must fix before customer/private beta",
        "status": "blocked",
        "next_valid_move": "Create privacy notice, terms, data deletion policy, and qualified legal/privacy review packet.",
    },
    {
        "id": "launch_claims",
        "title": "Launch Claims",
        "stage": "P1 - Must fix before public launch",
        "status": "blocked",
        "next_valid_move": "Keep public launch and external-action claims closed until human approvals and external proof exist.",
    },
]

REQUIRED_EVIDENCE = [
    "Fresh official-source refresh",
    "Qualified Canada compliance review",
    "Commercial/source contract",
    "Buyer/operator validation",
    "Restricted-party screening record",
]

AI_REVIEWERS = [
    ("canada_compliance", "Canada compliance simulation", "Compliance"),
    ("privacy_legal", "Privacy/legal simulation", "Legal / Privacy"),
    ("source_rights", "Source-rights simulation", "Operations"),
    ("buyer_validation", "Buyer-validation simulation", "Product"),
    ("launch_gate", "Launch-gate simulation", "Launch"),
]


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


def _sha256(text: str | bytes) -> str:
    data = text if isinstance(text, bytes) else text.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _evidence_for_packet(packet_id: str, evidence_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in evidence_items if str(row.get("packet_id")) == packet_id]


def _evidence_labels(row: dict[str, Any]) -> list[str]:
    labels = [str(row.get("evidence_type") or "evidence")]
    rights = str(row.get("rights_status") or "")
    freshness = str(row.get("freshness_status") or "")
    if rights in {"public_reference_only", "reference_only", "unknown", "fixture_only"}:
        labels.append("reference_only")
    if freshness in {"stale", "expired", "needs_current_refresh_before_claims"}:
        labels.append("stale")
    if freshness in {"source_fresh_reference_only", "fresh_reference_only", "fresh"}:
        labels.append("source_refreshed")
    if str(row.get("human_review_status") or "") == "reviewed":
        labels.append("human_reviewed")
    if row.get("review_required"):
        labels.append("review_required")
    if str(row.get("uploaded_by") or "").startswith("demo"):
        labels.append("fixture")
    return sorted(set(labels))


def _status_for_evidence(row: dict[str, Any]) -> str:
    if str(row.get("rights_status") or "") in {"blocked", "unknown", "fixture_only"}:
        return "blocked_reference_only"
    if str(row.get("freshness_status") or "") in {"stale", "expired", "needs_current_refresh_before_claims"}:
        return "blocked_stale_source"
    if row.get("review_required") and str(row.get("human_review_status") or "") != "reviewed":
        return "needs_expert_review"
    return "ready_for_internal_review"


def _evidence_summary(evidence_rows: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [label for row in evidence_rows for label in row.get("labels", _evidence_labels(row))]
    counts = {
        "attached": len(evidence_rows),
        "accepted": sum(1 for row in evidence_rows if str(row.get("ledger_status")) == "ready_for_internal_review"),
        "stale": labels.count("stale"),
        "reference_only": labels.count("reference_only"),
        "human_reviewed": labels.count("human_reviewed"),
    }
    missing = _missing_evidence(blockers)
    counts["missing"] = len(missing)
    return {
        **counts,
        "missing_items": missing,
        "summary": (
            f"{counts['attached']} attached / {len(missing)} missing; "
            f"{counts['stale']} stale; {counts['reference_only']} reference-only"
        ),
    }


def _missing_evidence(blockers: list[dict[str, Any]]) -> list[str]:
    modules = {str(row.get("module") or "") for row in blockers}
    missing = []
    if "official_source_refresh" in modules or "evidence_ledger" in modules:
        missing.append("Fresh official-source refresh")
    if "expert_review" in modules:
        missing.append("Qualified Canada compliance review")
    if "commercial_contract" in modules:
        missing.append("Commercial/source contract")
    if "buyer_validation" in modules:
        missing.append("Buyer/operator validation")
    if "restricted_party_screening" in modules:
        missing.append("Restricted-party screening record")
    for item in REQUIRED_EVIDENCE:
        if item not in missing:
            missing.append(item)
    return missing


def _group_rule(row: dict[str, Any]) -> dict[str, str]:
    module = str(row.get("module") or "")
    return BLOCKER_GROUP_RULES.get(
        module,
        {
            "id": "product_improvement",
            "title": "Product Improvements",
            "stage": "P2 - Product improvements",
            "owner_role": str(row.get("owner") or "operator"),
            "evidence_required": "Attach scoped evidence for this blocker.",
            "next_valid_move": str(row.get("next_valid_move") or "Attach scoped evidence and rerun review."),
        },
    )


def group_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {
        "source_freshness": 0,
        "compliance_review": 1,
        "source_rights_contract": 2,
        "buyer_validation": 3,
        "legal_privacy": 4,
        "security_private_beta_controls": 5,
        "launch_claims": 6,
    }
    grouped: dict[str, dict[str, Any]] = {}
    for row in blockers:
        rule = _group_rule(row)
        group = grouped.setdefault(
            rule["id"],
            {
                "id": rule["id"],
                "title": rule["title"],
                "stage": rule["stage"],
                "owner_role": rule["owner_role"],
                "status": "blocked",
                "priority": priority.get(rule["id"], 99),
                "blocker_count": 0,
                "issues": [],
                "evidence_required": rule["evidence_required"],
                "next_valid_move": rule["next_valid_move"],
                "blocker_ids": [],
            },
        )
        group["blocker_count"] += 1
        group["issues"].append(str(row.get("issue")))
        group["blocker_ids"].append(str(row.get("id")))
    ordered = sorted(grouped.values(), key=lambda row: (int(row.get("priority", 99)), str(row["title"])))
    return ordered


def build_evidence_ledger(
    evidence_items: list[dict[str, Any]], *, generated_at: str | None = None
) -> dict[str, Any]:
    rows = []
    counts: dict[str, int] = {}
    quality_counts: dict[str, int] = {}
    for raw in evidence_items:
        row = dict(raw)
        row.setdefault("evidence_id", row.get("id") or f"evidence-{len(rows) + 1}")
        row.setdefault("review_required", True)
        row.setdefault("human_review_status", "not_reviewed")
        row["ledger_status"] = _status_for_evidence(row)
        row["labels"] = _evidence_labels(row)
        row["quality_status"] = (
            "accepted"
            if row["ledger_status"] == "ready_for_internal_review"
            else "stale"
            if "stale" in row["labels"]
            else "reference_only"
            if "reference_only" in row["labels"]
            else "review_required"
        )
        counts[row["ledger_status"]] = counts.get(row["ledger_status"], 0) + 1
        quality_counts[row["quality_status"]] = quality_counts.get(row["quality_status"], 0) + 1
        rows.append(row)
    return {
        "generated_at": generated_at or _now(),
        "kind": "evidence_ledger",
        "status": "evidence_ledger_ready_internal",
        "evidence_count": len(rows),
        "counts_by_status": counts,
        "counts_by_quality": quality_counts,
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
        rule = BLOCKER_GROUP_RULES.get(module, {})
        blockers.append(
            {
                "id": f"{packet_id}:{suffix}",
                "packet_id": packet_id,
                "module": module,
                "group": rule.get("id", "product_improvement"),
                "group_title": rule.get("title", "Product Improvements"),
                "severity": severity,
                "issue": issue,
                "owner": owner,
                "owner_role": rule.get("owner_role", owner),
                "gate": "closed",
                "status": "open",
                "unsafe_to_bypass": True,
                "evidence": f"source packet {packet_id}",
                "evidence_required": rule.get("evidence_required", "Attach scoped evidence for this blocker."),
                "claim_blocked": rule.get("title", "external claim"),
                "resolution_actions": ["attach_evidence", "request_review", "add_note", "resolve_with_evidence", "mark_not_applicable"],
                "human_gate_required": True,
                "human_reviewer": "not_assigned",
                "review_type": "not_started",
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


def _status_reason(status: str) -> str:
    return CUSTOMER_STATUS_COPY.get(status, status.replace("_", " "))


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


def build_ai_review_run(
    workflow: dict[str, Any], packet_id: str, *, generated_at: str | None = None
) -> dict[str, Any]:
    packets = {str(packet.get("packet_id")): packet for packet in workflow.get("packets", [])}
    packet = packets[packet_id]
    blocker_groups = packet.get("blocker_groups", [])
    group_titles = {str(row.get("title")) for row in blocker_groups}
    results = []
    for reviewer_id, title, owner_role in AI_REVIEWERS:
        relevant = [
            row
            for row in blocker_groups
            if row.get("title") in group_titles
            and (
                owner_role in str(row.get("owner_role"))
                or row.get("title") in {"Compliance Review", "Legal / Privacy", "Buyer Validation", "Source Rights / Contract", "Launch Claims"}
            )
        ]
        results.append(
            {
                "reviewer_id": reviewer_id,
                "title": title,
                "owner_role": owner_role,
                "review_type": "AI simulated review",
                "human_gate_required": True,
                "human_reviewer": "not_assigned",
                "status": "blocked_human_gate_required",
                "finding": "Simulation can create blockers and next moves; it cannot open external-world approval gates.",
                "blocker_group_ids": [str(row.get("id")) for row in relevant],
                "next_valid_move": "Export the expert review packet and collect a scoped human decision.",
            }
        )
    return {
        "run_id": f"ai-review-{packet_id}-{(generated_at or _now()).replace(':', '').replace('+', 'Z')}",
        "packet_id": packet_id,
        "generated_at": generated_at or _now(),
        "review_type": "AI simulated review",
        "status": "simulated_review_complete_human_gates_closed",
        "human_gate": "required_before_external_claims",
        "results": results,
        "claim_boundary": "AI simulated review creates blockers and next moves only. It does not replace brokers, counsel, buyers, operators, or qualified reviewers.",
    }


def _private_beta_readiness(blocker_groups: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [dict(row) for row in blocker_groups]
    for row in PRIVATE_BETA_BLOCKERS:
        if row["id"] not in {str(group.get("id")) for group in blocked}:
            blocked.append(dict(row))
    return {
        "status": "blocked",
        "display_status": PRIVATE_BETA_STATUS,
        "ready": [
            "Internal operator logic",
            "Blocker engine",
            "Official source registry",
            "Unsafe gate closure",
            "Customer packet prototype",
            "Evidence ledger",
        ],
        "blocked": blocked,
        "next_valid_move": "Complete source refresh proof, privacy/legal terms, qualified review workflow, buyer validation, source contracts, and private-beta security controls.",
    }


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
        evidence_summary = _evidence_summary(linked_evidence, blockers)
        blocker_groups = group_blockers(blockers)
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
                "customer_visible_status_label": _status_reason(customer_status),
                "readiness_status": "not_ready_for_external_action" if blockers else "internal_review_ready",
                "readiness_status_label": (
                    "Blocked - not ready for external action"
                    if blockers
                    else "Internal review ready - external claims blocked"
                ),
                "display_status": SAFE_DISPLAY_STATUS,
                "evidence_count": len(linked_evidence),
                "evidence_summary": evidence_summary,
                "blocker_count": len(blockers),
                "blocked_claims": BLOCKED_CLAIMS,
                "blocked_claims_display": [BLOCKED_CLAIM_COPY[claim] for claim in BLOCKED_CLAIMS],
                "blockers": blockers,
                "blocker_groups": blocker_groups,
                "top_blockers": blocker_groups[:6],
                "allowed_actions": [
                    "Internal review",
                    "Draft readiness report",
                    "Expert review packet",
                    "AI simulated review",
                    "Official-source refresh record",
                ],
                "not_allowed_actions": [
                    "Import readiness claim",
                    "Tariff confirmation",
                    "CFIA clearance",
                    "Supplier recommendation",
                    "Buyer validation claim",
                    "Public launch claim",
                ],
                "evidence_items": linked_evidence,
                "official_reference_count": len(official_sources),
                "safe_summary": _safe_report_summary(customer_status),
                "actions": [
                    {
                        "id": "refresh_sources",
                        "label": "Refresh Official Sources",
                        "method": "POST",
                        "route": f"/source-packets/{packet_id}/actions",
                    },
                    {
                        "id": "upload_evidence",
                        "label": "Upload Evidence",
                        "method": "POST",
                        "route": f"/source-packets/{packet_id}/actions",
                    },
                    {
                        "id": "request_operator_review",
                        "label": "Request Operator Review",
                        "method": "POST",
                        "route": f"/source-packets/{packet_id}/actions",
                    },
                    {
                        "id": "run_ai_review",
                        "label": "Run AI Review",
                        "method": "POST",
                        "route": f"/source-packets/{packet_id}/actions",
                    },
                    {
                        "id": "generate_expert_packet",
                        "label": "Generate Expert Review Packet",
                        "method": "POST",
                        "route": f"/source-packets/{packet_id}/actions",
                    },
                    {
                        "id": "export_report",
                        "label": "Export Readiness Report",
                        "method": "GET",
                        "route": f"/source-packets/{packet_id}/export",
                    },
                ],
                "next_valid_move": (
                    blocker_groups[0]["next_valid_move"]
                    if blocker_groups
                    else "Proceed to internal operator review; external claims stay closed."
                ),
            }
        )
    workflow_blocker_groups = group_blockers(all_blockers)
    workflow: dict[str, Any] = {
        "generated_at": generated,
        "kind": "customer_source_packet_workflow",
        "status": "customer_workflow_ready_internal",
        "display_status": SAFE_DISPLAY_STATUS,
        "operator_display_status": OPERATOR_WORKBENCH_STATUS,
        "customer_stage": "Customer packet prototype",
        "customer_stage_status": CUSTOMER_PROTOTYPE_STATUS,
        "private_beta_status": "blocked",
        "packet_count": len(packets),
        "evidence_count": ledger["evidence_count"],
        "blocker_count": len(all_blockers),
        "blocker_groups": workflow_blocker_groups,
        "top_blockers": _private_beta_readiness(workflow_blocker_groups)["blocked"][:6],
        "packets": packets,
        "evidence_ledger": ledger,
        "blocked_claims": BLOCKED_CLAIMS,
        "blocked_claims_display": [BLOCKED_CLAIM_COPY[claim] for claim in BLOCKED_CLAIMS],
        "official_sources": official_sources,
        "private_beta_readiness": _private_beta_readiness(workflow_blocker_groups),
        "next_valid_move": "Use this workflow for internal/customer beta review only; collect missing evidence before external claims.",
        "proof_boundary": (
            f"{CUSTOMER_PROTOTYPE_STATUS}. It produces safe readiness reports and blockers, not import "
            "approval, tariff confirmation, CFIA clearance, supplier recommendations, buyer validation, "
            "legal advice, or launch approval."
        ),
    }
    workflow["ai_review_runs"] = [
        build_ai_review_run(workflow, str(packet["packet_id"]), generated_at=generated)
        for packet in packets
    ]
    return {
        **workflow,
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


def _default_fetch_source(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "ImporterSourceReadinessCopilot/0.1"})
    try:
        with urlopen(request, timeout=8) as response:  # noqa: S310 - user-triggered reference refresh.
            content = response.read(300_000)
            return {
                "http_status": int(getattr(response, "status", 0) or 0),
                "content": content,
                "error": "",
            }
    except HTTPError as exc:
        return {"http_status": exc.code, "content": b"", "error": str(exc)}
    except URLError as exc:
        return {"http_status": 0, "content": b"", "error": str(exc)}
    except TimeoutError as exc:
        return {"http_status": 0, "content": b"", "error": str(exc)}


def refresh_packet_sources(
    *,
    packet_id: str,
    evidence_items: list[dict[str, Any]],
    actor: str = "local_operator",
    generated_at: str | None = None,
    fetcher: Any | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = generated_at or _now()
    fetch = fetcher or _default_fetch_source
    refresh_run_id = f"source-refresh-{packet_id}-{generated.replace(':', '').replace('+', 'Z')}"
    updated: list[dict[str, Any]] = []
    rows = []
    for raw in evidence_items:
        row = dict(raw)
        if str(row.get("packet_id")) != packet_id or not str(row.get("source_url") or ""):
            updated.append(row)
            continue
        before_hash = str(row.get("content_hash") or "")
        result = fetch(str(row["source_url"]))
        content = result.get("content") or b""
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = bytes(content)
        content_hash = _sha256(content_bytes or str(row.get("source_url") or ""))
        http_status = int(result.get("http_status") or 0)
        row.update(
            {
                "accessed_at": generated,
                "last_verified_at": generated if http_status and http_status < 500 else str(row.get("last_verified_at") or ""),
                "content_hash": content_hash,
                "http_status": http_status,
                "refresh_actor": actor,
                "refresh_run_id": refresh_run_id,
                "source_changed": bool(before_hash and before_hash != content_hash),
                "refresh_error": str(result.get("error") or ""),
            }
        )
        if 200 <= http_status < 400:
            row["freshness_status"] = "source_fresh_reference_only"
            row["claim_boundary"] = (
                "Fresh reference-only source. It still does not prove tariff, CFIA, supplier, buyer, "
                "legal, customs, or import readiness without qualified review."
            )
        rows.append(
            {
                "evidence_id": row.get("evidence_id"),
                "source_url": row.get("source_url"),
                "http_status": http_status,
                "content_hash": content_hash,
                "source_changed": row.get("source_changed"),
                "freshness_status": row.get("freshness_status"),
                "error": row.get("refresh_error"),
            }
        )
        updated.append(row)
    report = {
        "refresh_run_id": refresh_run_id,
        "packet_id": packet_id,
        "actor": actor,
        "generated_at": generated,
        "status": "source_refresh_recorded",
        "row_count": len(rows),
        "rows": rows,
        "claim_boundary": "Refresh records close stale-source proof only when HTTP access succeeds. They do not approve external claims.",
    }
    return updated, report


def expert_review_packet_markdown(workflow: dict[str, Any], packet_id: str) -> str:
    packets = {str(packet["packet_id"]): packet for packet in workflow.get("packets", [])}
    packet = packets[packet_id]
    refs = "\n".join(
        f"- {row.get('name')}: {row.get('url')} ({row.get('claim_boundary')})"
        for row in workflow.get("official_sources", [])[:8]
    )
    evidence = "\n".join(
        f"- {row.get('evidence_id')}: {row.get('evidence_type')} | {row.get('ledger_status')} | {row.get('claim_boundary')}"
        for row in packet.get("evidence_items", [])
    )
    questions = "\n".join(
        [
            "- What exact import, tariff, CFIA, food, or customs claims can be supported by the evidence?",
            "- Which claims must remain closed?",
            "- Which additional documents, source records, or screenings are required?",
            "- Is the review limited to reference orientation, or does it support a scoped operational decision?",
        ]
    )
    blockers = "\n".join(
        f"- {row.get('title')}: {row.get('next_valid_move')}" for row in packet.get("blocker_groups", [])
    )
    return "\n".join(
        [
            "# Expert Review Packet",
            "",
            f"Packet: {packet['packet_name']}",
            f"Product: {packet.get('product_name')}",
            f"Destination: {packet.get('destination_country')}",
            "",
            "## Review Scope",
            "",
            "This packet requests scoped human/expert review. AI simulation and source refresh records do not open external-world gates.",
            "",
            "## Evidence Items",
            "",
            evidence or "- No evidence attached.",
            "",
            "## Grouped Blockers",
            "",
            blockers or "- No grouped blockers.",
            "",
            "## Official References",
            "",
            refs or "- No official references.",
            "",
            "## Questions For Reviewer",
            "",
            questions,
            "",
            "## Reviewer Response Template",
            "",
            "- Reviewer name:",
            "- Qualification / organization:",
            "- Scope reviewed:",
            "- Claims supported:",
            "- Claims rejected or still blocked:",
            "- Additional evidence required:",
            "- Date:",
            "",
        ]
    )


def markdown_report(workflow: dict[str, Any], packet_id: str) -> str:
    packets = {str(packet["packet_id"]): packet for packet in workflow.get("packets", [])}
    packet = packets[packet_id]
    blocker_lines = "\n".join(
        f"- {row['title']}: {row['next_valid_move']}" for row in packet.get("blocker_groups", [])
    ) or "- No blockers for internal review; external claims remain closed."
    claims = "\n".join(f"- {claim}" for claim in packet.get("blocked_claims_display", []))
    missing = "\n".join(f"- {item}" for item in packet.get("evidence_summary", {}).get("missing_items", []))
    refs = "\n".join(
        f"- {row.get('name')}: {row.get('claim_boundary')}"
        for row in workflow.get("official_sources", [])[:6]
    )
    return "\n".join(
        [
            "# Importer Source Readiness Report",
            "",
            f"Packet: {packet['packet_name']}",
            f"Status: {packet['display_status']}",
            f"Customer-visible status: {packet['customer_visible_status_label']}",
            "",
            "## Summary",
            "",
            packet["safe_summary"],
            "",
            "## Evidence Summary",
            "",
            str(packet.get("evidence_summary", {}).get("summary", "")),
            "",
            "## Missing Evidence",
            "",
            missing,
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
            "## Official References",
            "",
            refs,
            "",
            "## Review Required",
            "",
            "Qualified human review is required before external-world claims can open.",
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
