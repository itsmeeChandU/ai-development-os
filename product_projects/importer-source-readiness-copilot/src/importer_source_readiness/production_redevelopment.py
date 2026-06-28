"""Production redevelopment contract for Trade Readiness Copilot.

This module turns the full-scale redevelopment brief into a machine-checkable
product surface. It preserves the current business-rule engine as the reference
logic while defining the production layers, entities, services, APIs, gates,
and research anchors needed for a real SaaS rebuild.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


TODAY = date(2026, 6, 28).isoformat()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _layer(layer_id: int, name: str, purpose: str, current_basis: list[str], production_outputs: list[str]) -> dict[str, Any]:
    return {
        "layer_id": layer_id,
        "name": name,
        "purpose": purpose,
        "current_basis": current_basis,
        "production_outputs": production_outputs,
        "status": "production_layer_contract_ready",
    }


def build_production_layers() -> list[dict[str, Any]]:
    return [
        _layer(1, "Product doctrine", "Lock what the product is and is not.", ["PRODUCT_DOCTRINE.md", "business_identity_lock"], ["claim boundary policy", "commercial wedge statement"]),
        _layer(2, "Domain model", "Make all product behavior map to durable entities.", ["Trade Readiness Packet contract", "field provenance"], ["production ERD", "type contracts", "migration map"]),
        _layer(3, "Data platform", "Move JSON/SQLite proof into governed production persistence.", ["customer_workflow.sqlite", "generated JSON artifacts"], ["Postgres schema", "object storage contract", "source lineage tables"]),
        _layer(4, "Workflow engine", "Run packets through explicit lifecycle states and review gates.", ["packet stages", "product operations log"], ["packet state machine", "domain events", "work queues"]),
        _layer(5, "Country-pack engine", "Scale country-specific routing and claim boundaries.", ["Canada/Vietnam/India/Generic packs"], ["country pack registry", "coverage levels", "reviewer requirements"]),
        _layer(6, "Source intelligence engine", "Track official-source permissions, freshness, diffs, and packet impact.", ["source monitoring contract", "policy monitor"], ["source snapshots", "diff classifier", "stale packet logic"]),
        _layer(7, "Market intelligence engine", "Produce source-backed research signals without demand claims.", ["bounded market signal score"], ["trade data signals", "market access comparison", "buyer/importer lead routes"]),
        _layer(8, "Evidence and document intelligence engine", "Extract, confirm, and govern evidence from files.", ["document processing", "evidence ledger"], ["upload pipeline", "field extraction", "user confirmation trail"]),
        _layer(9, "Decision and rules engine", "Explain capped scores and blocked claims.", ["six business scores", "business gate decision"], ["claim gate engine", "score reason contract", "next action rules"]),
        _layer(10, "AI copilot layer", "Use AI for assistance, never approval.", ["AI data policy", "model router", "manual no-AI workflow"], ["AI output labels", "redaction checks", "review work-order drafting"]),
        _layer(11, "Expert review network", "Turn human review into product workflow.", ["reviewer lanes", "expert work orders"], ["reviewer profiles", "scoped links", "finding decisions"]),
        _layer(12, "User portals", "Give each user type a complete workflow.", ["public tools", "workspace", "review routes", "admin routes"], ["public/exporter/importer/reviewer/admin/enterprise portals"]),
        _layer(13, "Enterprise platform", "Support firms, teams, clients, APIs, audit, and retention controls.", ["auth/RBAC matrix", "team workspace", "agent API"], ["organizations", "workspaces", "API keys", "audit exports"]),
        _layer(14, "Production operations and go-live system", "Operate only approved scopes with observable controls.", ["launch operations", "final go-live report"], ["environment control plane", "approval gates", "incident and rollback runbooks"]),
    ]


def build_domain_entities() -> list[dict[str, Any]]:
    entities = [
        ("Organization", ["organization_id", "name", "billing_account_id", "retention_policy_id"]),
        ("User", ["user_id", "organization_id", "email", "status"]),
        ("Role", ["role_id", "organization_id", "permissions"]),
        ("Workspace", ["workspace_id", "organization_id", "name", "client_id"]),
        ("TradeReadinessPacket", ["packet_id", "workspace_id", "trade_lane_id", "state", "claim_boundary_status"]),
        ("TradeLane", ["trade_lane_id", "origin_country", "destination_country", "direction", "incoterm_id"]),
        ("ProductProfile", ["product_profile_id", "packet_id", "name", "category", "intended_use"]),
        ("CountryPack", ["country_pack_id", "country_code", "direction", "coverage_level", "reviewer_required"]),
        ("SourceRecord", ["source_id", "country_pack_id", "canonical_url", "source_type", "allowed_use"]),
        ("SourceSnapshot", ["snapshot_id", "source_id", "content_hash", "fetched_at", "diff_status"]),
        ("EvidenceItem", ["evidence_id", "packet_id", "type", "provenance", "confidence", "freshness"]),
        ("Document", ["document_id", "packet_id", "storage_key", "quarantine_status", "classification"]),
        ("ExtractedField", ["field_id", "document_id", "field_name", "value", "confidence", "confirmation_status"]),
        ("FieldProvenance", ["field_id", "mode", "source_reference", "reviewer_id"]),
        ("BuyerProfile", ["buyer_profile_id", "packet_id", "evidence_level", "claim_status"]),
        ("SupplierProfile", ["supplier_profile_id", "packet_id", "evidence_level", "claim_status"]),
        ("ResponsibilityPath", ["responsibility_path_id", "packet_id", "importer_of_record", "incoterms", "warnings"]),
        ("IncotermRecord", ["incoterm_id", "code", "responsibility_summary", "confirmation_status"]),
        ("MarketSignal", ["market_signal_id", "packet_id", "signal_level", "confidence", "source_refs"]),
        ("OpportunitySignal", ["opportunity_signal_id", "packet_id", "research_signal", "claim_boundary"]),
        ("BlockedClaim", ["blocked_claim_id", "packet_id", "claim", "reason", "required_evidence"]),
        ("DecisionScore", ["score_id", "packet_id", "score_name", "label", "reason", "next_action"]),
        ("ReviewerLane", ["reviewer_lane_id", "scope", "required_credentials", "gate_can_open"]),
        ("ReviewRequest", ["review_request_id", "packet_id", "reviewer_lane_id", "status", "scope"]),
        ("ReviewFinding", ["finding_id", "review_request_id", "severity", "decision", "required_changes"]),
        ("Report", ["report_id", "packet_id", "report_type", "watermark", "version"]),
        ("AuditEvent", ["audit_event_id", "actor_id", "event_type", "packet_id", "created_at"]),
        ("BillingAccount", ["billing_account_id", "organization_id", "processor_customer_id", "live_mode_enabled"]),
        ("Subscription", ["subscription_id", "billing_account_id", "tier", "status"]),
        ("UsageRecord", ["usage_record_id", "billing_account_id", "meter", "quantity", "external_charge_created"]),
        ("ResearchIntake", ["research_intake_id", "phase", "question", "required_depth", "owner"]),
        ("SourceRegistry", ["source_registry_id", "source_id", "source_area", "authority_level", "allowed_use"]),
        ("DatasetConnector", ["dataset_connector_id", "source_id", "access_mode", "license_status", "credential_status"]),
        ("CountryPackSource", ["country_pack_source_id", "country_pack_id", "source_id", "source_area", "claim_boundary"]),
        ("MarketSignalSource", ["market_signal_source_id", "market_signal_id", "source_id", "metric", "limitation"]),
        ("LegalBoundarySource", ["legal_boundary_source_id", "claim", "source_id", "required_reviewer_lane"]),
        ("ExpertFindingSource", ["expert_finding_source_id", "finding_id", "source_id", "review_scope"]),
        ("EvidenceMapper", ["evidence_mapper_id", "evidence_id", "supports_claim", "blocks_claim"]),
        ("ClaimGateMapper", ["claim_gate_mapper_id", "claim_type", "required_evidence", "required_source_ids", "required_reviewer_lane"]),
    ]
    return [
        {
            "entity": entity,
            "required_fields": fields,
            "production_status": "schema_contract_ready",
        }
        for entity, fields in entities
    ]


def build_service_boundaries() -> list[dict[str, Any]]:
    services = [
        ("Packet service", "/app/packets", ["TradeReadinessPacket", "TradeLane", "ProductProfile"], ["create packet", "update packet", "export views"]),
        ("Evidence service", "/app/evidence", ["EvidenceItem", "BlockedClaim"], ["evidence ledger", "claim support map"]),
        ("Document intelligence service", "/app/documents", ["Document", "ExtractedField"], ["quarantine", "extract", "confirm fields"]),
        ("Source intelligence service", "/app/sources", ["SourceRecord", "SourceSnapshot"], ["permission check", "snapshot", "diff", "packet stale logic"]),
        ("Market intelligence service", "/app/market_intelligence", ["MarketSignal", "OpportunitySignal"], ["trade data signal", "market access comparison"]),
        ("Country-pack service", "/app/country_packs", ["CountryPack"], ["coverage levels", "source routing"]),
        ("Decision/rules engine", "/app/decision_engine", ["DecisionScore", "BlockedClaim"], ["score caps", "safe next moves"]),
        ("AI orchestration service", "/app/ai", ["AuditEvent", "EvidenceItem"], ["safe summary", "draft extraction", "review work order"]),
        ("Expert review service", "/app/reviews", ["ReviewerLane", "ReviewRequest", "ReviewFinding"], ["queue", "finding submission", "claim gate update"]),
        ("Report generation service", "/app/reports", ["Report"], ["HTML preview", "PDF export", "JSON export"]),
        ("Billing/entitlement service", "/app/billing", ["BillingAccount", "Subscription", "UsageRecord"], ["quote", "entitlement", "usage reservation"]),
        ("Audit/compliance service", "/app/audit", ["AuditEvent"], ["audit trail", "retention", "incident export"]),
    ]
    return [
        {
            "service": service,
            "module_path": module_path,
            "owns_entities": owns_entities,
            "responsibilities": responsibilities,
            "architecture_choice": "modular_monolith_first",
        }
        for service, module_path, owns_entities, responsibilities in services
    ]


def build_packet_state_machine() -> dict[str, Any]:
    states = [
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
    ]
    return {
        "status": "packet_state_machine_contract_ready",
        "state_count": len(states),
        "states": states,
        "terminal_states": ["paid_packet_ready", "archived"],
        "claim_rule": "State progress never opens customs, tariff, buyer, supplier, shipment, legal, payment, or public-launch claims without evidence gates.",
    }


def build_research_anchors() -> list[dict[str, Any]]:
    return [
        {
            "id": "ised-trade-data-online",
            "source_name": "ISED Trade Data Online",
            "url": "https://ised-isde.canada.ca/site/trade-data-online/en/overview",
            "checked_on": TODAY,
            "supports_phases": [4, 5],
            "source_area": "Canada market intelligence",
            "usable_fact": "Trade Data Online is the Canada trade data route for import/export market and competition research.",
            "claim_boundary": "Supports research routing only; it does not validate buyer demand or profitability.",
        },
        {
            "id": "itc-market-access-map",
            "source_name": "International Trade Centre Market Access Map",
            "url": "https://www.macmap.org/",
            "checked_on": TODAY,
            "supports_phases": [4, 5],
            "source_area": "Market access comparison",
            "usable_fact": "Market Access Map is the market-access route for tariffs, trade measures, regulatory requirements, and preference comparisons.",
            "claim_boundary": "Supports market-access comparison routing only; qualified review is required before tariff or market-access claims.",
        },
        {
            "id": "cbsa-import-commercial-goods",
            "source_name": "Canada Border Services Agency commercial import guidance",
            "url": "https://www.cbsa-asfc.gc.ca/import/menu-eng.html",
            "checked_on": TODAY,
            "supports_phases": [0, 5, 7, 20],
            "source_area": "Canada import process",
            "usable_fact": "CBSA is the official routing source for commercial importing topics such as business/import accounts, tariff resources, other government requirements, origin, rulings, and accounting.",
            "claim_boundary": "Routes users to official and qualified review paths; the product does not replace CBSA or a customs professional.",
        },
        {
            "id": "cfia-airs",
            "source_name": "CFIA Automated Import Reference System",
            "url": "https://inspection.canada.ca/en/importing-food-plants-animals/airs",
            "checked_on": TODAY,
            "supports_phases": [0, 5, 20],
            "source_area": "CFIA regulated food, plant, animal",
            "usable_fact": "AIRS is the CFIA reference route for food, plant, animal, and regulated-commodity import requirements.",
            "claim_boundary": "Reference route only; importers and reviewers must confirm current requirements for the exact product and import time.",
        },
        {
            "id": "owasp-file-upload",
            "source_name": "OWASP File Upload Cheat Sheet",
            "url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
            "checked_on": TODAY,
            "supports_phases": [10, 19],
            "source_area": "Upload security",
            "usable_fact": "File-upload security needs defense in depth: extension/type validation, generated filenames, size limits, authorization, isolated storage, malware checks, updated libraries, and CSRF protection.",
            "claim_boundary": "Security implementation guidance; hosted readiness still requires product-specific security review.",
        },
        {
            "id": "nist-ai-rmf",
            "source_name": "NIST AI Risk Management Framework",
            "url": "https://www.nist.gov/itl/ai-risk-management-framework",
            "checked_on": TODAY,
            "supports_phases": [13, 19],
            "source_area": "AI safety",
            "usable_fact": "NIST AI RMF is the AI governance route for trustworthy AI design, development, use, and evaluation.",
            "claim_boundary": "Governance reference only; it does not certify the product or approve AI outputs.",
        },
        {
            "id": "stripe-go-live",
            "source_name": "Stripe go-live checklist",
            "url": "https://docs.stripe.com/get-started/checklist/go-live",
            "checked_on": TODAY,
            "supports_phases": [18, 20],
            "source_area": "Payments",
            "usable_fact": "Payment launch must cover live/test mode differences, API keys, live-mode objects, webhooks, edge cases, logging, and duplicate/delayed/out-of-order events.",
            "claim_boundary": "Payment implementation reference only; live checkout remains disabled until payment review and production setup are complete.",
        },
        {
            "id": "opc-pipeda-principles",
            "source_name": "Office of the Privacy Commissioner of Canada PIPEDA principles",
            "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/",
            "checked_on": TODAY,
            "supports_phases": [19, 20],
            "source_area": "Privacy",
            "usable_fact": "Canada privacy governance should account for accountability, purpose identification, consent, limiting collection/use/retention, safeguards, openness, access, and challenge rights.",
            "claim_boundary": "Privacy design input only; legal/privacy approval requires qualified review for the product and data flows.",
        },
        {
            "id": "cbsa-customs-tariff-2026",
            "source_name": "CBSA Canadian Customs Tariff 2026",
            "url": "https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/2026/menu-eng.html",
            "checked_on": TODAY,
            "supports_phases": [0, 1, 4, 5, 7, 11],
            "source_area": "Canada tariff orientation",
            "usable_fact": "The Canadian Customs Tariff is the source route for Canadian tariff orientation and HS candidate research.",
            "claim_boundary": "Tariff classification and treatment remain blocked until qualified review or authoritative ruling evidence exists.",
        },
        {
            "id": "cbsa-licensed-customs-brokers",
            "source_name": "CBSA Licensed Customs Brokers",
            "url": "https://www.cbsa-asfc.gc.ca/services/cb-cd/cb-cd-eng.html",
            "checked_on": TODAY,
            "supports_phases": [0, 7, 14],
            "source_area": "Broker boundary",
            "usable_fact": "Licensed broker routing is the human-review path for customs broker work and importer responsibility boundaries.",
            "claim_boundary": "The product must not act as a customs broker or imply a broker relationship/signoff.",
        },
        {
            "id": "gac-sanctions",
            "source_name": "Global Affairs Canada sanctions",
            "url": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/index.aspx?lang=eng",
            "checked_on": TODAY,
            "supports_phases": [0, 5, 6, 20],
            "source_area": "Sanctions and restricted countries",
            "usable_fact": "Global Affairs Canada is the sanctions/restricted-country routing source for Canada-focused screening warnings.",
            "claim_boundary": "Sanctions screening claims require dated searches and reviewer signoff before action.",
        },
        {
            "id": "canada-cid",
            "source_name": "Canadian Importers Database",
            "url": "https://ised-isde.canada.ca/site/ised/en/research-and-business-intelligence/canadian-importers-database",
            "checked_on": TODAY,
            "supports_phases": [4, 8],
            "source_area": "Canadian buyer/importer discovery",
            "usable_fact": "The Canadian Importers Database is a lead-discovery route for companies importing goods into Canada.",
            "claim_boundary": "A listed importer is a possible lead only; it is not buyer validation.",
        },
        {
            "id": "india-dgft-foreign-trade-policy",
            "source_name": "India Directorate General of Foreign Trade",
            "url": "https://www.dgft.gov.in/",
            "checked_on": TODAY,
            "supports_phases": [1, 5, 7],
            "source_area": "India exporter origin pack",
            "usable_fact": "DGFT is the India origin export-policy route for IEC, export/import policy, certificates, SCOMET, trade stats, and export management topics.",
            "claim_boundary": "India export permission, licensing, incentives, and product-specific compliance require current source review and qualified advice.",
        },
        {
            "id": "world-bank-wits",
            "source_name": "World Bank World Integrated Trade Solution",
            "url": "https://wits.worldbank.org/",
            "checked_on": TODAY,
            "supports_phases": [4],
            "source_area": "Global trade data",
            "usable_fact": "WITS is a route for international merchandise trade, tariff, and non-tariff measures data.",
            "claim_boundary": "Global trade data supports research signals only; it does not prove buyer demand, margin, or compliance.",
        },
        {
            "id": "itc-trade-map",
            "source_name": "International Trade Centre Trade Map",
            "url": "https://www.trademap.org/",
            "checked_on": TODAY,
            "supports_phases": [4],
            "source_area": "Global trade data",
            "usable_fact": "Trade Map is a route for import/export values, volumes, growth, market share, and company-directory research.",
            "claim_boundary": "Trade Map supports research and lead routing only; it does not validate demand or buyers.",
        },
        {
            "id": "wco-harmonized-system",
            "source_name": "World Customs Organization Harmonized System",
            "url": "https://www.wcoomd.org/en/topics/nomenclature/overview/what-is-the-harmonized-system.aspx",
            "checked_on": TODAY,
            "supports_phases": [0, 1, 4, 11],
            "source_area": "HS-code doctrine",
            "usable_fact": "The HS is the global commodity-description and coding route for HS candidate logic.",
            "claim_boundary": "HS candidate generation is not classification confirmation.",
        },
        {
            "id": "icc-incoterms-2020",
            "source_name": "ICC Incoterms 2020",
            "url": "https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/",
            "checked_on": TODAY,
            "supports_phases": [1, 7, 12],
            "source_area": "Incoterms and responsibility",
            "usable_fact": "Incoterms are the responsibility-path route for tasks, costs, and risks between sellers and buyers.",
            "claim_boundary": "Responsibility-path guidance requires user confirmation and, where needed, broker/legal review.",
        },
        {
            "id": "owasp-llm01-prompt-injection",
            "source_name": "OWASP GenAI prompt injection guidance",
            "url": "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
            "checked_on": TODAY,
            "supports_phases": [13, 19],
            "source_area": "AI safety",
            "usable_fact": "Indirect prompt injection can come from external files or websites and can manipulate outputs, leak information, or affect decisions.",
            "claim_boundary": "AI safety controls require implementation evidence and review before real document use.",
        },
    ]


def build_redevelopment_phases() -> list[dict[str, Any]]:
    phase_defs = [
        {
            "phase": 0,
            "name": "Product doctrine and claim boundary",
            "layers": [1],
            "build_track": ["ClaimPolicy module contract", "allowed/blocked claims list", "report-language rules", "source-citation rules"],
            "research_track": ["customs broker boundary", "importer responsibility", "CFIA reference-only language", "tariff classification limits", "sanctions routing limits", "AI output limits"],
            "source_track": ["cbsa-import-commercial-goods", "cbsa-licensed-customs-brokers", "cbsa-customs-tariff-2026", "cfia-airs", "gac-sanctions", "wco-harmonized-system"],
            "evidence_track": ["claim policy row with required evidence", "reviewer lane assignment", "user-facing explanation"],
            "gate_track": ["approved", "compliant", "ready_to_ship", "tariff_confirmed", "cfia_approved", "buyer_validated", "supplier_verified"],
        },
        {
            "phase": 1,
            "name": "Production domain model",
            "layers": [2, 3],
            "build_track": ["production entity schema", "domain event list", "entity lifecycle rules", "JSON to Postgres migration map"],
            "research_track": ["WCO HS structure", "Incoterms responsibility fields", "Canada import data requirements", "India IEC/export fields", "source metadata requirements"],
            "source_track": ["wco-harmonized-system", "icc-incoterms-2020", "cbsa-import-commercial-goods", "india-dgft-foreign-trade-policy"],
            "evidence_track": ["field provenance", "source snapshot references", "audit event for every business action"],
            "gate_track": ["field_presence_is_not_proof", "parser_draft_is_not_confirmation"],
        },
        {
            "phase": 2,
            "name": "Trade Readiness Packet engine",
            "layers": [4, 9],
            "build_track": ["packet state machine", "starter/market/buyer/supplier/broker/operator/executive/blocked-claim packet views"],
            "research_track": ["required fields by direction", "required fields by product class", "regulated-product question set"],
            "source_track": ["cbsa-import-commercial-goods", "cfia-airs", "gac-import-controls"],
            "evidence_track": ["packet state transition log", "packet view export", "blocked-claims packet"],
            "gate_track": ["reviewer_ready_not_approved", "packet_complete_not_trade_ready"],
        },
        {
            "phase": 3,
            "name": "No-document beginner intelligence",
            "layers": [4, 9, 12],
            "build_track": ["explore/import/export intake", "starter packet", "market checklist", "source map", "buyer/supplier/broker questions"],
            "research_track": ["market data availability", "HS candidate lookup methods", "country-pack coverage", "common beginner mistakes"],
            "source_track": ["ised-trade-data-online", "wco-harmonized-system", "itc-market-access-map", "cbsa-import-commercial-goods"],
            "evidence_track": ["no-document starter packet", "research plan", "blocked claims", "next safe move"],
            "gate_track": ["research_plan_not_market_conclusion", "no_documents_no_external_claims"],
        },
        {
            "phase": 4,
            "name": "Market intelligence engine",
            "layers": [7],
            "build_track": ["HS candidate route", "destination import value", "3-5 year trend", "top origin countries", "unit value", "market access barriers", "lead routes"],
            "research_track": ["ISED TDO", "Canadian Importers Database", "WITS", "ITC Trade Map", "Market Access Map", "UN Comtrade if API access is needed", "dataset licensing and terms"],
            "source_track": ["ised-trade-data-online", "canada-cid", "world-bank-wits", "itc-trade-map", "itc-market-access-map"],
            "evidence_track": ["MarketSignal record per metric", "source period", "confidence", "limitation", "next validation"],
            "gate_track": ["no_profitable_market_claim", "no_guaranteed_demand_claim", "buyer_validation_required"],
        },
        {
            "phase": 5,
            "name": "Country-pack platform",
            "layers": [5, 6],
            "build_track": ["country pack schema", "Canada destination pack", "India origin pack", "Vietnam sample pack", "Generic fallback", "US/UK/EU/UAE queue"],
            "research_track": ["Canada import sources", "India export sources", "Vietnam proof sources", "expansion-country source availability"],
            "source_track": ["cbsa-import-commercial-goods", "cbsa-customs-tariff-2026", "cfia-airs", "gac-sanctions", "india-dgft-foreign-trade-policy"],
            "evidence_track": ["coverage level", "claim boundary", "last checked", "reviewer required", "unsupported areas"],
            "gate_track": ["unsupported_country_generic_research_only", "country_claim_requires_full_coverage_and_review"],
        },
        {
            "phase": 6,
            "name": "Official-source intelligence and monitoring",
            "layers": [6],
            "build_track": ["source lifecycle", "robots/terms/license fields", "source states", "diff classification", "packet impact calculation"],
            "research_track": ["robots status", "terms", "data license", "update cadence", "source owner", "allowed automation", "manual-only restrictions"],
            "source_track": ["official_source_registry"],
            "evidence_track": ["SourceRecord", "SourceSnapshot", "content hash", "diff classification", "packet stale event"],
            "gate_track": ["source_route_not_current_law", "material_change_requires_reviewer"],
        },
        {
            "phase": 7,
            "name": "Import/export workflow engine",
            "layers": [4, 5, 9],
            "build_track": ["ExportPathEngine", "ImportPathEngine", "ResponsibilityPathEngine", "broker/expert routing"],
            "research_track": ["Canada import process", "India export process", "Incoterms", "broker responsibility", "regulated goods", "origin export controls"],
            "source_track": ["cbsa-import-commercial-goods", "india-dgft-foreign-trade-policy", "icc-incoterms-2020", "cbsa-licensed-customs-brokers", "cfia-airs"],
            "evidence_track": ["responsibility path", "import/export unresolved questions", "review route"],
            "gate_track": ["cannot_say_you_can_import", "cannot_say_you_can_export"],
        },
        {
            "phase": 8,
            "name": "Buyer discovery and buyer-evidence engine",
            "layers": [7, 8, 9],
            "build_track": ["buyer evidence ladder", "possible importer list", "buyer questions", "outreach preparation", "buyer packet", "validation gap"],
            "research_track": ["Canadian Importers Database", "public importer directories", "trade fairs", "industry associations", "anti-spam rules"],
            "source_track": ["canada-cid"],
            "evidence_track": ["lead source", "contact evidence", "reply evidence", "meeting notes", "LOI/PO/paid order evidence"],
            "gate_track": ["database_record_is_lead_not_validation", "never_say_buyer_validated_without_threshold_evidence"],
        },
        {
            "phase": 9,
            "name": "Supplier evidence engine",
            "layers": [8, 9],
            "build_track": ["supplier evidence ladder", "supplier document request", "risk questions", "missing evidence", "reviewer packet"],
            "research_track": ["company registries", "export licenses", "product certificates", "food/agri/seafood certifications", "inspection body standards", "fraud indicators"],
            "source_track": ["india-dgft-foreign-trade-policy", "cfia-airs"],
            "evidence_track": ["registration", "export ability", "product docs", "certificates", "inspection", "prior shipment", "commercial reference", "reviewer assessment"],
            "gate_track": ["supplier_evidence_collected_not_supplier_verified"],
        },
        {
            "phase": 10,
            "name": "Document intelligence platform",
            "layers": [8, 14],
            "build_track": ["upload", "malware scan", "file signature check", "quarantine", "OCR/text extraction", "classification", "field extraction", "redaction preview"],
            "research_track": ["trade document templates", "commercial invoice", "packing list", "certificate of origin", "bill of lading", "PO/contract", "inspection report", "upload security"],
            "source_track": ["owasp-file-upload"],
            "evidence_track": ["document id", "page/section", "extracted value", "confidence", "provenance", "confirmation status", "claim boundary"],
            "gate_track": ["parser_extraction_is_draft_evidence", "real_uploads_blocked_until_security_privacy_controls"],
        },
        {
            "phase": 11,
            "name": "Evidence ledger and claim-gate engine",
            "layers": [8, 9],
            "build_track": ["EvidenceItem schema", "can_show_claim(claim_type, packet_id)", "supports/blocks claim map", "stale evidence blocking"],
            "research_track": ["evidence requirements by claim type", "HS candidate", "tariff route", "CFIA relevance", "buyer/supplier evidence", "origin claim", "Incoterms", "market signal"],
            "source_track": ["cbsa-customs-tariff-2026", "cfia-airs", "wco-harmonized-system", "icc-incoterms-2020", "ised-trade-data-online"],
            "evidence_track": ["claim reason", "evidence trail", "source snapshot", "reviewer requirement"],
            "gate_track": ["no_evidence_no_claim", "stale_evidence_blocks_claim"],
        },
        {
            "phase": 12,
            "name": "Decision and scoring engine",
            "layers": [9],
            "build_track": ["six permanent scores", "score reason", "blocking fields", "next action", "cap policy"],
            "research_track": ["thresholds by packet stage", "country coverage", "product category", "evidence strength", "source freshness", "reviewer status"],
            "source_track": ["official_source_registry"],
            "evidence_track": ["score output record", "cap reason", "next action"],
            "gate_track": ["no_single_global_readiness_score", "no_approval_language"],
        },
        {
            "phase": 13,
            "name": "AI copilot layer",
            "layers": [10, 14],
            "build_track": ["intake assistant", "document assistant", "source summarizer", "market research assistant", "packet writer", "review work-order drafter", "redaction assistant", "QA assistant"],
            "research_track": ["AI provider data-use terms", "retention settings", "no-training guarantees", "redaction tests", "prompt-injection tests", "model routing", "human review"],
            "source_track": ["owasp-llm01-prompt-injection", "nist-ai-rmf"],
            "evidence_track": ["AI output label", "permission record", "prompt-injection test result", "redaction result"],
            "gate_track": ["ai_cannot_open_any_external_gate"],
        },
        {
            "phase": 14,
            "name": "Expert review network",
            "layers": [11],
            "build_track": ["reviewer profile", "credentials", "scope", "packet review link", "finding form", "severity", "decision values", "audit trail"],
            "research_track": ["customs broker qualifications", "trade consultant categories", "freight expert scope", "privacy/legal/security/AI/payment reviewer criteria"],
            "source_track": ["cbsa-licensed-customs-brokers"],
            "evidence_track": ["review finding", "required changes", "approved scope", "evidence attachment"],
            "gate_track": ["no_reviewer_lane_no_claim_lane", "scope_limited_approval_only"],
        },
        {
            "phase": 15,
            "name": "Reports and deliverables engine",
            "layers": [9, 12, 13],
            "build_track": ["starter packet", "market brief", "buyer-ready packet", "supplier request", "broker packet", "missing evidence", "blocked claims", "country source map", "source freshness", "expert summary", "executive report", "audit export"],
            "research_track": ["beginner exporter needs", "experienced exporter needs", "Canadian importer needs", "broker/supplier/buyer/operator/reviewer report needs"],
            "source_track": ["official_source_registry"],
            "evidence_track": ["HTML preview", "PDF export", "JSON export", "citations", "version history", "watermark", "review status"],
            "gate_track": ["reports_must_keep_blocked_claims_visible"],
        },
        {
            "phase": 16,
            "name": "User portals and workflows",
            "layers": [12],
            "build_track": ["public portal", "exporter portal", "importer portal", "reviewer portal", "admin/operator portal", "enterprise portal"],
            "research_track": ["exporter/importer UX testing", "accessibility", "terminology", "mobile review", "blocked vs approved confusion testing"],
            "source_track": ["user_research_required"],
            "evidence_track": ["workflow smoke result", "terminology feedback", "accessibility result"],
            "gate_track": ["public_no_unrestricted_uploads", "public_no_live_payment", "public_no_strong_claims"],
        },
        {
            "phase": 17,
            "name": "Enterprise SaaS and API platform",
            "layers": [13],
            "build_track": ["organizations", "workspaces", "RBAC", "client accounts", "multi-packet dashboard", "comments", "review assignment", "audit export", "API keys", "webhooks", "usage limits", "white-label reports"],
            "research_track": ["broker/advisor workflow", "enterprise retention", "API use cases", "audit requirements", "multi-client permissions", "white-label needs"],
            "source_track": ["enterprise_user_validation_required"],
            "evidence_track": ["API contract", "RBAC test", "audit export", "retention policy"],
            "gate_track": ["api_outputs_follow_same_claim_gate_engine"],
        },
        {
            "phase": 18,
            "name": "Payments and monetization",
            "layers": [13, 14],
            "build_track": ["free quick check", "starter packet", "pro workspace", "expert review add-on", "broker/advisor workspace", "enterprise", "API/data access"],
            "research_track": ["Stripe live-mode requirements", "refund/support policy", "tax/accounting review", "price testing", "willingness to pay", "payment wording"],
            "source_track": ["stripe-go-live"],
            "evidence_track": ["pricing approval", "refund/support policy", "tax review", "webhook test", "payment security review", "claim-language review"],
            "gate_track": ["charge_for_preparation_not_approval", "live_checkout_disabled_until_review"],
        },
        {
            "phase": 19,
            "name": "Security, privacy, reliability, and production trust",
            "layers": [8, 10, 14],
            "build_track": ["managed auth", "admin MFA", "org RBAC", "secure sessions", "CSRF", "rate limits", "private object storage", "malware scanning", "audit logs", "deletion", "retention", "vendor register", "backup/restore", "monitoring", "incident runbooks"],
            "research_track": ["PIPEDA", "data residency", "AI vendor terms", "upload threat model", "retention periods", "breach process", "security findings"],
            "source_track": ["opc-pipeda-principles", "owasp-file-upload", "owasp-llm01-prompt-injection", "nist-ai-rmf"],
            "evidence_track": ["auth proof", "upload security proof", "privacy review", "vendor inventory", "backup restore test", "incident runbook"],
            "gate_track": ["real_file_uploads_blocked_until_controls_proven"],
        },
        {
            "phase": 20,
            "name": "Launch control plane",
            "layers": [14],
            "build_track": ["business logic gate", "country-pack gate", "source freshness gate", "market-data gate", "security gate", "privacy gate", "AI safety gate", "trade-language gate", "expert-review gate", "payment gate", "real-user evidence gate", "production infrastructure gate", "final owner gate"],
            "research_track": ["public copy review", "source refresh proof", "reviewer signoffs", "user outcomes", "hosted proof", "payment proof"],
            "source_track": ["official_source_registry", "reviewer_findings", "user_validation_records"],
            "evidence_track": ["gate state", "approved scope", "expiry", "owner approval"],
            "gate_track": ["launch_only_for_exact_approved_scope"],
        },
    ]
    rows = []
    for phase in phase_defs:
        rows.append(
            {
                **phase,
                "local_status": "phase_research_build_source_evidence_gate_tracks_ready",
                "deliverables": phase["build_track"],
                "external_gates": phase["gate_track"],
                "claim_state": "external_claims_closed",
                "next_valid_move": (
                    "Build the production implementation for this phase and attach the listed evidence before any gated claim can open."
                ),
            }
        )
    return rows


def build_first_five_work_packages() -> list[dict[str, Any]]:
    return [
        {
            "id": "production_data_model",
            "phase": 1,
            "must_build": ["TradeReadinessPacket", "EvidenceItem", "SourceRecord", "CountryPack", "DecisionScore", "BlockedClaim", "ReviewRequest", "Report"],
            "current_repo_basis": ["business_logic_phase_report.json", "customer_source_packets.json", "evidence_ledger.json"],
            "implementation_status": "local_schema_proof_ready_external_db_gates_closed",
            "artifacts": [
                "migrations/0002_production_domain_model.sql",
                "system_review_graph/production_data_model_manifest.json",
                "system_review_graph/production_data_model_seed.json",
                "docs/PRODUCTION_DATA_MODEL.md",
            ],
            "proof": "Postgres-oriented schema, tenant isolation policy, domain event list, seed fixture, and JSON-to-table migration map are generated by scripts/run_production_data_model.py",
        },
        {
            "id": "packet_engine",
            "phase": 2,
            "must_build": ["create packet", "update packet", "score packet", "block claims", "generate packet views", "export packet"],
            "current_repo_basis": ["source_packet_workflow.py", "product_operations.py", "business_logic.py"],
            "implementation_status": "local_state_machine_and_view_engine_ready_external_gates_closed",
            "artifacts": [
                "system_review_graph/production_packet_engine_manifest.json",
                "system_review_graph/production_packet_events.json",
                "system_review_graph/production_packet_views/",
                "docs/PRODUCTION_PACKET_ENGINE.md",
            ],
            "proof": "Packet state, events, eight packet views, six scores, source routes, blockers, and next moves are generated from real local packet/evidence/source/review/report artifacts by scripts/run_production_packet_engine.py",
        },
        {
            "id": "country_source_engine",
            "phase": 6,
            "must_build": ["Canada pack", "India origin pack", "source registry", "source snapshots", "source freshness", "stale packet logic"],
            "current_repo_basis": ["official_source_registry.json", "policy_intelligence.py", "country_coverage_report.json"],
            "implementation_status": "local_country_pack_and_source_lifecycle_engine_ready_external_gates_closed",
            "artifacts": [
                "system_review_graph/production_country_source_engine_manifest.json",
                "system_review_graph/production_country_packs.json",
                "system_review_graph/production_source_lifecycle.json",
                "docs/PRODUCTION_COUNTRY_SOURCE_ENGINE.md",
            ],
            "proof": "Canada, India, Vietnam demo, and generic fallback country packs, source lifecycle rows, source freshness states, packet impacts, and claim gates are generated from the official source registry and dated source-refresh records by scripts/run_production_country_source_engine.py",
        },
        {
            "id": "market_intelligence_engine",
            "phase": 4,
            "must_build": ["product/HS discovery", "trade data signal", "competitor countries", "market access comparison", "buyer/importer lead routes", "confidence labels"],
            "current_repo_basis": ["opportunity_scanner_report.json", "business_logic.py"],
            "implementation_status": "local_source_routed_market_signal_engine_ready_no_demand_claims",
            "artifacts": [
                "system_review_graph/production_market_intelligence_manifest.json",
                "system_review_graph/production_market_signals.json",
                "system_review_graph/production_market_dataset_connectors.json",
                "docs/PRODUCTION_MARKET_INTELLIGENCE_ENGINE.md",
            ],
            "proof": "Market metrics, source routes, dataset connector states, capped market score, blocked demand/profit/buyer claims, and next validation moves are generated from the packet and official source registry by scripts/run_production_market_intelligence_engine.py",
        },
        {
            "id": "report_engine",
            "phase": 15,
            "must_build": ["starter packet", "market brief", "buyer-ready packet", "broker packet", "missing evidence report", "blocked claims report", "executive decision report"],
            "current_repo_basis": ["report_exports.json", "generated_reports", "output/pdf"],
            "proof": "report requirements keep claim boundaries, citations, evidence links, versions, and watermarks",
        },
    ]


def build_api_contracts() -> list[dict[str, Any]]:
    routes = [
        ("POST", "/packets", "create packet draft", False),
        ("GET", "/packets/{id}", "read packet", False),
        ("POST", "/packets/{id}/evidence", "attach evidence", False),
        ("POST", "/documents/upload", "quarantine upload", False),
        ("POST", "/documents/{id}/extract", "extract draft fields", False),
        ("GET", "/country-packs/{country}", "read country pack", False),
        ("POST", "/sources/refresh", "record source refresh request", False),
        ("GET", "/packets/{id}/scores", "read decision scores", False),
        ("GET", "/packets/{id}/blocked-claims", "read blocked claims", False),
        ("POST", "/reviews", "create review request", False),
        ("POST", "/reports", "generate safe report", False),
        ("POST", "/ai/safe-summary", "generate AI-labeled draft summary", False),
        ("POST", "/billing/quote", "reserve quote without live charge", False),
    ]
    return [
        {
            "method": method,
            "path": path,
            "purpose": purpose,
            "external_effects_allowed": external_effects_allowed,
            "forbidden": ["approval", "claim_gate_override", "external_outreach", "live_charge"],
        }
        for method, path, purpose, external_effects_allowed in routes
    ]


def build_launch_control_plane() -> dict[str, Any]:
    gates = [
        "business_gate",
        "security_gate",
        "privacy_gate",
        "ai_safety_gate",
        "trade_language_gate",
        "source_freshness_gate",
        "country_pack_gate",
        "payment_gate",
        "user_validation_gate",
        "expert_review_gate",
        "production_infrastructure_gate",
        "final_launch_owner_gate",
    ]
    return {
        "status": "launch_control_plane_contract_ready_public_launch_blocked",
        "gate_count": len(gates),
        "gates": [
            {
                "gate": gate,
                "state": "blocked",
                "allowed_states": ["not_started", "in_progress", "needs_changes", "blocked", "approved_for_scope", "expired"],
                "unsafe_to_bypass": True,
            }
            for gate in gates
        ],
        "public_launch_ready": False,
        "hosted_production_ready": False,
        "live_payment_ready": False,
    }


def build_production_redevelopment_plan() -> dict[str, Any]:
    layers = build_production_layers()
    phases = build_redevelopment_phases()
    entities = build_domain_entities()
    service_boundaries = build_service_boundaries()
    research_anchors = build_research_anchors()
    first_five = build_first_five_work_packages()
    api_contracts = build_api_contracts()
    control_plane = build_launch_control_plane()
    return {
        "generated_at": _now(),
        "status": "production_redevelopment_contract_ready_with_external_build_gates",
        "product": "Trade Readiness Copilot",
        "redevelopment_decision": "preserve_business_logic_rebuild_platform_around_it",
        "current_repo_role": "business_rule_reference_implementation_and_proof_engine",
        "platform_architecture": "modular_monolith_first",
        "production_layer_count": len(layers),
        "phase_count": len(phases),
        "domain_entity_count": len(entities),
        "service_boundary_count": len(service_boundaries),
        "research_anchor_count": len(research_anchors),
        "first_rebuild_package_count": len(first_five),
        "api_route_count": len(api_contracts),
        "production_layers": layers,
        "redevelopment_phases": phases,
        "domain_entities": entities,
        "service_boundaries": service_boundaries,
        "packet_state_machine": build_packet_state_machine(),
        "research_anchors": research_anchors,
        "first_five_rebuild_work_packages": first_five,
        "api_contracts": api_contracts,
        "launch_control_plane": control_plane,
        "external_claims_opened": False,
        "public_launch_ready": False,
        "hosted_production_ready": False,
        "live_payment_ready": False,
        "qualified_review_complete": False,
        "buyer_supplier_validation_complete": False,
        "real_user_validation_complete": False,
        "proof_boundary": (
            "This artifact completes the local production redevelopment contract. "
            "It does not prove production deployment, legal/privacy/security approval, "
            "qualified customs/trade review, buyer/supplier validation, live payments, "
            "real user outcomes, or public go/no-go approval."
        ),
    }


def write_production_redevelopment_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    plan_path = graph / "production_redevelopment_plan.json"
    research_path = graph / "production_research_anchors.json"
    doc_path = docs / "PRODUCTION_REDEVELOPMENT.md"
    plan_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    research_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_research_anchors_ready",
                "source_count": payload["research_anchor_count"],
                "sources": payload["research_anchors"],
                "proof_boundary": "Research anchors route product work; they do not approve external claims.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_production_redevelopment_markdown(payload), encoding="utf-8")
    return {"plan": plan_path, "research": research_path, "doc": doc_path}


def render_production_redevelopment_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Redevelopment Contract",
        "",
        f"Status: `{payload['status']}`",
        "",
        "Trade Readiness Copilot keeps the current business-rule engine and rebuilds the production platform around it.",
        "",
        "## Current Decision",
        "",
        f"- Product: {payload['product']}",
        f"- Architecture: {payload['platform_architecture']}",
        "- Current repo role: business-rule reference implementation and proof engine.",
        "- External claims opened: false.",
        "- Public launch ready: false.",
        "",
        "## Counts",
        "",
        f"- Production layers: {payload['production_layer_count']}",
        f"- Redevelopment phases: {payload['phase_count']} including phase 0",
        f"- Domain entities: {payload['domain_entity_count']}",
        f"- Service boundaries: {payload['service_boundary_count']}",
        f"- Dated research anchors: {payload['research_anchor_count']}",
        f"- First rebuild work packages: {payload['first_rebuild_package_count']}",
        "",
        "## Fourteen Production Layers",
        "",
    ]
    for layer in payload["production_layers"]:
        lines.append(f"- {layer['layer_id']}. {layer['name']}: {layer['purpose']}")
    lines.extend(["", "## Redevelopment Phases", ""])
    for phase in payload["redevelopment_phases"]:
        lines.extend(
            [
                f"### Phase {phase['phase']}: {phase['name']}",
                "",
                f"- Local status: `{phase['local_status']}`",
                f"- Build track: {', '.join(phase['build_track'])}.",
                f"- Research track: {', '.join(phase['research_track'])}.",
                f"- Source track: {', '.join(phase['source_track'])}.",
                f"- Evidence track: {', '.join(phase['evidence_track'])}.",
                f"- Claims still closed: {', '.join(phase['gate_track'])}.",
                f"- Next valid move: {phase['next_valid_move']}",
                "",
            ]
        )
    lines.extend(["", "## Permanent Research Intelligence Entities", ""])
    research_entities = {
        "ResearchIntake",
        "SourceRegistry",
        "SourceSnapshot",
        "DatasetConnector",
        "CountryPackSource",
        "MarketSignalSource",
        "LegalBoundarySource",
        "ExpertFindingSource",
        "EvidenceMapper",
        "ClaimGateMapper",
    }
    for entity in payload["domain_entities"]:
        if entity["entity"] in research_entities:
            lines.append(f"- {entity['entity']}: {', '.join(entity['required_fields'])}.")
    lines.extend(["", "## First Five Rebuild Packages", ""])
    for package in payload["first_five_rebuild_work_packages"]:
        lines.append(f"- {package['id']}: {', '.join(package['must_build'])}.")
    lines.extend(["", "## Research Anchors", ""])
    for source in payload["research_anchors"]:
        lines.append(f"- {source['source_name']}: {source['url']}")
    lines.extend(
        [
            "",
            "## Proof Boundary",
            "",
            payload["proof_boundary"],
            "",
        ]
    )
    return "\n".join(lines)
