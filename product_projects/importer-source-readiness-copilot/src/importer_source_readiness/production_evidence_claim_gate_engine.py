"""Production evidence ledger and claim-gate engine.

This module makes the Phase 11 claim-gate contract executable. It consumes the
current packet, evidence ledger, source lifecycle, market, document, and review
artifacts, then answers can_show_claim(claim_type, packet_id) with a concrete
evidence trail and fail-closed reason.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_evidence_claim_gate_engine_ready_claims_fail_closed"
QUALIFIED_CUSTOMS_TRADE_REVIEW_FALLBACK_GATE_COUNT = 14

SAFE_RESEARCH_LEVEL = "safe_research_or_preparation_statement"
BLOCKED_LEVEL = "blocked_external_or_unproven_claim"

REFERENCE_SOURCE_IDS = {
    "wco-harmonized-system",
    "cbsa-customs-tariff-2026",
    "cfia-airs",
    "icc-incoterms-2020",
    "ised-trade-data-online",
    "canada-cid",
    "cbsa-import-commercial-goods",
    "india-dgft-foreign-trade-policy",
    "india-cbic-customs",
}

CLAIM_RULES: tuple[dict[str, Any], ...] = (
    {
        "claim_type": "product_context_recorded",
        "label": "Product and lane context recorded",
        "claim_family": "packet_context",
        "allowed_wording": "Product, origin, destination, and trade direction can be shown as user-submitted draft context.",
        "blocked_wording": "Do not imply the product or lane is approved.",
        "required_packet_fields": ("product_name", "origin_country", "destination_country", "trade_direction"),
        "required_source_ids": (),
        "required_evidence_types": ("user_input",),
        "required_reviewer_lane": "",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Use the context to build the packet and collect missing evidence.",
    },
    {
        "claim_type": "hs_candidate_research_route",
        "label": "HS candidate research route identified",
        "claim_family": "classification_research",
        "allowed_wording": "An HS candidate and official HS/tariff research routes can be shown for preparation.",
        "blocked_wording": "Do not say HS classification or tariff treatment is confirmed.",
        "required_packet_fields": ("hs_code_value",),
        "required_source_ids": ("wco-harmonized-system", "cbsa-customs-tariff-2026"),
        "required_evidence_types": ("official_source_reference", "market_signal"),
        "required_reviewer_lane": "customs_or_trade_review",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Ask a qualified customs/trade reviewer to assess the HS candidate before tariff or classification wording is used.",
    },
    {
        "claim_type": "tariff_route_identified",
        "label": "Tariff route identified",
        "claim_family": "tariff_research",
        "allowed_wording": "The relevant tariff research route can be shown as source routing only.",
        "blocked_wording": "Do not say tariff is confirmed or payable amount is known.",
        "required_packet_fields": ("destination_country",),
        "required_source_ids": ("cbsa-customs-tariff-2026",),
        "required_evidence_types": ("official_source_reference",),
        "required_reviewer_lane": "customs_or_trade_review",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Attach current tariff-source evidence and route to qualified review before tariff treatment is stated.",
    },
    {
        "claim_type": "cfia_relevance_route",
        "label": "CFIA or regulated-product route identified",
        "claim_family": "regulated_goods_research",
        "allowed_wording": "CFIA/AIRS can be shown as a regulated-product reference route when the product may be food, plant, animal, or seafood.",
        "blocked_wording": "Do not say CFIA clearance, permit, admissibility, or compliance is approved.",
        "required_packet_fields": ("product_name", "destination_country"),
        "required_source_ids": ("cfia-airs",),
        "required_evidence_types": ("official_source_reference",),
        "required_reviewer_lane": "canada_food_or_regulated_goods_review",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Run a dated CFIA/AIRS check and send product specifics to a qualified reviewer.",
    },
    {
        "claim_type": "regulated_product_review_needed",
        "label": "Regulated-product review needed",
        "claim_family": "regulated_goods_research",
        "allowed_wording": "The product can be flagged for regulated-product review.",
        "blocked_wording": "Do not say the product is admissible or exempt.",
        "required_packet_fields": ("product_name",),
        "required_source_ids": ("cfia-airs",),
        "required_evidence_types": ("official_source_reference",),
        "required_reviewer_lane": "canada_food_or_regulated_goods_review",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Collect product composition/intended-use details and attach a dated regulated-goods review result.",
    },
    {
        "claim_type": "market_signal_source_routed",
        "label": "Market signal source-routed",
        "claim_family": "market_research",
        "allowed_wording": "A source-routed market research signal can be shown without demand or profitability claims.",
        "blocked_wording": "Do not say demand, profitability, market size, or buyer interest is proven.",
        "required_packet_fields": ("product_name", "destination_country"),
        "required_source_ids": ("ised-trade-data-online",),
        "required_evidence_types": ("market_signal",),
        "required_reviewer_lane": "market_or_operator_review",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Attach dated trade dataset rows and buyer evidence before any market conclusion.",
    },
    {
        "claim_type": "buyer_lead_route_identified",
        "label": "Buyer/importer lead route identified",
        "claim_family": "buyer_research",
        "allowed_wording": "Importer or buyer lead-discovery routes can be shown as leads only.",
        "blocked_wording": "Do not say buyer validated, demand proven, or customer interest confirmed.",
        "required_packet_fields": ("destination_country",),
        "required_source_ids": ("canada-cid",),
        "required_evidence_types": ("official_source_reference", "buyer_signal"),
        "required_reviewer_lane": "buyer_validation_review",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Collect dated outreach, reply, meeting, LOI, PO, or paid-order evidence before buyer validation language.",
    },
    {
        "claim_type": "incoterms_responsibility_path",
        "label": "Responsibility path recorded",
        "claim_family": "responsibility",
        "allowed_wording": "A responsibility path can be shown when Incoterms or role split is user-confirmed.",
        "blocked_wording": "Do not treat missing or unreviewed Incoterms as a legal responsibility decision.",
        "required_packet_fields": ("incoterms_if_known", "importer_of_record"),
        "required_source_ids": ("icc-incoterms-2020",),
        "required_evidence_types": ("user_input", "official_source_reference"),
        "required_reviewer_lane": "freight_or_legal_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": False,
        "next_valid_move": "Ask buyer/importer who is importer of record and which Incoterm applies; route to freight/legal review if needed.",
    },
    {
        "claim_type": "origin_evidence_collected",
        "label": "Origin evidence collected",
        "claim_family": "origin",
        "allowed_wording": "Origin evidence can be shown as collected only when actual origin documents are attached and confirmed.",
        "blocked_wording": "Do not say origin is confirmed from a country name or source route.",
        "required_packet_fields": ("origin_country",),
        "required_source_ids": ("india-dgft-foreign-trade-policy",),
        "required_evidence_types": ("document", "origin_document", "reviewer_finding"),
        "required_reviewer_lane": "origin_or_customs_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": False,
        "next_valid_move": "Attach certificate of origin or origin-supporting documents and route to scoped review.",
    },
    {
        "claim_type": "document_field_extraction_draft",
        "label": "Document fields extracted as draft",
        "claim_family": "document_intelligence",
        "allowed_wording": "Extracted document fields can be shown as draft evidence when they come from customer documents and require confirmation.",
        "blocked_wording": "Do not treat parser output as authenticity, completeness, or compliance proof.",
        "required_packet_fields": (),
        "required_source_ids": (),
        "required_evidence_types": ("document_field",),
        "required_reviewer_lane": "document_or_operator_review",
        "safe_without_reviewer": True,
        "forbidden_external_claim": False,
        "next_valid_move": "Ask the user to confirm extracted fields, then route the packet to the correct reviewer lane.",
    },
    {
        "claim_type": "supplier_evidence_collected",
        "label": "Supplier evidence collected",
        "claim_family": "supplier_evidence",
        "allowed_wording": "Supplier evidence can be shown as collected only when supporting registration/product/certificate/inspection evidence is attached.",
        "blocked_wording": "Do not say supplier verified or recommended.",
        "required_packet_fields": ("supplier_name",),
        "required_source_ids": (),
        "required_evidence_types": ("supplier_registration", "supplier_document", "inspection_report", "reviewer_finding"),
        "required_reviewer_lane": "supplier_evidence_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": False,
        "next_valid_move": "Request supplier registration, export ability, product docs, certificates, inspection, and prior-shipment evidence.",
    },
    {
        "claim_type": "tariff_confirmed",
        "label": "Tariff confirmed",
        "claim_family": "forbidden_external_claim",
        "allowed_wording": "",
        "blocked_wording": "Tariff confirmed remains blocked until authoritative tariff/ruling evidence and qualified review exist.",
        "required_packet_fields": ("hs_code_value",),
        "required_source_ids": ("cbsa-customs-tariff-2026",),
        "required_evidence_types": ("reviewer_finding", "official_ruling"),
        "required_reviewer_lane": "qualified_customs_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": True,
        "next_valid_move": "Obtain a qualified customs review or authoritative ruling evidence.",
    },
    {
        "claim_type": "cfia_approved",
        "label": "CFIA approved",
        "claim_family": "forbidden_external_claim",
        "allowed_wording": "",
        "blocked_wording": "CFIA approved remains blocked until official permit/admissibility evidence and qualified review exist.",
        "required_packet_fields": ("product_name",),
        "required_source_ids": ("cfia-airs",),
        "required_evidence_types": ("reviewer_finding", "official_permit_or_result"),
        "required_reviewer_lane": "canada_food_or_regulated_goods_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": True,
        "next_valid_move": "Attach dated CFIA/AIRS result or permit evidence and qualified reviewer finding.",
    },
    {
        "claim_type": "buyer_validated",
        "label": "Buyer validated",
        "claim_family": "forbidden_external_claim",
        "allowed_wording": "",
        "blocked_wording": "Buyer validated remains blocked until dated buyer response, meeting, LOI, PO, or paid-order evidence exists.",
        "required_packet_fields": ("buyer_name",),
        "required_source_ids": (),
        "required_evidence_types": ("buyer_reply", "buyer_meeting", "loi", "purchase_order", "paid_order"),
        "required_reviewer_lane": "buyer_validation_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": True,
        "next_valid_move": "Collect dated buyer evidence; directory rows are lead sources only.",
    },
    {
        "claim_type": "supplier_verified",
        "label": "Supplier verified",
        "claim_family": "forbidden_external_claim",
        "allowed_wording": "",
        "blocked_wording": "Supplier verified remains blocked until registration, export ability, product evidence, certificates/inspection, and reviewer assessment exist.",
        "required_packet_fields": ("supplier_name",),
        "required_source_ids": (),
        "required_evidence_types": ("supplier_registration", "inspection_report", "reviewer_finding"),
        "required_reviewer_lane": "supplier_evidence_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": True,
        "next_valid_move": "Collect supplier proof and route to a scoped reviewer.",
    },
    {
        "claim_type": "customs_ready",
        "label": "Customs ready",
        "claim_family": "forbidden_external_claim",
        "allowed_wording": "",
        "blocked_wording": "Customs ready remains blocked until broker/customs review and required import/export evidence exist.",
        "required_packet_fields": ("importer_of_record", "incoterms_if_known"),
        "required_source_ids": ("cbsa-import-commercial-goods",),
        "required_evidence_types": ("reviewer_finding", "broker_finding"),
        "required_reviewer_lane": "qualified_customs_review",
        "safe_without_reviewer": False,
        "forbidden_external_claim": True,
        "next_valid_move": "Resolve importer of record, Incoterms, source freshness, and broker/customs review.",
    },
    {
        "claim_type": "shipment_approved",
        "label": "Shipment approved",
        "claim_family": "forbidden_external_claim",
        "allowed_wording": "",
        "blocked_wording": "Shipment approved is not supported by this product scope.",
        "required_packet_fields": (),
        "required_source_ids": (),
        "required_evidence_types": ("reviewer_finding", "broker_finding", "freight_forwarder_finding"),
        "required_reviewer_lane": "final_owner_gate",
        "safe_without_reviewer": False,
        "forbidden_external_claim": True,
        "next_valid_move": "Use the packet for preparation only; final shipment decisions require qualified professionals and owner approval.",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _known(value: Any) -> bool:
    text = _text(value).lower()
    return bool(text and text not in {"unknown", "n/a", "na", "none", "not known", "not_confirmed"})


def _packet_by_id(customer: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {_text(packet.get("packet_id")): packet for packet in customer.get("packets", []) if _text(packet.get("packet_id"))}


def _rules_by_type() -> dict[str, dict[str, Any]]:
    return {rule["claim_type"]: rule for rule in CLAIM_RULES}


def _source_ids_from_country(country_engine: dict[str, Any]) -> set[str]:
    source_ids: set[str] = set()
    for row in country_engine.get("source_lifecycle", []):
        source_id = _text(row.get("source_id"))
        if source_id:
            source_ids.add(source_id)
    for impact in country_engine.get("packet_source_impacts", []):
        source_ids.update(_text(source_id) for source_id in impact.get("matched_source_ids", []) if _text(source_id))
    return source_ids


def _source_lifecycle_by_id(country_engine: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {_text(row.get("source_id")): row for row in country_engine.get("source_lifecycle", []) if _text(row.get("source_id"))}


def _source_refresh_by_url(source_refresh_runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    for run in source_refresh_runs:
        for row in run.get("rows", []):
            url = _text(row.get("source_url"))
            if url:
                by_url[url] = row
    return by_url


def _market_signals_by_packet(market: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for signal in market.get("signals", []):
        packet_id = _text(signal.get("packet_id"))
        if packet_id:
            rows.setdefault(packet_id, []).append(signal)
    return rows


def _document_fields_by_packet(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for field in document.get("extracted_fields", []):
        packet_id = _text(field.get("packet_id"))
        if packet_id:
            rows.setdefault(packet_id, []).append(field)
    return rows


def _document_evidence_by_packet(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for evidence in document.get("evidence_records", []):
        packet_id = _text(evidence.get("packet_id"))
        if packet_id:
            rows.setdefault(packet_id, []).append(evidence)
    return rows


def _reviews_by_packet(review_requests: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for review in review_requests:
        packet_ids = review.get("packet_ids") or [review.get("packet_id")]
        for packet_id in packet_ids:
            packet_key = _text(packet_id)
            if packet_key:
                rows.setdefault(packet_key, []).append(review)
    return rows


def _source_evidence(source_id: str, source_lifecycle: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    row = source_lifecycle.get(source_id)
    if not row:
        return None
    return {
        "evidence_id": f"source:{source_id}",
        "type": "official_source_reference",
        "source_id": source_id,
        "source_name": row.get("name") or source_id,
        "freshness": row.get("source_state") or "unknown",
        "provenance": "official_source_registry",
        "claim_boundary": row.get("claim_boundary", ""),
        "review_required": bool(row.get("review_required_if_material_change", True)),
        "supports_claims": row.get("supports_claims", []),
        "blocked_claims": row.get("blocked_claims", []),
        "url": row.get("canonical_url", ""),
    }


def _packet_field_evidence(packet: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    value = packet.get(field_name)
    if not _known(value):
        return None
    return {
        "evidence_id": f"packet-field:{packet.get('packet_id')}:{field_name}",
        "type": "user_input",
        "field": field_name,
        "value": value,
        "freshness": "user_input_current_for_packet",
        "provenance": "user_input",
        "claim_boundary": "User input supports packet preparation only until evidence and review exist.",
        "review_required": True,
        "supports_claims": ["product_context_recorded"],
        "blocked_claims": [],
    }


def _evidence_is_stale_or_reference_only(evidence: dict[str, Any]) -> bool:
    freshness = _text(evidence.get("freshness") or evidence.get("freshness_status") or evidence.get("ledger_status")).lower()
    labels = " ".join(_text(label).lower() for label in evidence.get("labels", []))
    boundary = _text(evidence.get("claim_boundary")).lower()
    if any(token in freshness for token in ("stale", "not_checked", "unknown", "needs_current_refresh")):
        return True
    if "reference_only" in freshness or "reference_only" in labels or "reference-only" in boundary:
        return True
    return False


def _source_routes_for_rule(rule: dict[str, Any], source_lifecycle: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    evidence = []
    missing = []
    for source_id in rule["required_source_ids"]:
        source = _source_evidence(source_id, source_lifecycle)
        if source:
            evidence.append(source)
        else:
            missing.append(source_id)
    return evidence, missing


def _market_evidence_for_claim(packet_id: str, claim_type: str, market_by_packet: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    evidence = []
    for signal in market_by_packet.get(packet_id, []):
        metric = _text(signal.get("metric"))
        if claim_type == "market_signal_source_routed" or (
            claim_type == "hs_candidate_research_route" and metric == "hs_candidate_route"
        ) or (
            claim_type == "buyer_lead_route_identified" and metric == "buyer_importer_lead_routes"
        ):
            evidence.append(
                {
                    "evidence_id": signal.get("market_signal_id"),
                    "type": "market_signal",
                    "metric": metric,
                    "freshness": signal.get("confidence") or "research_plan",
                    "provenance": "system_derived_from_source_routes",
                    "claim_boundary": signal.get("limitation", ""),
                    "review_required": True,
                    "supports_claims": [claim_type],
                    "blocked_claims": signal.get("blocked_claims", []),
                }
            )
    return evidence


def _document_field_evidence_for_claim(
    packet_id: str,
    document_fields_by_packet: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for field in document_fields_by_packet.get(packet_id, []):
        status = _text(field.get("user_confirmation_status")).lower()
        provenance = _text(field.get("provenance")).lower()
        if "sample" in status or "sample" in provenance or "synthetic" in provenance:
            continue
        rows.append(
            {
                "evidence_id": field.get("field_id"),
                "type": "document_field",
                "field_name": field.get("field_name"),
                "freshness": "parser_draft_needs_user_confirmation",
                "provenance": field.get("provenance") or "parser_draft",
                "claim_boundary": field.get("claim_boundary", ""),
                "review_required": True,
                "supports_claims": ["document_field_extraction_draft"],
                "blocked_claims": field.get("blocked_claims", []),
            }
        )
    return rows


def _document_gap_evidence(
    packet_id: str,
    document_evidence_by_packet: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    evidence = []
    for row in document_evidence_by_packet.get(packet_id, []):
        evidence.append(
            {
                "evidence_id": row.get("evidence_id"),
                "type": row.get("type") or "document_gap",
                "freshness": row.get("freshness") or "unknown",
                "provenance": row.get("provenance"),
                "claim_boundary": row.get("claim_boundary"),
                "review_required": row.get("review_required", True),
                "supports_claims": row.get("supports_claims", []),
                "blocked_claims": row.get("blocked_claims", []),
            }
        )
    return evidence


def _customer_evidence_for_rule(packet: dict[str, Any], rule: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = []
    for field in rule["required_packet_fields"]:
        field_evidence = _packet_field_evidence(packet, field)
        if field_evidence:
            evidence.append(field_evidence)
    for row in packet.get("evidence_items", []):
        evidence_type = _text(row.get("evidence_type"))
        if evidence_type and evidence_type in rule["required_evidence_types"]:
            mapped = dict(row)
            mapped["type"] = evidence_type
            mapped["freshness"] = row.get("freshness_status") or row.get("ledger_status") or row.get("quality_status")
            mapped["provenance"] = row.get("evidence_type")
            evidence.append(mapped)
    return evidence


def _review_evidence_for_rule(
    packet_id: str,
    rule: dict[str, Any],
    reviews_by_packet: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    evidence = []
    required_lane = _text(rule.get("required_reviewer_lane"))
    if not required_lane:
        return evidence
    for review in reviews_by_packet.get(packet_id, []):
        role_scope = " ".join(_text(review.get(key)).lower() for key in ("review_type", "reviewer_role", "scope"))
        status = _text(review.get("status")).lower()
        if status in {"approved_for_scope", "completed", "reviewed"} and any(part in role_scope for part in required_lane.split("_")):
            evidence.append(
                {
                    "evidence_id": review.get("id"),
                    "type": "reviewer_finding",
                    "freshness": "reviewer_current_for_scope",
                    "provenance": "reviewer_verified",
                    "claim_boundary": review.get("scope", ""),
                    "review_required": False,
                    "supports_claims": [rule["claim_type"]],
                    "blocked_claims": [],
                }
            )
    return evidence


def _gather_evidence_for_claim(
    packet: dict[str, Any],
    rule: dict[str, Any],
    source_lifecycle: dict[str, dict[str, Any]],
    market_by_packet: dict[str, list[dict[str, Any]]],
    document_fields_by_packet: dict[str, list[dict[str, Any]]],
    document_evidence_by_packet: dict[str, list[dict[str, Any]]],
    reviews_by_packet: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    packet_id = _text(packet.get("packet_id"))
    evidence = _customer_evidence_for_rule(packet, rule)
    missing_reasons: list[str] = []
    source_evidence, missing_sources = _source_routes_for_rule(rule, source_lifecycle)
    evidence.extend(source_evidence)
    evidence.extend(_market_evidence_for_claim(packet_id, rule["claim_type"], market_by_packet))
    if rule["claim_type"] == "document_field_extraction_draft":
        field_evidence = _document_field_evidence_for_claim(packet_id, document_fields_by_packet)
        evidence.extend(field_evidence)
        if not field_evidence:
            evidence.extend(_document_gap_evidence(packet_id, document_evidence_by_packet))
            missing_reasons.append("missing customer document field extraction")
    evidence.extend(_review_evidence_for_rule(packet_id, rule, reviews_by_packet))
    for field in rule["required_packet_fields"]:
        if not _known(packet.get(field)):
            missing_reasons.append(f"missing packet field: {field}")
    for source_id in missing_sources:
        missing_reasons.append(f"missing required source route: {source_id}")
    present_types = {
        _text(row.get("type") or row.get("evidence_type"))
        for row in evidence
        if _text(row.get("type") or row.get("evidence_type"))
    }
    required_types = {_text(item) for item in rule["required_evidence_types"] if _text(item)}
    if required_types and not (present_types & required_types):
        missing_reasons.append(f"missing required evidence type: {' or '.join(sorted(required_types))}")
    stale_ids = [str(row.get("evidence_id")) for row in evidence if _evidence_is_stale_or_reference_only(row)]
    return evidence, missing_reasons, stale_ids


def _safe_route_claim(rule: dict[str, Any], evidence: list[dict[str, Any]], missing_reasons: list[str]) -> bool:
    if rule["forbidden_external_claim"]:
        return False
    if missing_reasons:
        return False
    if rule["claim_type"] == "product_context_recorded":
        return True
    if not evidence:
        return False
    if rule["safe_without_reviewer"]:
        return True
    return any(_text(row.get("type")) == "reviewer_finding" for row in evidence)


def _decision_for_claim(
    packet: dict[str, Any],
    rule: dict[str, Any],
    source_lifecycle: dict[str, dict[str, Any]],
    market_by_packet: dict[str, list[dict[str, Any]]],
    document_fields_by_packet: dict[str, list[dict[str, Any]]],
    document_evidence_by_packet: dict[str, list[dict[str, Any]]],
    reviews_by_packet: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    packet_id = _text(packet.get("packet_id"))
    evidence, missing_reasons, stale_ids = _gather_evidence_for_claim(
        packet,
        rule,
        source_lifecycle,
        market_by_packet,
        document_fields_by_packet,
        document_evidence_by_packet,
        reviews_by_packet,
    )
    can_show = _safe_route_claim(rule, evidence, missing_reasons)
    if rule["forbidden_external_claim"]:
        reason = "forbidden_external_claim_requires_real_reviewer_or_official_evidence"
    elif missing_reasons:
        reason = "missing_required_evidence"
    elif not evidence:
        reason = "no_evidence_no_claim"
    elif stale_ids and not rule["safe_without_reviewer"]:
        reason = "stale_or_reference_only_evidence_blocks_claim"
        can_show = False
    elif can_show:
        reason = "safe_research_or_preparation_statement_only"
    else:
        reason = "reviewer_finding_required"
    if stale_ids and rule["forbidden_external_claim"]:
        reason = "reference_only_or_stale_evidence_cannot_open_external_claim"
    return {
        "claim_gate_decision_id": f"claim-gate:{packet_id}:{rule['claim_type']}",
        "packet_id": packet_id,
        "claim_type": rule["claim_type"],
        "claim_family": rule["claim_family"],
        "label": rule["label"],
        "can_show_claim": can_show,
        "display_level": SAFE_RESEARCH_LEVEL if can_show else BLOCKED_LEVEL,
        "allowed_wording": rule["allowed_wording"] if can_show else "",
        "blocked_wording": rule["blocked_wording"],
        "reason": reason,
        "required_packet_fields": list(rule["required_packet_fields"]),
        "required_source_ids": list(rule["required_source_ids"]),
        "required_evidence_types": list(rule["required_evidence_types"]),
        "required_reviewer_lane": rule["required_reviewer_lane"],
        "evidence_trail": [
            {
                "evidence_id": row.get("evidence_id"),
                "type": row.get("type") or row.get("evidence_type"),
                "freshness": row.get("freshness") or row.get("freshness_status") or row.get("ledger_status"),
                "provenance": row.get("provenance"),
                "claim_boundary": row.get("claim_boundary"),
            }
            for row in evidence
            if row.get("evidence_id")
        ],
        "evidence_count": len([row for row in evidence if row.get("evidence_id")]),
        "stale_or_reference_only_evidence_ids": stale_ids,
        "missing_evidence": missing_reasons,
        "next_valid_move": rule["next_valid_move"],
        "external_effects_created": False,
        "claims_opened": False,
    }


def _claim_gate_mappers() -> list[dict[str, Any]]:
    return [
        {
            "claim_gate_mapper_id": f"claim-gate-mapper:{rule['claim_type']}",
            "claim_type": rule["claim_type"],
            "claim_family": rule["claim_family"],
            "required_packet_fields": list(rule["required_packet_fields"]),
            "required_evidence_types": list(rule["required_evidence_types"]),
            "required_source_ids": list(rule["required_source_ids"]),
            "required_reviewer_lane": rule["required_reviewer_lane"],
            "safe_without_reviewer": rule["safe_without_reviewer"],
            "forbidden_external_claim": rule["forbidden_external_claim"],
            "blocked_wording": rule["blocked_wording"],
        }
        for rule in CLAIM_RULES
    ]


def _evidence_mappers(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        for evidence in decision["evidence_trail"]:
            evidence_id = _text(evidence.get("evidence_id"))
            if not evidence_id:
                continue
            row = mapped.setdefault(
                evidence_id,
                {
                    "evidence_mapper_id": f"evidence-mapper:{evidence_id}",
                    "evidence_id": evidence_id,
                    "type": evidence.get("type"),
                    "freshness": evidence.get("freshness"),
                    "provenance": evidence.get("provenance"),
                    "claim_boundary": evidence.get("claim_boundary"),
                    "supports_claims": [],
                    "blocks_claims": [],
                },
            )
            if decision["can_show_claim"]:
                row["supports_claims"].append(decision["claim_type"])
            else:
                row["blocks_claims"].append(decision["claim_type"])
    for row in mapped.values():
        row["supports_claims"] = sorted(set(row["supports_claims"]))
        row["blocks_claims"] = sorted(set(row["blocks_claims"]))
    return sorted(mapped.values(), key=lambda item: item["evidence_id"])


def build_production_evidence_claim_gate_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    customer = _load_json(root / "system_review_graph" / "customer_readiness_report.json", {})
    country = _load_json(root / "system_review_graph" / "production_country_source_engine_manifest.json", {})
    market = _load_json(root / "system_review_graph" / "production_market_intelligence_manifest.json", {})
    document = _load_json(root / "system_review_graph" / "production_document_intelligence_manifest.json", {})
    reviews = _load_json(root / "system_review_graph" / "review_requests.json", [])
    source_refresh = _load_json(root / "system_review_graph" / "source_refresh_runs.json", [])
    customs_trade_review = _load_json(root / "system_review_graph" / "qualified_customs_trade_review_manifest.json", {})
    packet_lookup = _packet_by_id(customer)
    source_lifecycle = _source_lifecycle_by_id(country)
    market_by_packet = _market_signals_by_packet(market)
    document_fields = _document_fields_by_packet(document)
    document_evidence = _document_evidence_by_packet(document)
    reviews_for_packet = _reviews_by_packet(reviews)
    decisions = []
    for packet in packet_lookup.values():
        for rule in CLAIM_RULES:
            decisions.append(
                _decision_for_claim(
                    packet,
                    rule,
                    source_lifecycle,
                    market_by_packet,
                    document_fields,
                    document_evidence,
                    reviews_for_packet,
                )
            )
    safe_count = sum(1 for decision in decisions if decision["can_show_claim"])
    blocked_count = len(decisions) - safe_count
    forbidden_count = sum(1 for decision in decisions if _rules_by_type()[decision["claim_type"]]["forbidden_external_claim"])
    evidence_mappers = _evidence_mappers(decisions)
    claim_gate_mappers = _claim_gate_mappers()
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "packet_count": len(packet_lookup),
        "claim_type_count": len(CLAIM_RULES),
        "claim_gate_decision_count": len(decisions),
        "safe_research_claim_count": safe_count,
        "blocked_claim_count": blocked_count,
        "forbidden_external_claim_count": forbidden_count,
        "evidence_mapper_count": len(evidence_mappers),
        "claim_gate_mapper_count": len(claim_gate_mappers),
        "source_refresh_record_count": sum(len(run.get("rows", [])) for run in source_refresh),
        "source_route_count": len(_source_ids_from_country(country)),
        "packet_ids": sorted(packet_lookup),
        "claim_gate_decisions": decisions,
        "evidence_mappers": evidence_mappers,
        "claim_gate_mappers": claim_gate_mappers,
        "qualified_customs_trade_review_evidence_status": customs_trade_review.get(
            "status",
            "qualified_customs_trade_review_manifest_missing",
        ),
        "qualified_customs_trade_review_record_count": customs_trade_review.get("review_record_count", 0),
        "qualified_customs_trade_accepted_review_record_count": customs_trade_review.get(
            "accepted_review_record_count",
            0,
        ),
        "qualified_customs_trade_review_blocked_gate_count": customs_trade_review.get(
            "blocked_gate_count",
            QUALIFIED_CUSTOMS_TRADE_REVIEW_FALLBACK_GATE_COUNT,
        ),
        "qualified_customs_trade_reviewed_by_evidence": customs_trade_review.get(
            "customs_trade_reviewed_by_evidence",
            False,
        ),
        "tariff_confirmed_by_review_evidence": customs_trade_review.get(
            "tariff_confirmed_by_review_evidence",
            False,
        ),
        "cfia_approved_by_review_evidence": customs_trade_review.get("cfia_approved_by_review_evidence", False),
        "customs_ready_by_review_evidence": customs_trade_review.get("customs_ready_by_review_evidence", False),
        "qualified_customs_trade_claims_opened_by_intake": customs_trade_review.get("claims_opened_by_intake", False),
        "blocked_external_claims": [
            rule["claim_type"] for rule in CLAIM_RULES if rule["forbidden_external_claim"]
        ],
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "live_payment_ready": False,
        "proof_boundary": (
            "The claim-gate engine can show only safe preparation/research statements. "
            "Reference-only, stale, missing, parser-draft, or unreviewed evidence blocks "
            "customs, tariff, CFIA, buyer, supplier, shipment, payment, legal, and launch claims."
        ),
    }


def can_show_claim(
    claim_type: str,
    packet_id: str,
    repo_root: Path | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = manifest or build_production_evidence_claim_gate_engine(repo_root)
    claim_type_text = _text(claim_type)
    packet_id_text = _text(packet_id)
    for decision in payload.get("claim_gate_decisions", []):
        if decision.get("claim_type") == claim_type_text and decision.get("packet_id") == packet_id_text:
            return decision
    return {
        "claim_gate_decision_id": f"claim-gate:{packet_id_text}:{claim_type_text}",
        "packet_id": packet_id_text,
        "claim_type": claim_type_text,
        "can_show_claim": False,
        "display_level": BLOCKED_LEVEL,
        "blocked_wording": "Unknown claim type or packet; no evidence, no claim.",
        "reason": "unknown_claim_or_packet",
        "evidence_trail": [],
        "missing_evidence": ["registered claim rule and packet record"],
        "external_effects_created": False,
        "claims_opened": False,
    }


def render_evidence_claim_gate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Evidence Claim-Gate Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Claim Gate Summary",
        "",
        f"- Claim types: {payload['claim_type_count']}",
        f"- Decisions: {payload['claim_gate_decision_count']}",
        f"- Safe research/preparation statements: {payload['safe_research_claim_count']}",
        f"- Blocked claims: {payload['blocked_claim_count']}",
        f"- Forbidden external claims: {payload['forbidden_external_claim_count']}",
        f"- Evidence mappers: {payload['evidence_mapper_count']}",
        f"- Claim gate mappers: {payload['claim_gate_mapper_count']}",
        f"- Qualified customs/trade review status: `{payload['qualified_customs_trade_review_evidence_status']}`",
        f"- Qualified customs/trade review records: {payload['qualified_customs_trade_review_record_count']}",
        f"- Qualified customs/trade blocked gates: {payload['qualified_customs_trade_review_blocked_gate_count']}",
        f"- Tariff confirmed by review evidence: {str(payload['tariff_confirmed_by_review_evidence']).lower()}",
        f"- CFIA approved by review evidence: {str(payload['cfia_approved_by_review_evidence']).lower()}",
        "",
        "## Packet Decisions",
        "",
    ]
    for packet_id in payload["packet_ids"]:
        lines.append(f"### {packet_id}")
        lines.append("")
        packet_decisions = [row for row in payload["claim_gate_decisions"] if row["packet_id"] == packet_id]
        for decision in packet_decisions:
            state = "show" if decision["can_show_claim"] else "blocked"
            lines.append(
                f"- `{decision['claim_type']}`: {state}; reason `{decision['reason']}`; evidence {decision['evidence_count']}."
            )
        lines.append("")
    lines.extend(
        [
            "## Closed Gates",
            "",
            "- External effects created: false",
            "- Claims opened: false",
            "- Public launch ready: false",
            "- Live payment ready: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_evidence_claim_gate_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_evidence_claim_gate_manifest.json"
    decisions_path = graph / "production_claim_gate_decisions.json"
    mappers_path = graph / "production_evidence_claim_mappers.json"
    doc_path = docs / "PRODUCTION_EVIDENCE_CLAIM_GATE_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decisions_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_claim_gate_decisions_ready_fail_closed",
                "claim_gate_decision_count": payload["claim_gate_decision_count"],
                "safe_research_claim_count": payload["safe_research_claim_count"],
                "blocked_claim_count": payload["blocked_claim_count"],
                "decisions": payload["claim_gate_decisions"],
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    mappers_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_evidence_claim_mappers_ready",
                "evidence_mapper_count": payload["evidence_mapper_count"],
                "claim_gate_mapper_count": payload["claim_gate_mapper_count"],
                "evidence_mappers": payload["evidence_mappers"],
                "claim_gate_mappers": payload["claim_gate_mappers"],
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_evidence_claim_gate_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "decisions": decisions_path,
        "mappers": mappers_path,
        "doc": doc_path,
    }
