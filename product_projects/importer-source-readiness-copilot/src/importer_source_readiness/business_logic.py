"""Business-decision logic for trade readiness packets.

The functions in this module turn packet/evidence state into decision-prep
outputs. They deliberately stop short of compliance, buyer, supplier, tariff,
or market-demand claims unless real evidence is attached elsewhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


BUSINESS_PHASE_IDS = [
    "decision_tree_before_features",
    "market_intelligence_module",
    "country_pack_architecture",
    "source_monitoring_contract",
    "commercial_packet_outputs",
]

BUSINESS_SCORE_IDS = [
    "market_signal_score",
    "evidence_completeness_score",
    "source_freshness_score",
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
    blockers = [row for row in questions if str(row["status"]).startswith(("blocked", "needs"))]
    return {
        "status": "decision_tree_ready_claims_blocked",
        "question_count": len(questions),
        "questions": questions,
        "blocked_or_review_step_count": len(blockers),
        "next_valid_move": questions[-1]["answer"],
        "proof_boundary": "The decision tree prepares the next safe move; it does not approve import, export, tariff, buyer, supplier, or shipment decisions.",
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
    if missing_core:
        stage = "starter"
    elif evidence_count == 0:
        stage = "starter"
    elif decision_missing:
        stage = "document"
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
    for country, role in ((destination, "destination_import_pack"), (origin, "origin_export_pack"), ("Generic", "generic_fallback_pack")):
        if country in {row.get("country") for row in countries}:
            continue
        sources = _sources_for_country(official_sources, country)
        pack = {
            "country": country,
            "role": role,
            "status": "country_pack_ready_reference_only" if sources else "country_pack_required",
            "source_count": len(sources),
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
            "source_routes": importer_sources,
            "claim_boundary": "Importer or buyer sources create possible leads only; buyer validation needs dated contact, terms, demand, and legitimacy evidence.",
            "outputs": ["possible lead source", "buyer questions", "buyer validation tracker", "outreach packet not sent automatically"],
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
                "parser_contract": "extract date/status/hash and classify change type before packet impact",
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


def _score(color: str, value: int, status: str, meaning: str, next_valid_move: str) -> dict[str, Any]:
    return {
        "value": value,
        "color": color,
        "status": status,
        "meaning": meaning,
        "next_valid_move": next_valid_move,
        "external_claims_opened": False,
    }


def build_business_scores(
    packet: dict[str, Any],
    market: dict[str, Any],
    source_monitor: dict[str, Any],
) -> dict[str, Any]:
    evidence = packet.get("evidence_summary", {})
    missing = int(evidence.get("missing") or 0)
    attached = int(evidence.get("attached") or packet.get("evidence_count") or 0)
    stale = int(evidence.get("stale") or 0)
    blocker_count = int(packet.get("blocker_count") or 0)
    responsibility = packet.get("responsibility_path", {})
    responsibility_level = str(responsibility.get("responsibility_level") or "unknown")
    evidence_value = int(round((attached / max(attached + missing, 1)) * 100))
    source_value = 20 if stale else min(80, 30 + source_monitor.get("source_count", 0) * 5)
    responsibility_value = 30 if responsibility_level == "unknown" else 60 if "high" in responsibility_level else 75
    safety_value = 20 if blocker_count else 70
    scores = {
        "market_signal_score": _score(
            "grey",
            25,
            "research_required",
            "Market signal cannot be scored until trade dataset, access-barrier, and buyer evidence are attached.",
            market["next_valid_move"],
        ),
        "evidence_completeness_score": _score(
            "red" if missing else "yellow",
            evidence_value,
            "blocked_missing_evidence" if missing else "internal_review_ready_external_claims_blocked",
            f"{attached} evidence rows attached and {missing} required items missing.",
            "Attach missing product, commercial, origin, review, buyer, and source evidence.",
        ),
        "source_freshness_score": _score(
            "red" if stale else "yellow",
            source_value,
            "blocked_stale_source" if stale else "reference_sources_routed_review_required",
            "Official/reference sources are routed, but current-source proof and qualified review are still required.",
            "Run dated source refresh and record hash/change classification.",
        ),
        "responsibility_clarity_score": _score(
            "red" if responsibility_level == "unknown" else "yellow",
            responsibility_value,
            "blocked_responsibility_unknown" if responsibility_level == "unknown" else "responsibility_path_identified_review_required",
            responsibility.get("guidance") or "Importer of record and Incoterms must be confirmed.",
            "Confirm importer of record, Incoterms, buyer/importer role, and broker review path.",
        ),
        "decision_safety_score": _score(
            "red" if blocker_count else "yellow",
            safety_value,
            "blocked_external_decision_unsafe" if blocker_count else "internal_review_only_external_claims_blocked",
            f"{blocker_count} blocker rows keep external decisions closed.",
            packet.get("public_summary", {}).get("next_valid_move") or "Proceed only to internal review.",
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


def build_business_logic_phases(
    workflow: dict[str, Any],
    official_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    packet_rows = []
    for packet in workflow.get("packets", []):
        canonical_packet = build_canonical_packet_contract(packet)
        decision_tree = build_decision_tree(packet, official_sources)
        country_packs = build_country_packs(packet, official_sources)
        market = build_market_intelligence(packet, official_sources)
        source_monitor = build_source_monitoring_contract(packet, official_sources)
        outputs = build_packet_outputs(packet)
        scores = build_business_scores(packet, market, source_monitor)
        packet_rows.append(
            {
                "packet_id": _packet_id(packet),
                "product_name": packet.get("product_name"),
                "business_positioning": "trade_decision_preparation_not_compliance_approval",
                "recommended_first_wedge": "foreign_exporters_selling_into_canada",
                "commercial_wedge_detail": "export-to-Canada readiness packets for food/agri/seafood/general goods exporters",
                "canonical_packet_contract": canonical_packet,
                "decision_tree": decision_tree,
                "market_intelligence": market,
                "country_packs": country_packs,
                "source_monitoring_contract": source_monitor,
                "packet_outputs": outputs,
                "business_scores": scores,
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
    phases = [
        {
            "phase_id": "phase-1",
            "name": "Decision tree before more features",
            "status": "implemented_from_packet_state",
            "artifact_section": "packet_rows[].decision_tree",
        },
        {
            "phase_id": "phase-2",
            "name": "Market intelligence module",
            "status": "implemented_as_research_plan_with_gates",
            "artifact_section": "packet_rows[].market_intelligence",
        },
        {
            "phase_id": "phase-3",
            "name": "Country-pack architecture",
            "status": "implemented_reference_country_packs",
            "artifact_section": "packet_rows[].country_packs",
        },
        {
            "phase_id": "phase-4",
            "name": "Source monitor",
            "status": "implemented_local_monitoring_contract_no_live_freshness_claim",
            "artifact_section": "packet_rows[].source_monitoring_contract",
        },
        {
            "phase_id": "phase-5",
            "name": "Packet outputs",
            "status": "implemented_commercial_outputs_claims_blocked",
            "artifact_section": "packet_rows[].packet_outputs",
        },
    ]
    return {
        "generated_at": _now(),
        "status": "business_logic_phases_ready_with_evidence_gates",
        "phase_count": len(phases),
        "score_ids": BUSINESS_SCORE_IDS,
        "phase_ids": BUSINESS_PHASE_IDS,
        "phases": phases,
        "reviewer_signoff_framework": build_reviewer_signoff_framework(),
        "hosted_beta_control_contract": build_hosted_beta_control_contract(),
        "packet_count": len(packet_rows),
        "packet_rows": packet_rows,
        "blocked_claim_policy": "Business logic prepares decisions; it never approves import/export, tariff, buyer, supplier, shipment, compliance, legal, or market-demand claims.",
        "proof_boundary": "This business logic is generated from local packet/evidence/source state. External market datasets, buyer/supplier validation, source freshness, and qualified reviews remain evidence gates.",
    }
