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
                    "status": "accepted_for_local_dry_run",
                    "can_open_claim_gate": False,
                    "external_effects_created": False,
                },
            }
        )
    return {
        "generated_at": _now(),
        "status": "agent_api_gateway_ready_local_dry_run",
        "tools": tool_rows,
        "forbidden_tools": agent_api.get("forbidden_tools", []),
        "billing_plans": billing.get("plans", []),
        "proof_boundary": "The gateway contract is executable as local dry-run routes; it does not expose a live public API, credentials, payment integration, or claim-opening authority.",
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
        ("stage-00", "Beginner starter", "implemented_local", ["/start"], ["Starter Checklist.pdf"]),
        ("stage-01", "PDF quick check", "implemented_local", ["/trade-check", "/tools/document-check"], ["public_upload_manifest.json"]),
        ("stage-02", "Confirmation and missing evidence", "implemented_local", ["/public/packets/:id/confirm"], ["Missing Evidence Checklist.pdf"]),
        ("stage-03", "Saved workspace", "implemented_local", ["/workspace", "/packets"], ["customer_workflow.sqlite"]),
        ("stage-04", "AI/no-AI routing", "implemented_local_with_policy_gates", ["/settings/ai-data-policy", "/ai-data-policy"], ["ai_model_router.json"]),
        ("stage-05", "Policy source monitoring", "implemented_local_with_refresh_gates", ["/packets/:id/source-monitoring"], ["intelligence_hub_policy_monitor.json"]),
        ("stage-06", "Opportunity scanner", opportunity["status"], ["/opportunities"], ["opportunity_scanner_report.json"]),
        ("stage-07", "Country coverage", coverage["status"], ["/country-coverage"], ["country_coverage_report.json"]),
        ("stage-08", "Transport readiness", transport["status"], ["/transport-readiness"], ["transport_readiness_report.json"]),
        ("stage-09", "Billing and credits", billing["status"], ["/pricing", "/billing"], ["billing_credit_controls.json", "billing_usage_ledger.json"]),
        ("stage-10", "Agent/API layer", gateway["status"], ["/agent-api"], ["agent_api_manifest.json", "agent_api_gateway_contract.json"]),
        ("stage-11", "Traffic and sample reports", traffic["status"], ["/reports/sample", "/tools/:slug"], ["traffic_pages_manifest.json"]),
        ("stage-12", "Research execution", research["status"], ["/research-plan"], ["research_execution_plan.json"]),
        ("stage-13", "Expert network", experts["status"], ["/expert-network"], ["expert_network_report.json"]),
        ("stage-14", "Team workspace", team["status"], ["/team-workspace"], ["team_workspace_report.json"]),
        ("stage-15", "Launch operations", launch_ops["status"], ["/launch-operations"], ["launch_operations_report.json"]),
    ]
    return {
        "generated_at": _now(),
        "status": "all_local_stages_implemented_with_external_gates",
        "stage_count": len(stages),
        "implemented_stage_count": len(stages),
        "external_gate_count": 8,
        "stages": [
            {
                "stage_id": stage_id,
                "name": name,
                "status": status,
                "routes": routes,
                "artifacts": artifacts,
                "can_use_locally_now": True,
                "external_claims_opened": False,
                "next_valid_move": "Use locally, collect real evidence, and keep external claims closed until owner or qualified-human approval.",
            }
            for stage_id, name, status, routes, artifacts in stages
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
        ],
        "proof_boundary": "All locally implementable product stages are represented by usable routes, APIs, artifacts, and tests. Real-world approvals remain explicit gates.",
    }


def build_completion_platform(workflow: dict[str, Any], official_sources: list[dict[str, Any]]) -> dict[str, Any]:
    coverage = build_country_coverage(workflow, official_sources)
    opportunity = build_opportunity_scanner(workflow, coverage)
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
        "proof_boundary": "Every locally implementable stage has a route/API/artifact surface; production hosting, payment activation, live expert signoff, source freshness, buyer validation, legal/customs/compliance proof, and public launch remain external gates.",
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
    _write(graph / "research_execution_plan.json", payload["research_execution_plan"])
    _write(graph / "team_workspace_report.json", payload["team_workspace"])
    _write(graph / "expert_network_report.json", payload["expert_network"])
    _write(graph / "billing_usage_ledger.json", payload["billing_usage_ledger"])
    _write(graph / "agent_api_gateway_contract.json", payload["agent_api_gateway"])
    _write(graph / "launch_operations_report.json", payload["launch_operations"])
    _write(graph / "all_stage_readiness_report.json", payload["all_stage_readiness"])
    return payload
