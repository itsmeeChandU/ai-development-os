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

from .product_runtime import AI_PROCESSING_MODES, SENSITIVITY_LEVELS, route_ai_task

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
    "ready_to_export_to_canada",
    "canadian_importer_confirmed",
    "export_documentation_complete",
    "trade_agreement_preference_confirmed",
    "public_launch_ready",
    "customs_or_tariff_advice_ready",
    "legal_or_compliance_approved",
]

PUBLIC_PRODUCT_NAME = "Trade Readiness Copilot"
PUBLIC_PRODUCT_PROMISE = "Before you import or export, know what is missing."
TRADE_DIRECTIONS = {"import", "export", "both", "unknown"}
INCOTERMS = {"EXW", "FCA", "FOB", "CFR", "CIF", "DAP", "DPU", "DDP", "unknown"}
IMPORTER_OF_RECORD_VALUES = {"buyer", "importer", "exporter", "seller", "broker", "unknown"}
EXPORTER_USER_TYPES = {"foreign_exporter", "seller_to_canada", "foreign exporter / seller to canada"}

TRADE_DOCUMENT_FIELDS = [
    "product_documents",
    "commercial_documents",
    "certificates",
    "proof_of_origin",
    "product_specs",
    "commercial_invoice",
    "packing_list",
    "shipping_method",
    "food_health_docs",
    "source_supplier_docs",
    "contract_po",
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
    "ready_to_export_to_canada": "Export-to-Canada readiness",
    "canadian_importer_confirmed": "Canadian buyer/importer confirmation",
    "export_documentation_complete": "Export document completeness",
    "trade_agreement_preference_confirmed": "Trade agreement or MoU preference claim",
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
    "importer_of_record": {
        "id": "canada_import_responsibility",
        "title": "Canada Import Responsibility",
        "stage": "P0 - Must fix before shipment or buyer packet",
        "owner_role": "Trade Ops",
        "evidence_required": "Canadian buyer/importer of record, Incoterms, responsibility split, and broker/reviewer boundary.",
        "next_valid_move": "Confirm who is importer of record, whether terms are buyer-import or delivered/DDP, and route to broker review.",
    },
    "import_controls": {
        "id": "canada_import_controls",
        "title": "Canada Import Controls",
        "stage": "P0 - Must fix before shipment decision",
        "owner_role": "Compliance",
        "evidence_required": "Current Canadian import-control, CBSA/CARM, CFIA/AIRS when relevant, permit, and broker-review evidence.",
        "next_valid_move": "Check official Canadian references and generate a broker review packet before any shipment decision.",
    },
    "product_documentation": {
        "id": "document_readiness",
        "title": "Document Readiness",
        "stage": "P0 - Must fix before buyer/broker packet",
        "owner_role": "Customer",
        "evidence_required": "Product specs, invoice/proforma, packing list, certificates, shipping docs, and buyer/broker correspondence where available.",
        "next_valid_move": "Upload missing product, commercial, certificate, and shipping documents.",
    },
    "proof_of_origin": {
        "id": "document_readiness",
        "title": "Document Readiness",
        "stage": "P0 - Must fix before buyer/broker packet",
        "owner_role": "Customer",
        "evidence_required": "Country-of-origin proof and any preference/MoU claim evidence with official review boundary.",
        "next_valid_move": "Attach proof of origin and keep preference or MoU claims blocked until official evidence and qualified review exist.",
    },
    "exporter_side_readiness": {
        "id": "exporter_side_readiness",
        "title": "Exporter-Side Readiness",
        "stage": "P1 - Must fix before export packet",
        "owner_role": "Exporter",
        "evidence_required": "Exporter-side registration, permits, certificates, banking/shipping, and country-specific export documents.",
        "next_valid_move": "Collect origin-country export readiness evidence or assign an expert lane for country-specific review.",
    },
    "trade_agreement_claim": {
        "id": "trade_agreement_review",
        "title": "Trade Agreement / Preference Review",
        "stage": "P0 - Must fix before commercial claim",
        "owner_role": "Compliance",
        "evidence_required": "Official agreement, MoU, rules-of-origin, certificate, and qualified-review evidence for any preference claim.",
        "next_valid_move": "Keep agreement/preference claims blocked and generate an expert review packet.",
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
    "Canadian buyer/importer and importer-of-record confirmation",
    "Incoterms or delivery responsibility record",
    "Product and commercial documents",
    "Proof of origin",
    "Broker/expert review packet",
]

AI_REVIEWERS = [
    ("canada_compliance", "Canada compliance simulation", "Compliance"),
    ("privacy_legal", "Privacy/legal simulation", "Legal / Privacy"),
    ("source_rights", "Source-rights simulation", "Operations"),
    ("buyer_validation", "Buyer-validation simulation", "Product"),
    ("launch_gate", "Launch-gate simulation", "Launch"),
]

KNOWN_ORGANIZATION_IDS = {"org-importer-demo", "org-other-demo", "org-internal-ops"}
LEGACY_ORGANIZATION_ALIASES = {
    "demo-importer-org": "org-importer-demo",
    "local-organization": "org-importer-demo",
    "local-customer": "org-importer-demo",
}


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


def _organization_id(row: dict[str, Any]) -> str:
    raw = str(row.get("organization_id") or "").strip()
    if raw in KNOWN_ORGANIZATION_IDS:
        return raw
    return LEGACY_ORGANIZATION_ALIASES.get(raw, "org-importer-demo")


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
    if str(row.get("ai_processing_mode") or "") in {"no_ai", "on_prem_manual"} or row.get("ai_processing_allowed") is False:
        labels.append("ai_blocked")
    else:
        labels.append("ai_allowed")
    if row.get("redaction_required"):
        labels.append("redaction_required")
    if str(row.get("uploaded_by") or "").startswith("demo"):
        labels.append("fixture")
    return sorted(set(labels))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,;\n]+", text) if part.strip()]


def _truthy_text(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return bool(text and text not in {"unknown", "missing", "not sure", "n/a", "none", "no"})


def _country_is_canada(value: Any) -> bool:
    return str(value or "").strip().lower() in {"canada", "ca", "can"}


def _valid_trade_direction(value: Any, *, default: str = "unknown") -> str:
    candidate = str(value or default).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "imports": "import",
        "import_to_canada": "import",
        "exports": "export",
        "export_to_canada": "export",
        "import_export": "both",
        "import_and_export": "both",
    }
    direction = aliases.get(candidate, candidate)
    return direction if direction in TRADE_DIRECTIONS else default


def _trade_direction(packet: dict[str, Any]) -> str:
    explicit = _valid_trade_direction(packet.get("trade_direction"))
    if explicit != "unknown":
        return explicit
    user_type = str(packet.get("user_type") or "").strip().lower()
    if user_type in EXPORTER_USER_TYPES or ("exporter" in user_type and _country_is_canada(packet.get("destination_country"))):
        return "export"
    if _country_is_canada(packet.get("destination_country")) and not _country_is_canada(packet.get("origin_country")):
        return "import"
    return "unknown"


def _normal_importer_of_record(packet: dict[str, Any]) -> str:
    raw = (
        packet.get("importer_of_record")
        or packet.get("import_responsibility")
        or packet.get("canadian_import_responsibility")
        or "unknown"
    )
    candidate = str(raw).strip().lower().replace(" ", "_")
    aliases = {
        "canadian_buyer": "buyer",
        "buyer_importer": "buyer",
        "foreign_exporter": "exporter",
        "seller_to_canada": "exporter",
        "nri": "exporter",
        "non_resident_importer": "exporter",
        "customs_broker": "broker",
    }
    value = aliases.get(candidate, candidate)
    return value if value in IMPORTER_OF_RECORD_VALUES else "unknown"


def _normal_incoterms(packet: dict[str, Any]) -> str:
    raw = packet.get("incoterms_if_known") or packet.get("incoterms") or packet.get("delivery_responsibility") or "unknown"
    candidate = str(raw).strip().upper().replace(" ", "_")
    return candidate if candidate in INCOTERMS else "unknown"


def _evidence_text(evidence_rows: list[dict[str, Any]]) -> str:
    fields = ["title", "description", "evidence_type", "document_type", "claim_supported", "file_path", "source_url"]
    return " ".join(str(row.get(field) or "") for row in evidence_rows for field in fields).lower()


def _document_flags(packet: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, bool]:
    packet_text = " ".join(
        " ".join(_as_list(packet.get(field))) if field in packet else ""
        for field in TRADE_DOCUMENT_FIELDS
    ).lower()
    text = f"{packet_text} {_evidence_text(evidence_rows)}"
    return {
        "product_documents": _truthy_text(packet.get("product_documents"))
        or _truthy_text(packet.get("product_specs"))
        or any(keyword in text for keyword in ("product spec", "specification", "lab report", "certificate")),
        "commercial_documents": _truthy_text(packet.get("commercial_documents"))
        or _truthy_text(packet.get("commercial_invoice"))
        or _truthy_text(packet.get("contract_po"))
        or any(keyword in text for keyword in ("invoice", "proforma", "packing list", "purchase order", "contract")),
        "certificates": _truthy_text(packet.get("certificates"))
        or _truthy_text(packet.get("food_health_docs"))
        or any(keyword in text for keyword in ("certificate", "coo", "origin", "health", "food safety")),
        "proof_of_origin": _truthy_text(packet.get("proof_of_origin"))
        or any(keyword in text for keyword in ("certificate of origin", "proof of origin", "country of origin")),
        "buyer_or_broker_correspondence": any(keyword in text for keyword in ("buyer email", "broker", "correspondence")),
    }


def _responsibility_path(packet: dict[str, Any]) -> dict[str, str]:
    importer_of_record = _normal_importer_of_record(packet)
    incoterms = _normal_incoterms(packet)
    if importer_of_record in {"buyer", "importer"} and incoterms != "DDP":
        return {
            "path": "Path A - Canadian buyer/importer handles import",
            "responsibility_level": "buyer_importer_led",
            "guidance": "Prepare a buyer-ready export packet and questions for the Canadian importer or broker.",
        }
    if importer_of_record == "exporter" or incoterms == "DDP":
        return {
            "path": "Path B - exporter may carry Canadian import responsibility",
            "responsibility_level": "high_exporter_responsibility",
            "guidance": "Generate a broker review packet before any delivered-into-Canada or importer-of-record decision.",
        }
    return {
        "path": "Responsibility path unknown",
        "responsibility_level": "unknown",
        "guidance": "Confirm importer of record and Incoterms before shipment or buyer claims.",
    }


def _lane_status(blockers: list[dict[str, Any]], modules: set[str], default_next: str) -> dict[str, Any]:
    rows = [row for row in blockers if str(row.get("module")) in modules]
    groups = group_blockers(rows)
    return {
        "status": "blocked" if rows else "draft_ready_for_internal_review",
        "blocker_count": len(rows),
        "blocker_ids": [str(row.get("id")) for row in rows],
        "blocker_groups": groups,
        "next_valid_move": groups[0]["next_valid_move"] if groups else default_next,
    }


def _readiness_lanes(packet: dict[str, Any], evidence_rows: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    direction = _trade_direction(packet)
    lanes = [
        {
            "id": "exporter_side_readiness",
            "name": "Exporter-side readiness",
            "trade_direction": direction,
            "country_scope": str(packet.get("exporter_country") or packet.get("origin_country") or "origin country"),
            "fields": {
                "exporter_name": packet.get("exporter_name") or "",
                "exporter_country": packet.get("exporter_country") or packet.get("origin_country") or "",
                "documents": _as_list(packet.get("product_documents")) + _as_list(packet.get("commercial_documents")) + _as_list(packet.get("certificates")),
            },
            **_lane_status(
                blockers,
                {"exporter_side_readiness", "product_documentation", "proof_of_origin", "commercial_contract"},
                "Prepare exporter-side documents for internal review; external claims stay blocked.",
            ),
        },
        {
            "id": "importer_side_readiness",
            "name": "Importer-side readiness",
            "trade_direction": direction,
            "country_scope": str(packet.get("importer_country") or packet.get("destination_country") or "destination country"),
            "fields": {
                "importer_name": packet.get("importer_name") or packet.get("buyer_name") or "",
                "importer_of_record": _normal_importer_of_record(packet),
                "incoterms": _normal_incoterms(packet),
            },
            **_lane_status(
                blockers,
                {"importer_of_record", "import_controls", "expert_review", "restricted_party_screening", "official_source_refresh"},
                "Confirm Canadian importer, controls, and broker review before shipment decisions.",
            ),
        },
    ]
    if direction in {"import", "both", "unknown"}:
        lanes[0]["note"] = "Source/exporter-side facts still matter even when the customer is the Canadian importer."
    return lanes


def _buyer_broker_questions(packet: dict[str, Any]) -> list[str]:
    responsibility = _responsibility_path(packet)
    return [
        "Who is the Canadian importer of record for this shipment?",
        "Which Incoterms or delivery responsibility applies?",
        "What HS/tariff classification should a qualified reviewer use for the product?",
        "Does the product need CFIA/AIRS, import permit, controlled goods, sanctions, or restricted-party review?",
        "Which product specs, invoice/proforma, packing list, certificate, proof-of-origin, and contract documents are still missing?",
        "Can the Canadian buyer or broker confirm the next valid evidence to collect?",
        f"Responsibility path: {responsibility['path']}.",
    ]


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
        "requires_review": labels.count("review_required"),
        "ai_allowed": labels.count("ai_allowed"),
        "ai_blocked": labels.count("ai_blocked"),
        "redaction_required": labels.count("redaction_required"),
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
    if "importer_of_record" in modules:
        missing.append("Canadian buyer/importer and importer-of-record confirmation")
        missing.append("Incoterms or delivery responsibility record")
    if "import_controls" in modules:
        missing.append("Canadian import-control, CBSA/CARM, CFIA/AIRS, permit, or broker review")
    if "product_documentation" in modules:
        missing.append("Product and commercial documents")
    if "proof_of_origin" in modules:
        missing.append("Proof of origin")
    if "exporter_side_readiness" in modules:
        missing.append("Origin-country exporter-side readiness evidence")
    if "trade_agreement_claim" in modules:
        missing.append("Official trade-agreement, MoU, or preference review evidence")
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
        "canada_import_responsibility": 2,
        "canada_import_controls": 3,
        "document_readiness": 4,
        "exporter_side_readiness": 5,
        "source_rights_contract": 6,
        "buyer_validation": 7,
        "trade_agreement_review": 8,
        "legal_privacy": 9,
        "security_private_beta_controls": 10,
        "launch_claims": 11,
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
        row["organization_id"] = _organization_id(row)
        row.setdefault("title", row.get("claim_supported") or row["evidence_id"])
        row.setdefault("description", row.get("claim_boundary") or "")
        sensitivity = str(row.get("sensitivity_level") or ("public" if row.get("evidence_type") in {"official_reference", "source_url"} else "internal"))
        row["sensitivity_level"] = sensitivity if sensitivity in SENSITIVITY_LEVELS else "internal"
        mode = str(row.get("ai_processing_mode") or row.get("ai_processing_permission") or "metadata_only")
        row["ai_processing_mode"] = mode if mode in AI_PROCESSING_MODES else "metadata_only"
        row["ai_processing_permission"] = row["ai_processing_mode"]
        row["ai_processing_allowed"] = row["ai_processing_mode"] not in {"no_ai", "on_prem_manual"}
        row["redaction_required"] = bool(row.get("redaction_required")) or row["sensitivity_level"] in {"confidential", "restricted", "regulated"} or row["ai_processing_mode"] == "redacted"
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

    if not str(packet.get("source_url") or "").strip() and not packet.get("offline_evidence_only"):
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
    trade_direction = _trade_direction(packet)
    if trade_direction in {"export", "both"} and _country_is_canada(packet.get("destination_country")):
        importer_of_record = _normal_importer_of_record(packet)
        incoterms = _normal_incoterms(packet)
        document_flags = _document_flags(packet, evidence_rows)
        importer_name = packet.get("importer_name") or packet.get("buyer_name") or packet.get("canadian_buyer_importer_name")
        if importer_of_record == "unknown":
            add(
                "importer-of-record-unknown",
                "importer_of_record",
                "Canadian importer of record is unknown",
                "trade_ops",
                "Confirm whether the Canadian buyer/importer, exporter, broker, or another party is importer of record.",
                "P0_blocks_shipment_decision",
            )
        if not _truthy_text(importer_name):
            add(
                "canadian-buyer-importer-missing",
                "importer_of_record",
                "Canadian buyer/importer is not confirmed",
                "sales_ops",
                "Add the Canadian buyer/importer name or mark the packet as broker-ready with the importer still unknown.",
                "P0_blocks_buyer_packet",
            )
        if incoterms == "unknown":
            add(
                "incoterms-missing",
                "importer_of_record",
                "Incoterms or delivery responsibility are missing",
                "trade_ops",
                "Record Incoterms or delivery responsibility before generating a shipment decision.",
                "P0_blocks_shipment_decision",
            )
        if importer_of_record == "exporter" or incoterms == "DDP":
            add(
                "exporter-import-responsibility-review",
                "importer_of_record",
                "Exporter may carry Canadian import/DDP/non-resident importer responsibility",
                "compliance",
                "Generate a Canadian broker review packet before the exporter accepts delivered-into-Canada responsibility.",
                "P0_blocks_shipment_decision",
            )
        if not _truthy_text(packet.get("hs_code_value")):
            add(
                "hs-classification-missing",
                "expert_review",
                "HS/tariff classification is not ready for external use",
                "compliance",
                "Collect product details and route HS/tariff classification to a qualified reviewer.",
                "P0_blocks_shipment_decision",
            )
        if str(packet.get("import_control_review_status") or "missing") not in {"complete", "reviewed", "not_applicable"}:
            add(
                "import-control-review-missing",
                "import_controls",
                "Canadian import permit/control review is missing",
                "compliance",
                "Check official Canadian references and collect broker/expert review before shipment decisions.",
                "P0_blocks_shipment_decision",
            )
        category = str(packet.get("product_category") or "").lower()
        if any(keyword in category for keyword in ("food", "health", "plant", "animal", "seafood", "agri")) and str(packet.get("cfia_airs_review_status") or "missing") not in {"complete", "reviewed", "not_applicable"}:
            add(
                "cfia-airs-review-missing",
                "import_controls",
                "CFIA/AIRS or food/health review is missing for this product category",
                "compliance",
                "Check CFIA/AIRS applicability and generate a broker review packet before food/health claims.",
                "P0_blocks_shipment_decision",
            )
        if not document_flags["product_documents"]:
            add(
                "product-documents-missing",
                "product_documentation",
                "Product specs, lab report, certificate, or technical documents are incomplete",
                "customer",
                "Upload product specs, lab reports, certificates, or source/supplier documents.",
                "P1_blocks_buyer_packet",
            )
        if not document_flags["commercial_documents"]:
            add(
                "commercial-documents-missing",
                "product_documentation",
                "Commercial invoice/proforma, packing list, or contract terms are incomplete",
                "customer",
                "Upload invoice/proforma, packing list, contract or PO, and shipping terms.",
                "P1_blocks_buyer_packet",
            )
        if not document_flags["proof_of_origin"]:
            add(
                "proof-of-origin-missing",
                "proof_of_origin",
                "Proof of origin is missing",
                "customer",
                "Attach proof of origin before country-of-origin or preference claims.",
                "P1_blocks_buyer_packet",
            )
        if str(packet.get("origin_country") or "").strip().lower() == "india" and str(packet.get("india_export_readiness_status") or "missing") not in {"complete", "reviewed", "not_applicable"}:
            add(
                "india-export-readiness-review-missing",
                "exporter_side_readiness",
                "India-side export readiness evidence is missing",
                "exporter",
                "Collect or mark not-applicable PAN/GST/IEC/RCMC/ICEGATE/AD-code style evidence through an India export review lane.",
                "P1_blocks_export_packet",
            )
        if str(packet.get("broker_review_status") or "missing") not in {"complete", "reviewed"}:
            add(
                "canadian-broker-review-missing",
                "expert_review",
                "Canadian broker/expert review is missing",
                "compliance",
                "Generate the broker review packet and collect a scoped reviewer decision.",
                "P0_blocks_shipment_decision",
            )
        if _truthy_text(packet.get("trade_agreement_claim")) or _truthy_text(packet.get("mou_claim")):
            add(
                "trade-agreement-claim-review-missing",
                "trade_agreement_claim",
                "Trade agreement, preference, or MoU claim lacks official evidence and review",
                "compliance",
                "Keep preference/MoU claims blocked until official evidence and qualified review exist.",
                "P0_blocks_commercial_claim",
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
    organization_id = _organization_id(packet)
    blocker_groups = packet.get("blocker_groups", [])
    group_titles = {str(row.get("title")) for row in blocker_groups}
    evidence_ids = [str(row.get("evidence_id")) for row in packet.get("evidence_items", [])]
    source_ids = [str(row.get("id")) for row in workflow.get("official_sources", [])]
    route_decisions = [
        route_ai_task(
            organization_id=organization_id,
            packet_id=packet_id,
            evidence_id=str(row.get("evidence_id")),
            task_type="simulated_readiness_review",
            document_sensitivity=str(row.get("sensitivity_level") or "internal"),
            requested_mode=str(row.get("ai_processing_mode") or "metadata_only"),
            evidence_permission=str(row.get("ai_processing_permission") or row.get("ai_processing_mode") or "metadata_only"),
        )
        for row in packet.get("evidence_items", [])
    ]
    allowed_routes = [row for row in route_decisions if row.get("allowed")]
    primary_route = allowed_routes[0] if allowed_routes else (route_decisions[0] if route_decisions else {})
    status = "simulated_review_complete_human_gates_closed" if allowed_routes else "manual_no_ai_required_human_gates_closed"
    results = []
    findings = []
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
                "can_open_gate": False,
                "status": "blocked_human_gate_required",
                "finding": "Simulation can create blockers and next moves; it cannot open external-world approval gates.",
                "blocker_group_ids": [str(row.get("id")) for row in relevant],
                "next_valid_move": "Export the expert review packet and collect a scoped human decision.",
            }
        )
        findings.append(
            {
                "title": title,
                "severity": "P1_blocks_external_claim",
                "issue": "Simulated review found missing evidence or review proof for external claims.",
                "evidence_used": evidence_ids,
                "sources_used": source_ids[:3],
                "blocked_claims": [
                    "tariff_classification_claim",
                    "food_safety_claim",
                    "launch_readiness_claim",
                ],
                "next_valid_move": "Collect evidence and request scoped human review before any external claim.",
                "human_review_required": True,
            }
        )
    return {
        "run_id": f"ai-review-{packet_id}-{(generated_at or _now()).replace(':', '').replace('+', 'Z')}",
        "packet_id": packet_id,
        "organization_id": organization_id,
        "generated_at": generated_at or _now(),
        "review_type": "canada_compliance_simulation",
        "scope": "Simulated review for missing evidence, risky wording, and next valid moves.",
        "model_provider": "local_rule_simulator",
        "model_name": "deterministic-safety-rules",
        "model_mode": primary_route.get("mode") or "manual_no_ai",
        "model_name_or_endpoint": primary_route.get("model_endpoint_id") or "local_rule_simulator",
        "model_route_decisions": route_decisions,
        "redaction_applied": any(row.get("redaction_required") for row in route_decisions),
        "prompt_stored": any(row.get("store_prompt") for row in route_decisions),
        "output_stored": True,
        "input_snapshot_hash": _sha256(json.dumps(packet, sort_keys=True)),
        "evidence_ids_used": evidence_ids,
        "source_ids_used": source_ids,
        "status": status,
        "can_open_gate": False,
        "human_review_required": True,
        "human_gate": "required_before_external_claims",
        "findings": findings,
        "blocked_claims": [
            "tariff_classification_claim",
            "food_safety_claim",
            "source_rights_claim",
            "buyer_validation_claim",
            "launch_readiness_claim",
        ],
        "results": results,
        "validation_result": {
            "status": "fail_closed_validated",
            "can_open_gate": False,
            "human_gate_required": True,
            "route_count": len(route_decisions),
            "allowed_route_count": len(allowed_routes),
        },
        "output_json": {
            "findings": findings,
            "blocked_claims": [
                "tariff_classification_claim",
                "food_safety_claim",
                "source_rights_claim",
                "buyer_validation_claim",
                "launch_readiness_claim",
            ],
            "can_open_gate": False,
        },
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
        trade_direction = _trade_direction(packet)
        responsibility_path = _responsibility_path(packet)
        readiness_lanes = _readiness_lanes(packet, linked_evidence, blockers)
        document_flags = _document_flags(packet, linked_evidence)
        packets.append(
            {
                "packet_id": packet_id,
                "organization_id": _organization_id(packet),
                "public_product_name": PUBLIC_PRODUCT_NAME,
                "public_product_promise": PUBLIC_PRODUCT_PROMISE,
                "packet_name": packet.get("packet_name") or packet.get("product_name"),
                "product_name": packet.get("product_name"),
                "product_category": packet.get("product_category"),
                "trade_direction": trade_direction,
                "origin_country": packet.get("origin_country"),
                "destination_country": packet.get("destination_country"),
                "exporter_country": packet.get("exporter_country") or packet.get("origin_country"),
                "importer_country": packet.get("importer_country") or packet.get("destination_country"),
                "exporter_name": packet.get("exporter_name") or packet.get("supplier_name") or "",
                "importer_name": packet.get("importer_name") or packet.get("buyer_name") or "",
                "buyer_name": packet.get("buyer_name") or packet.get("importer_name") or "",
                "manufacturer_name": packet.get("manufacturer_name") or "",
                "importer_of_record": _normal_importer_of_record(packet),
                "exporter_of_record": packet.get("exporter_of_record") or packet.get("exporter_name") or packet.get("supplier_name") or "",
                "incoterms_if_known": _normal_incoterms(packet),
                "delivery_responsibility": packet.get("delivery_responsibility") or "",
                "responsibility_path": responsibility_path,
                "supplier_name": packet.get("supplier_name"),
                "supplier_country": packet.get("supplier_country"),
                "hs_code_known": bool(packet.get("hs_code_known")),
                "hs_code_value": packet.get("hs_code_value"),
                "hs_code_if_known": packet.get("hs_code_value"),
                "source_url": packet.get("source_url"),
                "source_type": packet.get("source_type") or "customer_submitted",
                "intended_use": packet.get("intended_use"),
                "offline_evidence_only": bool(packet.get("offline_evidence_only")),
                "beginner_mode": bool(packet.get("beginner_mode")),
                "current_stage": packet.get("current_stage") or "",
                "research_depth_requested": packet.get("research_depth_requested") or "",
                "unknown_fields": packet.get("unknown_fields") or [],
                "confirmation_status": packet.get("confirmation_status") or "not_confirmed",
                "shareable_status": (
                    "draft_shareable_after_user_confirmation_with_external_gates"
                    if (packet.get("confirmation_status") or "not_confirmed") == "user_confirmed_draft_fields"
                    else "blocked_until_user_confirmation"
                ),
                "document_flags": document_flags,
                "product_documents": _as_list(packet.get("product_documents")),
                "commercial_documents": _as_list(packet.get("commercial_documents")),
                "certificates": _as_list(packet.get("certificates")),
                "proof_of_origin": _as_list(packet.get("proof_of_origin")),
                "shipping_method": packet.get("shipping_method") or "",
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
                "readiness_lanes": readiness_lanes,
                "buyer_broker_questions": _buyer_broker_questions(packet),
                "public_summary": {
                    "title": "Export-to-Canada Packet" if trade_direction == "export" else "Trade Readiness Packet",
                    "status": "Blocked - not ready for shipment decision" if blockers else "Draft ready for internal review",
                    "main_reason": blocker_groups[0]["title"] if blocker_groups else "Internal review ready",
                    "evidence_counts": evidence_summary,
                    "next_valid_move": blocker_groups[0]["next_valid_move"] if blocker_groups else "Proceed to internal review; external claims stay blocked.",
                    "privacy_notice": "Draft public checks do not need a login; uploaded files should be deleted or expire after processing.",
                    "ai_disclosure": "AI can summarize or structure evidence when allowed, but it cannot approve customs, tariff, legal, or compliance claims.",
                },
                "allowed_actions": [
                    "Internal review",
                    "Draft readiness report",
                    "Buyer-ready packet",
                    "Broker review packet",
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
                    "Shipment decision",
                    "Export-to-Canada ready claim",
                    "Trade agreement preference claim",
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
                    {
                        "id": "generate_buyer_packet",
                        "label": "Generate Buyer Packet",
                        "method": "GET",
                        "route": f"/api/public/packets/{packet_id}/reports/buyer.pdf",
                    },
                    {
                        "id": "generate_broker_review_packet",
                        "label": "Generate Broker Review Packet",
                        "method": "GET",
                        "route": f"/api/public/packets/{packet_id}/reports/broker.pdf",
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
        "public_product_name": PUBLIC_PRODUCT_NAME,
        "public_product_promise": PUBLIC_PRODUCT_PROMISE,
        "public_surface": "public_quick_check_plus_logged_operator_workspace",
        "trade_directions": sorted(TRADE_DIRECTIONS),
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
    hs_code = fields.get("hs_code_value") or fields.get("hs_code_if_known") or ""
    destination_country = fields.get("destination_country") or fields.get("destination_canada") or "Canada"
    origin_country = fields.get("origin_country") or fields.get("exporter_country") or ""
    trade_direction = _valid_trade_direction(fields.get("trade_direction"), default="unknown")
    if trade_direction == "unknown" and str(fields.get("user_type") or "").strip().lower() in EXPORTER_USER_TYPES:
        trade_direction = "export"
    return {
        "packet_id": packet_id,
        "packet_name": fields.get("packet_name") or product_name,
        "customer_id": fields.get("customer_id") or "local-customer",
        "organization_id": _organization_id(fields),
        "user_type": fields.get("user_type") or "",
        "product_name": product_name,
        "product_category": fields.get("product_category") or "",
        "trade_direction": trade_direction,
        "hs_code_known": bool(hs_code or fields.get("hs_code_known")),
        "hs_code_value": hs_code,
        "origin_country": origin_country,
        "destination_country": destination_country,
        "exporter_country": fields.get("exporter_country") or origin_country,
        "importer_country": fields.get("importer_country") or destination_country,
        "exporter_name": fields.get("exporter_name") or fields.get("supplier_name") or "",
        "importer_name": fields.get("importer_name") or fields.get("canadian_buyer_importer_name") or fields.get("buyer_name") or "",
        "buyer_name": fields.get("buyer_name") or fields.get("canadian_buyer_importer_name") or fields.get("importer_name") or "",
        "manufacturer_name": fields.get("manufacturer_name") or "",
        "importer_of_record": _normal_importer_of_record(fields),
        "exporter_of_record": fields.get("exporter_of_record") or fields.get("exporter_name") or "",
        "incoterms_if_known": _normal_incoterms(fields),
        "delivery_responsibility": fields.get("delivery_responsibility") or "",
        "shipping_method": fields.get("shipping_method") or "",
        "supplier_name": fields.get("supplier_name") or "",
        "supplier_country": fields.get("supplier_country") or "",
        "source_url": fields.get("source_url") or "",
        "source_type": fields.get("source_type") or "customer_submitted",
        "intended_use": fields.get("intended_use") or "",
        "documents": fields.get("documents") or [],
        "product_documents": _as_list(fields.get("product_documents")),
        "commercial_documents": _as_list(fields.get("commercial_documents")),
        "certificates": _as_list(fields.get("certificates")),
        "proof_of_origin": _as_list(fields.get("proof_of_origin")),
        "product_specs": fields.get("product_specs") or "",
        "commercial_invoice": fields.get("commercial_invoice") or "",
        "packing_list": fields.get("packing_list") or "",
        "food_health_docs": fields.get("food_health_docs") or "",
        "source_supplier_docs": fields.get("source_supplier_docs") or "",
        "contract_po": fields.get("contract_po") or "",
        "trade_agreement_claim": fields.get("trade_agreement_claim") or "",
        "mou_claim": fields.get("mou_claim") or "",
        "offline_evidence_only": bool(fields.get("offline_evidence_only")),
        "notes": fields.get("notes") or "",
        "beginner_mode": bool(fields.get("beginner_mode")),
        "current_stage": fields.get("current_stage") or "",
        "research_depth_requested": fields.get("research_depth_requested") or "",
        "unknown_fields": _as_list(fields.get("unknown_fields")),
        "confirmation_status": fields.get("confirmation_status") or "not_confirmed",
        "restricted_party_screening_status": fields.get("restricted_party_screening_status") or "missing",
        "qualified_review_status": fields.get("qualified_review_status") or "missing",
        "buyer_validation_status": fields.get("buyer_validation_status") or "missing",
        "contract_status": fields.get("contract_status") or "missing",
        "import_control_review_status": fields.get("import_control_review_status") or "missing",
        "cfia_airs_review_status": fields.get("cfia_airs_review_status") or "missing",
        "broker_review_status": fields.get("broker_review_status") or "missing",
        "india_export_readiness_status": fields.get("india_export_readiness_status") or "missing",
        "created_at": _now(),
    }


def evidence_from_submission(packet: dict[str, Any]) -> dict[str, Any]:
    source_url = str(packet.get("source_url") or "")
    return {
        "evidence_id": f"evidence-{packet['packet_id']}-source",
        "packet_id": packet["packet_id"],
        "organization_id": _organization_id(packet),
        "title": "Initial customer source reference",
        "description": "Source URL submitted during packet intake.",
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
        "sensitivity_level": "public" if source_url else "internal",
        "ai_processing_mode": "metadata_only",
        "ai_processing_permission": "metadata_only",
        "ai_processing_allowed": True,
        "redaction_required": False,
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
        f"- {question}" for question in _buyer_broker_questions(packet)
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
            f"Trade direction: {packet.get('trade_direction')}",
            f"Origin: {packet.get('origin_country')}",
            f"Destination: {packet.get('destination_country')}",
            f"Responsibility path: {packet.get('responsibility_path', {}).get('path')}",
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
    lanes = "\n".join(
        f"- {lane.get('name')} ({lane.get('country_scope')}): {lane.get('status')} - {lane.get('next_valid_move')}"
        for lane in packet.get("readiness_lanes", [])
    )
    questions = "\n".join(f"- {question}" for question in packet.get("buyer_broker_questions", []))
    refs = "\n".join(
        f"- {row.get('name')}: {row.get('claim_boundary')}"
        for row in workflow.get("official_sources", [])[:6]
    )
    return "\n".join(
        [
            "# Trade Readiness Report",
            "",
            f"Packet: {packet['packet_name']}",
            f"Public product: {packet.get('public_product_name', PUBLIC_PRODUCT_NAME)}",
            f"Status: {packet['display_status']}",
            f"Customer-visible status: {packet['customer_visible_status_label']}",
            f"Trade direction: {packet.get('trade_direction')}",
            f"Origin: {packet.get('origin_country')}",
            f"Destination: {packet.get('destination_country')}",
            f"Importer of record: {packet.get('importer_of_record')}",
            f"Incoterms: {packet.get('incoterms_if_known')}",
            "",
            "## Summary",
            "",
            packet["safe_summary"],
            "",
            "## Readiness Lanes",
            "",
            lanes or "- No readiness lanes generated.",
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
            "## Buyer / Broker Questions",
            "",
            questions or "- No questions generated.",
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
