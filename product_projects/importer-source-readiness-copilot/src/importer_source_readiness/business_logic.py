"""Business-decision logic for trade readiness packets.

The functions in this module turn packet/evidence state into decision-prep
outputs. They deliberately stop short of compliance, buyer, supplier, tariff,
or market-demand claims unless real evidence is attached elsewhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


BUSINESS_PHASE_IDS = [f"phase-{index}" for index in range(1, 14)]

BUSINESS_COMPLETION_PHASE_IDS = [f"phase_{index}" for index in range(14)]

BUSINESS_SCORE_IDS = [
    "market_signal_score",
    "evidence_completeness_score",
    "source_freshness_score",
    "buyer_supplier_evidence_score",
    "responsibility_clarity_score",
    "decision_safety_score",
]

PROVENANCE_MODES = [
    "user_input",
    "parser_extracted_draft",
    "official_source_reference",
    "system_derived",
    "reviewer_verified",
]

BUYER_EVIDENCE_LADDER = [
    {"level": 0, "label": "lead_found", "allowed_language": "buyer lead found"},
    {"level": 1, "label": "contact_attempted", "allowed_language": "buyer contact attempted"},
    {"level": 2, "label": "reply_received", "allowed_language": "buyer replied on a dated channel"},
    {"level": 3, "label": "meeting_completed", "allowed_language": "buyer meeting completed and notes attached"},
    {"level": 4, "label": "loi_received", "allowed_language": "letter of intent or equivalent evidence attached"},
    {"level": 5, "label": "po_or_paid_order", "allowed_language": "purchase order or paid order evidence attached"},
]

SUPPLIER_EVIDENCE_LADDER = [
    {"level": 0, "label": "supplier_named", "allowed_language": "supplier named by user"},
    {"level": 1, "label": "business_registration_attached", "allowed_language": "registration evidence collected"},
    {"level": 2, "label": "export_ability_evidence_attached", "allowed_language": "export ability evidence collected"},
    {"level": 3, "label": "product_docs_attached", "allowed_language": "product documents collected"},
    {"level": 4, "label": "inspection_or_certificate_attached", "allowed_language": "inspection or certificate evidence collected"},
    {"level": 5, "label": "prior_shipment_evidence_attached", "allowed_language": "prior shipment evidence collected"},
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _country(value: Any) -> str:
    text = str(value or "Generic").strip() or "Generic"
    return {
        "CA": "Canada",
        "CAN": "Canada",
        "US": "United States",
        "USA": "United States",
        "UK": "United Kingdom",
        "GB": "United Kingdom",
        "IN": "India",
        "IND": "India",
        "VN": "Vietnam",
        "VNM": "Vietnam",
    }.get(text, text)


def _source_summary(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source.get("id"),
        "name": source.get("name"),
        "url": source.get("url"),
        "jurisdiction": _country(source.get("jurisdiction")),
        "evidence_role": source.get("evidence_role"),
        "claim_boundary": source.get("claim_boundary"),
        "accessed_at": source.get("accessed_at"),
    }


def _normalized_source_registry_row(source: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    summary = _source_summary(source)
    source_text = " ".join(
        str(source.get(key) or "")
        for key in ("id", "name", "evidence_role", "claim_boundary", "url")
    ).lower()
    if "tariff" in source_text or "market access" in source_text:
        source_type = "tariff_or_market_access"
    elif "trade data" in source_text or "importer" in source_text:
        source_type = "market_or_buyer_research"
    elif "sanction" in source_text or "restricted" in source_text:
        source_type = "restricted_party_or_control"
    elif "food" in source_text or "cfia" in source_text or "airs" in source_text:
        source_type = "regulated_product_requirements"
    else:
        source_type = "official_reference"
    return {
        **summary,
        "source_type": source_type,
        "canonical_url": source.get("url"),
        "fetch_mode": "registered_reference_manual_refresh",
        "cadence": "before_packet_decision_or_when_source_changes",
        "robots_status": "must_check_before_fetch",
        "terms_status": "must_check_before_fetch",
        "auth_required": "unknown_until_source_review",
        "parser_type": "metadata_hash_or_structured_export_when_allowed",
        "content_hash": "",
        "diff_strategy": "hash_then_classify_material_change_before_claim_update",
        "packet_tags": [
            _packet_id(packet),
            _country(packet.get("origin_country")),
            _country(packet.get("destination_country")),
            _category(packet),
        ],
    }


def _sources_for_country(official_sources: list[dict[str, Any]], country: str) -> list[dict[str, Any]]:
    return [source for source in official_sources if _country(source.get("jurisdiction")) == country]


def _sources_matching(official_sources: list[dict[str, Any]], *needles: str) -> list[dict[str, Any]]:
    lowered = [needle.lower() for needle in needles]
    rows = []
    for source in official_sources:
        text = " ".join(
            str(source.get(key) or "")
            for key in ("id", "name", "evidence_role", "claim_boundary", "url")
        ).lower()
        if any(needle in text for needle in lowered):
            rows.append(source)
    return rows


def _packet_id(packet: dict[str, Any]) -> str:
    return str(packet.get("packet_id") or "unknown-packet")


def _category(packet: dict[str, Any]) -> str:
    return str(packet.get("product_category") or "general_trade").strip() or "general_trade"


def _is_regulated_category(packet: dict[str, Any]) -> bool:
    category = _category(packet).lower()
    product = str(packet.get("product_name") or "").lower()
    return any(
        word in f"{category} {product}"
        for word in ("food", "seafood", "animal", "plant", "health", "medical", "chemical")
    )


def _known(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple, set)):
        return bool(value)
    text = str(value).strip().lower()
    return bool(text and text not in {"unknown", "none", "missing", "not_known", "not known"})


def _answer(value: Any, missing_label: str = "unknown") -> str:
    return str(value).strip() if _known(value) else missing_label


def _packet_evidence(packet: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in packet.get("evidence_items", []) if isinstance(row, dict)]


def _text_blob(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        elif isinstance(value, (list, tuple, set)):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    return " ".join(parts).lower()


def _status_value(value: Any) -> str:
    return str(value or "missing").strip().lower()


def _review_done(value: Any) -> bool:
    return _status_value(value) in {"complete", "reviewed", "signed", "approved_for_scope", "validated"}


def _source_category(source: dict[str, Any]) -> str:
    return str(_normalized_source_registry_row(source, {})["source_type"])


def _has_source_category(sources: list[dict[str, Any]], *categories: str) -> bool:
    wanted = set(categories)
    return any(_source_category(source) in wanted for source in sources)


def _field_check(packet: dict[str, Any], field: str, label: str | None = None) -> dict[str, Any]:
    known = _known(packet.get(field))
    return {
        "field": field,
        "label": label or field.replace("_", " "),
        "status": "provided" if known else "missing",
        "has_value": known,
        "value": packet.get(field) if known else "",
    }


def _best_level(ladder: list[dict[str, Any]], labels: set[str]) -> dict[str, Any]:
    best = {"level": -1, "label": "no_evidence", "allowed_language": "no evidence collected"}
    for row in ladder:
        if str(row["label"]) in labels and int(row["level"]) > int(best["level"]):
            best = dict(row)
    return best


def _decision_answer_state(status: str) -> str:
    if status == "answered":
        return "answered"
    if status in {"needs_user_input", "needs_buyer_or_importer_discovery"}:
        return "unknown"
    if status in {"needs_research", "beginner_packet_supported"}:
        return "needs_research"
    if status in {"blocked_until_confirmed", "blocked_missing_source_routes"}:
        return "blocked"
    if status in {"needs_qualified_review", "needs_regulated_product_review", "standard_review_still_required"}:
        return "needs_expert_review"
    if status == "source_routes_ready_reference_only":
        return "needs_user_confirmation"
    return "needs_user_confirmation"


def build_decision_tree(packet: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the 12-question trade decision tree recommended by the review."""

    source_ids = [str(source.get("id")) for source in official_sources]
    regulated = _is_regulated_category(packet)
    questions = [
        {
            "step": 1,
            "question": "Are you importing, exporting, or exploring?",
            "answer": _answer(packet.get("trade_direction"), "exploring_or_unknown"),
            "status": "answered" if _known(packet.get("trade_direction")) else "needs_user_input",
        },
        {
            "step": 2,
            "question": "What product/category is involved?",
            "answer": _answer(packet.get("product_name") or packet.get("product_category")),
            "status": "answered" if _known(packet.get("product_name") or packet.get("product_category")) else "needs_user_input",
        },
        {
            "step": 3,
            "question": "What is the origin country?",
            "answer": _answer(packet.get("origin_country")),
            "status": "answered" if _known(packet.get("origin_country")) else "needs_user_input",
        },
        {
            "step": 4,
            "question": "What is the destination country?",
            "answer": _answer(packet.get("destination_country")),
            "status": "answered" if _known(packet.get("destination_country")) else "needs_user_input",
        },
        {
            "step": 5,
            "question": "Do you know the HS code?",
            "answer": _answer(packet.get("hs_code_value"), "hs_candidate_research_required"),
            "status": "needs_qualified_review" if _known(packet.get("hs_code_value")) else "needs_research",
        },
        {
            "step": 6,
            "question": "Do you have a buyer/importer?",
            "answer": _answer(packet.get("buyer_name") or packet.get("importer_name")),
            "status": "answered" if _known(packet.get("buyer_name") or packet.get("importer_name")) else "needs_buyer_or_importer_discovery",
        },
        {
            "step": 7,
            "question": "Who is importer of record?",
            "answer": _answer(packet.get("importer_of_record")),
            "status": "answered" if _known(packet.get("importer_of_record")) else "blocked_until_confirmed",
        },
        {
            "step": 8,
            "question": "What Incoterms or delivery responsibility applies?",
            "answer": _answer(packet.get("incoterms_if_known") or packet.get("delivery_responsibility")),
            "status": "answered" if _known(packet.get("incoterms_if_known") or packet.get("delivery_responsibility")) else "blocked_until_confirmed",
        },
        {
            "step": 9,
            "question": "Do you have documents?",
            "answer": "documents_attached" if int(packet.get("evidence_count") or 0) > 0 else "no_documents_or_not_linked",
            "status": "answered" if int(packet.get("evidence_count") or 0) > 0 else "beginner_packet_supported",
        },
        {
            "step": 10,
            "question": "Is the product likely regulated?",
            "answer": "likely_regulated" if regulated else "not_indicated_by_category",
            "status": "needs_regulated_product_review" if regulated else "standard_review_still_required",
        },
        {
            "step": 11,
            "question": "What official sources must be checked?",
            "answer": ", ".join(source_ids[:8]) if source_ids else "official_source_registry_missing",
            "status": "source_routes_ready_reference_only" if source_ids else "blocked_missing_source_routes",
        },
        {
            "step": 12,
            "question": "What is the next safe move?",
            "answer": packet.get("public_summary", {}).get("next_valid_move") or packet.get("next_valid_move") or "collect missing evidence and route to review",
            "status": "next_valid_move_available",
        },
    ]
    for question in questions:
        question["answer_state"] = _decision_answer_state(str(question["status"]))
    blockers = [row for row in questions if str(row["status"]).startswith(("blocked", "needs"))]
    return {
        "status": "decision_tree_ready_claims_blocked",
        "question_count": len(questions),
        "answer_state_policy": [
            "answered",
            "unknown",
            "needs_research",
            "needs_user_confirmation",
            "needs_expert_review",
            "blocked",
        ],
        "questions": questions,
        "blocked_or_review_step_count": len(blockers),
        "next_valid_move": questions[-1]["answer"],
        "proof_boundary": "The decision tree prepares the next safe move; it does not approve import, export, tariff, buyer, supplier, or shipment decisions.",
    }


def build_beginner_flow(packet: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate the no-document starter flow from actual packet fields."""

    minimum_checks = [
        _field_check(packet, "product_name", "product"),
        _field_check(packet, "origin_country", "origin country"),
        _field_check(packet, "destination_country", "destination country"),
        _field_check(packet, "trade_direction", "trade direction"),
        _field_check(packet, "intended_use", "intended use"),
    ]
    buyer_known = _known(packet.get("buyer_name") or packet.get("importer_name"))
    minimum_checks.append(
        {
            "field": "buyer_or_importer_status",
            "label": "buyer or importer status",
            "status": "provided" if buyer_known else "unknown_allowed_for_starter",
            "has_value": buyer_known,
            "value": packet.get("buyer_name") or packet.get("importer_name") or "",
        }
    )
    missing = [row["field"] for row in minimum_checks if row["status"] == "missing"]
    source_routes = [
        _source_summary(source)
        for source in official_sources
        if _country(source.get("jurisdiction")) in {_country(packet.get("origin_country")), _country(packet.get("destination_country")), "Generic", "International"}
    ]
    starter_ready = not missing and bool(source_routes)
    return {
        "status": "starter_flow_executable" if starter_ready else "starter_flow_blocked_missing_inputs",
        "entry_buttons": ["Explore a market", "Prepare buyer packet", "Check my documents"],
        "minimum_input_checks": minimum_checks,
        "missing_required_inputs": missing,
        "source_route_count": len(source_routes),
        "source_routes": source_routes[:10],
        "can_generate_starter_packet": starter_ready,
        "can_generate_buyer_packet": starter_ready,
        "can_send_outreach": False,
        "outreach_policy": "questions_only_no_automatic_sending",
        "starter_outputs": [
            "product assumptions",
            "missing fields",
            "official source routes",
            "buyer/broker/supplier questions",
            "document checklist",
            "responsibility split warning",
            "next safe action",
        ],
        "next_valid_move": (
            "Generate a starter packet with blocked claims and questions."
            if starter_ready
            else "Collect missing starter inputs before packet generation."
        ),
        "proof_boundary": "Starter flow prepares a research packet only; it never proves market demand, source freshness, or trade readiness.",
    }


def _field_provenance(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return field-level provenance for the canonical packet fields."""

    parser_status = "parser_extracted_draft" if packet.get("confirmation_status") == "parser_draft" else "user_input"
    system_fields = {
        "packet_id",
        "organization_id",
        "public_product_name",
        "public_product_promise",
        "responsibility_path",
        "readiness_lanes",
        "buyer_broker_questions",
        "blocked_claims",
        "public_summary",
        "evidence_summary",
    }
    official_fields = {"source_url", "source_type"}
    reviewer_fields = {
        "restricted_party_screening_status",
        "qualified_review_status",
        "broker_review_status",
        "cfia_airs_review_status",
        "import_control_review_status",
        "buyer_validation_status",
    }
    fields = [
        "packet_id",
        "packet_name",
        "product_name",
        "product_category",
        "trade_direction",
        "origin_country",
        "destination_country",
        "intended_use",
        "hs_code_value",
        "exporter_name",
        "importer_name",
        "buyer_name",
        "supplier_name",
        "manufacturer_name",
        "importer_of_record",
        "exporter_of_record",
        "incoterms_if_known",
        "delivery_responsibility",
        "shipping_method",
        "product_documents",
        "commercial_documents",
        "certificates",
        "proof_of_origin",
        "source_url",
        "source_type",
        "restricted_party_screening_status",
        "qualified_review_status",
        "broker_review_status",
        "cfia_airs_review_status",
        "import_control_review_status",
        "buyer_validation_status",
        "confirmation_status",
        "responsibility_path",
        "readiness_lanes",
        "buyer_broker_questions",
        "blocked_claims",
        "public_summary",
        "evidence_summary",
    ]
    provenance: dict[str, dict[str, Any]] = {}
    for field in fields:
        if field in system_fields:
            mode = "system_derived"
        elif field in official_fields:
            mode = "official_source_reference"
        elif field in reviewer_fields:
            mode = "reviewer_verified" if str(packet.get(field) or "") == "reviewed" else "user_input"
        elif field in {"hs_code_value", "importer_name", "buyer_name", "supplier_name", "incoterms_if_known"}:
            mode = parser_status
        else:
            mode = "user_input"
        provenance[field] = {
            "mode": mode,
            "has_value": _known(packet.get(field)),
            "evidence_id": "",
            "source_id": "packet_source" if field in official_fields and _known(packet.get(field)) else "",
            "confirmed_at": packet.get("created_at") if mode in {"user_input", "official_source_reference"} else "",
            "claim_boundary": "Field value is not externally authoritative until confirmed by the relevant evidence or reviewer.",
        }
    return provenance


def build_canonical_packet_contract(packet: dict[str, Any]) -> dict[str, Any]:
    missing_core = [
        field
        for field in ("product_name", "trade_direction", "origin_country", "destination_country")
        if not _known(packet.get(field))
    ]
    decision_missing = [
        field
        for field in ("importer_of_record", "incoterms_if_known")
        if not _known(packet.get(field))
    ]
    evidence_count = int(packet.get("evidence_count") or 0)
    reviewer_ready = not missing_core and not decision_missing and evidence_count > 0
    beta_ready = reviewer_ready and str(packet.get("qualified_review_status") or "") == "reviewed"
    if missing_core:
        stage = "starter"
    elif evidence_count == 0:
        stage = "starter"
    elif decision_missing:
        stage = "document"
    elif beta_ready:
        stage = "beta_ready"
    elif reviewer_ready:
        stage = "reviewer_ready"
    else:
        stage = "decision"
    return {
        "status": "canonical_trade_packet_contract_ready",
        "packet_id": _packet_id(packet),
        "stage": stage,
        "stage_required_answers": {
            "starter": ["product_name", "trade_direction", "origin_country_or_destination_country", "intended_use"],
            "document": ["starter_fields", "evidence_item_or_offline_flag", "source_url_or_file_reference", "confirmation_path"],
            "decision": [
                "document_stage_fields",
                "importer_of_record",
                "incoterms_or_delivery_responsibility",
                "buyer_or_importer_identity_or_broker_ready_rationale",
                "source_freshness",
                "category_review_statuses",
            ],
            "reviewer_ready": [
                "decision_stage_fields",
                "broker_or_expert_review_packet",
                "blocked_claims_report",
                "review_scope",
                "source_snapshot_or_stale_source_blocker",
            ],
            "beta_ready": [
                "reviewer_ready_fields",
                "scoped reviewer findings",
                "metadata_only_private_beta_controls",
                "hosted_beta_or_local_review_boundary",
            ],
        },
        "missing_core_fields": missing_core,
        "missing_decision_fields": decision_missing,
        "provenance_modes": PROVENANCE_MODES,
        "field_provenance": _field_provenance(packet),
        "schema_required_fields": ["packet_id", "product_name", "trade_direction", "stage", "provenance"],
        "entity_model": [
            "TRADE_PACKET contains EVIDENCE_ITEM",
            "TRADE_PACKET produces SCORE_SNAPSHOT",
            "TRADE_PACKET routes_to REVIEW_REQUEST",
            "TRADE_PACKET depends_on SOURCE_REGISTRY_ENTRY",
            "SOURCE_REGISTRY_ENTRY tracks SOURCE_SNAPSHOT and SOURCE_DIFF",
        ],
        "proof_boundary": "The canonical packet contract records what kind of belief each field supports; field presence alone does not prove readiness.",
    }


def build_country_packs(packet: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Build destination/origin/generic country-pack rows from the source registry."""

    origin = _country(packet.get("origin_country"))
    destination = _country(packet.get("destination_country"))
    countries = []
    for country, role in (
        (destination, "destination_import_pack"),
        (origin, "origin_export_pack"),
        ("India", "strategic_next_origin_pack"),
        ("Generic", "generic_fallback_pack"),
    ):
        if country in {row.get("country") for row in countries}:
            continue
        sources = _sources_for_country(official_sources, country)
        required_checks = [
            {
                "id": "import_or_customs_route",
                "required": role in {"destination_import_pack", "strategic_next_origin_pack"},
                "satisfied": _has_source_category(sources, "official_reference", "tariff_or_market_access", "restricted_party_or_control"),
                "next_valid_move": "Add official import/customs route source.",
            },
            {
                "id": "tariff_or_market_access_route",
                "required": role == "destination_import_pack",
                "satisfied": _has_source_category(sources, "tariff_or_market_access"),
                "next_valid_move": "Add official tariff or market-access route source.",
            },
            {
                "id": "regulated_product_route",
                "required": role == "destination_import_pack" and _is_regulated_category(packet),
                "satisfied": _has_source_category(sources, "regulated_product_requirements"),
                "next_valid_move": "Add regulated-product source route such as food/plant/animal/health reference.",
            },
            {
                "id": "restricted_party_or_control_route",
                "required": role == "destination_import_pack",
                "satisfied": _has_source_category(sources, "restricted_party_or_control"),
                "next_valid_move": "Add restricted-party, sanctions, import-control, or permit route source.",
            },
            {
                "id": "market_or_buyer_research_route",
                "required": role == "destination_import_pack",
                "satisfied": _has_source_category(sources, "market_or_buyer_research"),
                "next_valid_move": "Add market data or buyer/importer discovery route source.",
            },
        ]
        required_missing = [row for row in required_checks if row["required"] and not row["satisfied"]]
        pack = {
            "country": country,
            "role": role,
            "status": "country_pack_ready_reference_only" if sources else "country_pack_required",
            "source_count": len(sources),
            "coverage_check_status": "reference_routes_complete_review_required" if not required_missing and sources else "missing_required_source_routes",
            "required_route_checks": required_checks,
            "missing_required_routes": [row["id"] for row in required_missing],
            "import_sources": [_source_summary(source) for source in _sources_matching(sources, "import", "customs", "carm")],
            "export_sources": [_source_summary(source) for source in _sources_matching(sources, "export", "foreign trade", "dgft")],
            "tariff_sources": [_source_summary(source) for source in _sources_matching(sources, "tariff", "market access", "customs tariff")],
            "tax_vat_duty_sources": [_source_summary(source) for source in _sources_matching(sources, "duty", "tax", "carm")],
            "food_plant_animal_sources": [_source_summary(source) for source in _sources_matching(sources, "cfia", "food", "plant", "animal", "airs")],
            "sanctions_sources": [_source_summary(source) for source in _sources_matching(sources, "sanction", "restricted")],
            "trade_data_sources": [_source_summary(source) for source in _sources_matching(sources, "trade data", "ised")],
            "buyer_discovery_sources": [_source_summary(source) for source in _sources_matching(sources, "importer", "buyer", "database")],
            "permitted_automation_methods": ["manual_review", "dated_source_refresh", "hash_snapshot", "terms_or_api_check_before_fetch"],
            "claim_boundaries": [
                "country pack routes users to sources only",
                "country pack does not prove current rules",
                "qualified review and source refresh are required before country-specific claims",
            ],
            "reviewer_requirements": [
                "customs or trade reviewer for tariff/import path",
                "regulated-product reviewer when category requires it",
                "broker or logistics reviewer before shipment decisions",
            ],
        }
        countries.append(pack)
    return {
        "status": "country_packs_ready_with_reference_boundaries",
        "packet_id": _packet_id(packet),
        "origin_country": origin,
        "destination_country": destination,
        "packs": countries,
        "coverage_policy": {
            "full": "country path has product-relevant source routes, freshness checks, and reviewer lane mapping",
            "partial": "country path has source routes but still needs product/category-specific evidence",
            "generic_fallback": "country path is research-only until official source coverage is added",
        },
        "next_valid_move": "Promote country packs only after current official-source refresh and qualified review.",
        "proof_boundary": "Country packs are routing and review-contract surfaces, not country-specific compliance proof.",
    }


def build_market_intelligence(packet: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Build safe market intelligence and data requirements without unsupported demand claims."""

    tdo_sources = [_source_summary(source) for source in _sources_matching(official_sources, "trade data online", "ised")]
    market_access_sources = [_source_summary(source) for source in _sources_matching(official_sources, "market access", "tariff", "macmap")]
    importer_sources = [_source_summary(source) for source in _sources_matching(official_sources, "importers database", "importer discovery")]
    hs_known = _known(packet.get("hs_code_value"))
    category = _category(packet)
    competitor_countries = [
        country
        for country in {
            _country(packet.get("origin_country")),
            "China",
            "Vietnam",
            "Mexico",
            "United States",
            "European Union",
        }
        if country and country != "Generic"
    ]
    data_requirements = [
        "destination import value and quantity by HS/product",
        "3-5 year import trend",
        "top origin countries and unit values",
        "tariff/access comparison for competitor origins",
        "possible importer or buyer lead source",
        "buyer/operator validation notes",
    ]
    buyer_supplier = evaluate_buyer_supplier_evidence(packet)
    components = {
        "hs_or_product_specificity": 15 if hs_known else 5,
        "trade_dataset_route": 15 if tdo_sources else 0,
        "market_access_route": 15 if market_access_sources else 0,
        "buyer_or_importer_route": 10 if importer_sources else 0,
        "buyer_evidence_level": max(0, int(buyer_supplier["buyer"]["current_level"])) * 8,
        "reviewer_verified_market_evidence": 20 if _review_done(packet.get("qualified_review_status")) else 0,
    }
    component_total = min(59, sum(components.values()))
    confidence = (
        "document_backed"
        if int(buyer_supplier["buyer"]["current_level"]) >= 2 and _packet_evidence(packet)
        else "source_backed"
        if tdo_sources or market_access_sources or importer_sources
        else "research_plan"
    )
    return {
        "status": "market_intelligence_ready_as_research_plan",
        "packet_id": _packet_id(packet),
        "hs_product_keyword_search": {
            "status": "hs_code_available_for_research_not_confirmed" if hs_known else "hs_candidate_research_required",
            "hs_code": packet.get("hs_code_value") or "",
            "product_keywords": [packet.get("product_name"), category],
            "qualified_review_required": True,
        },
        "market_size_and_trend": {
            "status": "dataset_required",
            "required_metrics": [
                "total imports by destination country",
                "3-5 year import trend",
                "average unit value",
                "seasonality if available",
                "top origin countries",
            ],
            "source_routes": tdo_sources,
        },
        "import_dependency_signal": {
            "status": "unknown_until_trade_and_production_data_attached",
            "confidence_level": "research_plan",
            "safe_interpretations": [
                "high imports plus growing trend means potential demand worth validating",
                "high imports plus few source countries means possible supplier-diversification research",
                "high imports plus high tariffs means market exists but access cost may be difficult",
                "low imports plus high restrictions means niche, restricted, or unattractive until proven otherwise",
                "data unavailable means research required",
            ],
        },
        "tariff_and_market_access_comparison": {
            "status": "research_required_not_preference_claim",
            "exporter_origin": _country(packet.get("origin_country")),
            "destination": _country(packet.get("destination_country")),
            "competitor_source_countries": competitor_countries,
            "source_routes": market_access_sources,
            "blocked_claims": ["tariff_advantage_confirmed", "preference_qualified", "market_access_approved"],
        },
        "buyer_importer_discovery": {
            "status": "lead_discovery_only",
            "confidence_level": "research_plan",
            "source_routes": importer_sources,
            "claim_boundary": "Importer or buyer sources create possible leads only; buyer validation needs dated contact, terms, demand, and legitimacy evidence.",
            "outputs": ["possible lead source", "buyer questions", "buyer validation tracker", "outreach packet not sent automatically"],
        },
        "decision_support_policy": {
            "confidence_levels": ["no_data", "research_plan", "source_backed", "document_backed", "reviewer_verified"],
            "required_on_every_signal": ["source", "date_or_accessed_at", "limitation", "next_validation_step"],
            "safe_statement_template": "This appears worth deeper research because a named source shows a signal, but buyer demand is not validated until direct buyer evidence exists.",
            "blocked_statement": "This is a profitable market.",
        },
        "market_signal_evaluation": {
            "status": "local_signal_computed_external_evidence_required",
            "score_cap": 59,
            "score": component_total,
            "confidence_level": confidence,
            "components": components,
            "can_claim_market_demand": False,
            "can_claim_profitable_product": False,
            "next_required_evidence": [
                "dated trade dataset row",
                "market-access comparison row",
                "buyer reply or interview note",
                "qualified reviewer note before external market claims",
            ],
        },
        "data_requirements": data_requirements,
        "next_valid_move": "Attach dated trade dataset rows, market-access comparison, and buyer/operator validation before treating the signal as a decision.",
        "proof_boundary": "Market intelligence is a research plan and signal layer; it does not prove demand, margin, buyer validation, or market entry readiness.",
    }


def build_source_monitoring_contract(packet: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for source in official_sources:
        jurisdiction = _country(source.get("jurisdiction"))
        if jurisdiction not in {
            _country(packet.get("origin_country")),
            _country(packet.get("destination_country")),
            "Generic",
            "International",
        }:
            continue
        rows.append(
            {
                **_normalized_source_registry_row(source, packet),
                "refresh_method": "manual_or_permitted_fetch_after_terms_check",
                "freshness_status": "not_checked",
                "parser_contract": "extract date/status/hash and classify change type before packet impact",
                "diff_classifier": [
                    "wording_change",
                    "date_change",
                    "tariff_or_regulatory_change",
                    "source_unavailable",
                ],
                "packet_impact_logic": "critical source changes mark affected packet outputs stale until refreshed evidence and reviewer review are attached",
                "content_hash_required": True,
                "packet_stale_alert": "create stale-source blocker if source content changes or freshness expires",
                "claim_boundary": source.get("claim_boundary") or "Reference only; does not prove current external requirements.",
            }
        )
    return {
        "status": "source_monitoring_contract_ready_no_live_fetch_claim",
        "packet_id": _packet_id(packet),
        "registry_required_fields": [
            "source_id",
            "jurisdiction",
            "source_type",
            "canonical_url",
            "fetch_mode",
            "cadence",
            "robots_status",
            "terms_status",
            "auth_required",
            "parser_type",
            "content_hash",
            "diff_strategy",
            "claim_boundary",
            "packet_tags",
        ],
        "fetch_policy": [
            "register first, fetch later",
            "prefer official structured endpoints over HTML parsing",
            "store only the minimum snapshot needed for diffing and audit",
            "treat robots and terms as required metadata fields",
            "route every material source change back into packet review",
        ],
        "fetch_methods": [
            {"method": "structured_download", "best_use": "official machine-readable feeds or exports", "recommendation": "preferred where allowed"},
            {"method": "official_verification_service", "best_use": "AIRS/verification workflows", "recommendation": "reviewer or verification lanes only"},
            {"method": "html_snapshot", "best_use": "orientation and change watch", "recommendation": "use only with terms/robots approval"},
            {"method": "metadata_only", "best_use": "registered source before approval", "recommendation": "default safe mode"},
        ],
        "source_count": len(rows),
        "sources": rows,
        "source_changed_flow": [
            "official/reference source changes or expires",
            "content hash or dated manual check changes",
            "affected packets become stale",
            "user sees recheck required",
            "old output remains blocked until refreshed evidence and review are attached",
        ],
        "blocked_claims": ["current_law_confirmed", "rules_current", "tariff_current", "permit_status_confirmed"],
        "next_valid_move": "Run dated source refresh with permitted method and record hash/change classification.",
        "proof_boundary": "The source monitor contract describes local monitoring behavior; it does not prove live official-source freshness.",
    }


def build_packet_outputs(packet: dict[str, Any]) -> dict[str, Any]:
    missing = packet.get("evidence_summary", {}).get("missing_items", [])
    questions = packet.get("buyer_broker_questions", [])
    return {
        "status": "commercial_packet_outputs_ready_claims_blocked",
        "packet_id": _packet_id(packet),
        "beginner_output": {
            "sections": [
                "starter checklist",
                "market research prompt",
                "product/category risk level",
                "country source checklist",
                "documents to collect",
                "buyer/supplier questions",
                "broker/expert questions",
                "next valid move",
            ],
            "ready": True,
        },
        "exporter_output": {
            "sections": [
                "export-to-destination readiness packet",
                "buyer-ready packet",
                "destination import responsibility map",
                "competitor/source-country comparison research",
                "market access/tariff research checklist",
                "documents required from exporter",
                "questions for buyer and broker",
            ],
            "ready": True,
        },
        "importer_output": {
            "sections": [
                "import readiness packet",
                "supplier document request list",
                "official source checklist",
                "importer-of-record responsibility check",
                "regulated product flags",
                "broker packet",
                "missing evidence report",
            ],
            "ready": True,
        },
        "operator_expert_output": {
            "sections": [
                "evidence ledger",
                "blocker groups",
                "review scope",
                "source freshness status",
                "claims allowed or blocked",
                "reviewer response template",
            ],
            "ready": True,
        },
        "supplier_document_request": {
            "status": "ready_to_prepare_not_sent",
            "requested_items": [
                "product specs",
                "commercial invoice or proforma",
                "packing list",
                "certificates",
                "proof of origin",
                "regulated-product documents",
                "shipping and handling details",
            ],
        },
        "question_sets": {
            "buyer_or_importer": questions,
            "broker_or_expert": questions,
            "supplier": [
                "Can you provide product specifications and intended-use details?",
                "Can you provide invoice/proforma, packing list, certificates, and proof of origin?",
                "Who is responsible for export documents, shipment booking, insurance, and origin proof?",
                "Can you provide dated evidence for permits, regulated-product documents, or tests if applicable?",
            ],
        },
        "missing_evidence_items": missing,
        "blocked_claims": packet.get("blocked_claims", []),
        "next_valid_move": packet.get("public_summary", {}).get("next_valid_move") or "Collect missing evidence and route to review.",
        "proof_boundary": "Packet outputs prepare commercial review work only; no report is sent externally and no buyer/supplier/broker approval is implied.",
    }


def evaluate_buyer_supplier_evidence(packet: dict[str, Any]) -> dict[str, Any]:
    """Compute buyer and supplier evidence levels from packet and evidence rows."""

    rows = _packet_evidence(packet)
    non_reference_rows = [
        row
        for row in rows
        if str(row.get("evidence_type") or "").lower() not in {"official_reference", "source_url", "reference"}
    ]
    direct_party_blob = _text_blob(
        packet.get("buyer_name"),
        packet.get("importer_name"),
        packet.get("supplier_name"),
        packet.get("manufacturer_name"),
        *non_reference_rows,
    )
    document_blob = _text_blob(
        packet.get("product_documents"),
        packet.get("commercial_documents"),
        packet.get("certificates"),
        packet.get("proof_of_origin"),
        packet.get("product_specs"),
        packet.get("commercial_invoice"),
        packet.get("packing_list"),
        packet.get("contract_po"),
        *non_reference_rows,
    )
    if "placeholder" in document_blob:
        document_blob = ""
    buyer_labels: set[str] = set()
    supplier_labels: set[str] = set()

    if _known(packet.get("buyer_name") or packet.get("importer_name")) or any(
        word in direct_party_blob for word in ("buyer lead", "importer lead", "importer discovery")
    ):
        buyer_labels.add("lead_found")
    if any(word in direct_party_blob for word in ("contact attempted", "outreach", "sent email", "called buyer", "buyer call")):
        buyer_labels.add("contact_attempted")
    if any(word in direct_party_blob for word in ("buyer replied", "email reply", "reply received", "received reply", "dated reply")):
        buyer_labels.add("reply_received")
    if any(word in direct_party_blob for word in ("meeting", "call notes", "meeting notes", "buyer interview")):
        buyer_labels.add("meeting_completed")
    if any(word in direct_party_blob for word in ("loi", "letter of intent", "intent letter")):
        buyer_labels.add("loi_received")
    if any(word in direct_party_blob for word in ("purchase order", "paid order", "po attached", "payment received")):
        buyer_labels.add("po_or_paid_order")
    if _review_done(packet.get("buyer_validation_status")) and buyer_labels:
        buyer_labels.add("meeting_completed")

    if _known(packet.get("supplier_name") or packet.get("manufacturer_name")):
        supplier_labels.add("supplier_named")
    if any(word in document_blob for word in ("business registration", "company registration", "registration certificate", "corporate registry")):
        supplier_labels.add("business_registration_attached")
    if any(word in document_blob for word in ("export license", "export registration", "iec", "dgft", "export ability", "export permit")):
        supplier_labels.add("export_ability_evidence_attached")
    if any(word in document_blob for word in ("product spec", "specification", "product document", "technical data sheet", "invoice", "packing list")):
        supplier_labels.add("product_docs_attached")
    if any(word in document_blob for word in ("inspection", "certificate", "lab report", "health certificate", "quality certificate")):
        supplier_labels.add("inspection_or_certificate_attached")
    if any(word in document_blob for word in ("prior shipment", "bill of lading", "shipment record", "export history")):
        supplier_labels.add("prior_shipment_evidence_attached")

    buyer_level = _best_level(BUYER_EVIDENCE_LADDER, buyer_labels)
    supplier_level = _best_level(SUPPLIER_EVIDENCE_LADDER, supplier_labels)
    buyer_missing = int(buyer_level["level"]) < 2
    supplier_missing = int(supplier_level["level"]) < 3
    return {
        "status": "buyer_supplier_evidence_evaluated_claims_blocked",
        "buyer": {
            "current_level": buyer_level["level"],
            "current_label": buyer_level["label"],
            "allowed_language": buyer_level["allowed_language"],
            "evidence_labels_found": sorted(buyer_labels),
            "minimum_private_beta_level": 2,
            "minimum_before_demand_claim": 4,
            "minimum_before_commercial_commitment": 5,
            "can_say_buyer_validated": False,
            "next_valid_move": (
                "Collect dated buyer reply, call notes, LOI, PO, or paid-order evidence."
                if buyer_missing
                else "Route buyer evidence to scoped review; keep validation claims blocked."
            ),
        },
        "supplier": {
            "current_level": supplier_level["level"],
            "current_label": supplier_level["label"],
            "allowed_language": supplier_level["allowed_language"],
            "evidence_labels_found": sorted(supplier_labels),
            "minimum_private_beta_level": 1,
            "minimum_before_supplier_confidence_claim": 4,
            "minimum_before_recommendation_claim": 5,
            "can_say_supplier_verified": False,
            "next_valid_move": (
                "Collect registration, export ability, product documents, inspection/certificate, and prior-shipment evidence."
                if supplier_missing
                else "Route supplier evidence to scoped review; keep verification/recommendation claims blocked."
            ),
        },
        "blocked_language": ["buyer_validated", "supplier_verified", "supplier_recommended", "market_demand_proven"],
        "mvp_outreach_policy": "questions_only_no_automatic_sending",
        "external_claims_opened": False,
        "proof_boundary": "The product records evidence levels; it does not validate buyers or verify suppliers.",
    }


def evaluate_source_freshness(packet: dict[str, Any], source_monitor: dict[str, Any]) -> dict[str, Any]:
    """Evaluate source freshness from attached evidence and registered sources."""

    rows = _packet_evidence(packet)
    source_rows = []
    stale_count = 0
    reviewed_count = 0
    refreshed_count = 0
    for row in rows:
        freshness = _status_value(row.get("freshness_status"))
        reviewed = _review_done(row.get("human_review_status"))
        last_verified = row.get("last_verified_at") or ""
        content_hash = row.get("content_hash") or row.get("hash") or ""
        is_fresh = freshness in {"fresh", "source_fresh_reference_only", "fresh_reference_only"} and _known(last_verified)
        is_stale = freshness in {"stale", "expired", "needs_current_refresh_before_claims", "missing", ""}
        stale_count += 1 if is_stale else 0
        refreshed_count += 1 if is_fresh else 0
        reviewed_count += 1 if reviewed else 0
        source_rows.append(
            {
                "evidence_id": row.get("evidence_id"),
                "source_url": row.get("source_url") or row.get("url") or "",
                "freshness_status": freshness or "missing",
                "last_verified_at": last_verified,
                "content_hash_present": _known(content_hash),
                "human_review_status": row.get("human_review_status") or "not_reviewed",
                "claim_boundary": row.get("claim_boundary") or "Reference only until refreshed and reviewed.",
                "packet_impact": "blocks_current_source_claims" if is_stale or not reviewed else "reference_fresh_for_internal_review_only",
            }
        )
    registered_count = int(source_monitor.get("source_count") or 0)
    ready = bool(source_rows) and stale_count == 0 and reviewed_count == len(source_rows)
    return {
        "status": "source_freshness_ready_for_internal_review" if ready else "source_freshness_blocked_until_refresh_and_review",
        "attached_source_count": len(source_rows),
        "registered_source_count": registered_count,
        "fresh_or_refreshed_count": refreshed_count,
        "stale_or_unproven_count": stale_count,
        "reviewed_source_count": reviewed_count,
        "source_rows": source_rows,
        "can_claim_current_sources": False,
        "can_use_for_internal_review": ready,
        "next_valid_move": (
            "Use refreshed reviewed sources for internal review only; external claims stay blocked."
            if ready
            else "Run dated source refresh, store hash/status, and collect qualified review before current-source claims."
        ),
        "external_claims_opened": False,
        "proof_boundary": "Freshness evaluation is local and packet-specific; it does not prove current law, tariff, permit, or compliance status.",
    }


def evaluate_business_gate_decision(
    packet: dict[str, Any],
    *,
    beginner_flow: dict[str, Any],
    canonical_packet: dict[str, Any],
    decision_tree: dict[str, Any],
    buyer_supplier: dict[str, Any],
    source_freshness: dict[str, Any],
) -> dict[str, Any]:
    """Compute the product's local business decision without opening external gates."""

    blocker_count = int(packet.get("blocker_count") or 0)
    hard_blocks = [
        "open_packet_blockers" if blocker_count else "",
        "starter_inputs_missing" if not beginner_flow.get("can_generate_starter_packet") else "",
        "source_freshness_missing" if source_freshness.get("stale_or_unproven_count") else "",
        "buyer_evidence_missing" if int(buyer_supplier["buyer"]["current_level"]) < 2 else "",
        "supplier_evidence_insufficient" if int(buyer_supplier["supplier"]["current_level"]) < 1 else "",
        "reviewer_verification_missing" if canonical_packet.get("stage") != "beta_ready" else "",
    ]
    hard_blocks = [block for block in hard_blocks if block]
    can_prepare_packet = bool(beginner_flow.get("can_generate_starter_packet"))
    can_prepare_reviewer_packet = can_prepare_packet and canonical_packet.get("stage") in {"document", "decision", "reviewer_ready", "beta_ready"}
    return {
        "status": "business_logic_executable_external_gates_blocked",
        "packet_id": _packet_id(packet),
        "local_actions_allowed": {
            "generate_starter_packet": can_prepare_packet,
            "generate_missing_evidence_report": True,
            "generate_buyer_packet_draft": can_prepare_packet,
            "generate_broker_or_expert_packet": can_prepare_reviewer_packet,
            "refresh_sources_record": True,
            "send_outreach": False,
            "take_payment": False,
            "approve_trade_action": False,
        },
        "external_actions_blocked": [
            "customs_or_tariff_advice",
            "cfia_or_regulated_product_clearance",
            "buyer_validation_claim",
            "supplier_verification_or_recommendation",
            "shipment_or_export_ready_claim",
            "live_payment_checkout",
            "public_launch_approval",
        ],
        "hard_blocks": hard_blocks,
        "decision_tree_blocked_or_review_steps": decision_tree.get("blocked_or_review_step_count", 0),
        "customer_visible_decision": "draft_packet_allowed_external_claims_blocked" if can_prepare_packet else "collect_minimum_inputs_first",
        "next_valid_move": packet.get("next_valid_move") or decision_tree.get("next_valid_move"),
        "external_claims_opened": False,
    }


def _score(color: str, value: int, status: str, meaning: str, next_valid_move: str, cap_reason: str) -> dict[str, Any]:
    return {
        "value": value,
        "color": color,
        "status": status,
        "meaning": meaning,
        "cap_reason": cap_reason,
        "next_valid_move": next_valid_move,
        "external_claims_opened": False,
    }


def build_business_scores(
    packet: dict[str, Any],
    market: dict[str, Any],
    source_monitor: dict[str, Any],
    buyer_supplier: dict[str, Any],
    source_freshness: dict[str, Any],
) -> dict[str, Any]:
    evidence = packet.get("evidence_summary", {})
    missing = int(evidence.get("missing") or 0)
    attached = int(evidence.get("attached") or packet.get("evidence_count") or 0)
    stale = int(source_freshness.get("stale_or_unproven_count") or evidence.get("stale") or 0)
    blocker_count = int(packet.get("blocker_count") or 0)
    responsibility = packet.get("responsibility_path", {})
    responsibility_level = str(responsibility.get("responsibility_level") or "unknown")
    evidence_value = int(round((attached / max(attached + missing, 1)) * 100))
    source_value = 20 if stale else min(80, 30 + source_monitor.get("source_count", 0) * 5)
    responsibility_value = 30 if responsibility_level == "unknown" else 60 if "high" in responsibility_level else 75
    safety_value = 20 if blocker_count else 70
    market_eval = market.get("market_signal_evaluation", {})
    market_value = int(market_eval.get("score") or 0)
    buyer_level = int(buyer_supplier["buyer"]["current_level"])
    supplier_level = int(buyer_supplier["supplier"]["current_level"])
    buyer_supplier_value = min(59, max(0, buyer_level) * 9 + max(0, supplier_level) * 7)
    scores = {
        "market_signal_score": _score(
            "grey" if market_value < 40 else "yellow",
            market_value,
            "research_required",
            f"Local market signal score is {market_value}/100 before external demand, dataset, and buyer proof.",
            market["next_valid_move"],
            "Capped at 59 because official trade dataset rows, access comparison, and direct buyer evidence are not all attached and reviewed.",
        ),
        "evidence_completeness_score": _score(
            "red" if missing else "yellow",
            evidence_value,
            "blocked_missing_evidence" if missing else "internal_review_ready_external_claims_blocked",
            f"{attached} evidence rows attached and {missing} required items missing.",
            "Attach missing product, commercial, origin, review, buyer, and source evidence.",
            "Capped because the packet still has missing required evidence or review fields.",
        ),
        "source_freshness_score": _score(
            "red" if stale else "yellow",
            source_value,
            "blocked_stale_source" if stale else "reference_sources_routed_review_required",
            "Official/reference sources are routed, but current-source proof and qualified review are still required.",
            "Run dated source refresh and record hash/change classification.",
            "Capped because routed official sources are not the same as current, reviewed source proof.",
        ),
        "buyer_supplier_evidence_score": _score(
            "red" if buyer_level < 2 or supplier_level < 1 else "yellow",
            buyer_supplier_value,
            "buyer_supplier_evidence_missing" if buyer_level < 2 or supplier_level < 1 else "buyer_supplier_evidence_collected_review_required",
            f"Buyer level {buyer_level} and supplier level {supplier_level} are recorded without validation/verification claims.",
            "Collect dated buyer interaction and supplier evidence, then route to review.",
            "Capped because evidence levels do not equal buyer validation, supplier verification, or market demand proof.",
        ),
        "responsibility_clarity_score": _score(
            "red" if responsibility_level == "unknown" else "yellow",
            responsibility_value,
            "blocked_responsibility_unknown" if responsibility_level == "unknown" else "responsibility_path_identified_review_required",
            responsibility.get("guidance") or "Importer of record and Incoterms must be confirmed.",
            "Confirm importer of record, Incoterms, buyer/importer role, and broker review path.",
            "Capped because importer of record, Incoterms, or role split are not confirmed enough for external decisions.",
        ),
        "decision_safety_score": _score(
            "red" if blocker_count else "yellow",
            safety_value,
            "blocked_external_decision_unsafe" if blocker_count else "internal_review_only_external_claims_blocked",
            f"{blocker_count} blocker rows keep external decisions closed.",
            packet.get("public_summary", {}).get("next_valid_move") or "Proceed only to internal review.",
            "Capped because open blocker rows and external gates prevent approval-style decisions.",
        ),
    }
    return {
        "status": "five_business_scores_ready_no_approval_claims",
        "score_count": len(scores),
        "scores": scores,
        "formula_contract": {
            "market_signal_score": "100*(0.25*demand_trend + 0.20*market_size + 0.20*import_dependency + 0.15*competitor_gap + 0.10*lead_signal + 0.10*access_factor); cap at 59 until official datasets are attached",
            "evidence_completeness_score": "weighted completion of identity, route, parties, docs, source evidence, and review statuses; cap at 49 if core fields or evidence are missing",
            "source_freshness_score": "weighted by source age, cadence, and diff review; zero if a critical source changed and review is pending",
            "buyer_supplier_evidence_score": "weighted buyer ladder and supplier evidence ladder; cap at 59 until dated direct buyer evidence, supplier evidence, and reviewer checks exist",
            "responsibility_clarity_score": "weighted by importer of record, Incoterms, buyer/importer identity, role split, and broker path; cap at 39 if importer of record or Incoterms are unknown",
            "decision_safety_score": "minimum of blocker gate state and weighted composite of the other scores; cap at 39 while P0 shipment/compliance blockers are open",
        },
        "threshold_contract": {
            "0-39": "unknown_or_blocked",
            "40-59": "research_required",
            "60-79": "internal_review_ready",
            "80-100": "expert_review_ready_external_claims_still_scoped",
        },
        "score_policy": {
            "green": "internally usable only when evidence and review are sufficient for the local scope",
            "yellow": "research or qualified review needed",
            "red": "blocked",
            "grey": "unknown or no data",
            "forbidden_labels": [
                "approved",
                "compliant",
                "ready_to_ship",
                "tariff_confirmed",
                "buyer_validated",
                "supplier_verified",
            ],
        },
    }


def build_reviewer_signoff_framework() -> dict[str, Any]:
    lanes = [
        ("UX/Product", True, True, "users understand flows, blockers, outputs, and non-approved claims"),
        ("Security/Public Upload", True, True, "upload handling, auth, storage isolation, deletion, and audit"),
        ("Privacy/Legal", True, True, "notices, consent, retention, deletion, data handling, and claim boundaries"),
        ("AI Safety/Prompt Injection", True, True, "model routing, redaction, manual fallback, and prompt-injection controls"),
        ("DevOps/Production", True, True, "staging proof, secrets, storage, monitoring, backup, and rollback"),
        ("Trade-Boundary/Customs Language", False, True, "reference-only customs, tariff, CFIA, sanctions, and broker-language boundaries"),
        ("Freight/Logistics", False, True, "shipment, forwarder, route, cost, and readiness-language boundaries"),
        ("Report Language", False, True, "customer-facing report wording and uncertainty labels"),
        ("Billing/Payment", False, True, "checkout, webhooks, support, refunds, tax/account treatment"),
    ]
    return {
        "status": "reviewer_signoff_framework_ready_no_approval_substitution",
        "lanes": [
            {
                "reviewer_lane": lane,
                "blocks_hosted_beta": beta,
                "blocks_public_launch": launch,
                "must_approve": scope,
                "ai_can_prepare_packet": True,
                "ai_can_approve": False,
            }
            for lane, beta, launch, scope in lanes
        ],
        "standard_decision_template": {
            "review_record_type": "external_review_decision_record",
            "reviewer_name": "",
            "reviewer_role": "",
            "qualification_basis": "",
            "scope_reviewed": "",
            "artifacts_reviewed": [],
            "commit_sha": "",
            "package_sha256": "",
            "top_findings": [],
            "claims_product_must_not_make": [],
            "decision": "looks_ok_for_my_area|not_ready_yet|need_more_evidence|not_my_area|send_to_different_reviewer",
            "signed_at": "",
        },
        "customs_trade_template": {
            "review_record_type": "customs_trade_review_record",
            "reviewer": "",
            "credential": "",
            "product_category": "",
            "hs_code_candidate": "",
            "origin": "",
            "destination": "",
            "official_sources_used": [],
            "assumptions": [],
            "approved_reference_only_language": [],
            "blocked_claims": [],
            "conditions_before_stronger_claims": [],
            "decision": "reference_only_ok|not_ready|needs_more_evidence",
            "signed_at": "",
        },
        "final_rule": "no reviewer lane, no claim lane",
    }


def build_hosted_beta_control_contract() -> dict[str, Any]:
    return {
        "status": "hosted_beta_controls_blocked_until_real_platform_proof",
        "controls": [
            {"area": "authentication", "minimum": "no demo users; real identity provider or hardened passwordless auth"},
            {"area": "session_security", "minimum": "secure cookies, CSRF, short expiry, organization isolation"},
            {"area": "upload_handling", "minimum": "extension/MIME allowlist, malware scan, storage isolation, no direct serving, rate limits"},
            {"area": "data_governance", "minimum": "privacy notice, AI-use notice, retention/deletion controls, breach process"},
            {"area": "ai_routing", "minimum": "no-AI/manual mode, metadata-only mode, redaction preview, provider inventory"},
            {"area": "auditability", "minimum": "upload, review, export, and deletion logs"},
            {"area": "recovery", "minimum": "backups and restore test"},
            {"area": "observability", "minimum": "health checks, error logging, security events"},
        ],
        "storage_recommendation": "managed Postgres plus object storage for hosted beta; local SQLite and filesystem remain dev/local only",
        "payment_policy": "payments remain downstream; live checkout stays disabled until scope, support, refund, tax, webhook, and claim-boundary reviews pass",
    }


def build_business_identity_lock() -> dict[str, Any]:
    return {
        "status": "business_identity_locked_local_claims_blocked",
        "public_product_name": "Trade Readiness Copilot",
        "internal_engine_name": "Importer Source Readiness Copilot",
        "first_wedge": "foreign_exporters_preparing_to_sell_into_canada",
        "first_category_scope": "food_seafood_agri_plus_general_goods",
        "first_persona": "beginner_to_intermediate_exporter",
        "secondary_personas": ["canadian_importer", "internal_reviewer", "broker_or_expert"],
        "one_sentence_promise": (
            "Trade Readiness Copilot helps exporters prepare evidence-backed buyer and broker packets for selling into Canada, "
            "showing missing documents, official-source checks, blocked claims, and next safe actions."
        ),
        "forbidden_claims": [
            "approved",
            "compliant",
            "ready_to_ship",
            "tariff_confirmed",
            "buyer_validated",
            "supplier_verified",
        ],
    }


def build_beginner_flow_contract() -> dict[str, Any]:
    return {
        "status": "no_document_beginner_flow_contract_ready",
        "default_first_screen": "exporter_quick_start",
        "entry_buttons": ["Explore a market", "Prepare buyer packet", "Check my documents"],
        "minimum_inputs": [
            "product",
            "origin_country",
            "destination_country",
            "trade_direction",
            "intended_use",
            "buyer_or_importer_status",
        ],
        "starter_packet_outputs": [
            "product assumptions",
            "missing fields",
            "official source routes",
            "first buyer/broker/supplier questions",
            "document checklist",
            "responsibility split warning",
            "next safe action",
        ],
        "beginner_language": "You are at the research stage; the packet prepares questions and evidence before buyer, broker, or reviewer action.",
        "proof_boundary": "No-document flow can prepare a starter packet, but it cannot prove market demand, source freshness, or trade readiness.",
    }


def build_buyer_supplier_validation_contract() -> dict[str, Any]:
    return {
        "status": "buyer_supplier_validation_ladders_ready_claims_blocked",
        "buyer_evidence_ladder": BUYER_EVIDENCE_LADDER,
        "supplier_evidence_ladder": SUPPLIER_EVIDENCE_LADDER,
        "blocked_language": ["buyer_validated", "supplier_verified"],
        "mvp_outreach_policy": "questions_only_no_automatic_sending",
        "proof_boundary": "The product records evidence levels; it does not validate buyers or verify suppliers.",
    }


def build_metadata_only_beta_contract() -> dict[str, Any]:
    return {
        "status": "metadata_only_beta_contract_ready_real_users_required",
        "phase_policy": "private beta phase 1 uses metadata-only packets plus optional sample or redacted documents",
        "target_user_count": "5-10 exporter or intermediary users",
        "required_observations": [
            "who the product helps most",
            "which output matters most",
            "which fields users can answer",
            "which fields confuse users",
            "whether users would use, share, or pay for the packet",
            "whether users understand blocked versus approved language",
        ],
        "external_evidence_required": True,
        "proof_boundary": "This contract prepares beta measurement; it does not create real beta outcomes.",
    }


def build_real_file_beta_contract() -> dict[str, Any]:
    return {
        "status": "controlled_real_file_beta_blocked_until_hosted_review",
        "starting_scope": "3-5 trusted users only after hosted upload/privacy/security controls pass",
        "required_controls": [
            "explicit upload consent",
            "AI-use consent before model processing",
            "redaction preview",
            "manual/no-AI option",
            "visible retention period",
            "tested deletion path",
            "upload audit trail",
        ],
        "proof_boundary": "Real-file beta requires hosted security, privacy, upload, and AI-safety review before use with sensitive documents.",
    }


def build_payment_pricing_contract() -> dict[str, Any]:
    return {
        "status": "payment_pricing_contract_ready_live_checkout_disabled",
        "recommended_model": "free starter plus paid prepared packet or review-preparation package",
        "paid_scope": "prepared trade readiness packet and evidence organization",
        "forbidden_paid_scope": ["customs approval", "tariff confirmation", "shipment readiness"],
        "required_before_live_checkout": [
            "pricing decision",
            "refund/support policy",
            "tax/account review",
            "payment processor setup",
            "webhook handling review",
            "billing/payment reviewer signoff",
            "claim-boundary wording review",
        ],
        "live_checkout_enabled": False,
    }


def build_public_launch_contract() -> dict[str, Any]:
    return {
        "status": "public_launch_contract_ready_launch_blocked_until_real_approval",
        "safe_initial_public_scope": [
            "landing page",
            "quick check",
            "metadata-only starter packet",
            "sample packet",
            "waitlist or demo booking",
            "safe educational source routing",
        ],
        "blocked_public_scope": [
            "unrestricted real file uploads",
            "live payments",
            "automated buyer outreach",
            "supplier verification claims",
            "tariff/CFIA/customs confirmation",
            "shipment approval language",
        ],
        "required_before_public_launch": [
            "locked business logic",
            "private beta outcomes",
            "hosted controls proof",
            "expert reviews recorded",
            "public claims reviewed",
            "named launch owner approval",
        ],
        "public_launch_ready": False,
    }


def build_completion_phase_contracts() -> dict[str, Any]:
    phases = [
        {
            "phase": 0,
            "name": "Business identity lock",
            "status": "implemented_executable_identity_rules_claims_blocked",
            "main_output": "wedge_persona_name_promise",
            "artifact": "business_identity_lock",
            "exit_criteria_status": "met_locally",
        },
        {
            "phase": 1,
            "name": "Business logic runtime",
            "status": "implemented_executable_packet_rules_claims_blocked",
            "main_output": "decision_tree_stages_scores_provenance_gate_decision",
            "artifact": "packet_rows",
            "exit_criteria_status": "met_locally",
        },
        {
            "phase": 2,
            "name": "No-document beginner flow",
            "status": "implemented_executable_starter_flow_claims_blocked",
            "main_output": "starter_packet_input_checks_and_outputs",
            "artifact": "packet_rows[].beginner_flow",
            "exit_criteria_status": "met_locally",
        },
        {
            "phase": 3,
            "name": "Market intelligence",
            "status": "implemented_local_signal_scoring_real_datasets_required",
            "main_output": "bounded_market_signal_components",
            "artifact": "packet_rows[].market_intelligence",
            "exit_criteria_status": "met_locally_data_evidence_required_for_stronger_claims",
        },
        {
            "phase": 4,
            "name": "Country packs",
            "status": "implemented_executable_country_route_checks_reference_boundaries",
            "main_output": "canada_india_vietnam_generic_country_pack_route_checks",
            "artifact": "packet_rows[].country_packs",
            "exit_criteria_status": "met_locally_reference_only",
        },
        {
            "phase": 5,
            "name": "Source monitoring",
            "status": "implemented_executable_source_freshness_no_live_claim",
            "main_output": "freshness_status_diff_classifier_packet_impact_logic_and_evidence_eval",
            "artifact": "packet_rows[].source_freshness",
            "exit_criteria_status": "met_locally_live_refresh_evidence_required",
        },
        {
            "phase": 6,
            "name": "Packet outputs",
            "status": "implemented_executable_packet_outputs_claims_blocked",
            "main_output": "trade_readiness_packet_views",
            "artifact": "packet_rows[].packet_outputs",
            "exit_criteria_status": "met_locally",
        },
        {
            "phase": 7,
            "name": "Human review gates",
            "status": "local_review_lane_contract_ready_external_evidence_required",
            "main_output": "reviewer_signoff_records",
            "artifact": "reviewer_signoff_framework",
            "exit_criteria_status": "blocked_until_real_reviewer_records",
        },
        {
            "phase": 8,
            "name": "Metadata-only beta",
            "status": "metadata_only_beta_contract_ready_real_user_evidence_required",
            "main_output": "real_user_workflow_evidence",
            "artifact": "metadata_only_beta_contract",
            "exit_criteria_status": "blocked_until_real_user_outcomes",
        },
        {
            "phase": 9,
            "name": "Hosted beta infrastructure",
            "status": "hosted_control_contract_ready_external_platform_proof_required",
            "main_output": "auth_db_storage_logs_ai_controls",
            "artifact": "hosted_beta_control_contract",
            "exit_criteria_status": "blocked_until_hosted_proof",
        },
        {
            "phase": 10,
            "name": "Controlled real-file beta",
            "status": "real_file_beta_contract_ready_platform_and_consent_proof_required",
            "main_output": "supervised_document_workflow",
            "artifact": "real_file_beta_contract",
            "exit_criteria_status": "blocked_until_real_file_beta_controls_pass",
        },
        {
            "phase": 11,
            "name": "Buyer/supplier evidence",
            "status": "implemented_executable_evidence_ladders_real_evidence_required",
            "main_output": "buyer_supplier_evidence_levels_and_blocked_language",
            "artifact": "packet_rows[].buyer_supplier_evidence",
            "exit_criteria_status": "met_locally_blocked_until_real_buyer_supplier_evidence_for_claims",
        },
        {
            "phase": 12,
            "name": "Payments",
            "status": "local_contract_complete_live_checkout_disabled",
            "main_output": "paid_packet_scope_and_payment_gates",
            "artifact": "payment_pricing_contract",
            "exit_criteria_status": "blocked_until_payment_review_and_live_setup",
        },
        {
            "phase": 13,
            "name": "Public launch",
            "status": "launch_contract_ready_public_launch_blocked",
            "main_output": "narrow_reviewed_launch_scope",
            "artifact": "public_launch_contract",
            "exit_criteria_status": "blocked_until_named_owner_go_no_go",
        },
    ]
    externally_blocked = [phase for phase in phases if "blocked" in str(phase["exit_criteria_status"]) or "required" in phase["status"]]
    locally_met = [phase for phase in phases if str(phase["exit_criteria_status"]).startswith("met_locally")]
    return {
        "status": "local_business_logic_implemented_external_gates_preserved",
        "phase_ids": BUSINESS_COMPLETION_PHASE_IDS,
        "phase_count": len(phases),
        "local_executable_phase_count": len(locally_met),
        "local_contract_ready_phase_count": len(phases),
        "externally_blocked_phase_count": len(externally_blocked),
        "controlled_private_beta_candidate_local": True,
        "controlled_private_beta_ready_with_real_users": False,
        "public_launch_ready": False,
        "phases": phases,
        "completion_definition_controlled_private_beta": (
            "A foreign exporter selling into Canada can enter product and country details, with or without documents, and receive a packet with market research requirements, missing evidence, official source routes, responsibility gaps, blocked claims, buyer/broker/supplier questions, and next safe move."
        ),
        "completion_definition_public_launch": (
            "Public launch requires locked logic, beta outcomes, hosted controls, expert reviews, reviewed public claims, and named launch-owner approval."
        ),
    }


def build_business_phase_surfaces(completion_contracts: dict[str, Any]) -> list[dict[str, Any]]:
    contracts_by_phase = {
        int(row["phase"]): row
        for row in completion_contracts.get("phases", [])
        if isinstance(row, dict) and "phase" in row
    }
    surface_rows = [
        {
            "phase": 1,
            "artifact_section": "packet_rows[].decision_tree + packet_rows[].business_scores + packet_rows[].business_gate_decision",
            "local_completion_surface": "12 decision questions, canonical packet stage, six scores, provenance, blocked claims, and allowed/blocked local actions",
        },
        {
            "phase": 2,
            "artifact_section": "packet_rows[].beginner_flow",
            "local_completion_surface": "starter input checks, source-route prompts, starter packet output, buyer packet draft, and no-send outreach policy",
        },
        {
            "phase": 3,
            "artifact_section": "packet_rows[].market_intelligence",
            "local_completion_surface": "bounded market signal, importer/buyer discovery routes, tariff/market-access comparison routes, and demand-claim blocks",
        },
        {
            "phase": 4,
            "artifact_section": "packet_rows[].country_packs",
            "local_completion_surface": "Canada, origin-country, India strategic, and Generic fallback route checks with country-specific claim gates",
        },
        {
            "phase": 5,
            "artifact_section": "packet_rows[].source_monitoring_contract + packet_rows[].source_freshness",
            "local_completion_surface": "registered source rows, refresh cadence, stale-source impact rules, evidence freshness evaluation, and current-source claim blocks",
        },
        {
            "phase": 6,
            "artifact_section": "packet_rows[].packet_outputs",
            "local_completion_surface": "starter, exporter, importer, operator, supplier, buyer/broker, expert, missing-evidence, and blocked-claim outputs",
        },
        {
            "phase": 7,
            "artifact_section": "reviewer_signoff_framework",
            "local_completion_surface": "review lanes, scope templates, decision values, required evidence fields, and no-reviewer-no-claim rule",
        },
        {
            "phase": 8,
            "artifact_section": "metadata_only_beta_contract",
            "local_completion_surface": "metadata-only beta scope, outcome capture requirements, and real-user evidence gate",
        },
        {
            "phase": 9,
            "artifact_section": "hosted_beta_control_contract",
            "local_completion_surface": "hosted auth, database, storage, audit, backup, AI routing, observability, and payment gate checklist",
        },
        {
            "phase": 10,
            "artifact_section": "real_file_beta_contract",
            "local_completion_surface": "controlled real-file beta scope, upload consent, AI-use consent, redaction, deletion, and audit requirements",
        },
        {
            "phase": 11,
            "artifact_section": "packet_rows[].buyer_supplier_evidence + buyer_supplier_validation_contract",
            "local_completion_surface": "buyer and supplier evidence ladders, safe allowed language, and validation/verification claim blocks",
        },
        {
            "phase": 12,
            "artifact_section": "payment_pricing_contract",
            "local_completion_surface": "paid scope, forbidden paid scope, pricing/review prerequisites, and live-checkout-disabled gate",
        },
        {
            "phase": 13,
            "artifact_section": "public_launch_contract",
            "local_completion_surface": "safe initial public scope, blocked public scope, approval prerequisites, and public-launch-ready false",
        },
    ]
    phases = []
    for row in surface_rows:
        contract = contracts_by_phase[row["phase"]]
        exit_status = str(contract["exit_criteria_status"])
        phases.append(
            {
                "phase": row["phase"],
                "phase_id": f"phase-{row['phase']}",
                "completion_contract_id": f"phase_{row['phase']}",
                "name": contract["name"],
                "status": contract["status"],
                "main_output": contract["main_output"],
                "artifact": contract["artifact"],
                "artifact_section": row["artifact_section"],
                "local_completion_surface": row["local_completion_surface"],
                "exit_criteria_status": exit_status,
                "external_gate_status": (
                    "closed_until_real_evidence"
                    if "blocked" in exit_status or "required" in str(contract["status"])
                    else "local_scope_complete_claims_still_limited"
                ),
            }
        )
    return phases


def build_business_logic_phases(
    workflow: dict[str, Any],
    official_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    packet_rows = []
    for packet in workflow.get("packets", []):
        canonical_packet = build_canonical_packet_contract(packet)
        decision_tree = build_decision_tree(packet, official_sources)
        beginner_flow = build_beginner_flow(packet, official_sources)
        country_packs = build_country_packs(packet, official_sources)
        market = build_market_intelligence(packet, official_sources)
        source_monitor = build_source_monitoring_contract(packet, official_sources)
        source_freshness = evaluate_source_freshness(packet, source_monitor)
        buyer_supplier = evaluate_buyer_supplier_evidence(packet)
        outputs = build_packet_outputs(packet)
        scores = build_business_scores(packet, market, source_monitor, buyer_supplier, source_freshness)
        gate_decision = evaluate_business_gate_decision(
            packet,
            beginner_flow=beginner_flow,
            canonical_packet=canonical_packet,
            decision_tree=decision_tree,
            buyer_supplier=buyer_supplier,
            source_freshness=source_freshness,
        )
        packet_rows.append(
            {
                "packet_id": _packet_id(packet),
                "product_name": packet.get("product_name"),
                "business_positioning": "trade_decision_preparation_not_compliance_approval",
                "recommended_first_wedge": "foreign_exporters_selling_into_canada",
                "commercial_wedge_detail": "export-to-Canada readiness packets for food/agri/seafood/general goods exporters",
                "canonical_packet_contract": canonical_packet,
                "decision_tree": decision_tree,
                "beginner_flow": beginner_flow,
                "market_intelligence": market,
                "country_packs": country_packs,
                "source_monitoring_contract": source_monitor,
                "source_freshness": source_freshness,
                "buyer_supplier_evidence": buyer_supplier,
                "packet_outputs": outputs,
                "business_scores": scores,
                "business_gate_decision": gate_decision,
                "blocked_claims": [
                    "approved",
                    "compliant",
                    "ready_to_ship",
                    "tariff_confirmed",
                    "buyer_validated",
                    "supplier_verified",
                    "supplier_recommended",
                    "market_demand_proven",
                    "profitable_product",
                ],
                "next_valid_move": decision_tree["next_valid_move"],
            }
        )
    completion_phase_contracts = build_completion_phase_contracts()
    phases = build_business_phase_surfaces(completion_phase_contracts)
    return {
        "generated_at": _now(),
        "status": "business_logic_implemented_with_external_evidence_gates",
        "phase_count": len(phases),
        "score_ids": BUSINESS_SCORE_IDS,
        "phase_ids": BUSINESS_PHASE_IDS,
        "top_level_phase_scope": "business_phases_1_to_13",
        "phase_zero_identity_contract": completion_phase_contracts["phases"][0],
        "phases": phases,
        "business_identity_lock": build_business_identity_lock(),
        "beginner_flow_contract": build_beginner_flow_contract(),
        "buyer_supplier_validation_contract": build_buyer_supplier_validation_contract(),
        "metadata_only_beta_contract": build_metadata_only_beta_contract(),
        "real_file_beta_contract": build_real_file_beta_contract(),
        "payment_pricing_contract": build_payment_pricing_contract(),
        "public_launch_contract": build_public_launch_contract(),
        "completion_phase_contracts": completion_phase_contracts,
        "reviewer_signoff_framework": build_reviewer_signoff_framework(),
        "hosted_beta_control_contract": build_hosted_beta_control_contract(),
        "packet_count": len(packet_rows),
        "packet_rows": packet_rows,
        "blocked_claim_policy": "Business logic prepares decisions; it never approves import/export, tariff, buyer, supplier, shipment, compliance, legal, or market-demand claims.",
        "proof_boundary": "This business logic is generated from local packet/evidence/source state. External market datasets, buyer/supplier validation, source freshness, and qualified reviews remain evidence gates.",
    }
