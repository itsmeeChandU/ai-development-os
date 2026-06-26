"""Completion-stage local contracts for the Trade Readiness platform."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _category(packet: dict[str, Any]) -> str:
    return str(packet.get("product_category") or "general_trade").strip() or "general_trade"


def build_country_coverage(workflow: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    countries = sorted(
        {
            str(packet.get(key))
            for packet in workflow.get("packets", [])
            for key in ("origin_country", "destination_country")
            if packet.get(key)
        }
        | {"Canada", "India", "United States", "United Kingdom", "Generic"}
    )
    source_count_by_country: dict[str, int] = {}
    for source in official_sources:
        jurisdiction = str(source.get("jurisdiction") or "Generic")
        country = "Canada" if jurisdiction in {"CA", "Canada"} else jurisdiction
        source_count_by_country[country] = source_count_by_country.get(country, 0) + 1
    rows = []
    for country in countries:
        count = source_count_by_country.get(country, 0)
        tier = 3 if country == "Canada" and count >= 5 else 1 if country not in {"", "Generic"} else 0
        rows.append(
            {
                "country": country,
                "coverage_tier": tier,
                "coverage_label": {
                    0: "selectable only",
                    1: "generic starter checklist",
                    2: "reference sources catalogued",
                    3: "monitored sources",
                    4: "category template support",
                    5: "expert-reviewed templates",
                }[tier],
                "source_count": count,
                "can_make_country_specific_claims": False,
                "next_valid_move": "Add monitored official sources and expert-reviewed templates before country-specific claims.",
            }
        )
    packet_rows = []
    for packet in workflow.get("packets", []):
        origin = str(packet.get("origin_country") or "Generic")
        destination = str(packet.get("destination_country") or "Generic")
        origin_tier = next((row["coverage_tier"] for row in rows if row["country"] == origin), 1)
        destination_tier = next((row["coverage_tier"] for row in rows if row["country"] == destination), 1)
        effective = min(origin_tier, destination_tier)
        packet_rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "origin_country": origin,
                "destination_country": destination,
                "product_category": _category(packet),
                "effective_coverage_tier": effective,
                "coverage_status": "country_specific_claims_blocked",
                "next_valid_move": "Use generic readiness output unless both countries and category have monitored/expert-reviewed coverage.",
            }
        )
    return {
        "generated_at": _now(),
        "status": "country_coverage_ready_with_claim_gates",
        "coverage_levels": {
            "0": "selectable only",
            "1": "generic starter checklist",
            "2": "reference sources catalogued",
            "3": "monitored sources",
            "4": "category template support",
            "5": "expert-reviewed templates",
        },
        "countries": rows,
        "packet_coverage": packet_rows,
        "proof_boundary": "Coverage tiers describe product support level only; they do not prove country-specific legal, customs, tariff, or compliance correctness.",
    }


def build_opportunity_scanner(workflow: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for packet in workflow.get("packets", []):
        category = _category(packet)
        coverage_row = next(
            (row for row in coverage.get("packet_coverage", []) if row.get("packet_id") == packet.get("packet_id")),
            {},
        )
        complexity = "high" if any(word in category.lower() for word in ("food", "health", "animal", "plant", "seafood")) else "medium"
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
                "coverage_confidence": coverage_row.get("effective_coverage_tier", 0),
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
        "blocked_claims": ["guaranteed_demand", "profitable_product", "confirmed_surplus", "buyer_validated"],
        "proof_boundary": "Opportunity rows are signals and research prompts only, not recommendations, demand proof, margin proof, or buyer validation.",
    }


def build_transport_readiness(workflow: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for packet in workflow.get("packets", []):
        missing = []
        if str(packet.get("incoterms_if_known") or "unknown") == "unknown":
            missing.append("Incoterms or delivery responsibility")
        if not packet.get("shipping_method"):
            missing.append("Transport mode")
        for item in ("dimensions/weight", "packing list", "insurance decision", "ports", "forwarder"):
            missing.append(item)
        if any(word in _category(packet).lower() for word in ("food", "seafood", "health")):
            missing.append("Temperature/cold-chain requirement")
        rows.append(
            {
                "packet_id": packet.get("packet_id"),
                "status": "transport_questions_ready_claims_blocked",
                "missing_transport_inputs": missing,
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
        ("ocr_page", 2, True),
        ("ai_extraction", 4, True),
        ("large_document_packet", 10, True),
        ("saved_workspace", 1, False),
        ("buyer_ready_packet", 3, False),
        ("broker_ready_packet", 3, False),
        ("source_monitoring", 5, True),
        ("opportunity_report", 4, True),
        ("expert_review_request", 0, True),
        ("private_ai", 8, True),
        ("api_agent_usage", 2, True),
    ]
    rows = [
        {
            "action": action,
            "estimated_credits": credits,
            "heavy_job": heavy,
            "free_plan_behavior": "blocked_requires_upgrade" if heavy else "allowed_with_limits",
            "external_charge_created": False,
        }
        for action, credits, heavy in actions
    ]
    return {
        "generated_at": _now(),
        "status": "billing_credit_controls_ready_local_no_live_checkout",
        "plans": [
            {"id": "free", "packet_limit": 3, "monthly_credits": 20, "heavy_jobs": "blocked_requires_upgrade"},
            {"id": "pro", "packet_limit": 50, "monthly_credits": 500, "heavy_jobs": "metered"},
            {"id": "business", "packet_limit": 500, "monthly_credits": 5000, "heavy_jobs": "metered_team"},
            {"id": "enterprise", "packet_limit": "contract", "monthly_credits": "contract", "heavy_jobs": "private_contract"},
        ],
        "billable_actions": rows,
        "authorization_algorithm": [
            "estimate cost",
            "check plan and credits",
            "block heavy free-plan jobs",
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
        "create_trade_packet",
        "generate_starter_checklist",
        "generate_missing_evidence_report",
        "generate_chatgpt_safe_summary",
        "generate_broker_packet",
        "get_packet_status",
        "request_billing_quote",
    ]
    forbidden = [
        "approve_import",
        "confirm_tariff",
        "verify_supplier",
        "validate_buyer",
        "ship_goods",
        "send_report_externally_without_confirmation",
    ]
    return {
        "generated_at": _now(),
        "status": "agent_api_manifest_ready_scoped_and_metered",
        "allowed_tools": [
            {
                "name": tool,
                "scope_required": "packet:write" if tool.startswith("create") or tool.startswith("generate") else "packet:read",
                "billing_gate": "metered" if tool in {"generate_broker_packet", "generate_missing_evidence_report", "request_billing_quote"} else "included_with_limits",
                "can_open_claim_gate": False,
            }
            for tool in allowed_tools
        ],
        "forbidden_tools": forbidden,
        "safety_rules": [
            "Agents can create packets and reports only through backend claim/blocker rules.",
            "Agents cannot approve import/export, tariff, supplier, buyer, shipment, or launch claims.",
            "Billable or heavy jobs require plan/credit authorization before execution.",
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


def build_completion_platform(workflow: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    coverage = build_country_coverage(workflow, official_sources)
    opportunity = build_opportunity_scanner(workflow, coverage)
    transport = build_transport_readiness(workflow)
    billing = build_billing_controls()
    agent_api = build_agent_api_manifest()
    traffic = build_traffic_pages_manifest()
    return {
        "generated_at": _now(),
        "status": "completion_platform_contracts_ready_with_external_gates",
        "country_coverage": coverage,
        "opportunity_scanner": opportunity,
        "transport_readiness": transport,
        "billing_credit_controls": billing,
        "agent_api_manifest": agent_api,
        "traffic_pages_manifest": traffic,
        "proof_boundary": "Completion-stage contracts make the next product stages executable locally; production hosting, payments, source monitoring, traffic validation, and qualified review remain external gates.",
    }


def write_completion_platform_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    graph = repo_root / "system_review_graph"
    _write(graph / "completion_platform_manifest.json", payload)
    _write(graph / "country_coverage_report.json", payload["country_coverage"])
    _write(graph / "opportunity_scanner_report.json", payload["opportunity_scanner"])
    _write(graph / "transport_readiness_report.json", payload["transport_readiness"])
    _write(graph / "billing_credit_controls.json", payload["billing_credit_controls"])
    _write(graph / "agent_api_manifest.json", payload["agent_api_manifest"])
    _write(graph / "traffic_pages_manifest.json", payload["traffic_pages_manifest"])
    return payload
