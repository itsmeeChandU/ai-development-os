"""Production trade discovery engine.

This module covers the pre-packet question the user raised: a business owner
may not know which product, country lane, source, or document path to explore.
It turns official source routes into beginner-friendly discovery records while
refusing to recommend products, prove demand, validate buyers, or open launch
claims without dated data rows and review evidence.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_trade_discovery_engine_ready_beginner_research_routed_no_opportunity_claims"

DISCOVERY_BLOCKED_CLAIMS = (
    "best_product_to_import",
    "best_product_to_export",
    "profitable_market",
    "guaranteed_demand",
    "buyer_validated",
    "supplier_verified",
    "tariff_confirmed",
    "cfia_approved",
    "customs_approved",
    "ready_to_ship",
    "public_launch_ready",
)

DISCOVERY_SOURCE_FACTS: tuple[dict[str, Any], ...] = (
    {
        "source_id": "ised-trade-data-online",
        "source_area": "canada_trade_browse",
        "usable_fact": "Browse Canada import and export reports by product, partner country, and period before choosing a lane.",
        "product_use": "Canada import/export category and country-lane research.",
        "claim_boundary": "Trade rows can support research signals only; they do not prove demand, profit, or buyer intent.",
    },
    {
        "source_id": "canada-cid",
        "source_area": "canada_importer_leads",
        "usable_fact": "Find possible Canadian importer leads by product, city, and country of origin.",
        "product_use": "Lead discovery after a product/category is chosen.",
        "claim_boundary": "Importer rows are lead sources only and never buyer validation.",
    },
    {
        "source_id": "statcan-wds",
        "source_area": "canada_trade_dataset_access",
        "usable_fact": "Use Statistics Canada data service routes for Canadian international merchandise trade tables after table and license review.",
        "product_use": "Machine-readable Canada merchandise trade dataset route.",
        "claim_boundary": "A data-service route does not prove a value until a dated dataset row is ingested and cited.",
    },
    {
        "source_id": "cbsa-import-commercial-goods",
        "source_area": "canada_import_workflow",
        "usable_fact": "Route Canada import preparation to CBSA commercial-import steps and importer responsibility questions.",
        "product_use": "Import workflow, business number/RM, origin, rulings, and other government requirement prompts.",
        "claim_boundary": "The product routes preparation only and does not act as CBSA, a broker, or legal adviser.",
    },
    {
        "source_id": "cbsa-customs-tariff-2026",
        "source_area": "canada_tariff_orientation",
        "usable_fact": "Use the Canada tariff source route for HS candidate and tariff-orientation research.",
        "product_use": "HS candidate and tariff source routing.",
        "claim_boundary": "HS candidates are not classification or tariff confirmation.",
    },
    {
        "source_id": "cfia-airs",
        "source_area": "regulated_product_screening",
        "usable_fact": "Route food, plant, animal, seafood, and other CFIA-regulated suspicion to AIRS reference checks.",
        "product_use": "Early regulated-goods warning before the user invests in a lane.",
        "claim_boundary": "AIRS routing does not prove admissibility, CFIA approval, or current import compliance.",
    },
    {
        "source_id": "gac-sanctions",
        "source_area": "sanctions_country_screening",
        "usable_fact": "Route restricted-country and sanctions questions to Global Affairs Canada sanctions records.",
        "product_use": "Country-lane and party-screening warning.",
        "claim_boundary": "Sanctions route presence does not prove screening is complete or clear.",
    },
    {
        "source_id": "world-bank-wits",
        "source_area": "global_trade_comparison",
        "usable_fact": "Compare global merchandise trade, tariff, and non-tariff-measure context.",
        "product_use": "Fallback global market research when Canada-specific rows need context.",
        "claim_boundary": "Global indicators are research context only.",
    },
    {
        "source_id": "itc-trade-map",
        "source_area": "global_trade_and_company_directory",
        "usable_fact": "Route global import/export values, growth, market share, and company-directory research.",
        "product_use": "Compare markets and identify possible company-directory leads.",
        "claim_boundary": "Directory or trade rows do not validate buyers or demand.",
    },
    {
        "source_id": "itc-market-access-map",
        "source_area": "market_access_comparison",
        "usable_fact": "Route tariff, trade-remedy, regulatory, and preferential-access comparison.",
        "product_use": "Market access issue spotting before a packet is sent to review.",
        "claim_boundary": "Market-access routes do not confirm tariff treatment or market-entry approval.",
    },
    {
        "source_id": "wco-harmonized-system",
        "source_area": "hs_doctrine",
        "usable_fact": "Use HS structure to explain why product wording needs a classification candidate.",
        "product_use": "Beginner HS-candidate education and next questions.",
        "claim_boundary": "HS doctrine supports candidate research only, not classification confirmation.",
    },
    {
        "source_id": "canada-trade-commissioner-export-guide",
        "source_area": "canada_export_beginner_guidance",
        "usable_fact": "Route Canadian exporters to Government of Canada export-planning guidance.",
        "product_use": "Export-from-Canada beginner flow and export checklist prompts.",
        "claim_boundary": "General guidance does not prove a specific exporter, product, or destination is export-ready.",
    },
    {
        "source_id": "gac-export-controls",
        "source_area": "canada_export_controls",
        "usable_fact": "Route Canadian export-control and permit questions to Global Affairs Canada controls.",
        "product_use": "Export-from-Canada controlled-goods warning and review routing.",
        "claim_boundary": "Export-control routing does not prove permit status, destination permission, or compliance.",
    },
)

DATASET_ROUTES: tuple[dict[str, Any], ...] = (
    {
        "dataset_route_id": "canada-import-export-browser",
        "source_id": "ised-trade-data-online",
        "direction_support": ["import_into_canada", "export_from_canada"],
        "data_access_status": "manual_query_or_connector_after_terms_review",
        "values_loaded": False,
        "supports_after_ingestion": ["source_backed_trade_flow_signal", "top_origin_country_signal", "trend_signal"],
        "cannot_support": ["profitable_market", "guaranteed_demand", "buyer_validated"],
    },
    {
        "dataset_route_id": "canada-importer-lead-browser",
        "source_id": "canada-cid",
        "direction_support": ["import_into_canada"],
        "data_access_status": "manual_query_or_connector_after_terms_review",
        "values_loaded": False,
        "supports_after_ingestion": ["possible_importer_lead_route"],
        "cannot_support": ["buyer_validated", "purchase_intent_confirmed"],
    },
    {
        "dataset_route_id": "canada-merchandise-trade-wds",
        "source_id": "statcan-wds",
        "direction_support": ["import_into_canada", "export_from_canada"],
        "data_access_status": "table_route_research_required_before_ingestion",
        "values_loaded": False,
        "supports_after_ingestion": ["dated_canada_trade_table_row"],
        "cannot_support": ["legal_currentness", "profitability", "buyer_demand"],
    },
    {
        "dataset_route_id": "global-trade-context",
        "source_id": "world-bank-wits",
        "direction_support": ["import_into_canada", "export_from_canada", "compare_other_markets"],
        "data_access_status": "manual_query_or_connector_after_terms_review",
        "values_loaded": False,
        "supports_after_ingestion": ["global_trade_context_signal"],
        "cannot_support": ["canada_import_approval", "buyer_validation"],
    },
    {
        "dataset_route_id": "global-trade-map-context",
        "source_id": "itc-trade-map",
        "direction_support": ["import_into_canada", "export_from_canada", "compare_other_markets"],
        "data_access_status": "manual_query_or_connector_after_terms_review",
        "values_loaded": False,
        "supports_after_ingestion": ["trade_value_volume_growth_signal", "company_directory_route"],
        "cannot_support": ["buyer_validation", "guaranteed_demand"],
    },
    {
        "dataset_route_id": "market-access-map-context",
        "source_id": "itc-market-access-map",
        "direction_support": ["import_into_canada", "export_from_canada", "compare_other_markets"],
        "data_access_status": "manual_query_or_connector_after_terms_review",
        "values_loaded": False,
        "supports_after_ingestion": ["market_access_issue_signal"],
        "cannot_support": ["tariff_confirmed", "market_entry_approved"],
    },
)

BEGINNER_FLOWS: tuple[dict[str, Any], ...] = (
    {
        "flow_id": "browse_canada_imports",
        "label": "Browse goods Canada imports",
        "plain_language_goal": "Help a user choose a product family and origin country to research before making a packet.",
        "build_track": ["show category families", "show diverse origin lanes", "show source routes", "create starter packet"],
        "research_track": ["Canada import trade data", "possible importer leads", "CBSA import workflow", "CFIA regulated-goods suspicion"],
        "source_track": ["ised-trade-data-online", "canada-cid", "cbsa-import-commercial-goods", "cfia-airs", "gac-sanctions"],
        "evidence_track": ["dated trade-data row", "selected product family", "origin country", "buyer/importer lead evidence if available"],
        "gate_track": ["no best-product claim", "no demand claim", "no buyer validation", "no import approval"],
    },
    {
        "flow_id": "browse_canada_exports",
        "label": "Browse goods Canada exports",
        "plain_language_goal": "Help a Canadian exporter explore product families and destination markets safely.",
        "build_track": ["show Canada export category families", "show destination research routes", "create export starter packet"],
        "research_track": ["Canada export trade data", "export controls", "destination-country source pack", "market access comparison"],
        "source_track": ["ised-trade-data-online", "canada-trade-commissioner-export-guide", "gac-export-controls", "itc-market-access-map"],
        "evidence_track": ["dated export-data row", "destination country", "product identity", "controlled-goods screen"],
        "gate_track": ["no export-ready claim", "no destination approval", "no demand or profit claim"],
    },
    {
        "flow_id": "compare_origin_lanes_to_canada",
        "label": "Compare origin countries into Canada",
        "plain_language_goal": "Show which origin-country lanes need official source and evidence checks before a user commits.",
        "build_track": ["show country lanes", "show source coverage level", "show missing evidence", "route to packet"],
        "research_track": ["partner-country trade rows", "sanctions/restricted-country checks", "origin export rules", "Canadian import rules"],
        "source_track": ["ised-trade-data-online", "gac-sanctions", "world-bank-wits", "itc-trade-map"],
        "evidence_track": ["country selected", "product family selected", "source routes checked", "supplier evidence if known"],
        "gate_track": ["no country recommendation", "no sanctions clearance", "no supplier verification"],
    },
    {
        "flow_id": "check_regulated_goods_early",
        "label": "Check if goods may be regulated",
        "plain_language_goal": "Warn users early when food, plant, animal, seafood, health, chemical, or controlled goods need review.",
        "build_track": ["regulated-risk tags", "official source route", "document checklist", "expert lane"],
        "research_track": ["CFIA AIRS", "CBSA import workflow", "Global Affairs controls", "destination regulations"],
        "source_track": ["cfia-airs", "cbsa-import-commercial-goods", "gac-import-controls", "gac-export-controls"],
        "evidence_track": ["product description", "intended use", "ingredient/material details", "certificates if available"],
        "gate_track": ["no CFIA approval", "no import/export permission", "no legal advice"],
    },
    {
        "flow_id": "prepare_buyer_questions",
        "label": "Prepare buyer questions",
        "plain_language_goal": "Help an exporter ask a potential buyer/importer the right readiness questions.",
        "build_track": ["buyer question set", "importer-of-record prompt", "Incoterms prompt", "evidence ladder"],
        "research_track": ["Canadian importer leads", "responsibility path", "buyer evidence ladder"],
        "source_track": ["canada-cid", "icc-incoterms-2020", "cbsa-import-commercial-goods"],
        "evidence_track": ["buyer reply", "meeting notes", "sample request", "LOI or PO if available"],
        "gate_track": ["no buyer validation", "no purchase intent unless evidence attached"],
    },
    {
        "flow_id": "prepare_supplier_questions",
        "label": "Prepare supplier questions",
        "plain_language_goal": "Help an importer or exporter request evidence from a supplier before relying on them.",
        "build_track": ["supplier evidence checklist", "document request", "risk questions", "reviewer packet"],
        "research_track": ["origin-country export rules", "company registry route", "product certificate route"],
        "source_track": ["india-dgft-foreign-trade-policy", "vietnam-customs-portal", "world-bank-wits"],
        "evidence_track": ["registration", "export ability", "product spec", "certificate", "inspection report"],
        "gate_track": ["no supplier verification", "no authenticity claim"],
    },
    {
        "flow_id": "create_no_document_starter_packet",
        "label": "Create a starter packet without documents",
        "plain_language_goal": "Turn early browsing into a useful packet even when the user has no files.",
        "build_track": ["starter packet", "missing evidence list", "source map", "next safe move"],
        "research_track": ["product family", "origin/destination", "regulated suspicion", "buyer/supplier known flags"],
        "source_track": ["wco-harmonized-system", "ised-trade-data-online", "cbsa-import-commercial-goods", "cfia-airs"],
        "evidence_track": ["user input", "source reference", "blocked claims", "review lane if needed"],
        "gate_track": ["no document authenticity claim", "no market conclusion", "no approval"],
    },
    {
        "flow_id": "route_to_expert_or_broker",
        "label": "Prepare for expert or broker review",
        "plain_language_goal": "Package the unresolved questions so a broker, trade consultant, or reviewer can answer the exact scope.",
        "build_track": ["broker questions", "review scope", "source citations", "blocked claims"],
        "research_track": ["broker boundary", "country source pack", "document requirements", "claim-language limits"],
        "source_track": ["cbsa-licensed-customs-brokers", "cbsa-import-commercial-goods", "cbsa-customs-tariff-2026", "cfia-airs"],
        "evidence_track": ["review request", "source snapshots", "documents", "expert finding"],
        "gate_track": ["reviewer can approve only exact scoped language", "no product-wide approval"],
    },
)

CATEGORY_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "category_id": "food_agri_seafood",
        "label": "Food, agriculture, and seafood",
        "plain_language_examples": ["packaged foods", "spices", "frozen seafood", "grains", "fresh produce"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 1-24 often need detailed product and ingredient review.",
        "source_routes": ["ised-trade-data-online", "cfia-airs", "cbsa-import-commercial-goods", "canada-cid"],
        "regulated_risk_tags": ["food", "plant", "animal", "seafood", "labeling"],
        "starter_questions": ["What exactly is the product?", "Is it for human consumption?", "Is it fresh, frozen, canned, dried, or processed?", "Who will be importer of record?"],
    },
    {
        "category_id": "apparel_textiles",
        "label": "Apparel and textiles",
        "plain_language_examples": ["garments", "fabric", "home textiles", "footwear accessories"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 50-63 commonly need material composition and origin evidence.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "canada-cid", "itc-market-access-map"],
        "regulated_risk_tags": ["origin", "labeling", "material_composition"],
        "starter_questions": ["What is the fibre composition?", "Is the supplier able to provide origin documents?", "Is the buyer asking for private-label packaging?"],
    },
    {
        "category_id": "home_furniture_goods",
        "label": "Furniture and home goods",
        "plain_language_examples": ["wood furniture", "decor", "kitchenware", "lighting"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 44, 70, 94, and related chapters may apply depending on material and use.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "canada-cid"],
        "regulated_risk_tags": ["wood_material", "consumer_product_safety", "packaging"],
        "starter_questions": ["What materials are used?", "Does it contain wood, electrical parts, or chemicals?", "What documents can the supplier provide?"],
    },
    {
        "category_id": "machinery_parts_tools",
        "label": "Machinery, tools, and industrial parts",
        "plain_language_examples": ["machine parts", "tools", "pumps", "industrial fittings"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 82, 84, and related chapters often need technical specs.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "itc-market-access-map"],
        "regulated_risk_tags": ["technical_specification", "standards", "controlled_goods_check"],
        "starter_questions": ["What is the end use?", "Can the supplier provide technical datasheets?", "Is the buyer asking for certification?"],
    },
    {
        "category_id": "electronics_components",
        "label": "Electronics and components",
        "plain_language_examples": ["consumer electronics", "cables", "components", "small appliances"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 85 and related chapters often need product specs and safety/standards review.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "itc-market-access-map", "gac-export-controls"],
        "regulated_risk_tags": ["electrical_safety", "controlled_goods_check", "battery_or_radio"],
        "starter_questions": ["Does it include batteries or wireless features?", "What certifications are available?", "What is the destination end use?"],
    },
    {
        "category_id": "automotive_parts",
        "label": "Automotive parts",
        "plain_language_examples": ["replacement parts", "vehicle accessories", "rubber parts", "filters"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 40, 84, 85, 87, and related chapters may apply.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "itc-market-access-map"],
        "regulated_risk_tags": ["standards", "safety", "origin"],
        "starter_questions": ["Is it OEM or aftermarket?", "Does it affect safety?", "Can the supplier provide product specs and origin evidence?"],
    },
    {
        "category_id": "health_beauty_cosmetics",
        "label": "Health, beauty, and cosmetics",
        "plain_language_examples": ["cosmetics", "personal care", "supplements", "medical-adjacent products"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 30, 33, and related chapters may need health/regulatory review.",
        "source_routes": ["ised-trade-data-online", "cfia-airs", "cbsa-import-commercial-goods", "itc-market-access-map"],
        "regulated_risk_tags": ["health_claims", "ingredients", "labeling", "regulated_product_suspicion"],
        "starter_questions": ["Does the product make health claims?", "What are the ingredients?", "Is it cosmetic, food, supplement, or medical?"],
    },
    {
        "category_id": "chemicals_cleaning_materials",
        "label": "Chemicals, cleaning products, and materials",
        "plain_language_examples": ["cleaners", "industrial chemicals", "paints", "adhesives"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 28-38 can require chemical identity and safety data sheets.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "gac-import-controls", "gac-export-controls"],
        "regulated_risk_tags": ["dangerous_goods", "sds_required", "controlled_goods_check"],
        "starter_questions": ["What is the chemical composition?", "Is there an SDS?", "Is it hazardous or controlled?"],
    },
    {
        "category_id": "building_materials",
        "label": "Building materials",
        "plain_language_examples": ["tiles", "stone", "fixtures", "metal products", "wood products"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 25, 44, 68-83, and related chapters may apply.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "canada-cid"],
        "regulated_risk_tags": ["wood_material", "standards", "origin"],
        "starter_questions": ["What material is it made of?", "Is it structural or decorative?", "Can the supplier provide specs and origin evidence?"],
    },
    {
        "category_id": "packaging_paper_printed_goods",
        "label": "Packaging, paper, and printed goods",
        "plain_language_examples": ["paper packaging", "labels", "cartons", "printed inserts"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 48-49 often depend on paper type and printed content.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "canada-cid"],
        "regulated_risk_tags": ["food_contact", "labeling", "material_spec"],
        "starter_questions": ["Will it touch food?", "Is it printed or blank?", "What material and coating are used?"],
    },
    {
        "category_id": "metals_minerals_raw_materials",
        "label": "Metals, minerals, and raw materials",
        "plain_language_examples": ["ores", "metal products", "scrap", "stone", "industrial inputs"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapters 25-27 and 72-83 may apply depending on material and form.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "itc-market-access-map", "gac-export-controls"],
        "regulated_risk_tags": ["origin", "controlled_goods_check", "environmental_or_safety"],
        "starter_questions": ["What is the material composition?", "Is it raw, semi-finished, or finished?", "Are controls or permits possible?"],
    },
    {
        "category_id": "general_consumer_goods",
        "label": "General consumer goods",
        "plain_language_examples": ["toys", "sports goods", "bags", "stationery", "gift items"],
        "directions": ["import_into_canada", "export_from_canada"],
        "hs_hint": "HS Chapter depends on material, function, and end use.",
        "source_routes": ["ised-trade-data-online", "cbsa-customs-tariff-2026", "canada-cid"],
        "regulated_risk_tags": ["consumer_safety", "labeling", "material_spec"],
        "starter_questions": ["Who will use it?", "What material is it made of?", "Does it touch food, children, skin, or electricity?"],
    },
    {
        "category_id": "services_not_merchandise_scope",
        "label": "Services and digital products",
        "plain_language_examples": ["software services", "consulting", "digital subscriptions"],
        "directions": ["explore_only"],
        "hs_hint": "Merchandise HS and customs-document flows may not apply.",
        "source_routes": ["canada-trade-commissioner-export-guide"],
        "regulated_risk_tags": ["out_of_merchandise_scope", "tax_privacy_contract_review"],
        "starter_questions": ["Is there any physical good crossing a border?", "Is the issue tax, privacy, contract, or market access instead?"],
    },
)

COUNTRY_LANES: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "IN-to-CA",
        "origin_country": "India",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "India origin pack is the next explicit product strategy lane.",
        "common_research_categories": ["food_agri_seafood", "apparel_textiles", "home_furniture_goods", "general_consumer_goods"],
        "source_routes": ["india-dgft-foreign-trade-policy", "ised-trade-data-online", "canada-cid", "cbsa-import-commercial-goods", "cfia-airs"],
    },
    {
        "lane_id": "VN-to-CA",
        "origin_country": "Vietnam",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Vietnam remains the proof/demo origin for seafood and general goods examples.",
        "common_research_categories": ["food_agri_seafood", "apparel_textiles", "home_furniture_goods"],
        "source_routes": ["vietnam-customs-portal", "ised-trade-data-online", "canada-cid", "cbsa-import-commercial-goods", "cfia-airs"],
    },
    {
        "lane_id": "US-to-CA",
        "origin_country": "United States",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Neighbouring-country lane useful for baseline Canada import comparison.",
        "common_research_categories": ["machinery_parts_tools", "automotive_parts", "electronics_components", "food_agri_seafood"],
        "source_routes": ["ised-trade-data-online", "cbsa-import-commercial-goods", "cbsa-customs-tariff-2026", "canada-cid"],
    },
    {
        "lane_id": "MX-to-CA",
        "origin_country": "Mexico",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "North American lane useful for agri, auto, industrial, and consumer-goods comparison.",
        "common_research_categories": ["food_agri_seafood", "automotive_parts", "machinery_parts_tools"],
        "source_routes": ["ised-trade-data-online", "cbsa-import-commercial-goods", "itc-market-access-map", "canada-cid"],
    },
    {
        "lane_id": "CN-to-CA",
        "origin_country": "China",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Broad manufacturing lane that needs careful source, supplier, standards, and sanctions checks.",
        "common_research_categories": ["electronics_components", "home_furniture_goods", "general_consumer_goods", "machinery_parts_tools"],
        "source_routes": ["ised-trade-data-online", "canada-cid", "cbsa-import-commercial-goods", "gac-sanctions"],
    },
    {
        "lane_id": "BD-to-CA",
        "origin_country": "Bangladesh",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Textile/apparel lane that needs origin, supplier, and documentation checks.",
        "common_research_categories": ["apparel_textiles"],
        "source_routes": ["ised-trade-data-online", "canada-cid", "cbsa-customs-tariff-2026", "itc-market-access-map"],
    },
    {
        "lane_id": "TR-to-CA",
        "origin_country": "Turkey",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Textiles, food, furniture, and industrial-goods lane for source-backed exploration.",
        "common_research_categories": ["apparel_textiles", "food_agri_seafood", "home_furniture_goods", "machinery_parts_tools"],
        "source_routes": ["ised-trade-data-online", "canada-cid", "itc-market-access-map"],
    },
    {
        "lane_id": "BR-to-CA",
        "origin_country": "Brazil",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Food, agri, minerals, and materials lane that needs CFIA/source routing when relevant.",
        "common_research_categories": ["food_agri_seafood", "metals_minerals_raw_materials"],
        "source_routes": ["ised-trade-data-online", "cfia-airs", "canada-cid", "world-bank-wits"],
    },
    {
        "lane_id": "EU-to-CA",
        "origin_country": "European Union",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Regional lane for market access, standards, origin, and supplier-document comparison.",
        "common_research_categories": ["health_beauty_cosmetics", "machinery_parts_tools", "food_agri_seafood"],
        "source_routes": ["ised-trade-data-online", "itc-market-access-map", "canada-cid", "cbsa-import-commercial-goods"],
    },
    {
        "lane_id": "UK-to-CA",
        "origin_country": "United Kingdom",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Country lane for packaged food, consumer goods, and industrial comparison.",
        "common_research_categories": ["food_agri_seafood", "general_consumer_goods", "machinery_parts_tools"],
        "source_routes": ["ised-trade-data-online", "itc-market-access-map", "canada-cid"],
    },
    {
        "lane_id": "UAE-to-CA",
        "origin_country": "United Arab Emirates",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Trading-hub lane that needs supplier/origin evidence before relying on source country claims.",
        "common_research_categories": ["general_consumer_goods", "metals_minerals_raw_materials", "electronics_components"],
        "source_routes": ["ised-trade-data-online", "world-bank-wits", "gac-sanctions", "canada-cid"],
    },
    {
        "lane_id": "CA-to-US",
        "origin_country": "Canada",
        "destination_country": "United States",
        "direction": "export_from_canada",
        "why_user_might_browse": "Export-from-Canada comparison lane for nearby destination-market exploration.",
        "common_research_categories": ["food_agri_seafood", "machinery_parts_tools", "automotive_parts", "building_materials"],
        "source_routes": ["ised-trade-data-online", "canada-trade-commissioner-export-guide", "gac-export-controls", "itc-market-access-map"],
    },
    {
        "lane_id": "CA-to-EU",
        "origin_country": "Canada",
        "destination_country": "European Union",
        "direction": "export_from_canada",
        "why_user_might_browse": "Export-from-Canada regional lane for market-access and destination-rule research.",
        "common_research_categories": ["food_agri_seafood", "machinery_parts_tools", "health_beauty_cosmetics"],
        "source_routes": ["ised-trade-data-online", "canada-trade-commissioner-export-guide", "itc-market-access-map", "gac-export-controls"],
    },
    {
        "lane_id": "GENERIC-to-CA",
        "origin_country": "Generic or unsupported country",
        "destination_country": "Canada",
        "direction": "import_into_canada",
        "why_user_might_browse": "Fallback lane when a country pack is not yet supported.",
        "common_research_categories": ["general_consumer_goods", "food_agri_seafood", "machinery_parts_tools"],
        "source_routes": ["ised-trade-data-online", "world-bank-wits", "itc-trade-map", "cbsa-import-commercial-goods", "gac-sanctions"],
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


def _source_route(source_id: str, source_by_id: dict[str, dict[str, Any]], use: str) -> dict[str, Any]:
    source = source_by_id.get(source_id, {})
    fact = next((row for row in DISCOVERY_SOURCE_FACTS if row["source_id"] == source_id), {})
    return {
        "source_id": source_id,
        "name": source.get("name", source_id),
        "url": source.get("url", ""),
        "jurisdiction": source.get("jurisdiction", ""),
        "source_area": fact.get("source_area", "source_route"),
        "use": use,
        "registry_status": "registered" if source else "missing_from_registry",
        "automation_status": "manual_or_terms_checked_connector_required",
        "evidence_required_before_claim": True,
        "claim_boundary": fact.get("claim_boundary") or source.get("claim_boundary", "Reference route only; claims remain blocked."),
    }


def _category_record(row: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    routes = [_source_route(source_id, source_by_id, "category_discovery") for source_id in row["source_routes"]]
    return {
        **row,
        "status": "category_research_route_ready",
        "source_routes": routes,
        "source_route_count": len(routes),
        "dataset_values_loaded": False,
        "recommendation_claimed": False,
        "can_claim_opportunity": False,
        "can_claim_demand": False,
        "can_claim_profitability": False,
        "blocked_claims": list(DISCOVERY_BLOCKED_CLAIMS),
        "claim_boundary": "This category can be browsed and routed to sources; it is not a recommendation or market conclusion.",
        "next_valid_move": "Pick a product family, origin/destination, and source route, then create a starter packet with evidence gaps.",
    }


def _country_lane_record(row: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    routes = [_source_route(source_id, source_by_id, "country_lane_discovery") for source_id in row["source_routes"]]
    return {
        **row,
        "status": "country_lane_research_route_ready",
        "coverage_level": "reference_only" if row["lane_id"] != "GENERIC-to-CA" else "generic",
        "source_routes": routes,
        "source_route_count": len(routes),
        "trade_values_loaded": False,
        "recommendation_claimed": False,
        "can_claim_country_is_best": False,
        "can_claim_sanctions_clearance": False,
        "can_claim_supplier_verified": False,
        "blocked_claims": list(DISCOVERY_BLOCKED_CLAIMS),
        "claim_boundary": "Lane is a research route only; country choice, supplier proof, and compliance remain evidence-gated.",
        "next_valid_move": "Attach dated trade rows, supplier/buyer evidence, and source snapshots before using this lane externally.",
    }


def _beginner_flow_record(row: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    routes = [_source_route(source_id, source_by_id, "beginner_flow") for source_id in row["source_track"]]
    return {
        **row,
        "status": "beginner_flow_ready_local_source_routed",
        "source_routes": routes,
        "source_route_count": len(routes),
        "creates_external_effects": False,
        "recommendation_claimed": False,
        "opens_claims": False,
        "blocked_claims": list(DISCOVERY_BLOCKED_CLAIMS),
        "safe_user_copy": "Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.",
    }


def _source_registry_records(source_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for fact in DISCOVERY_SOURCE_FACTS:
        route = _source_route(fact["source_id"], source_by_id, "trade_discovery_source_registry")
        rows.append(
            {
                **fact,
                "name": route["name"],
                "url": route["url"],
                "registry_status": route["registry_status"],
                "automation_status": route["automation_status"],
                "evidence_required_before_claim": True,
            }
        )
    return rows


def _requirement_audit() -> dict[str, Any]:
    return {
        "status": "gap_closed_for_local_research_routed_discovery",
        "audited_gap": "Existing market intelligence starts after a product/packet exists; beginner users also need product, country, and import/export browsing before packet creation.",
        "implemented_now": [
            "beginner import/export discovery flows",
            "Canada import and export source routes",
            "diverse origin-to-Canada country lanes",
            "category-family map with regulated-risk warnings",
            "dataset route records with no invented values",
            "claim gates that block recommendations, demand, profitability, buyer validation, supplier verification, customs/CFIA approval, and shipment readiness",
        ],
        "still_external_or_data_gated": [
            "dated trade dataset ingestion",
            "automated connector terms/licensing review",
            "real buyer replies or orders",
            "real supplier evidence review",
            "qualified customs/trade review",
            "hosted UX testing with business owners",
        ],
    }


def build_production_trade_discovery_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    sources = _load_json(root / "data" / "official_source_registry.json", [])
    source_by_id = _source_registry_by_id(sources)
    categories = [_category_record(dict(row), source_by_id) for row in CATEGORY_FAMILIES]
    country_lanes = [_country_lane_record(dict(row), source_by_id) for row in COUNTRY_LANES]
    beginner_flows = [_beginner_flow_record(dict(row), source_by_id) for row in BEGINNER_FLOWS]
    source_records = _source_registry_records(source_by_id)
    dataset_routes = [
        {
            **dict(row),
            "source_route": _source_route(row["source_id"], source_by_id, "dataset_route"),
            "external_effects_created": False,
            "claims_opened": False,
        }
        for row in DATASET_ROUTES
    ]
    missing_registry_sources = sorted(
        {row["source_id"] for row in DISCOVERY_SOURCE_FACTS if row["source_id"] not in source_by_id}
    )
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "purpose": "Pre-packet beginner trade discovery for users who do not yet know which product, lane, or source route to research.",
        "requirement_audit": _requirement_audit(),
        "source_record_count": len(source_records),
        "dataset_route_count": len(dataset_routes),
        "category_count": len(categories),
        "country_lane_count": len(country_lanes),
        "beginner_flow_count": len(beginner_flows),
        "source_route_count": sum(row["source_route_count"] for row in categories + country_lanes + beginner_flows),
        "source_records": source_records,
        "dataset_routes": dataset_routes,
        "category_families": categories,
        "country_lanes": country_lanes,
        "beginner_flows": beginner_flows,
        "missing_registry_sources": missing_registry_sources,
        "blocked_claims": list(DISCOVERY_BLOCKED_CLAIMS),
        "recommendation_claimed": False,
        "market_opportunity_claimed": False,
        "demand_claimed": False,
        "profitability_claimed": False,
        "buyer_validation_claimed": False,
        "supplier_verification_claimed": False,
        "customs_approval_claimed": False,
        "cfia_approval_claimed": False,
        "public_launch_ready": False,
        "external_effects_created": False,
        "claims_opened": False,
        "next_valid_move": "Use discovery to choose a product family and lane, then create a starter packet and attach dated source/evidence rows.",
        "proof_boundary": (
            "Trade discovery is browse-and-prepare logic. It can show source-routed categories, country lanes, questions, and evidence gaps. "
            "It cannot tell a user what product is best, prove demand, confirm profit, validate buyers, verify suppliers, approve customs/CFIA status, or make shipment decisions."
        ),
    }


def render_trade_discovery_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Trade Discovery Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Requirement Audit",
        "",
        payload["requirement_audit"]["audited_gap"],
        "",
        "## Beginner Flows",
        "",
    ]
    for flow in payload["beginner_flows"]:
        lines.extend(
            [
                f"### {flow['label']}",
                "",
                flow["plain_language_goal"],
                "",
                f"- Source routes: {flow['source_route_count']}",
                "- Recommendation claimed: false",
                "- Claims opened: false",
                f"- Safe copy: {flow['safe_user_copy']}",
                "",
            ]
        )
    lines.extend(["## Category Families", ""])
    for category in payload["category_families"]:
        lines.append(
            f"- `{category['category_id']}`: {category['label']} "
            f"({category['source_route_count']} source routes; opportunity claim false)."
        )
    lines.extend(["", "## Country Lanes", ""])
    for lane in payload["country_lanes"]:
        lines.append(
            f"- `{lane['lane_id']}`: {lane['origin_country']} to {lane['destination_country']} "
            f"as `{lane['direction']}` ({lane['coverage_level']}; recommendation false)."
        )
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            "- Best product claim: false",
            "- Market opportunity claim: false",
            "- Demand claim: false",
            "- Profitability claim: false",
            "- Buyer validation claim: false",
            "- Supplier verification claim: false",
            "- Customs/CFIA approval claim: false",
            "- Public launch ready: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_trade_discovery_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_trade_discovery_manifest.json"
    categories_path = graph / "production_trade_discovery_category_map.json"
    lanes_path = graph / "production_trade_discovery_country_lanes.json"
    flows_path = graph / "production_trade_discovery_beginner_flows.json"
    sources_path = graph / "production_trade_discovery_source_registry.json"
    audit_path = graph / "production_trade_discovery_requirement_audit.json"
    doc_path = docs / "PRODUCTION_TRADE_DISCOVERY_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    categories_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_trade_discovery_categories_ready_source_routed",
                "category_count": payload["category_count"],
                "category_families": payload["category_families"],
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    lanes_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_trade_discovery_country_lanes_ready_reference_only",
                "country_lane_count": payload["country_lane_count"],
                "country_lanes": payload["country_lanes"],
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    flows_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_trade_discovery_beginner_flows_ready",
                "beginner_flow_count": payload["beginner_flow_count"],
                "beginner_flows": payload["beginner_flows"],
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    sources_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_trade_discovery_sources_registered",
                "source_record_count": payload["source_record_count"],
                "dataset_route_count": payload["dataset_route_count"],
                "source_records": payload["source_records"],
                "dataset_routes": payload["dataset_routes"],
                "missing_registry_sources": payload["missing_registry_sources"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    audit_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": payload["requirement_audit"]["status"],
                "requirement_audit": payload["requirement_audit"],
                "proof_boundary": payload["proof_boundary"],
                "blocked_claims": payload["blocked_claims"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_trade_discovery_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "categories": categories_path,
        "country_lanes": lanes_path,
        "beginner_flows": flows_path,
        "sources": sources_path,
        "audit": audit_path,
        "doc": doc_path,
    }
