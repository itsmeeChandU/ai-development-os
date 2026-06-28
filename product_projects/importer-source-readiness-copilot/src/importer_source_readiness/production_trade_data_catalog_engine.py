"""Production trade data catalog engine.

Trade discovery tells a beginner what they can research. This engine turns
that research into concrete data-query plans: which source to open, what inputs
are required, what output fields are allowed, and which claims stay blocked
until a dated dataset row is attached.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .production_trade_discovery_engine import build_production_trade_discovery_engine


STATUS = "production_trade_data_catalog_engine_ready_query_plans_no_values_loaded"

BLOCKED_DATA_CLAIMS = (
    "top_product_recommended",
    "best_origin_country",
    "best_destination_market",
    "confirmed_market_size",
    "guaranteed_demand",
    "profitable_market",
    "buyer_validated",
    "supplier_verified",
    "tariff_confirmed",
    "regulated_product_approved",
    "customs_approved",
    "ready_to_ship",
)

QUERY_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "template_id": "canada_imports_by_product_origin",
        "label": "Canada imports by product and origin",
        "plain_language_question": "What goods does Canada import, and from which origin countries?",
        "direction": "import_into_canada",
        "primary_source_ids": ["ised-trade-data-online", "statcan-wds"],
        "secondary_source_ids": ["world-bank-wits", "itc-trade-map"],
        "required_inputs": ["product_family_or_hs_candidate", "origin_country", "destination_country=Canada", "period"],
        "optional_inputs": ["hs_code_candidate", "unit_of_measure", "province_or_region_if_source_supports_it"],
        "allowed_output_fields_after_ingestion": [
            "period",
            "product_or_hs_label",
            "origin_country",
            "destination_country",
            "import_value",
            "quantity",
            "unit",
            "source_id",
            "source_url",
            "checked_at",
        ],
        "business_use": "Rank research lanes for deeper validation.",
        "claim_boundary": "Import rows are research signals only and do not prove demand, profit, buyer intent, or import approval.",
    },
    {
        "template_id": "canada_exports_by_product_destination",
        "label": "Canada exports by product and destination",
        "plain_language_question": "What goods does Canada export, and which destination countries should be researched?",
        "direction": "export_from_canada",
        "primary_source_ids": ["ised-trade-data-online", "statcan-wds"],
        "secondary_source_ids": ["canada-trade-commissioner-export-guide", "itc-market-access-map"],
        "required_inputs": ["product_family_or_hs_candidate", "origin_country=Canada", "destination_country", "period"],
        "optional_inputs": ["hs_code_candidate", "unit_of_measure", "destination_market_access_route"],
        "allowed_output_fields_after_ingestion": [
            "period",
            "product_or_hs_label",
            "origin_country",
            "destination_country",
            "export_value",
            "quantity",
            "unit",
            "source_id",
            "source_url",
            "checked_at",
        ],
        "business_use": "Help Canadian exporters choose which destination market deserves deeper validation.",
        "claim_boundary": "Export rows are research signals only and do not prove export readiness, demand, profit, or destination approval.",
    },
    {
        "template_id": "origin_country_comparison_for_canada",
        "label": "Origin-country comparison for Canada",
        "plain_language_question": "Which countries appear in source-backed Canada import research for this product family?",
        "direction": "import_into_canada",
        "primary_source_ids": ["ised-trade-data-online", "world-bank-wits", "itc-trade-map"],
        "secondary_source_ids": ["gac-sanctions", "itc-market-access-map"],
        "required_inputs": ["product_family_or_hs_candidate", "destination_country=Canada", "period"],
        "optional_inputs": ["origin_country_shortlist", "sanctions_screening_date", "market_access_notes"],
        "allowed_output_fields_after_ingestion": [
            "period",
            "origin_country",
            "trade_value",
            "share_or_rank_if_source_provides_it",
            "source_id",
            "source_url",
            "checked_at",
        ],
        "business_use": "Create a short list of origin countries to validate with supplier and buyer evidence.",
        "claim_boundary": "Country comparison does not prove the country is best, safe, sanctions-clear, profitable, or supplier-verified.",
    },
    {
        "template_id": "canadian_importer_lead_lookup",
        "label": "Possible Canadian importer leads",
        "plain_language_question": "Which Canadian companies might be lead sources for this product family?",
        "direction": "import_into_canada",
        "primary_source_ids": ["canada-cid"],
        "secondary_source_ids": ["ised-trade-data-online"],
        "required_inputs": ["product_family_or_hs_candidate", "origin_country"],
        "optional_inputs": ["city", "company_name", "lead_source_date"],
        "allowed_output_fields_after_ingestion": [
            "company_name",
            "city",
            "province",
            "product_or_hs_label",
            "origin_country",
            "source_id",
            "source_url",
            "checked_at",
        ],
        "business_use": "Prepare outreach questions and buyer-evidence ladder entries.",
        "claim_boundary": "Importer rows are possible lead sources only and never buyer validation or purchase intent.",
    },
    {
        "template_id": "regulated_goods_source_overlay",
        "label": "Regulated goods source overlay",
        "plain_language_question": "Could this product family trigger CFIA, import-control, export-control, or sanctions review?",
        "direction": "both",
        "primary_source_ids": ["cfia-airs", "gac-import-controls", "gac-export-controls", "gac-sanctions"],
        "secondary_source_ids": ["cbsa-import-commercial-goods"],
        "required_inputs": ["product_description", "intended_use", "origin_country", "destination_country"],
        "optional_inputs": ["ingredients_or_materials", "end_user", "certificate_type"],
        "allowed_output_fields_after_ingestion": [
            "source_id",
            "source_url",
            "risk_tag",
            "question_to_answer",
            "review_lane",
            "checked_at",
        ],
        "business_use": "Warn the user before they invest time in a regulated or controlled lane.",
        "claim_boundary": "Regulated-source routing does not prove CFIA approval, permit status, sanctions clearance, or legal compliance.",
    },
    {
        "template_id": "market_access_comparison",
        "label": "Market access comparison",
        "plain_language_question": "Which tariff, regulatory, or preference questions should be checked before choosing the lane?",
        "direction": "both",
        "primary_source_ids": ["itc-market-access-map"],
        "secondary_source_ids": ["cbsa-customs-tariff-2026", "wco-harmonized-system"],
        "required_inputs": ["product_family_or_hs_candidate", "origin_country", "destination_country"],
        "optional_inputs": ["trade_agreement_candidate", "tariff_line_candidate", "regulatory_requirement_notes"],
        "allowed_output_fields_after_ingestion": [
            "source_id",
            "source_url",
            "market_access_issue",
            "tariff_or_requirement_reference",
            "checked_at",
        ],
        "business_use": "Prepare broker or expert questions before external claims are made.",
        "claim_boundary": "Market-access comparison is not tariff confirmation, preference eligibility, or market-entry approval.",
    },
    {
        "template_id": "global_context_fallback",
        "label": "Global trade context fallback",
        "plain_language_question": "What global context should be checked when Canada-specific rows are not enough?",
        "direction": "both",
        "primary_source_ids": ["world-bank-wits", "itc-trade-map"],
        "secondary_source_ids": ["itc-market-access-map"],
        "required_inputs": ["product_family_or_hs_candidate", "origin_country", "destination_country", "period"],
        "optional_inputs": ["comparison_countries", "non_tariff_measure_notes"],
        "allowed_output_fields_after_ingestion": [
            "period",
            "country",
            "trade_flow",
            "trade_value",
            "indicator_name",
            "source_id",
            "source_url",
            "checked_at",
        ],
        "business_use": "Add context for unsupported or generic country packs.",
        "claim_boundary": "Global context does not prove Canada-specific demand, buyer validation, or compliance.",
    },
)

BROWSE_CARDS: tuple[dict[str, Any], ...] = (
    {
        "card_id": "browse_imports_into_canada",
        "label": "Browse imports into Canada",
        "template_ids": ["canada_imports_by_product_origin", "origin_country_comparison_for_canada"],
        "plain_language_value": "Start with what Canada appears to import, then narrow by product family and origin country.",
        "next_valid_move": "Choose a product family and origin lane, then attach dated import rows.",
    },
    {
        "card_id": "browse_exports_from_canada",
        "label": "Browse exports from Canada",
        "template_ids": ["canada_exports_by_product_destination", "market_access_comparison"],
        "plain_language_value": "Start with what Canada appears to export, then narrow by destination and access questions.",
        "next_valid_move": "Choose a destination and product family, then attach dated export rows.",
    },
    {
        "card_id": "compare_origin_countries",
        "label": "Compare origin countries",
        "template_ids": ["origin_country_comparison_for_canada", "regulated_goods_source_overlay"],
        "plain_language_value": "Compare lanes without calling one best or approved.",
        "next_valid_move": "Select the lane that deserves evidence collection and expert questions.",
    },
    {
        "card_id": "find_importer_leads",
        "label": "Find possible importer leads",
        "template_ids": ["canadian_importer_lead_lookup"],
        "plain_language_value": "Find possible lead sources after a product family is selected.",
        "next_valid_move": "Record the lead source and move through buyer evidence levels.",
    },
    {
        "card_id": "check_regulated_goods_first",
        "label": "Check regulated-goods risk",
        "template_ids": ["regulated_goods_source_overlay", "market_access_comparison"],
        "plain_language_value": "Spot food, plant, animal, controlled, or restricted-country questions early.",
        "next_valid_move": "Attach source snapshot and route to qualified review if risk tags appear.",
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


def _source_registry_by_id(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_text(source.get("id")): source for source in sources if _text(source.get("id"))}


def _source_routes(source_ids: list[str], source_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for source_id in source_ids:
        source = source_by_id.get(source_id, {})
        rows.append(
            {
                "source_id": source_id,
                "name": source.get("name", source_id),
                "url": source.get("url", ""),
                "registry_status": "registered" if source else "missing_from_registry",
                "access_mode": "manual_query_or_terms_checked_connector",
                "claim_boundary": source.get("claim_boundary", "Reference source only; claims remain blocked."),
            }
        )
    return rows


def _template_record(row: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_ids = [*row["primary_source_ids"], *row.get("secondary_source_ids", [])]
    return {
        **row,
        "status": "query_template_ready_no_values_loaded",
        "source_routes": _source_routes(source_ids, source_by_id),
        "values_loaded": False,
        "automation_ready": False,
        "terms_review_required": True,
        "allowed_to_show_numeric_values": False,
        "allowed_to_rank_as_research_signal_after_ingestion": True,
        "blocked_claims": list(BLOCKED_DATA_CLAIMS),
        "next_valid_move": "Collect required inputs, check source terms, run a manual or approved connector query, then attach dated rows.",
    }


def _template_ids_for_lane(lane: dict[str, Any], category: dict[str, Any]) -> list[str]:
    direction = lane.get("direction")
    template_ids: list[str] = []
    if direction == "import_into_canada":
        template_ids.extend(["canada_imports_by_product_origin", "origin_country_comparison_for_canada"])
        if category.get("category_id") != "services_not_merchandise_scope":
            template_ids.append("canadian_importer_lead_lookup")
    elif direction == "export_from_canada":
        template_ids.append("canada_exports_by_product_destination")
    else:
        template_ids.append("global_context_fallback")
    if set(category.get("regulated_risk_tags", [])) - {"origin", "material_spec", "labeling"}:
        template_ids.append("regulated_goods_source_overlay")
    if category.get("category_id") != "services_not_merchandise_scope":
        template_ids.append("market_access_comparison")
    return list(dict.fromkeys(template_ids))


def _query_work_orders(discovery: dict[str, Any], templates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    categories = {row["category_id"]: row for row in discovery.get("category_families", [])}
    work_orders: list[dict[str, Any]] = []
    for lane in discovery.get("country_lanes", []):
        for category_id in lane.get("common_research_categories", []):
            category = categories.get(category_id)
            if not category:
                continue
            for template_id in _template_ids_for_lane(lane, category):
                template = templates[template_id]
                work_orders.append(
                    {
                        "query_work_order_id": f"trade-data:{lane['lane_id']}:{category_id}:{template_id}",
                        "lane_id": lane["lane_id"],
                        "category_id": category_id,
                        "category_label": category.get("label"),
                        "origin_country": lane.get("origin_country"),
                        "destination_country": lane.get("destination_country"),
                        "direction": lane.get("direction"),
                        "template_id": template_id,
                        "template_label": template["label"],
                        "source_ids": template["primary_source_ids"],
                        "required_inputs": template["required_inputs"],
                        "input_status": "missing_exact_product_or_hs_until_user_selects",
                        "manual_query_ready": True,
                        "approved_connector_ready": False,
                        "values_loaded": False,
                        "dated_dataset_row_attached": False,
                        "allowed_output_before_ingestion": [
                            "query_plan",
                            "required_inputs",
                            "source_routes",
                            "blocked_claims",
                            "next_valid_move",
                        ],
                        "allowed_output_after_ingestion": template["allowed_output_fields_after_ingestion"],
                        "blocked_claims": list(BLOCKED_DATA_CLAIMS),
                        "claim_boundary": template["claim_boundary"],
                        "next_valid_move": "Use the template manually or through an approved connector, attach dated rows, then re-score the packet.",
                    }
                )
    return work_orders


def _browse_cards(templates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for row in BROWSE_CARDS:
        cards.append(
            {
                **row,
                "status": "browse_card_ready_no_values_loaded",
                "query_templates": [templates[template_id] for template_id in row["template_ids"]],
                "values_loaded": False,
                "recommendation_claimed": False,
                "blocked_claims": list(BLOCKED_DATA_CLAIMS),
            }
        )
    return cards


def build_production_trade_data_catalog_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    sources = _load_json(root / "data" / "official_source_registry.json", [])
    source_by_id = _source_registry_by_id(sources)
    discovery_path = root / "system_review_graph" / "production_trade_discovery_manifest.json"
    discovery = _load_json(discovery_path, {})
    if not discovery:
        discovery = build_production_trade_discovery_engine(root)
    template_rows = [_template_record(dict(row), source_by_id) for row in QUERY_TEMPLATES]
    templates = {row["template_id"]: row for row in template_rows}
    work_orders = _query_work_orders(discovery, templates)
    browse_cards = _browse_cards(templates)
    missing_registry_sources = sorted(
        {
            source_id
            for template in template_rows
            for source_id in [*template["primary_source_ids"], *template.get("secondary_source_ids", [])]
            if source_id not in source_by_id
        }
    )
    ingestion_policy = {
        "status": "trade_data_ingestion_policy_ready_fail_closed",
        "numeric_values_before_ingestion_allowed": False,
        "approved_connector_required_for_automation": True,
        "manual_query_allowed": True,
        "required_before_numeric_display": [
            "source_terms_or_manual-use check",
            "query parameters",
            "dated dataset row",
            "source URL",
            "period",
            "field mapping",
            "limitation text",
        ],
        "required_before_market_conclusion": [
            "dated dataset rows",
            "market-access comparison",
            "buyer evidence",
            "supplier evidence where relevant",
            "qualified reviewer finding for external wording",
        ],
        "blocked_claims": list(BLOCKED_DATA_CLAIMS),
    }
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "template_count": len(template_rows),
        "browse_card_count": len(browse_cards),
        "query_work_order_count": len(work_orders),
        "source_route_count": sum(len(row["source_routes"]) for row in template_rows),
        "missing_registry_sources": missing_registry_sources,
        "query_templates": template_rows,
        "browse_cards": browse_cards,
        "query_work_orders": work_orders,
        "ingestion_policy": ingestion_policy,
        "values_loaded": False,
        "numeric_values_shown": False,
        "recommendations_created": False,
        "demand_claimed": False,
        "profitability_claimed": False,
        "buyer_validation_claimed": False,
        "supplier_verification_claimed": False,
        "external_effects_created": False,
        "claims_opened": False,
        "blocked_claims": list(BLOCKED_DATA_CLAIMS),
        "proof_boundary": (
            "The trade-data catalog creates query plans, browse cards, input requirements, and work orders. "
            "It does not show numeric trade values, rank products as best, prove demand, prove profit, validate buyers, or approve trade action until dated rows and review evidence exist."
        ),
    }


def render_trade_data_catalog_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Trade Data Catalog Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Browse Cards",
        "",
    ]
    for card in payload["browse_cards"]:
        lines.extend(
            [
                f"### {card['label']}",
                "",
                card["plain_language_value"],
                "",
                f"- Query templates: {len(card['query_templates'])}",
                "- Values loaded: false",
                "- Recommendation claimed: false",
                f"- Next valid move: {card['next_valid_move']}",
                "",
            ]
        )
    lines.extend(["## Query Templates", ""])
    for template in payload["query_templates"]:
        lines.append(f"- `{template['template_id']}`: {template['label']} ({template['direction']}).")
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            "- Numeric values shown: false",
            "- Recommendations created: false",
            "- Demand claimed: false",
            "- Profitability claimed: false",
            "- Buyer validation claimed: false",
            "- Supplier verification claimed: false",
            "- Claims opened: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_trade_data_catalog_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_trade_data_catalog_manifest.json"
    templates_path = graph / "production_trade_data_query_templates.json"
    work_orders_path = graph / "production_trade_data_query_work_orders.json"
    browse_cards_path = graph / "production_trade_data_browse_cards.json"
    ingestion_policy_path = graph / "production_trade_data_ingestion_policy.json"
    doc_path = docs / "PRODUCTION_TRADE_DATA_CATALOG_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    templates_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_trade_data_query_templates_ready",
                "template_count": payload["template_count"],
                "query_templates": payload["query_templates"],
                "values_loaded": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    work_orders_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_trade_data_query_work_orders_ready_no_values_loaded",
                "query_work_order_count": payload["query_work_order_count"],
                "query_work_orders": payload["query_work_orders"],
                "values_loaded": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    browse_cards_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_trade_data_browse_cards_ready",
                "browse_card_count": payload["browse_card_count"],
                "browse_cards": payload["browse_cards"],
                "recommendations_created": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    ingestion_policy_path.write_text(
        json.dumps(payload["ingestion_policy"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_trade_data_catalog_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "templates": templates_path,
        "work_orders": work_orders_path,
        "browse_cards": browse_cards_path,
        "ingestion_policy": ingestion_policy_path,
        "doc": doc_path,
    }
