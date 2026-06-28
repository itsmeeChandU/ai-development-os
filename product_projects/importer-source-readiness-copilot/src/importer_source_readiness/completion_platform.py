"""Completion-stage local contracts for the Trade Readiness platform."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .business_logic import build_business_logic_phases


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _category(packet: dict[str, Any]) -> str:
    return str(packet.get("product_category") or "general_trade").strip() or "general_trade"


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


def _coverage_level_definitions() -> list[dict[str, Any]]:
    return [
        {
            "tier": 0,
            "label": "selectable only",
            "support": "Country can be selected in generic product flows only.",
            "country_specific_claims_allowed": False,
            "minimum_evidence": "No country-specific source coverage.",
        },
        {
            "tier": 1,
            "label": "generic starter checklist",
            "support": "Generic import/export checklist language may be shown.",
            "country_specific_claims_allowed": False,
            "minimum_evidence": "Country appears in a packet but lacks monitored official sources.",
        },
        {
            "tier": 2,
            "label": "reference sources catalogued",
            "support": "Reference sources can orient research, with claim gates closed.",
            "country_specific_claims_allowed": False,
            "minimum_evidence": "At least one official or official-adjacent source is catalogued.",
        },
        {
            "tier": 3,
            "label": "monitored sources",
            "support": "Multiple official sources are tracked for internal review prompts.",
            "country_specific_claims_allowed": False,
            "minimum_evidence": "Multiple official sources are recorded with access dates.",
        },
        {
            "tier": 4,
            "label": "category template support",
            "support": "Category-specific templates can be prepared for expert review.",
            "country_specific_claims_allowed": False,
            "minimum_evidence": "Country, category, and route templates are maintained.",
        },
        {
            "tier": 5,
            "label": "expert-reviewed templates",
            "support": "Expert-reviewed templates may support scoped country-specific product copy.",
            "country_specific_claims_allowed": True,
            "minimum_evidence": "Current official sources, category templates, and qualified review are attached.",
        },
    ]


def _coverage_label_map() -> dict[int, str]:
    return {row["tier"]: row["label"] for row in _coverage_level_definitions()}


def _coverage_tier(country: str, source_count: int) -> int:
    if country in {"", "Generic"}:
        return 0
    if source_count >= 5:
        return 3
    if source_count > 0:
        return 2
    return 1


def _source_summary(source: dict[str, Any], *, provenance_type: str = "official_source_registry") -> dict[str, Any]:
    return {
        "provenance_type": provenance_type,
        "source_id": source.get("id"),
        "name": source.get("name"),
        "url": source.get("url"),
        "jurisdiction": _country(source.get("jurisdiction")),
        "accessed_at": source.get("accessed_at"),
        "evidence_role": source.get("evidence_role"),
        "claim_boundary": source.get("claim_boundary"),
    }


def _source_provenance(packet: dict[str, Any], official_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_url = str(packet.get("source_url") or "").strip()
    countries = {
        _country(packet.get("origin_country")),
        _country(packet.get("destination_country")),
        _country(packet.get("supplier_country")),
    }
    provenance: list[dict[str, Any]] = []
    seen: set[str] = set()
    if packet_url:
        provenance.append(
            {
                "provenance_type": "packet_source_reference",
                "source_id": packet.get("source_type") or "packet_source",
                "name": packet.get("source_type") or "Packet source reference",
                "url": packet_url,
                "jurisdiction": _country(packet.get("destination_country")),
                "accessed_at": packet.get("created_at"),
                "evidence_role": "customer packet source reference",
                "claim_boundary": "Packet source is orientation only; it does not prove demand, supplier fit, tariff, compliance, or shipment readiness.",
            }
        )
        seen.add(packet_url)
    for source in official_sources:
        url = str(source.get("url") or "")
        jurisdiction = _country(source.get("jurisdiction"))
        if url in seen:
            continue
        if url == packet_url or jurisdiction in countries or jurisdiction == "Generic":
            provenance.append(_source_summary(source))
            seen.add(url)
    return provenance


def build_country_coverage(workflow: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    countries = sorted(
        {
            _country(packet.get(key))
            for packet in workflow.get("packets", [])
            for key in ("origin_country", "destination_country")
            if packet.get(key)
        }
        | {"Canada", "India", "United States", "United Kingdom", "Generic"}
    )
    sources_by_country: dict[str, list[dict[str, Any]]] = {}
    for source in official_sources:
        country = _country(source.get("jurisdiction"))
        sources_by_country.setdefault(country, []).append(source)
    rows = []
    labels = _coverage_label_map()
    for country in countries:
        country_sources = sources_by_country.get(country, [])
        count = len(country_sources)
        tier = _coverage_tier(country, count)
        country_specific_allowed = tier >= 5
        rows.append(
            {
                "country": country,
                "coverage_tier": tier,
                "coverage_label": labels[tier],
                "source_count": count,
                "source_provenance": [_source_summary(source) for source in country_sources],
                "can_make_country_specific_claims": country_specific_allowed,
                "claim_scope_allowed": "country_specific_template_copy" if country_specific_allowed else "generic_readiness_only",
                "unsupported_country_specific_claims": [
                    "customs_or_tariff_correctness",
                    "country_rules_current",
                    "permit_or_license_required",
                    "food_or_regulated_product_clearance",
                    "shipment_or_import_ready",
                ],
                "country_specific_claim_gate": {
                    "status": "blocked_unsupported_country_specific_claims"
                    if not country_specific_allowed
                    else "allowed_only_inside_expert_reviewed_template_scope",
                    "required_tier": 5,
                    "qualified_review_required": True,
                    "current_source_refresh_required": True,
                    "external_claims_opened": False,
                },
                "next_valid_move": "Add current monitored official sources, category templates, and qualified review before country-specific claims.",
            }
        )
    packet_rows = []
    for packet in workflow.get("packets", []):
        origin = _country(packet.get("origin_country"))
        destination = _country(packet.get("destination_country"))
        origin_tier = next((row["coverage_tier"] for row in rows if row["country"] == origin), 1)
        destination_tier = next((row["coverage_tier"] for row in rows if row["country"] == destination), 1)
        effective = min(origin_tier, destination_tier)
        country_specific_allowed = effective >= 5
        packet_rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "origin_country": origin,
                "destination_country": destination,
                "product_category": _category(packet),
                "effective_coverage_tier": effective,
                "coverage_label": labels.get(effective, "unknown"),
                "coverage_status": "country_specific_claims_allowed_scoped"
                if country_specific_allowed
                else "country_specific_claims_blocked",
                "can_make_country_specific_claims": country_specific_allowed,
                "blocked_country_specific_claims": [
                    "tariff_confirmed",
                    "customs_process_current",
                    "country_requirements_complete",
                    "regulated_product_clearance",
                    "import_or_export_approved",
                ],
                "next_valid_move": "Use generic readiness output unless both countries and category have monitored/expert-reviewed coverage.",
            }
        )
    return {
        "generated_at": _now(),
        "status": "country_coverage_ready_with_claim_gates",
        "coverage_levels": {
            str(row["tier"]): row["label"] for row in _coverage_level_definitions()
        },
        "tier_definitions": _coverage_level_definitions(),
        "country_specific_claim_policy": {
            "default": "blocked",
            "allowed_only_at_tier": 5,
            "requires_current_sources": True,
            "requires_qualified_review": True,
            "unsupported_claim_behavior": "block_and_emit_next_valid_move",
        },
        "countries": rows,
        "packet_coverage": packet_rows,
        "proof_boundary": "Coverage tiers describe product support level only; they do not prove country-specific legal, customs, tariff, or compliance correctness.",
    }


def build_opportunity_scanner(
    workflow: dict[str, Any],
    coverage: dict[str, Any],
    official_sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    official_sources = official_sources or []
    rows = []
    for packet in workflow.get("packets", []):
        category = _category(packet)
        coverage_row = next(
            (row for row in coverage.get("packet_coverage", []) if row.get("packet_id") == packet.get("packet_id")),
            {},
        )
        complexity = "high" if any(word in category.lower() for word in ("food", "health", "animal", "plant", "seafood")) else "medium"
        provenance = _source_provenance(packet, official_sources)
        coverage_tier = int(coverage_row.get("effective_coverage_tier") or 0)
        confidence_level = "medium" if coverage_tier >= 3 and provenance else "low"
        create_packet_hint = {
            "route": "/packets/new",
            "api_route": "/api/agent-tools/create_trade_packet",
            "agent_tool": "create_trade_packet",
            "method": "POST",
            "external_effects_allowed": False,
            "claim_gate_can_open": False,
        }
        rows.append(
            {
                "signal_id": f"opportunity:{packet.get('packet_id')}",
                "packet_id": packet.get("packet_id"),
                "country": packet.get("destination_country") or "Canada",
                "direction": packet.get("trade_direction") or "unknown",
                "category": category,
                "opportunity_signal": "possible opportunity signal",
                "demand_signal": "unknown_requires_external_research",
                "supply_or_surplus_signal": "unknown_requires_external_research",
                "trade_growth_signal": "unknown_requires_dataset",
                "trend_signal": "unknown_requires_dataset",
                "requirements_complexity": complexity,
                "transport_complexity": "unknown_until_dimensions_mode_and_temperature_requirements_known",
                "coverage_confidence": coverage_tier,
                "confidence_level": confidence_level,
                "confidence": {
                    "coverage_tier": coverage_tier,
                    "source_provenance_count": len(provenance),
                    "evidence_confidence": "reference_only",
                    "market_confidence": "unknown_requires_external_research",
                    "logistics_confidence": "unknown_requires_forwarder_inputs",
                    "claim_confidence": "blocked_until_buyer_source_logistics_and_expert_evidence",
                    "confidence_reason": "Local packet and source references can seed research, but no buyer, demand, margin, route, or qualified-review evidence is attached.",
                },
                "source_provenance": provenance,
                "source_provenance_count": len(provenance),
                "create_packet_hint": create_packet_hint,
                "buyer_validation": "missing",
                "recommendation_claim": "blocked",
                "next_step": "create or continue readiness packet; collect real buyer, demand, source, and logistics evidence.",
            }
        )
    return {
        "generated_at": _now(),
        "status": "opportunity_scanner_ready_with_research_gates",
        "signal_count": len(rows),
        "signals": rows,
        "create_packet_route": "/packets/new",
        "create_packet_api_hint": {
            "route": "/api/agent-tools/create_trade_packet",
            "tool": "create_trade_packet",
            "method": "POST",
            "requires_confirmation": True,
            "external_effects_allowed": False,
        },
        "confidence_fields": [
            "coverage_tier",
            "source_provenance_count",
            "evidence_confidence",
            "market_confidence",
            "logistics_confidence",
            "claim_confidence",
        ],
        "blocked_claims": ["guaranteed_demand", "profitable_product", "confirmed_surplus", "buyer_validated"],
        "proof_boundary": "Opportunity rows are signals and research prompts only, not recommendations, demand proof, margin proof, or buyer validation.",
    }


def build_transport_readiness(workflow: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for packet in workflow.get("packets", []):
        missing = []
        incoterms = str(packet.get("incoterms_if_known") or "").strip()
        mode = str(packet.get("shipping_method") or packet.get("transport_mode") or "").strip()
        weight = packet.get("gross_weight_kg") or packet.get("weight_kg") or packet.get("weight")
        dimensions = packet.get("dimensions_cm") or packet.get("dimensions")
        packing_list = packet.get("packing_list_received")
        commercial_invoice = packet.get("commercial_invoice_received")
        category = _category(packet).lower()
        cold_chain_required = any(word in category for word in ("food", "seafood", "health", "medical"))
        dangerous_goods_possible = any(word in category for word in ("chemical", "battery", "dangerous", "medical"))
        if not incoterms or incoterms == "unknown":
            missing.append("Incoterms or delivery responsibility")
        if not mode:
            missing.append("Transport mode")
        if not weight or not dimensions:
            missing.append("weight and dimensions")
        if packing_list is not True:
            missing.append("packing list")
        if commercial_invoice is not True:
            missing.append("commercial invoice")
        for item in ("insurance decision", "ports", "forwarder"):
            missing.append(item)
        if cold_chain_required and not packet.get("temperature_requirement"):
            missing.append("cold-chain requirement")
        if dangerous_goods_possible or not packet.get("dangerous_goods_declaration"):
            missing.append("dangerous goods declaration")
        freight_forwarder_sections = [
            {
                "section_id": "incoterms_and_responsibility",
                "title": "Incoterms and delivery responsibility",
                "status": "missing" if not incoterms or incoterms == "unknown" else "provided_for_review",
                "questions": ["Which Incoterms version and named place apply?", "Who is importer of record and who pays duty, freight, and insurance?"],
            },
            {
                "section_id": "mode_route_ports",
                "title": "Mode, route, ports, and transit constraints",
                "status": "missing" if not mode else "provided_for_review",
                "questions": ["Which mode is intended: ocean, air, road, rail, courier, or multimodal?", "Which origin/destination ports or terminals are planned?"],
            },
            {
                "section_id": "weight_dimensions_packaging",
                "title": "Weight, dimensions, packing, and palletization",
                "status": "missing" if not weight or not dimensions or packing_list is not True else "provided_for_review",
                "questions": ["What are gross weight, net weight, dimensions, carton count, pallet count, and packaging type?", "Does any wood packaging require ISPM 15 review?"],
            },
            {
                "section_id": "commercial_invoice_and_packing_list",
                "title": "Commercial invoice and packing list",
                "status": "missing" if commercial_invoice is not True or packing_list is not True else "provided_for_review",
                "questions": ["Does the commercial invoice include seller, buyer, description, HS code if known, value, currency, origin, and Incoterms?", "Does the packing list reconcile to invoice quantities and shipment units?"],
            },
            {
                "section_id": "cold_chain_and_dangerous_goods",
                "title": "Cold-chain, dangerous goods, and special handling",
                "status": "missing" if ("cold-chain requirement" in missing or "dangerous goods declaration" in missing) else "provided_for_review",
                "questions": ["Is temperature control required and what range/data logger proof is needed?", "Are dangerous goods, batteries, chemicals, or restricted handling declarations required?"],
            },
            {
                "section_id": "forwarder_quote_packet",
                "title": "Freight-forwarder quote packet",
                "status": "blocked_missing_inputs",
                "questions": ["Which documents and shipment facts should be sent to a forwarder for a quote?", "What remains internal until customer confirmation or qualified review is attached?"],
            },
        ]
        rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "status": "transport_questions_ready_claims_blocked",
                "missing_transport_inputs": missing,
                "shipment_profile": {
                    "incoterms": incoterms or "unknown",
                    "mode": mode or "unknown",
                    "weight_status": "provided" if weight else "missing",
                    "dimensions_status": "provided" if dimensions else "missing",
                    "packing_list_status": "provided" if packing_list is True else "missing",
                    "commercial_invoice_status": "provided" if commercial_invoice is True else "missing",
                    "cold_chain_status": "needs_review" if cold_chain_required else "not_indicated",
                    "dangerous_goods_status": "needs_declaration_or_review"
                    if dangerous_goods_possible or not packet.get("dangerous_goods_declaration")
                    else "declared_for_review",
                },
                "packing_and_invoice_sections": [
                    "commercial invoice fields",
                    "packing list quantities",
                    "gross/net weight and dimensions",
                    "cartons, pallets, marks, and packaging type",
                    "country of origin and HS code if known",
                ],
                "special_handling_sections": [
                    "cold-chain temperature range and monitoring" if cold_chain_required else "cold-chain not indicated",
                    "dangerous goods declaration or negative confirmation",
                    "wood packaging and fumigation/ISPM 15 review",
                ],
                "freight_forwarder_packet_sections": freight_forwarder_sections,
                "freight_forwarder_packet_status": "blocked_missing_transport_inputs",
                "freight_forwarder_questions": [
                    "What mode, route, ports, and transit constraints apply?",
                    "Are dimensions, gross weight, packaging, and palletization known?",
                    "Do Incoterms create buyer, seller, or DDP/importer responsibility?",
                    "Is temperature control, insurance, dangerous goods, or wood packaging review required?",
                ],
                "next_valid_move": "Collect shipment details and route to freight forwarder/broker review before transport cost or route claims.",
            }
        )
    return {
        "generated_at": _now(),
        "status": "transport_readiness_ready_with_forwarder_gates",
        "packet_count": len(rows),
        "rows": rows,
        "blocked_claims": ["shipping_cost_guaranteed", "route_optimized", "freight_forwarder_selected", "shipment_ready"],
        "proof_boundary": "Transport readiness prepares questions only; it does not optimize routes, guarantee costs, or approve shipment.",
    }


def build_billing_controls() -> dict[str, Any]:
    actions = [
        {"action": "ocr_page", "metering_category": "ocr_pages", "metered_unit": "page", "estimated_credits": 2, "heavy_job": False},
        {"action": "ocr_document_batch", "metering_category": "ocr_pages", "metered_unit": "document_batch", "estimated_credits": 12, "heavy_job": True},
        {"action": "ai_extraction", "metering_category": "ai_jobs", "metered_unit": "job", "estimated_credits": 4, "heavy_job": True},
        {"action": "ai_job_deep_research", "metering_category": "ai_jobs", "metered_unit": "job", "estimated_credits": 12, "heavy_job": True},
        {"action": "large_document_packet", "metering_category": "ai_jobs", "metered_unit": "packet", "estimated_credits": 10, "heavy_job": True},
        {"action": "saved_workspace", "metering_category": "workspace_storage", "metered_unit": "workspace", "estimated_credits": 1, "heavy_job": False},
        {"action": "report_export", "metering_category": "report_exports", "metered_unit": "export", "estimated_credits": 2, "heavy_job": False},
        {"action": "buyer_ready_packet", "metering_category": "report_exports", "metered_unit": "export", "estimated_credits": 3, "heavy_job": False},
        {"action": "broker_ready_packet", "metering_category": "report_exports", "metered_unit": "export", "estimated_credits": 3, "heavy_job": False},
        {"action": "source_monitoring", "metering_category": "source_monitoring", "metered_unit": "refresh", "estimated_credits": 5, "heavy_job": True},
        {"action": "source_monitoring_watchlist", "metering_category": "source_monitoring", "metered_unit": "watchlist", "estimated_credits": 8, "heavy_job": True},
        {"action": "opportunity_report", "metering_category": "report_exports", "metered_unit": "report", "estimated_credits": 4, "heavy_job": True},
        {"action": "expert_review_request", "metering_category": "human_review_routing", "metered_unit": "request", "estimated_credits": 0, "heavy_job": True},
        {"action": "private_ai", "metering_category": "ai_jobs", "metered_unit": "job", "estimated_credits": 8, "heavy_job": True},
        {"action": "agent_api_call", "metering_category": "agent_api_calls", "metered_unit": "call", "estimated_credits": 1, "heavy_job": False},
        {"action": "api_agent_usage", "metering_category": "agent_api_calls", "metered_unit": "tool_execution", "estimated_credits": 2, "heavy_job": True},
    ]
    rows = [
        {
            **action,
            "requires_pre_authorization": action["heavy_job"]
            or action["metering_category"] in {"ai_jobs", "source_monitoring", "agent_api_calls"},
            "heavy_job_gate": "blocked_requires_upgrade_or_manual_approval" if action["heavy_job"] else "standard_credit_metering",
            "free_plan_behavior": "blocked_requires_upgrade" if action["heavy_job"] else "allowed_with_limits",
            "external_charge_created": False,
        }
        for action in actions
    ]
    return {
        "generated_at": _now(),
        "status": "billing_credit_controls_ready_local_no_live_checkout",
        "metering_dimensions": [
            {"id": "ocr_pages", "unit": "page", "heavy_job_threshold": "large or batch OCR requires upgrade/manual approval"},
            {"id": "ai_jobs", "unit": "job", "heavy_job_threshold": "all model extraction, private AI, and deep-research jobs require authorization"},
            {"id": "report_exports", "unit": "export", "heavy_job_threshold": "large/opportunity report exports require authorization"},
            {"id": "source_monitoring", "unit": "refresh_or_watchlist", "heavy_job_threshold": "all monitoring refreshes require authorization"},
            {"id": "agent_api_calls", "unit": "call_or_tool_execution", "heavy_job_threshold": "agent tool execution requires scope and credit checks"},
        ],
        "plans": [
            {"id": "free", "packet_limit": 3, "monthly_credits": 20, "heavy_jobs": "blocked_requires_upgrade"},
            {"id": "pro", "packet_limit": 50, "monthly_credits": 500, "heavy_jobs": "metered"},
            {"id": "business", "packet_limit": 500, "monthly_credits": 5000, "heavy_jobs": "metered_team"},
            {"id": "enterprise", "packet_limit": "contract", "monthly_credits": "contract", "heavy_jobs": "private_contract"},
        ],
        "billable_actions": rows,
        "heavy_job_policy": {
            "status": "heavy_jobs_blocked_without_authorization",
            "free_plan_behavior": "block_before_worker_execution",
            "requires_credit_reservation": True,
            "requires_manual_approval_when_cost_or_external_review_risk_is_high": True,
            "external_charge_created": False,
        },
        "authorization_algorithm": [
            "estimate cost",
            "check plan and credits",
            "block heavy free-plan jobs",
            "require confirmation for OCR batches, AI jobs, source monitoring, and agent/API execution",
            "reserve credits before worker execution",
            "record usage",
            "refund or adjust on failed worker job",
        ],
        "live_checkout_enabled": False,
        "proof_boundary": "Billing controls define metering and cost gates only; no live payment, invoice, or checkout session is created.",
    }


def build_agent_api_manifest() -> dict[str, Any]:
    allowed_tools = [
        "get_supported_countries",
        "get_country_coverage",
        "get_business_logic_phase_report",
        "create_trade_packet",
        "generate_business_decision_report",
        "generate_starter_checklist",
        "generate_missing_evidence_report",
        "generate_chatgpt_safe_summary",
        "generate_broker_packet",
        "get_packet_status",
        "request_billing_quote",
    ]
    forbidden = [
        "approve_import",
        "approve_export",
        "confirm_tariff",
        "confirm_cfia_clearance",
        "provide_legal_advice",
        "verify_supplier",
        "validate_buyer",
        "collect_payment",
        "ship_goods",
        "book_freight",
        "send_email_or_external_message",
        "submit_government_form",
        "send_report_externally_without_confirmation",
    ]
    confirmation_required = {
        "create_trade_packet",
        "generate_business_decision_report",
        "generate_missing_evidence_report",
        "generate_chatgpt_safe_summary",
        "generate_broker_packet",
        "request_billing_quote",
    }
    metered_tools = {
        "generate_business_decision_report",
        "generate_broker_packet",
        "generate_missing_evidence_report",
        "request_billing_quote",
    }
    return {
        "generated_at": _now(),
        "status": "agent_api_manifest_ready_scoped_and_metered",
        "allowed_tools": [
            {
                "name": tool,
                "route": f"/api/agent-tools/{tool}",
                "method": "POST" if tool.startswith(("create", "generate", "request")) else "GET",
                "scope_required": "packet:write" if tool.startswith("create") or tool.startswith("generate") else "packet:read",
                "billing_gate": "metered" if tool in metered_tools else "included_with_limits",
                "requires_confirmation": tool in confirmation_required,
                "audit_event_required": True,
                "audit_event_type": f"agent_tool:{tool}",
                "input_scope_rule": "packet_scoped_fields_only",
                "external_effects_allowed": False,
                "can_open_claim_gate": False,
            }
            for tool in allowed_tools
        ],
        "forbidden_tools": forbidden,
        "forbidden_tool_patterns": [
            "approve_*",
            "confirm_tariff_or_compliance_*",
            "verify_supplier_or_buyer_*",
            "send_or_submit_external_*",
            "book_or_ship_goods_*",
            "collect_payment_*",
        ],
        "scope_rules": [
            "Every tool must execute inside a packet or read-only coverage scope.",
            "Write tools require packet:write scope and cannot modify external systems.",
            "Read tools require packet:read scope and must not expose private uploaded file contents outside the local product.",
            "Billing-sensitive tools require plan and credit authorization before worker execution.",
        ],
        "confirmation_rules": [
            "Customer-visible packet creation, report generation, safe-summary generation, broker packet generation, and billing quotes require explicit user confirmation.",
            "External sends are always disabled even after confirmation.",
            "Confirmation can start local work only; it cannot open customs, tariff, legal, buyer, supplier, payment, or shipment claims.",
        ],
        "audit_rules": [
            "Record actor, organization, packet_id, tool, scope, confirmation state, dry_run flag, and external_effects_allowed for every agent tool call.",
            "Record billing estimate and authorization result before heavy or metered jobs run.",
            "Record blocked forbidden-tool attempts as audit events with can_open_claim_gate=false.",
        ],
        "safety_rules": [
            "Agents can create packets and reports only through backend claim/blocker rules.",
            "Agents cannot approve import/export, tariff, supplier, buyer, shipment, or launch claims.",
            "Billable or heavy jobs require plan/credit authorization before execution.",
            "Agents must preserve audit, confirmation, and scope rules for every tool call.",
        ],
        "proof_boundary": "This is a local API/MCP contract. It does not expose a live public API gateway or payment integration.",
    }


def build_traffic_pages_manifest() -> dict[str, Any]:
    pages = [
        ("import-export-starter-checklist", "Import Export Starter Checklist"),
        ("export-from-canada-checklist", "Export from Canada Checklist"),
        ("import-into-canada-checklist", "Import into Canada Checklist"),
        ("export-documents-checklist", "Export Documents Checklist"),
        ("commercial-invoice-checklist", "Commercial Invoice Checklist"),
        ("packing-list-checklist", "Packing List Checklist"),
        ("certificate-of-origin-checklist", "Certificate of Origin Checklist"),
        ("broker-ready-packet-generator", "Broker-Ready Packet Generator"),
        ("buyer-ready-export-packet-generator", "Buyer-Ready Export Packet Generator"),
        ("food-import-readiness-checker", "Food Import Readiness Checker"),
    ]
    return {
        "generated_at": _now(),
        "status": "traffic_pages_manifest_ready",
        "pages": [
            {
                "slug": slug,
                "title": title,
                "sections": ["short explanation", "simple checklist", "tool CTA", "PDF generation", "account save CTA"],
                "route": f"/tools/{slug}",
                "claim_boundary": "Traffic page educates and routes to the tool; it is not legal, customs, tariff, supplier, buyer, or shipment advice.",
            }
            for slug, title in pages
        ],
    }


def build_research_execution_plan(workflow: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for packet in workflow.get("packets", []):
        category = _category(packet)
        needs_deep_research = any(
            word in category.lower()
            for word in ("food", "health", "animal", "plant", "seafood", "chemical", "medical")
        )
        rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "product_name": packet.get("product_name"),
                "research_mode": "deep_research_required" if needs_deep_research else "standard_research_required",
                "model_prior_use": "allowed_as_first_hypothesis_only",
                "normal_web_search": [
                    "buyer/operator interview targets",
                    "category vocabulary and common document names",
                    "public market orientation sources",
                ],
                "official_source_search": [
                    "country import/export agency sources",
                    "tariff and classification source",
                    "sanctions or restricted party source",
                    "regulated product source if category requires it",
                ],
                "dataset_or_api_needs": [
                    "trade volume or importer/exporter dataset if opportunity ranking is needed",
                    "logistics cost dataset or forwarder quote if route comparison is needed",
                ],
                "expert_or_user_validation": [
                    "customs broker or qualified trade reviewer",
                    "buyer/operator interview",
                    "privacy/security owner if customer data is uploaded",
                ],
                "blocked_claims_until_evidence": [
                    "demand_validated",
                    "country_rules_current",
                    "tariff_or_compliance_confirmed",
                    "supplier_or_buyer_validated",
                    "profitability_confirmed",
                ],
                "next_valid_move": "Collect dated official-source records, dataset references, buyer/operator notes, and qualified review findings before external claims.",
            }
        )
    return {
        "generated_at": _now(),
        "status": "research_execution_ready_with_evidence_gates",
        "rows": rows,
        "proof_boundary": "Research execution routes the work to model-prior, web, official-source, dataset, and expert/user evidence lanes; it does not itself prove the external facts.",
    }


def build_team_workspace(workflow: dict[str, Any]) -> dict[str, Any]:
    packets = workflow.get("packets", [])
    rows = []
    for packet in packets:
        rows.append(
            {
                "workspace_id": f"workspace:{packet.get('packet_id')}",
                "packet_id": packet.get("packet_id"),
                "team": [
                    {"role": "founder_or_customer", "permissions": ["packet_read", "packet_update", "report_download"]},
                    {"role": "operator", "permissions": ["queue_triage", "source_refresh", "review_request"]},
                    {"role": "expert_reviewer", "permissions": ["scoped_packet_read", "finding_submit"]},
                    {"role": "admin", "permissions": ["member_manage", "policy_manage", "audit_read"]},
                ],
                "approval_board": [
                    {"gate": "buyer_validation", "owner": "founder_or_customer", "status": "blocked"},
                    {"gate": "qualified_trade_review", "owner": "expert_reviewer", "status": "blocked"},
                    {"gate": "privacy_security_review", "owner": "admin", "status": "blocked"},
                    {"gate": "private_beta_launch", "owner": "operator", "status": "blocked"},
                ],
                "next_valid_move": "Assign owners, collect evidence, and keep the packet in private review until gates are approved.",
            }
        )
    return {
        "generated_at": _now(),
        "status": "team_workspace_ready_local_with_approval_gates",
        "workspace_count": len(rows),
        "workspaces": rows,
        "proof_boundary": "Team workspace roles and approvals are local coordination surfaces; they do not prove real owner approval or external launch permission.",
    }


def build_expert_network(workflow: dict[str, Any]) -> dict[str, Any]:
    packets = workflow.get("packets", [])
    expert_roles = [
        {
            "role_id": "customs_broker_or_trade_compliance",
            "label": "Customs Broker / Trade Compliance",
            "scope": "tariff, importer-of-record, customs process, broker packet review",
        },
        {
            "role_id": "food_or_regulated_product_reviewer",
            "label": "Food / Regulated Product Reviewer",
            "scope": "CFIA or regulated product requirement review where applicable",
        },
        {
            "role_id": "freight_forwarder",
            "label": "Freight Forwarder",
            "scope": "mode, route, packing, insurance, temperature, and shipment questions",
        },
        {
            "role_id": "privacy_security_reviewer",
            "label": "Privacy / Security Reviewer",
            "scope": "uploaded customer evidence, AI processing, retention, and hosted controls",
        },
        {
            "role_id": "finance_operator",
            "label": "Finance / Operations Reviewer",
            "scope": "credits, pricing, manual approval, and cost exposure",
        },
    ]
    review_queue = []
    for packet in packets:
        for role in expert_roles:
            review_queue.append(
                {
                    "review_id": f"review:{packet.get('packet_id')}:{role['role_id']}",
                    "packet_id": packet.get("packet_id"),
                    "role_id": role["role_id"],
                    "status": "ready_to_request_human_review",
                    "simulated_agent_can_prepare_questions": True,
                    "simulated_agent_can_approve": False,
                    "next_valid_move": "Send scoped packet to a qualified person and record dated finding before opening any external claim.",
                }
            )
    return {
        "generated_at": _now(),
        "status": "expert_network_ready_local_with_human_review_gates",
        "expert_roles": expert_roles,
        "review_queue": review_queue,
        "proof_boundary": "The product can prepare and route expert packets locally; real qualified review remains an external evidence gate.",
    }


def build_billing_usage_ledger(billing: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for packet in workflow.get("packets", []):
        for action in billing.get("billable_actions", []):
            allowed = action.get("free_plan_behavior") != "blocked_requires_upgrade"
            rows.append(
                {
                    "usage_id": f"usage:{packet.get('packet_id')}:{action.get('action')}",
                    "packet_id": packet.get("packet_id"),
                    "action": action.get("action"),
                    "estimated_credits": action.get("estimated_credits"),
                    "authorization_status": "allowed_local" if allowed else "blocked_requires_upgrade_or_manual_approval",
                    "credits_charged": 0,
                    "external_charge_created": False,
                }
            )
    return {
        "generated_at": _now(),
        "status": "billing_usage_ledger_ready_local_no_charges",
        "usage_rows": rows,
        "proof_boundary": "The usage ledger estimates and blocks cost exposure locally; no payment, invoice, or live checkout is performed.",
    }


def build_agent_api_gateway(agent_api: dict[str, Any], billing: dict[str, Any]) -> dict[str, Any]:
    tool_rows = []
    for tool in agent_api.get("allowed_tools", []):
        name = str(tool.get("name"))
        tool_rows.append(
            {
                "tool": name,
                "method": "POST" if name.startswith(("create", "generate", "request")) else "GET",
                "route": f"/api/agent-tools/{name}",
                "scope_required": tool.get("scope_required"),
                "billing_gate": tool.get("billing_gate"),
                "example_request": {
                    "packet_id": "packet-frozen-tuna-canada-001",
                    "dry_run": True,
                    "external_effects_allowed": False,
                },
                "example_response": {
                    "status": "accepted_for_local_execution",
                    "can_open_claim_gate": False,
                    "external_effects_created": False,
                },
            }
        )
    return {
        "generated_at": _now(),
        "status": "agent_api_gateway_ready_local_executor_no_external_effects",
        "tools": tool_rows,
        "forbidden_tools": agent_api.get("forbidden_tools", []),
        "billing_plans": billing.get("plans", []),
        "proof_boundary": "The gateway executes local product operations with external effects disabled; it does not expose a live public API, credentials, payment integration, or claim-opening authority.",
    }


def build_launch_operations(workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": _now(),
        "status": "launch_operations_ready_for_private_beta_review",
        "controls": [
            {"control": "feature_flags", "status": "local_contract_ready", "external_gate": "owner approval required"},
            {"control": "support_queue", "status": "local_contract_ready", "external_gate": "support owner required"},
            {"control": "rollback_plan", "status": "local_contract_ready", "external_gate": "deployment owner required"},
            {"control": "monitoring", "status": "local_contract_ready", "external_gate": "hosted observability required"},
            {"control": "incident_response", "status": "local_contract_ready", "external_gate": "security owner required"},
            {"control": "outcome_log", "status": "local_contract_ready", "external_gate": "real user/operator outcomes required"},
        ],
        "private_beta_entry": {
            "local_product_ready": True,
            "human_approval_required": True,
            "public_launch_allowed": False,
            "next_valid_move": "Use board/private-beta packet to approve or reject a controlled beta after human review gates are signed.",
        },
        "packet_count": len(workflow.get("packets", [])),
        "proof_boundary": "Launch operations are locally specified for private-beta review; they do not approve production deployment or public launch.",
    }


def build_all_stage_readiness(
    workflow: dict[str, Any],
    coverage: dict[str, Any],
    opportunity: dict[str, Any],
    transport: dict[str, Any],
    billing: dict[str, Any],
    agent_api: dict[str, Any],
    traffic: dict[str, Any],
    research: dict[str, Any],
    team: dict[str, Any],
    experts: dict[str, Any],
    usage: dict[str, Any],
    gateway: dict[str, Any],
    launch_ops: dict[str, Any],
) -> dict[str, Any]:
    stages = [
        {
            "stage_id": "stage-00",
            "runbook_stage": 0,
            "state_number": None,
            "name": "Freeze product promise",
            "status": "implemented_local_claim_language_frozen",
            "routes": ["/", "/security", "/ai-data-policy"],
            "artifacts": [
                "PRODUCT_DOCTRINE.md",
                "README.md",
                "docs/PUBLIC_TRADE_READINESS.md",
                "system_review_graph/public_trade_readiness_manifest.json",
                "system_review_graph/claims_gate_matrix.json",
            ],
            "acceptance": "No customer-facing route or report may imply approval, tariff confirmation, CFIA clearance, supplier verification, buyer validation, or legal/customs advice.",
            "local_proof": "Claim-boundary copy, blocked-claims manifests, product check, and package audit all preserve the promise: Before you import or export, know what is missing.",
            "external_gate": "Qualified legal/customs/privacy review is still required before public claims or advice language changes.",
            "next_valid_move": "Keep the promise frozen and route any stronger claim to qualified review plus dated evidence.",
        },
        {
            "stage_id": "stage-01",
            "runbook_stage": 1,
            "state_number": 1,
            "name": "Beginner Start UX",
            "status": "implemented_local",
            "routes": ["/start", "/tools/import-readiness", "/tools/export-readiness", "/tools/document-check"],
            "artifacts": [
                "system_review_graph/generated_reports/starter_checklist_packet-frozen-tuna-canada-001.json",
                "system_review_graph/customer_readiness_report.json",
            ],
            "acceptance": "A beginner can start with unknowns and leave with a starter checklist and blockers.",
            "local_proof": "Starter packet generation preserves unknown answers as missing-evidence blockers.",
            "external_gate": "Real beginner usability still needs private-beta users.",
            "next_valid_move": "Run timed beginner smoke tests with real users and record misunderstandings.",
        },
        {
            "stage_id": "stage-02",
            "runbook_stage": 2,
            "state_number": 2,
            "name": "Real PDF quick check",
            "status": "implemented_local",
            "routes": ["/trade-check", "/tools/document-check", "/public/packets/:id/result"],
            "artifacts": [
                "system_review_graph/public_upload_policy.json",
                "system_review_graph/public_upload_manifest.json",
                "system_review_graph/generated_reports/missing_evidence_packet-frozen-tuna-canada-001.json",
            ],
            "acceptance": "Digital-text PDFs produce extracted fields with confidence; scanned PDFs create OCR_REQUIRED blockers.",
            "local_proof": "Document triage, file limits, native extraction, OCR_REQUIRED routing, and confirmation gates are tested locally.",
            "external_gate": "Hosted upload security and OCR cost controls need qualified security/privacy review before public use.",
            "next_valid_move": "Run public-upload security review and hosted sandbox proof before opening production uploads.",
        },
        {
            "stage_id": "stage-03",
            "runbook_stage": 3,
            "state_number": 3,
            "name": "Field confirmation and missing evidence",
            "status": "implemented_local",
            "routes": [
                "/public/packets/:id/confirm",
                "/packets/:id/evidence",
                "/packets/:id/blockers",
                "/packets/:id/readiness",
            ],
            "artifacts": [
                "system_review_graph/customer_readiness_report.json",
                "system_review_graph/evidence_ledger.json",
                "system_review_graph/blockers.jsonl",
            ],
            "acceptance": "Critical product, country, buyer, supplier, and HS-code fields remain blocked until confirmed or corrected.",
            "local_proof": "Confirmation routes, grouped blockers, evidence ledger, and draft-unconfirmed behavior are exercised in local tests.",
            "external_gate": "Customer acceptance needs real user smoke testing.",
            "next_valid_move": "Observe users correcting extracted fields and record any failed comprehension as blocker rows.",
        },
        {
            "stage_id": "stage-04",
            "runbook_stage": 4,
            "state_number": 4,
            "name": "Customer-grade reports",
            "status": "implemented_local",
            "routes": ["/reports/sample", "/packets/:id/reports", "/api/public/packets/:id/reports/starter.pdf"],
            "artifacts": [
                "system_review_graph/public_report_types.json",
                "system_review_graph/report_exports.json",
                "system_review_graph/generated_reports/broker_packet_packet-frozen-tuna-canada-001.json",
                "system_review_graph/generated_reports/chatgpt_safe_summary_packet-frozen-tuna-canada-001.json",
            ],
            "acceptance": "Reports include summary, trade direction, documents, missing evidence, blocked claims, next valid moves, questions, coverage, AI/no-AI disclosure, and not-advice boundaries.",
            "local_proof": "Starter, missing-evidence, buyer, broker, expert, and ChatGPT-safe report artifacts are generated with closed claims.",
            "external_gate": "Report-language reviewer must approve customer-facing language before public launch.",
            "next_valid_move": "Send generated report samples to product, trade-boundary, and report-language reviewers.",
        },
        {
            "stage_id": "stage-05",
            "runbook_stage": 5,
            "state_number": 5,
            "name": "Public upload hardening",
            "status": "implemented_local_with_security_review_gate",
            "routes": ["/trade-check", "/api/public/packets/:id/delete-files"],
            "artifacts": [
                "system_review_graph/public_upload_policy.json",
                "system_review_graph/audit_events.json",
                "system_review_graph/deletion_requests.json",
            ],
            "acceptance": "Uploaded files are quarantined, generated-named, signature checked, size/page limited, not directly served, audited, deletable, and retention-gated.",
            "local_proof": "Local upload routes enforce PDF limits, no direct serving, delete-files behavior, audit rows, parser limits, rate-limit policy, and malware-scan compensating control.",
            "external_gate": "Production malware scanning, rate-limit enforcement, and public upload sandbox need security signoff.",
            "next_valid_move": "Run hosted upload threat review and decide malware scanning provider or compensating control owner.",
        },
        {
            "stage_id": "stage-06",
            "runbook_stage": 6,
            "state_number": 6,
            "name": "AI/no-AI production controls",
            "status": "implemented_local_fail_closed",
            "routes": ["/settings/ai-data-policy", "/ai-data-policy", "/packets/:id/ai-reviews"],
            "artifacts": [
                "system_review_graph/ai_data_policy.json",
                "system_review_graph/ai_model_router.json",
                "system_review_graph/redaction_pipeline.json",
                "system_review_graph/manual_no_ai_workflow.json",
                "system_review_graph/customer_ai_review_runs.json",
            ],
            "acceptance": "No customer document reaches AI unless organization policy and document permission allow it; AI can create blockers only.",
            "local_proof": "AI validation rejects gate-opening output, unsafe claim language, missing evidence IDs, and cross-organization evidence references.",
            "external_gate": "Live AI providers remain disabled until privacy/security/legal review and explicit configuration.",
            "next_valid_move": "Run prompt-injection/security review against hosted parser and model-route configuration.",
        },
        {
            "stage_id": "stage-07",
            "runbook_stage": 7,
            "state_number": 7,
            "name": "Saved workspace and account path",
            "status": "implemented_local_private_beta",
            "routes": ["/workspace", "/dashboard", "/packets", "/packets/new", "/settings/ai-data-policy"],
            "artifacts": [
                "system_review_graph/customer_workflow.sqlite",
                "system_review_graph/product_runtime_state.json",
                "system_review_graph/auth_rbac_matrix.json",
            ],
            "acceptance": "A user can create/save a packet locally, return through the workspace, inspect history, request deletion, manage AI policy, and use role-gated views.",
            "local_proof": "Local session auth, seeded users/orgs, RBAC, packet history, audit view, report history, and deletion requests are generated and tested.",
            "external_gate": "Hosted identity, account lifecycle, privacy, and deletion process require review before real users.",
            "next_valid_move": "Assign identity/privacy owner and run hosted account/session smoke before private beta.",
        },
        {
            "stage_id": "stage-08",
            "runbook_stage": 8,
            "state_number": 8,
            "name": "External expert review stage",
            "status": experts["status"],
            "routes": ["/expert-network", "/review/:token", "/packets/:id/reviews"],
            "artifacts": [
                "system_review_graph/expert_network_report.json",
                "system_review_graph/review_requests.json",
                "system_review_graph/human_review_findings.json",
                "system_review_graph/expert_review_packet_packet-frozen-tuna-canada-001.md",
                "board/expert_review_packet.md",
            ],
            "acceptance": "Role-specific review packets, scoped review requests, finding ingestion, and blocker conversion exist locally.",
            "local_proof": "The product generates expert queues and scoped review packets while preserving human approval gates.",
            "external_gate": "Real qualified reviewer findings must exist before any public launch or advice claim.",
            "next_valid_move": "Freeze the package and collect scoped findings from security, privacy/legal, AI safety, UX, trade-boundary, logistics, report-language, billing, and ops reviewers.",
        },
        {
            "stage_id": "stage-09",
            "runbook_stage": 9,
            "state_number": 9,
            "name": "Policy/source monitoring",
            "status": "implemented_local_with_refresh_gates",
            "routes": ["/packets/:id/source-monitoring"],
            "artifacts": [
                "system_review_graph/intelligence_hub_policy_monitor.json",
                "system_review_graph/policy_source_snapshots.json",
                "system_review_graph/policy_change_impact_report.json",
                "system_review_graph/policy_intelligence.sqlite",
            ],
            "acceptance": "Monitored source changes can mark packets stale and create review-required alerts.",
            "local_proof": "Source registry, snapshots, hashes, diff classifications, packet impacts, stale blockers, and SQLite store are generated locally.",
            "external_gate": "Live official-source fetching needs terms/robots/API permission and current-source owner review.",
            "next_valid_move": "Approve a source-refresh policy and run dated official-source refresh proof.",
        },
        {
            "stage_id": "stage-10",
            "runbook_stage": 10,
            "state_number": 10,
            "name": "Country coverage logic",
            "status": coverage["status"],
            "routes": ["/country-coverage", "/api/country-coverage"],
            "artifacts": ["system_review_graph/country_coverage_report.json"],
            "acceptance": "Every country-pair result shows coverage level and blocks unsupported country-specific claims.",
            "local_proof": "Tier 0-5 coverage policy, country pair rows, and Tier 5 claim gate are generated and tested.",
            "external_gate": "Country-specific copy above generic readiness needs current sources and qualified review.",
            "next_valid_move": "Promote a country/category only after monitored official sources and expert-reviewed templates exist.",
        },
        {
            "stage_id": "stage-11",
            "runbook_stage": 11,
            "state_number": 11,
            "name": "Opportunity scanner",
            "status": opportunity["status"],
            "routes": ["/opportunities", "/research-plan"],
            "artifacts": [
                "system_review_graph/opportunity_scanner_report.json",
                "system_review_graph/research_execution_plan.json",
                "system_review_graph/research_execution_runs.json",
            ],
            "acceptance": "Opportunity rows show signals, provenance, confidence, buyer-validation-missing state, and create-packet hints without recommendations.",
            "local_proof": "Signal rows, source provenance, confidence fields, and packet-creation hints are generated with demand/profit/buyer claims blocked.",
            "external_gate": "Demand, margin, supplier, and buyer validation remain external evidence lanes.",
            "next_valid_move": "Attach dated market/source/user evidence before treating a signal as an opportunity decision.",
        },
        {
            "stage_id": "stage-12",
            "runbook_stage": 12,
            "state_number": 12,
            "name": "Transport readiness lane",
            "status": transport["status"],
            "routes": ["/transport-readiness", "/api/transport-readiness"],
            "artifacts": ["system_review_graph/transport_readiness_report.json"],
            "acceptance": "The product generates freight-forwarder questions and missing transport evidence without guaranteeing route, cost, or delivery.",
            "local_proof": "Incoterms, mode, weight/dimensions, packing list, commercial invoice, cold-chain, dangerous goods, insurance, and forwarder checks are generated.",
            "external_gate": "Freight-forwarder selection, route, cost, insurance, and delivery claims require qualified/logistics evidence.",
            "next_valid_move": "Send the transport packet to a freight forwarder and record scoped dated feedback.",
        },
        {
            "stage_id": "stage-13",
            "runbook_stage": 13,
            "state_number": 13,
            "name": "Billing and credits",
            "status": billing["status"],
            "routes": ["/pricing", "/billing", "/billing/usage"],
            "artifacts": [
                "system_review_graph/billing_credit_controls.json",
                "system_review_graph/billing_usage_ledger.json",
            ],
            "acceptance": "Heavy actions are blocked behind local credits/subscription/confirmation; live checkout stays disabled until pricing is validated.",
            "local_proof": "OCR, AI, large packets, premium reports, monitoring, agent/API, and expert-review metering rows exist with no live charges.",
            "external_gate": "Live checkout, invoices, refunds, tax, pricing, and payment capture require finance/legal/payment-provider approval.",
            "next_valid_move": "Validate pricing and payment-provider terms before enabling checkout.",
        },
        {
            "stage_id": "stage-14",
            "runbook_stage": 14,
            "state_number": 14,
            "name": "Agent/API layer",
            "status": gateway["status"],
            "routes": ["/agent-api", "/api/agent-tools/:tool"],
            "artifacts": [
                "system_review_graph/agent_api_manifest.json",
                "system_review_graph/agent_api_gateway_contract.json",
            ],
            "acceptance": "Agent calls are scoped, audited, metered, and cannot create external effects without user confirmation.",
            "local_proof": "Allowed and forbidden tools, audit rules, scope rules, confirmation rules, and local executor proof are generated.",
            "external_gate": "Public API gateway, keys, quotas, third-party integrations, and payment routes remain disabled.",
            "next_valid_move": "Run API security review and issue scoped keys only after product-owner approval.",
        },
        {
            "stage_id": "stage-15",
            "runbook_stage": 15,
            "state_number": 15,
            "name": "UX and usability",
            "status": "ui_ux_audited_ready_for_external_review",
            "routes": ["/", "/start", "/trade-check", "/stages", "/operator/queue", "/reports/sample"],
            "artifacts": [
                "system_review_graph/ui_ux_audit_report.json",
                "system_review_graph/operator_dashboard.html",
                "docs/UI_UX_COMPONENT_SYSTEM.md",
            ],
            "acceptance": "Normal users can understand the flow, see plain-English blockers and next actions, and do not misread output as approval.",
            "local_proof": "Local UI audit covers desktop/mobile H1s, labels, overflow, blank controls, stale copy, tracebacks, and local-path leaks.",
            "external_gate": "Five-user usability test remains required before public launch.",
            "next_valid_move": "Run private-beta usability sessions for beginner, document, report, save, and deletion flows.",
        },
        {
            "stage_id": "stage-16",
            "runbook_stage": 16,
            "state_number": 16,
            "name": "Production deployment readiness",
            "status": "deployable_local_stack_ready_with_external_hosting_gates",
            "routes": ["/admin/system-health", "/launch-operations"],
            "artifacts": [
                "docs/DEPLOYMENT.md",
                "docs/SECURITY_PRIVACY.md",
                "system_review_graph/deployment_readiness_report.json",
                "system_review_graph/private_beta_readiness_checklist.json",
                "Dockerfile",
                "compose.yaml",
                ".github/workflows/ci.yml",
            ],
            "acceptance": "Private beta can run only after named owners exist for operations, security, support, rollback, incident response, backups, monitoring, and privacy/terms.",
            "local_proof": "Docker/Compose, env example, health endpoints, deployment report, private-beta checklist, and CI proof exist locally.",
            "external_gate": "Real staging/production hosting, TLS, secrets, backups, monitoring, support, and incident response require operator/security signoff.",
            "next_valid_move": "Provision staging and assign named owners for hosting, security, support, rollback, backups, and incident response.",
        },
        {
            "stage_id": "stage-17",
            "runbook_stage": 17,
            "state_number": 17,
            "name": "Private beta",
            "status": "private_beta_ready_for_human_approval_gates",
            "routes": ["/launch-operations", "/expert-network", "/team-workspace"],
            "artifacts": [
                "system_review_graph/private_beta_readiness_checklist.json",
                "system_review_graph/launch_operations_report.json",
                "system_review_graph/team_workspace_report.json",
                "board/launch_control_checklist.md",
            ],
            "acceptance": "The product has controlled-beta smoke scenarios and owner gates, but real users must complete the flows before beta approval.",
            "local_proof": "Private-beta checklist, launch controls, team workspace, support/feedback path, and closed public-launch state are generated.",
            "external_gate": "Minimum beta users and reviewer/broker/freight-forwarder feedback are not simulated as proof.",
            "next_valid_move": "Recruit beta users, run the listed smoke tests, record outcomes, and fix critical findings.",
        },
        {
            "stage_id": "stage-18",
            "runbook_stage": 18,
            "state_number": 18,
            "name": "Public go-live",
            "status": "public_go_live_subset_defined_blocked_until_approval",
            "routes": ["/start", "/trade-check", "/pricing", "/billing", "/security"],
            "artifacts": [
                "system_review_graph/public_trade_readiness_manifest.json",
                "system_review_graph/launch_operations_report.json",
                "system_review_graph/continuation_plan.json",
                "system_review_graph/board_go_live_readiness_report.json",
            ],
            "acceptance": "The safe public subset is defined and measured locally; public launch stays blocked until costs, support, hosting, reviews, beta outcomes, and owner approval pass.",
            "local_proof": "Beginner starter, PDF quick check, starter/missing-evidence reports, account save, AI/privacy settings, no live approvals, no unrestricted OCR/AI, and no autonomous effects are all represented locally.",
            "external_gate": "Public launch approval, production deployment, legal/privacy/security signoff, monitoring, support, and real-user smoke success are required.",
            "next_valid_move": "After private-beta fixes, run go/no-go and explicitly approve the safe public subset.",
        },
    ]
    return {
        "generated_at": _now(),
        "status": "all_local_stages_implemented_with_external_gates",
        "stage_count": len(stages),
        "implemented_stage_count": len(stages),
        "runbook_stage_range": "0-18",
        "go_live_state_count": 18,
        "external_gate_count": 10,
        "stages": [
            {
                **stage,
                "can_use_locally_now": True,
                "requires_external_evidence": stage["runbook_stage"] in {8, 15, 16, 17, 18},
                "external_claims_opened": False,
                "local_execution_report": "system_review_graph/product_operations_report.json",
            }
            for stage in stages
        ],
        "still_external": [
            "public hosting approval",
            "legal/privacy approval",
            "customs/tariff/CFIA or regulated compliance approval",
            "buyer validation",
            "supplier/manufacturer validation",
            "payment provider activation",
            "real expert signoff",
            "production observability and security signoff",
            "real private-beta user smoke testing",
            "public go-live owner approval",
        ],
        "proof_boundary": "Stage 0 and Stages 1-18 are represented by local routes, APIs, generated artifacts, tests, and blocker rows. Real reviewers, private-beta users, production hosting, monitoring, legal/privacy/security approval, payment activation, qualified trade review, and public go-live owner approval remain external gates.",
    }


def build_completion_platform(workflow: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    coverage = build_country_coverage(workflow, official_sources)
    opportunity = build_opportunity_scanner(workflow, coverage, official_sources)
    business_logic = build_business_logic_phases(workflow, official_sources)
    transport = build_transport_readiness(workflow)
    billing = build_billing_controls()
    agent_api = build_agent_api_manifest()
    traffic = build_traffic_pages_manifest()
    research = build_research_execution_plan(workflow)
    team = build_team_workspace(workflow)
    experts = build_expert_network(workflow)
    usage = build_billing_usage_ledger(billing, workflow)
    gateway = build_agent_api_gateway(agent_api, billing)
    launch_ops = build_launch_operations(workflow)
    all_stages = build_all_stage_readiness(
        workflow,
        coverage,
        opportunity,
        transport,
        billing,
        agent_api,
        traffic,
        research,
        team,
        experts,
        usage,
        gateway,
        launch_ops,
    )
    return {
        "generated_at": _now(),
        "status": "all_local_stages_implemented_with_external_gates",
        "country_coverage": coverage,
        "opportunity_scanner": opportunity,
        "business_logic_phases": business_logic,
        "transport_readiness": transport,
        "billing_credit_controls": billing,
        "agent_api_manifest": agent_api,
        "traffic_pages_manifest": traffic,
        "research_execution_plan": research,
        "team_workspace": team,
        "expert_network": experts,
        "billing_usage_ledger": usage,
        "agent_api_gateway": gateway,
        "launch_operations": launch_ops,
        "all_stage_readiness": all_stages,
        "proof_boundary": "Stage 0 and go-live States 1-18 each have a route/API/artifact surface where locally implementable; production hosting, payment activation, live expert signoff, source freshness, buyer validation, legal/customs/compliance proof, private-beta outcomes, and public launch approval remain external gates.",
    }


def write_completion_platform_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    graph = repo_root / "system_review_graph"
    _write(graph / "completion_platform_manifest.json", payload)
    _write(graph / "country_coverage_report.json", payload["country_coverage"])
    _write(graph / "opportunity_scanner_report.json", payload["opportunity_scanner"])
    _write(graph / "business_logic_phase_report.json", payload["business_logic_phases"])
    _write(graph / "transport_readiness_report.json", payload["transport_readiness"])
    _write(graph / "billing_credit_controls.json", payload["billing_credit_controls"])
    _write(graph / "agent_api_manifest.json", payload["agent_api_manifest"])
    _write(graph / "traffic_pages_manifest.json", payload["traffic_pages_manifest"])
    _write(graph / "research_execution_plan.json", payload["research_execution_plan"])
    _write(graph / "team_workspace_report.json", payload["team_workspace"])
    _write(graph / "expert_network_report.json", payload["expert_network"])
    _write(graph / "billing_usage_ledger.json", payload["billing_usage_ledger"])
    _write(graph / "agent_api_gateway_contract.json", payload["agent_api_gateway"])
    _write(graph / "launch_operations_report.json", payload["launch_operations"])
    _write(graph / "all_stage_readiness_report.json", payload["all_stage_readiness"])
    return payload
