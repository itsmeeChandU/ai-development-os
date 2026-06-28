"""Production packet engine for Trade Readiness Copilot.

This module turns the phase-2 production requirement into executable local
logic. It evaluates real repo packet/evidence/source/review/report artifacts,
derives a production packet state, emits packet views, records state events,
and keeps approval-style claims closed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_packet_engine_ready_local_state_machine_claim_gates_closed"

PACKET_STATES = (
    "draft",
    "starter_ready",
    "research_ready",
    "evidence_collecting",
    "document_reviewing",
    "source_checking",
    "decision_preparing",
    "reviewer_ready",
    "expert_reviewing",
    "customer_report_ready",
    "paid_packet_ready",
    "archived",
)

PACKET_VIEW_TYPES = (
    "starter_packet",
    "market_research_packet",
    "buyer_ready_packet",
    "supplier_request_packet",
    "broker_review_packet",
    "operator_packet",
    "executive_decision_packet",
    "blocked_claims_packet",
)

CORE_FIELDS = (
    "product_name",
    "product_category",
    "origin_country",
    "destination_country",
    "intended_use",
)

BUSINESS_SCORE_IDS = (
    "market_signal_score",
    "evidence_completeness_score",
    "source_freshness_score",
    "buyer_supplier_evidence_score",
    "responsibility_clarity_score",
    "decision_safety_score",
)

CLAIM_GATE_REQUIREMENTS = {
    "tariff_confirmed": ("qualified_trade_or_customs_review", "authoritative tariff/classification evidence"),
    "cfia_compliant": ("qualified_food_or_regulated_goods_review", "current CFIA/AIRS product-specific evidence"),
    "supplier_recommended": ("supplier_evidence_review", "supplier registration, product, certificate, and inspection evidence"),
    "buyer_validated": ("buyer_evidence_review", "dated buyer reply, meeting, sample, LOI, PO, or paid-order evidence"),
    "ready_to_import": ("qualified_import_review", "importer of record, Incoterms, source freshness, broker review"),
    "ready_to_export_to_canada": ("qualified_export_to_canada_review", "origin export and Canada import review evidence"),
    "canadian_importer_confirmed": ("buyer_importer_review", "dated importer confirmation and permission scope"),
    "export_documentation_complete": ("document_review", "confirmed product, commercial, origin, and shipping documents"),
    "trade_agreement_preference_confirmed": ("trade_agreement_review", "rules-of-origin and preference evidence"),
    "public_launch_ready": ("final_launch_owner_review", "all launch gates approved for exact public scope"),
    "customs_or_tariff_advice_ready": ("qualified_customs_review", "customs broker or qualified reviewer finding"),
    "legal_or_compliance_approved": ("legal_privacy_security_review", "qualified legal/privacy/security approval"),
    "ready_to_ship": ("qualified_trade_review", "shipment responsibility, documents, permits, and reviewer approval"),
}

PRODUCT_CLASS_DOCUMENTS = {
    "general_goods": ["commercial invoice", "packing list", "product specification", "proof of origin"],
    "food": ["product specification", "commercial invoice", "packing list", "CFIA/AIRS route", "health or food certificate when applicable"],
    "plant": ["product specification", "CFIA/AIRS route", "phytosanitary evidence when applicable"],
    "animal": ["product specification", "CFIA/AIRS route", "health certificate when applicable"],
    "seafood": ["product specification", "CFIA/AIRS route", "health or catch/processing evidence when applicable"],
    "textiles": ["composition details", "country of origin evidence", "labeling or standards route"],
    "controlled_goods": ["export/import control route", "permit question", "qualified review packet"],
    "regulated_goods": ["regulated-product source route", "permit question", "qualified review packet"],
}

OFFICIAL_SOURCE_PURPOSES = (
    "import process",
    "tariff orientation",
    "regulated goods",
    "sanctions or restricted party",
    "trade data",
    "buyer lead discovery",
    "broker discovery",
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
    return bool(text and text not in {"unknown", "missing", "none", "not_known", "not known"})


def _normalize_country(country: Any) -> str:
    text = _text(country)
    return {
        "CA": "Canada",
        "CAN": "Canada",
        "IN": "India",
        "IND": "India",
        "VN": "Vietnam",
        "VNM": "Vietnam",
        "US": "United States",
        "USA": "United States",
        "GB": "United Kingdom",
        "UK": "United Kingdom",
    }.get(text.upper(), text or "Generic")


def _infer_direction(packet: dict[str, Any]) -> tuple[str, str]:
    raw = _text(packet.get("trade_direction")).lower()
    if raw in {"import", "export", "both", "exploring"}:
        return raw, "user_input"
    category = _text(packet.get("product_category")).lower()
    destination = _normalize_country(packet.get("destination_country")).lower()
    origin = _normalize_country(packet.get("origin_country")).lower()
    if "import" in category or destination == "canada":
        return "import", "system_derived_needs_user_confirmation"
    if "export" in category or origin == "canada":
        return "export", "system_derived_needs_user_confirmation"
    return "exploring", "system_default_needs_user_confirmation"


def _product_class(packet: dict[str, Any]) -> str:
    blob = " ".join(
        _text(packet.get(key)).lower()
        for key in ("product_name", "product_category", "intended_use")
    )
    if any(word in blob for word in ("seafood", "fish", "tuna", "shrimp")):
        return "seafood"
    if any(word in blob for word in ("food", "edible", "ingredient")):
        return "food"
    if "plant" in blob:
        return "plant"
    if "animal" in blob:
        return "animal"
    if "textile" in blob:
        return "textiles"
    if any(word in blob for word in ("controlled", "weapon", "dual use", "scomet")):
        return "controlled_goods"
    if any(word in blob for word in ("regulated", "medical", "chemical")):
        return "regulated_goods"
    return "general_goods"


def _ledger_rows(evidence_ledger: Any) -> list[dict[str, Any]]:
    if isinstance(evidence_ledger, dict):
        return [row for row in evidence_ledger.get("rows", []) if isinstance(row, dict)]
    if isinstance(evidence_ledger, list):
        return [row for row in evidence_ledger if isinstance(row, dict)]
    return []


def _generated_packet_by_id(generated_packets: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(generated_packets, list):
        return {}
    return {
        _text(row.get("packet_id")): row
        for row in generated_packets
        if isinstance(row, dict) and _text(row.get("packet_id"))
    }


def _source_jurisdiction_matches(source: dict[str, Any], country: str) -> bool:
    jurisdiction = _normalize_country(source.get("jurisdiction")).lower()
    return jurisdiction in {country.lower(), "international"}


def _source_routes(packet: dict[str, Any], official_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    origin = _normalize_country(packet.get("origin_country"))
    destination = _normalize_country(packet.get("destination_country"))
    product_class = _product_class(packet)
    rows: list[dict[str, Any]] = []
    for source in official_sources:
        text = " ".join(
            _text(source.get(key)).lower()
            for key in ("id", "name", "evidence_role", "claim_boundary", "url")
        )
        matches_country = _source_jurisdiction_matches(source, destination) or _source_jurisdiction_matches(source, origin)
        matches_product = product_class not in {"food", "seafood", "plant", "animal"} or any(
            word in text for word in ("cfia", "airs", "food", "regulated", "import", "tariff", "broker")
        )
        if matches_country and matches_product:
            rows.append(
                {
                    "source_id": source.get("id"),
                    "name": source.get("name"),
                    "jurisdiction": _normalize_country(source.get("jurisdiction")),
                    "url": source.get("url"),
                    "evidence_role": source.get("evidence_role"),
                    "claim_boundary": source.get("claim_boundary"),
                    "route_status": "reference_route_only",
                    "terms_status": "must_check_before_fetch",
                    "supports_claims": [],
                    "blocked_claims": list(CLAIM_GATE_REQUIREMENTS),
                }
            )
    return rows


def _required_field_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    direction, provenance = _infer_direction(packet)
    rows = [
        {
            "field": "trade_direction",
            "value": direction,
            "status": "provided" if provenance == "user_input" else "needs_user_confirmation",
            "provenance": provenance,
        }
    ]
    for field in CORE_FIELDS:
        rows.append(
            {
                "field": field,
                "value": packet.get(field, ""),
                "status": "provided" if _known(packet.get(field)) else "missing",
                "provenance": "user_input" if _known(packet.get(field)) else "missing",
            }
        )
    for field in ("hs_code_value", "supplier_name", "buyer_name", "importer_name", "importer_of_record", "incoterms"):
        status = "provided" if _known(packet.get(field)) else "missing"
        if field == "hs_code_value" and status == "provided":
            status = "candidate_needs_qualified_review"
        rows.append(
            {
                "field": field,
                "value": packet.get(field, ""),
                "status": status,
                "provenance": "user_input" if _known(packet.get(field)) else "missing",
            }
        )
    return rows


def _evidence_summary(evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    stale = [
        row for row in evidence_rows
        if _text(row.get("freshness_status") or row.get("freshness") or row.get("quality_status")).lower()
        in {"needs_current_refresh_before_claims", "stale", "source_changed", "review_required"}
        or _text(row.get("quality_status")).lower() == "stale"
        or _text(row.get("ledger_status")).lower() in {"blocked_stale_source", "blocked_reference_only"}
    ]
    review_required = [row for row in evidence_rows if bool(row.get("review_required", False))]
    return {
        "evidence_count": len(evidence_rows),
        "stale_evidence_count": len(stale),
        "review_required_count": len(review_required),
        "evidence_ids": [_text(row.get("evidence_id")) for row in evidence_rows],
        "stale_evidence_ids": [_text(row.get("evidence_id")) for row in stale],
        "all_evidence_is_draft_or_reference_only": all(
            _text(row.get("human_review_status")).lower() not in {"reviewed", "approved_for_scope"}
            for row in evidence_rows
        ),
    }


def _blocker_rows(packet: dict[str, Any], generated_packet: dict[str, Any], evidence_summary: dict[str, Any]) -> list[dict[str, Any]]:
    blocked_claims = list(generated_packet.get("blocked_claims", [])) if generated_packet else []
    if not blocked_claims:
        blocked_claims = list(CLAIM_GATE_REQUIREMENTS)
    if "ready_to_ship" not in blocked_claims:
        blocked_claims.append("ready_to_ship")

    blockers = []
    for claim in blocked_claims:
        reviewer_lane, required_evidence = CLAIM_GATE_REQUIREMENTS.get(
            claim,
            ("qualified_reviewer", "claim-specific evidence and source freshness"),
        )
        reason = "Missing qualified review and claim-specific evidence."
        if evidence_summary["stale_evidence_count"]:
            reason = "Evidence is stale or reference-only; stronger claim must remain blocked."
        blockers.append(
            {
                "claim": claim,
                "status": "blocked",
                "reason": reason,
                "required_evidence": required_evidence,
                "required_reviewer_lane": reviewer_lane,
                "next_valid_move": "Attach current evidence and route this exact claim to a qualified reviewer.",
                "unsafe_to_bypass": True,
            }
        )
    if not _known(packet.get("importer_of_record")):
        blockers.append(
            {
                "claim": "responsibility_clarity",
                "status": "blocked",
                "reason": "Importer of record is missing.",
                "required_evidence": "Buyer/importer responsibility confirmation",
                "required_reviewer_lane": "trade_or_broker_review",
                "next_valid_move": "Confirm who is importer of record before any import-readiness statement.",
                "unsafe_to_bypass": True,
            }
        )
    if not _known(packet.get("incoterms")):
        blockers.append(
            {
                "claim": "incoterms_responsibility",
                "status": "blocked",
                "reason": "Incoterms or delivery responsibility are missing.",
                "required_evidence": "Incoterms or responsibility split confirmation",
                "required_reviewer_lane": "freight_logistics_review",
                "next_valid_move": "Ask buyer/importer and supplier who handles freight, customs, duties, and delivery risk.",
                "unsafe_to_bypass": True,
            }
        )
    return blockers


def _score_rows(packet: dict[str, Any], evidence_summary: dict[str, Any], blockers: list[dict[str, Any]], source_routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_fields = [
        row["field"]
        for row in _required_field_rows(packet)
        if row["status"] in {"missing", "needs_user_confirmation"}
    ]
    source_label = "red" if evidence_summary["stale_evidence_count"] else "yellow"
    responsibility_missing = [
        field for field in ("importer_of_record", "incoterms")
        if not _known(packet.get(field))
    ]
    return [
        {
            "score": "market_signal_score",
            "label": "yellow" if source_routes else "grey",
            "reason": "Official market/source routes exist as research signals only.",
            "blocking_fields": [],
            "next_action": "Attach source-backed market metrics before any market conclusion.",
        },
        {
            "score": "evidence_completeness_score",
            "label": "yellow" if evidence_summary["evidence_count"] else "red",
            "reason": "Some evidence exists, but missing fields and reviewer proof still cap the score.",
            "blocking_fields": missing_fields,
            "next_action": "Collect missing packet fields and confirm extracted or attached evidence.",
        },
        {
            "score": "source_freshness_score",
            "label": source_label,
            "reason": "Stale or reference-only source evidence blocks stronger claims." if source_label == "red" else "Sources still require review before claims.",
            "blocking_fields": evidence_summary["stale_evidence_ids"],
            "next_action": "Refresh official sources and attach source snapshots.",
        },
        {
            "score": "buyer_supplier_evidence_score",
            "label": "red",
            "reason": "Supplier is named, but buyer/supplier validation evidence is not attached.",
            "blocking_fields": ["buyer_evidence", "supplier_verification_evidence"],
            "next_action": "Collect buyer reply/meeting/LOI/PO evidence and supplier registration/product/certificate evidence.",
        },
        {
            "score": "responsibility_clarity_score",
            "label": "red" if responsibility_missing else "yellow",
            "reason": "Importer of record or Incoterms are missing." if responsibility_missing else "Responsibility fields need reviewer confirmation.",
            "blocking_fields": responsibility_missing,
            "next_action": "Confirm importer of record, Incoterms, and broker/reviewer responsibility path.",
        },
        {
            "score": "decision_safety_score",
            "label": "red" if blockers else "yellow",
            "reason": "External gates and blocked claims remain open.",
            "blocking_fields": sorted({row["claim"] for row in blockers}),
            "next_action": "Resolve blocker evidence and reviewer lanes before customer-visible stronger claims.",
        },
    ]


def _state_events(
    packet_id: str,
    state: str,
    evidence_summary: dict[str, Any],
    review_requests: list[dict[str, Any]],
    report_exports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reached = {
        "draft": True,
        "starter_ready": True,
        "research_ready": True,
        "evidence_collecting": evidence_summary["evidence_count"] > 0,
        "document_reviewing": evidence_summary["evidence_count"] > 0,
        "source_checking": evidence_summary["stale_evidence_count"] > 0,
        "decision_preparing": True,
        "reviewer_ready": bool(review_requests),
        "expert_reviewing": any(_text(row.get("status")).lower() == "in_review" for row in review_requests),
        "customer_report_ready": bool(report_exports),
        "paid_packet_ready": False,
        "archived": False,
    }
    events = []
    for index, state_name in enumerate(PACKET_STATES, start=1):
        if reached[state_name]:
            status = "reached"
            reason = "state requirements met for local/internal workflow"
        else:
            status = "blocked"
            reason = "external evidence, reviewer, payment, or archive condition not met"
        events.append(
            {
                "event_id": f"{packet_id}:{index:02d}:{state_name}",
                "packet_id": packet_id,
                "state": state_name,
                "event_type": "packet_state_reached" if status == "reached" else "packet_state_blocked",
                "status": status,
                "is_current_state": state_name == state,
                "reason": reason,
                "external_effects_created": False,
                "claims_opened": False,
            }
        )
    return events


def _current_state(evidence_summary: dict[str, Any], review_requests: list[dict[str, Any]], report_exports: list[dict[str, Any]]) -> str:
    if any(_text(row.get("status")).lower() == "in_review" for row in review_requests):
        return "expert_reviewing"
    if review_requests:
        return "reviewer_ready"
    if report_exports:
        return "customer_report_ready"
    if evidence_summary["stale_evidence_count"]:
        return "source_checking"
    if evidence_summary["evidence_count"]:
        return "document_reviewing"
    return "research_ready"


def _packet_views(
    packet: dict[str, Any],
    state: str,
    source_routes: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    evidence_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    packet_id = _text(packet.get("packet_id"))
    product_class = _product_class(packet)
    document_checklist = PRODUCT_CLASS_DOCUMENTS.get(product_class, PRODUCT_CLASS_DOCUMENTS["general_goods"])
    base = {
        "packet_id": packet_id,
        "current_state": state,
        "product": packet.get("product_name"),
        "origin_country": _normalize_country(packet.get("origin_country")),
        "destination_country": _normalize_country(packet.get("destination_country")),
        "blocked_claims_visible": True,
        "claim_boundary": "Preparation and evidence organization only; no approval, compliance, buyer, supplier, tariff, shipment, payment, or launch claim is opened.",
        "external_effects_created": False,
        "claims_opened": False,
    }
    view_defs = [
        ("starter_packet", "beginner_or_customer", "ready", ["required fields", "starter checklist", "next safe move"]),
        ("market_research_packet", "customer_or_operator", "reference_only", ["source routes", "market research questions", "limitations"]),
        ("buyer_ready_packet", "buyer_or_importer", "blocked_claims_visible", ["buyer questions", "evidence boundaries", "blocked buyer validation"]),
        ("supplier_request_packet", "supplier", "evidence_collection_ready", ["supplier documents", "risk questions", "missing evidence"]),
        ("broker_review_packet", "customs_broker_or_trade_expert", "ready_for_scoped_review", ["source routes", "HS candidate", "CFIA/tariff blockers"]),
        ("operator_packet", "internal_operator", "ready", ["state events", "scores", "blockers"]),
        ("executive_decision_packet", "owner_or_manager", "internal_decision_prep_only", ["six scores", "next move", "go/no-go blockers"]),
        ("blocked_claims_packet", "reviewer_or_operator", "ready", ["blocked claims", "required evidence", "reviewer lanes"]),
    ]
    return [
        {
            **base,
            "view_type": view_type,
            "audience": audience,
            "view_status": view_status,
            "includes": includes,
            "source_route_count": len(source_routes),
            "evidence_count": evidence_summary["evidence_count"],
            "blocked_claim_count": len(blockers),
            "score_count": len(scores),
            "document_checklist": document_checklist if view_type in {"starter_packet", "supplier_request_packet", "broker_review_packet"} else [],
            "next_valid_move": _next_valid_move(evidence_summary, blockers),
        }
        for view_type, audience, view_status, includes in view_defs
    ]


def _next_valid_move(evidence_summary: dict[str, Any], blockers: list[dict[str, Any]]) -> str:
    if evidence_summary["stale_evidence_count"]:
        return "Refresh official sources and attach dated source snapshots before reviewer assessment."
    if blockers:
        return blockers[0]["next_valid_move"]
    return "Prepare scoped reviewer packet; do not open external claims."


def _evaluate_packet(
    packet: dict[str, Any],
    generated_packet: dict[str, Any],
    official_sources: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    review_requests: list[dict[str, Any]],
    report_exports: list[dict[str, Any]],
) -> dict[str, Any]:
    packet_id = _text(packet.get("packet_id"))
    direction, direction_provenance = _infer_direction(packet)
    routes = _source_routes(packet, official_sources)
    evidence = _evidence_summary(evidence_rows)
    blockers = _blocker_rows(packet, generated_packet, evidence)
    scores = _score_rows(packet, evidence, blockers, routes)
    state = _current_state(evidence, review_requests, report_exports)
    events = _state_events(packet_id, state, evidence, review_requests, report_exports)
    views = _packet_views(packet, state, routes, blockers, scores, evidence)
    return {
        "packet_id": packet_id,
        "organization_id": packet.get("organization_id", "org-importer-demo"),
        "state": state,
        "state_index": PACKET_STATES.index(state),
        "state_machine_status": "local_state_machine_evaluated_external_gates_closed",
        "trade_direction": direction,
        "trade_direction_provenance": direction_provenance,
        "product_class": _product_class(packet),
        "required_fields": _required_field_rows(packet),
        "source_routes": routes,
        "source_route_count": len(routes),
        "evidence_summary": evidence,
        "blocked_claims": blockers,
        "blocked_claim_count": len(blockers),
        "scores": scores,
        "score_count": len(scores),
        "packet_views": views,
        "packet_view_count": len(views),
        "state_events": events,
        "state_event_count": len(events),
        "next_valid_move": _next_valid_move(evidence, blockers),
        "reviewer_ready_not_approved": state in {"reviewer_ready", "expert_reviewing"},
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "live_payment_ready": False,
        "proof_boundary": "Local packet engine proof only. Reviewer-ready is not approved, and packet progress is not trade readiness.",
    }


def build_production_packet_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    packets = _load_json(root / "data" / "customer_source_packets.json", [])
    generated_packets = _generated_packet_by_id(_load_json(root / "system_review_graph" / "customer_source_packets.json", []))
    official_sources = _load_json(root / "data" / "official_source_registry.json", [])
    evidence_rows = _ledger_rows(_load_json(root / "system_review_graph" / "evidence_ledger.json", []))
    review_requests = _load_json(root / "system_review_graph" / "review_requests.json", [])
    report_exports = _load_json(root / "system_review_graph" / "report_exports.json", [])
    packet_runs = []
    for packet in packets:
        packet_id = _text(packet.get("packet_id"))
        packet_evidence = [row for row in evidence_rows if _text(row.get("packet_id")) == packet_id]
        packet_reviews = [row for row in review_requests if packet_id in row.get("packet_ids", [row.get("packet_id")])]
        packet_reports = [row for row in report_exports if _text(row.get("packet_id")) == packet_id]
        packet_runs.append(
            _evaluate_packet(
                packet,
                generated_packets.get(packet_id, {}),
                official_sources,
                packet_evidence,
                packet_reviews,
                packet_reports,
            )
        )
    all_events = [event for run in packet_runs for event in run["state_events"]]
    all_views = [view for run in packet_runs for view in run["packet_views"]]
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "packet_state_machine_status": "implemented_local_engine_external_gates_closed",
        "state_count": len(PACKET_STATES),
        "states": list(PACKET_STATES),
        "packet_count": len(packet_runs),
        "packet_event_count": len(all_events),
        "packet_view_type_count": len(PACKET_VIEW_TYPES),
        "packet_view_count": len(all_views),
        "score_ids": list(BUSINESS_SCORE_IDS),
        "claim_gate_count": len(CLAIM_GATE_REQUIREMENTS),
        "official_source_purposes": list(OFFICIAL_SOURCE_PURPOSES),
        "packet_runs": packet_runs,
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "hosted_private_beta_ready": False,
        "live_payment_ready": False,
        "proof_boundary": (
            "This is a real local packet state/view/gate engine. It does not prove "
            "hosted production, live payments, legal/privacy/security approval, "
            "qualified customs/trade review, buyer validation, supplier verification, "
            "or public go-live approval."
        ),
    }


def render_packet_engine_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Packet Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This engine evaluates packet state from local packet, evidence, source, review, and report artifacts.",
        "",
        "## Proof Boundary",
        "",
        payload["proof_boundary"],
        "",
        "## State Machine",
        "",
    ]
    for index, state in enumerate(payload["states"], start=1):
        lines.append(f"{index}. `{state}`")
    lines.extend(["", "## Packet Runs", ""])
    for run in payload["packet_runs"]:
        lines.extend(
            [
                f"### {run['packet_id']}",
                "",
                f"- Current state: `{run['state']}`",
                f"- Product class: `{run['product_class']}`",
                f"- View count: {run['packet_view_count']}",
                f"- Source routes: {run['source_route_count']}",
                f"- Blocked claims: {run['blocked_claim_count']}",
                f"- Scores: {run['score_count']}",
                f"- Reviewer-ready is approved: false",
                f"- Next valid move: {run['next_valid_move']}",
                "",
            ]
        )
    lines.extend(["", "## Packet Views", ""])
    for view_type in PACKET_VIEW_TYPES:
        lines.append(f"- `{view_type}`")
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            "- External effects created: false",
            "- Claims opened: false",
            "- Public launch ready: false",
            "- Hosted private beta ready: false",
            "- Live payment ready: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_packet_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    views_root = graph / "production_packet_views"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    views_root.mkdir(parents=True, exist_ok=True)

    manifest_path = graph / "production_packet_engine_manifest.json"
    events_path = graph / "production_packet_events.json"
    doc_path = docs / "PRODUCTION_PACKET_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    events = [event for run in payload["packet_runs"] for event in run["state_events"]]
    events_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_packet_events_ready_no_external_effects",
                "event_count": len(events),
                "events": events,
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    view_paths: list[str] = []
    for run in payload["packet_runs"]:
        packet_dir = views_root / run["packet_id"]
        packet_dir.mkdir(parents=True, exist_ok=True)
        for view in run["packet_views"]:
            view_path = packet_dir / f"{view['view_type']}.json"
            view_path.write_text(json.dumps(view, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            view_paths.append(str(view_path.relative_to(repo_root)))
    doc_path.write_text(render_packet_engine_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "events": events_path,
        "views_root": views_root,
        "doc": doc_path,
        "view_paths": view_paths,
    }
