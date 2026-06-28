"""Production expert review network.

Phase 14 turns review from a simulated queue into an evidence-gated product
workflow. The module defines reviewer lanes, credential requirements, scoped
request records, finding templates, claim-gate impacts, and audit rows. It does
not record completed human signoff or open any external claim gate.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_expert_review_network_ready_scope_limited_no_external_claims"

REVIEW_DECISIONS = (
    "approved_for_scope",
    "needs_changes",
    "blocked",
    "not_my_scope",
)

SEVERITY_LEVELS = (
    "info",
    "low",
    "medium",
    "high",
    "critical",
)

FORBIDDEN_EXTERNAL_CLAIMS = (
    "customs_ready",
    "tariff_confirmed",
    "cfia_approved",
    "buyer_validated",
    "supplier_verified",
    "shipment_approved",
    "legal_or_privacy_approved",
    "security_approved",
    "payment_live_ready",
    "public_launch_ready",
)

REVIEWER_LANES: tuple[dict[str, Any], ...] = (
    {
        "reviewer_lane_id": "customs_trade_reviewer",
        "label": "Customs / Trade Boundary Reviewer",
        "scope": "HS candidate, tariff route, importer responsibility, broker-boundary, and customs-language review.",
        "source_ids": ("cbsa-licensed-customs-brokers", "cbsa-import-commercial-goods", "cbsa-customs-tariff-2026", "wco-harmonized-system"),
        "required_credential_evidence": (
            "Licensed customs broker status, customs brokerage employment, or documented customs/trade compliance qualification.",
            "Jurisdiction and product scope statement.",
            "Dated source list or ruling/official correspondence if stronger tariff wording is requested.",
        ),
        "claim_types": ("hs_candidate_research_route", "tariff_route_identified", "tariff_confirmed", "customs_ready"),
    },
    {
        "reviewer_lane_id": "regulated_food_product_reviewer",
        "label": "Food / Regulated Goods Reviewer",
        "scope": "Food, seafood, agri, plant, animal, CFIA/AIRS, permit, certificate, and admissibility-language review.",
        "source_ids": ("cfia-airs", "cbsa-import-commercial-goods"),
        "required_credential_evidence": (
            "Regulated-food, seafood, agri, plant, animal, CFIA, or import-control review experience.",
            "Product-specific composition, intended-use, and country lane reviewed.",
            "Dated AIRS/official-source result or reason it is not applicable.",
        ),
        "claim_types": ("cfia_relevance_route", "regulated_product_review_needed", "cfia_approved"),
    },
    {
        "reviewer_lane_id": "freight_logistics_reviewer",
        "label": "Freight / Logistics Reviewer",
        "scope": "Shipment path, Incoterms responsibility split, importer of record, packing, temperature, insurance, and forwarder questions.",
        "source_ids": ("icc-incoterms-2020", "cbsa-import-commercial-goods"),
        "required_credential_evidence": (
            "Freight forwarding, logistics, customs operations, or shipment planning experience.",
            "Mode, route, Incoterms, packing, and party-responsibility assumptions reviewed.",
            "Clear out-of-scope note for legal/customs approval language.",
        ),
        "claim_types": ("incoterms_responsibility_path", "shipment_approved"),
    },
    {
        "reviewer_lane_id": "market_trade_consultant_reviewer",
        "label": "Market / Buyer Evidence Reviewer",
        "scope": "Market signal, buyer lead route, outreach-readiness, and demand-language review.",
        "source_ids": ("ised-trade-data-online", "canada-cid", "itc-trade-map", "world-bank-wits"),
        "required_credential_evidence": (
            "Trade advisory, export development, buyer research, CRM, or market validation experience.",
            "Dated dataset/source rows and buyer-evidence level reviewed.",
            "Explicit distinction between lead discovery, reply evidence, LOI, PO, and paid-order evidence.",
        ),
        "claim_types": ("market_signal_source_routed", "buyer_lead_route_identified", "buyer_validated"),
    },
    {
        "reviewer_lane_id": "supplier_evidence_reviewer",
        "label": "Supplier Evidence Reviewer",
        "scope": "Supplier evidence checklist, registrations, product documents, certificates, inspections, and supplier-language review.",
        "source_ids": ("india-dgft-foreign-trade-policy",),
        "required_credential_evidence": (
            "Supplier due-diligence, sourcing, inspection, trade compliance, or product certification review experience.",
            "Attached supplier registration/product/certificate/inspection evidence reviewed.",
            "Clear statement that the product does not certify or verify the supplier.",
        ),
        "claim_types": ("supplier_evidence_collected", "supplier_verified"),
    },
    {
        "reviewer_lane_id": "privacy_legal_reviewer",
        "label": "Privacy / Legal Reviewer",
        "scope": "Privacy notice, consent, retention, deletion, data processing, legal-language, and customer-claim boundary review.",
        "source_ids": ("opc-pipeda-principles",),
        "required_credential_evidence": (
            "Privacy, legal, compliance, or data-protection review qualification.",
            "Product-specific data-flow, retention, deletion, vendor, and AI-use scope reviewed.",
            "Signed limitation that the finding is not blanket legal approval.",
        ),
        "claim_types": ("legal_or_privacy_approved",),
    },
    {
        "reviewer_lane_id": "security_upload_reviewer",
        "label": "Security / Upload Reviewer",
        "scope": "File upload pipeline, malware scanning, quarantine, storage isolation, auth, audit, and deletion review.",
        "source_ids": ("owasp-file-upload",),
        "required_credential_evidence": (
            "Application security, cloud security, secure upload, or threat-model review experience.",
            "Evidence of tested file controls, scanning, storage isolation, authorization, CSRF/rate limits, and logging.",
            "Hosted environment and restore/monitoring proof for production scope.",
        ),
        "claim_types": ("security_approved",),
    },
    {
        "reviewer_lane_id": "ai_safety_reviewer",
        "label": "AI Safety Reviewer",
        "scope": "Prompt injection, AI data policy, redaction, no-AI path, provider terms, and model-output label review.",
        "source_ids": ("owasp-llm01-prompt-injection", "nist-ai-rmf"),
        "required_credential_evidence": (
            "AI safety, model risk, prompt-injection, security, privacy, or product-governance review experience.",
            "Prompt-injection test results, redaction tests, model-routing policy, and provider terms reviewed.",
            "Explicit finding that AI remains draft-only and cannot open product gates.",
        ),
        "claim_types": ("ai_output_allowed",),
    },
    {
        "reviewer_lane_id": "report_language_reviewer",
        "label": "Report Language Reviewer",
        "scope": "Customer-facing report wording, uncertainty labels, blocked-claim section, and non-approval language review.",
        "source_ids": ("cbsa-licensed-customs-brokers", "opc-pipeda-principles", "owasp-llm01-prompt-injection"),
        "required_credential_evidence": (
            "Trade, legal/compliance, customer communication, or regulated-product wording review experience.",
            "Exact report artifacts, blocked wording, and allowed scope language reviewed.",
            "Approved wording list and claims the product must not make.",
        ),
        "claim_types": ("report_language_scope",),
    },
    {
        "reviewer_lane_id": "payment_billing_reviewer",
        "label": "Payment / Billing Reviewer",
        "scope": "Paid scope, refund/support wording, checkout, webhook, tax/accounting handoff, and live-payment gate review.",
        "source_ids": ("stripe-go-live",),
        "required_credential_evidence": (
            "Payments, billing operations, finance, Stripe, tax/accounting, or SaaS monetization review experience.",
            "Live-mode object, webhook, API key, duplicate/delayed/out-of-order event, logging, refund, and support evidence reviewed.",
            "Clear confirmation that paid scope is preparation, not approval.",
        ),
        "claim_types": ("payment_live_ready",),
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _source_registry(repo_root: Path) -> dict[str, dict[str, Any]]:
    registry = _load_json(repo_root / "data" / "official_source_registry.json", [])
    if not isinstance(registry, list):
        registry = registry.get("sources", [])
    anchors = _load_json(repo_root / "system_review_graph" / "production_research_anchors.json", [])
    if isinstance(anchors, dict):
        anchors = anchors.get("research_anchors", anchors.get("anchors", []))
    rows: dict[str, dict[str, Any]] = {}
    for row in list(registry) + list(anchors):
        source_id = str(row.get("id") or row.get("source_id") or "")
        if source_id:
            rows[source_id] = row
    return rows


def _packets(repo_root: Path) -> list[dict[str, Any]]:
    workflow = _load_json(repo_root / "system_review_graph" / "customer_readiness_report.json", {})
    packets = workflow.get("packets", [])
    if packets:
        return packets
    runtime = _load_json(repo_root / "system_review_graph" / "product_runtime_state.json", {})
    packets = runtime.get("packets", [])
    if packets:
        return packets
    return [{"packet_id": "packet-frozen-tuna-canada-001", "product_name": "frozen tuna", "destination_country": "Canada"}]


def _claim_rules(repo_root: Path) -> list[dict[str, Any]]:
    claim_gate = _load_json(repo_root / "system_review_graph" / "production_evidence_claim_gate_manifest.json", {})
    rows = claim_gate.get("claim_gate_decisions", [])
    if rows:
        return rows
    matrix = _load_json(repo_root / "system_review_graph" / "claims_gate_matrix.json", [])
    return matrix if isinstance(matrix, list) else matrix.get("claims", [])


def _source_status(source_ids: tuple[str, ...], source_registry: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for source_id in source_ids:
        source = source_registry.get(source_id, {})
        rows.append(
            {
                "source_id": source_id,
                "source_name": source.get("source_name") or source.get("name") or source_id,
                "url": source.get("url", ""),
                "available_in_registry": bool(source),
                "checked_on": source.get("checked_on") or source.get("last_checked") or "",
                "claim_boundary": source.get("claim_boundary") or source.get("use_boundary") or "Reference route only; scoped reviewer must confirm current applicability.",
            }
        )
    return rows


def _reviewer_profiles(source_registry: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    profiles = []
    for lane in REVIEWER_LANES:
        profiles.append(
            {
                "reviewer_profile_id": f"profile-required:{lane['reviewer_lane_id']}",
                "reviewer_lane_id": lane["reviewer_lane_id"],
                "label": lane["label"],
                "profile_status": "missing_real_reviewer",
                "credential_status": "missing",
                "identity_verification_status": "missing",
                "conflict_check_status": "missing",
                "scope": lane["scope"],
                "required_credential_evidence": list(lane["required_credential_evidence"]),
                "source_requirements": _source_status(lane["source_ids"], source_registry),
                "allowed_decisions": list(REVIEW_DECISIONS),
                "severity_levels": list(SEVERITY_LEVELS),
                "can_approve_only_exact_scope": True,
                "can_open_external_claim_gate": False,
                "can_replace_customs_broker_legal_security_payment_approval": False,
                "local_gate_status": "blocked_until_real_credential_and_signed_finding",
            }
        )
    return profiles


def _claim_dependencies(lane: dict[str, Any], claim_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claim_types = set(lane["claim_types"])
    rows = []
    for rule in claim_rules:
        claim_type = str(rule.get("claim_type") or rule.get("claim") or "")
        required_lane = str(rule.get("required_reviewer_lane") or rule.get("reviewer_lane") or "")
        if claim_type in claim_types or lane["reviewer_lane_id"] in required_lane:
            rows.append(
                {
                    "claim_type": claim_type,
                    "current_status": rule.get("decision") or rule.get("status") or rule.get("gate_status") or "blocked_or_reference_only",
                    "required_evidence_types": rule.get("required_evidence_types") or rule.get("evidence_required") or [],
                    "required_reviewer_lane": required_lane or lane["reviewer_lane_id"],
                    "safe_without_real_finding": bool(rule.get("safe_without_reviewer") is True),
                }
            )
    if rows:
        return rows
    return [
        {
            "claim_type": claim_type,
            "current_status": "blocked_until_real_finding",
            "required_evidence_types": ["reviewer_finding"],
            "required_reviewer_lane": lane["reviewer_lane_id"],
            "safe_without_real_finding": False,
        }
        for claim_type in lane["claim_types"]
    ]


def _review_questions(lane_id: str) -> list[str]:
    common = [
        "Is this packet understandable for your exact review scope?",
        "Which evidence is missing before the product may show stronger wording?",
        "Which wording must remain blocked or changed?",
    ]
    lane_questions = {
        "customs_trade_reviewer": [
            "Does the packet correctly avoid acting as a customs broker?",
            "Are HS/tariff/customs statements limited to source routing or scoped findings?",
        ],
        "regulated_food_product_reviewer": [
            "Does the packet route food/agri/seafood or regulated-product questions to the right official source path?",
            "What product details, permits, certificates, or dated source results are missing?",
        ],
        "freight_logistics_reviewer": [
            "Are importer-of-record, Incoterms, packing, temperature, and route responsibilities clear enough for planning?",
            "Which shipment decisions remain unsafe?",
        ],
        "market_trade_consultant_reviewer": [
            "Does the market/buyer evidence language distinguish source-backed signal from demand proof?",
            "What direct buyer evidence is needed next?",
        ],
        "supplier_evidence_reviewer": [
            "Are supplier registration, export ability, product documents, certificates, inspections, and prior shipment evidence separated correctly?",
            "Which supplier-verification wording must stay blocked?",
        ],
        "privacy_legal_reviewer": [
            "Are consent, purpose, retention, deletion, safeguards, and AI-use language adequate for the reviewed scope?",
            "Which legal or privacy claims must not be made?",
        ],
        "security_upload_reviewer": [
            "Are upload controls, scanning, quarantine, storage isolation, authorization, audit, and deletion proof sufficient for the reviewed environment?",
            "What production security proof is missing?",
        ],
        "ai_safety_reviewer": [
            "Do prompt-injection, redaction, model-routing, and no-AI controls keep AI draft-only?",
            "What provider terms or AI-risk evidence is missing?",
        ],
        "report_language_reviewer": [
            "Does report wording preserve uncertainty, blocked claims, and source boundaries?",
            "Which phrases should be approved for exact scope or removed?",
        ],
        "payment_billing_reviewer": [
            "Does paid scope clearly sell preparation, not approval?",
            "Which live checkout, webhook, refund, support, tax, and logging proof is missing?",
        ],
    }
    return common + lane_questions.get(lane_id, [])


def _review_requests(
    packets: list[dict[str, Any]],
    source_registry: dict[str, dict[str, Any]],
    claim_rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for packet in packets:
        packet_id = str(packet.get("packet_id") or "packet")
        for lane in REVIEWER_LANES:
            lane_id = lane["reviewer_lane_id"]
            rows.append(
                {
                    "review_request_id": f"production-review:{packet_id}:{lane_id}",
                    "packet_id": packet_id,
                    "reviewer_lane_id": lane_id,
                    "status": "draft_ready_to_send_no_external_effect",
                    "scoped_review_link_status": "token_required_not_sent",
                    "review_scope": lane["scope"],
                    "questions": _review_questions(lane_id),
                    "required_credential_evidence": list(lane["required_credential_evidence"]),
                    "source_requirements": _source_status(lane["source_ids"], source_registry),
                    "claim_dependencies": _claim_dependencies(lane, claim_rules),
                    "artifacts_in_scope": [
                        f"system_review_graph/production_packet_views/{packet_id}/broker_review_packet.json",
                        "system_review_graph/production_evidence_claim_gate_manifest.json",
                        "system_review_graph/production_decision_scoring_manifest.json",
                        "system_review_graph/production_ai_copilot_manifest.json",
                    ],
                    "out_of_scope_claims": list(FORBIDDEN_EXTERNAL_CLAIMS),
                    "external_effects_created": False,
                    "claims_opened": False,
                    "next_valid_move": "Send this scoped packet to a real qualified reviewer, attach credential evidence and dated findings, then rerun claim gates.",
                }
            )
    return rows


def _finding_templates() -> list[dict[str, Any]]:
    templates = []
    required_fields = [
        "finding_id",
        "review_request_id",
        "reviewer_profile_id",
        "reviewer_name",
        "reviewer_credential_basis",
        "scope_reviewed",
        "artifacts_reviewed",
        "sources_checked",
        "evidence_attachments",
        "decision",
        "severity",
        "approved_scope",
        "required_changes",
        "blocked_claims",
        "signed_at",
    ]
    for lane in REVIEWER_LANES:
        templates.append(
            {
                "finding_template_id": f"finding-template:{lane['reviewer_lane_id']}",
                "reviewer_lane_id": lane["reviewer_lane_id"],
                "required_fields": required_fields,
                "allowed_decisions": list(REVIEW_DECISIONS),
                "severity_levels": list(SEVERITY_LEVELS),
                "source_ids_required": list(lane["source_ids"]),
                "evidence_attachments_required": True,
                "approved_for_scope_requires": [
                    "real reviewer identity",
                    "credential basis",
                    "scope reviewed",
                    "dated finding",
                    "artifacts reviewed",
                    "source/evidence attachments",
                    "explicit blocked-claim list",
                ],
                "can_open_external_claim_gate": False,
                "can_update_only_scope_limited_wording": True,
                "forbidden_claims_remain_blocked": list(FORBIDDEN_EXTERNAL_CLAIMS),
            }
        )
    return templates


def _pending_findings(review_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "finding_id": f"pending-finding:{request['review_request_id']}",
            "review_request_id": request["review_request_id"],
            "reviewer_lane_id": request["reviewer_lane_id"],
            "status": "awaiting_real_reviewer_finding",
            "decision": "not_submitted",
            "severity": "unknown",
            "approved_scope": "",
            "evidence_attachments": [],
            "claims_opened": False,
            "external_effects_created": False,
            "next_valid_move": request["next_valid_move"],
        }
        for request in review_requests
    ]


def _gate_impacts(review_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for request in review_requests:
        for dependency in request["claim_dependencies"]:
            rows.append(
                {
                    "gate_impact_id": f"gate-impact:{request['review_request_id']}:{dependency['claim_type']}",
                    "review_request_id": request["review_request_id"],
                    "reviewer_lane_id": request["reviewer_lane_id"],
                    "claim_type": dependency["claim_type"],
                    "current_status": dependency["current_status"],
                    "impact_without_real_finding": "claim_remains_blocked_or_reference_only",
                    "can_show_after_local_request_only": False,
                    "can_show_after_real_scope_finding": "scope_limited_preparation_language_only",
                    "can_open_external_claim_gate": False,
                    "forbidden_claims_remain_blocked": list(FORBIDDEN_EXTERNAL_CLAIMS),
                }
            )
    return rows


def _audit_events(review_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "audit_event_id": f"audit:{request['review_request_id']}",
            "event_type": "production_review_request_drafted",
            "packet_id": request["packet_id"],
            "reviewer_lane_id": request["reviewer_lane_id"],
            "external_effects_created": False,
            "claims_opened": False,
            "created_at": _now(),
            "detail": "Draft scoped review request generated locally; no reviewer contacted and no approval recorded.",
        }
        for request in review_requests
    ]


def build_production_expert_review_network(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    source_registry = _source_registry(root)
    packets = _packets(root)
    claim_rules = _claim_rules(root)
    profiles = _reviewer_profiles(source_registry)
    review_requests = _review_requests(packets, source_registry, claim_rules)
    finding_templates = _finding_templates()
    pending_findings = _pending_findings(review_requests)
    gate_impacts = _gate_impacts(review_requests)
    audit_events = _audit_events(review_requests)
    source_ids = sorted({source_id for lane in REVIEWER_LANES for source_id in lane["source_ids"]})
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "reviewer_lane_count": len(REVIEWER_LANES),
        "profile_requirement_count": len(profiles),
        "review_request_count": len(review_requests),
        "finding_template_count": len(finding_templates),
        "pending_finding_count": len(pending_findings),
        "gate_impact_count": len(gate_impacts),
        "audit_event_count": len(audit_events),
        "source_ids": source_ids,
        "source_registry_coverage_count": sum(1 for source_id in source_ids if source_id in source_registry),
        "review_decisions": list(REVIEW_DECISIONS),
        "severity_levels": list(SEVERITY_LEVELS),
        "reviewer_lanes": list(REVIEWER_LANES),
        "reviewer_profiles": profiles,
        "review_requests": review_requests,
        "finding_templates": finding_templates,
        "pending_findings": pending_findings,
        "gate_impacts": gate_impacts,
        "audit_events": audit_events,
        "real_reviewer_signoff_recorded": False,
        "qualified_credentials_verified": False,
        "scope_limited_approval_recorded": False,
        "can_open_customs_tariff_cfia_buyer_supplier_security_privacy_payment_launch_gate": False,
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "The product can draft scoped review requests and finding templates; only real qualified reviewers with evidence attachments can create scoped findings, and those findings cannot become blanket approval.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _doc(manifest: dict[str, Any]) -> str:
    lane_lines = "\n".join(
        f"- {lane['label']}: {lane['scope']}"
        for lane in manifest["reviewer_lanes"]
    )
    return f"""# Production Expert Review Network

Status: `{manifest['status']}`

This phase turns human review into a product workflow. It defines reviewer
lanes, credential evidence, scoped review requests, finding templates, claim
gate impact rows, and audit events. It does not record completed human findings.

## Reviewer Lanes

{lane_lines}

## Counts

- Reviewer lanes: {manifest['reviewer_lane_count']}
- Profile requirements: {manifest['profile_requirement_count']}
- Draft review requests: {manifest['review_request_count']}
- Finding templates: {manifest['finding_template_count']}
- Gate impact rows: {manifest['gate_impact_count']}

## Gate Boundary

- Real reviewer signoff recorded: {str(manifest['real_reviewer_signoff_recorded']).lower()}
- Qualified credentials verified: {str(manifest['qualified_credentials_verified']).lower()}
- Scope-limited approval recorded: {str(manifest['scope_limited_approval_recorded']).lower()}
- Claims opened: {str(manifest['claims_opened']).lower()}
- External effects created: {str(manifest['external_effects_created']).lower()}

The final rule is: no reviewer lane, no claim lane. A reviewer can approve only
the exact scoped wording or workflow they reviewed, and only after credential
evidence, source/evidence attachments, and a dated finding are stored.
"""


def write_production_expert_review_network_artifacts(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Path]:
    root = repo_root or Path(__file__).resolve().parents[2]
    srg = root / "system_review_graph"
    docs = root / "docs"
    profiles = {
        "status": "production_reviewer_profiles_credentials_required",
        "profiles": manifest["reviewer_profiles"],
    }
    requests = {
        "status": "production_review_requests_ready_no_external_effects",
        "review_requests": manifest["review_requests"],
        "pending_findings": manifest["pending_findings"],
        "audit_events": manifest["audit_events"],
    }
    findings = {
        "status": "production_review_finding_contracts_ready_scope_limited",
        "finding_templates": manifest["finding_templates"],
        "gate_impacts": manifest["gate_impacts"],
    }
    paths = {
        "manifest": srg / "production_expert_review_network_manifest.json",
        "profiles": srg / "production_reviewer_profiles.json",
        "requests": srg / "production_review_requests.json",
        "findings": srg / "production_review_finding_contracts.json",
        "doc": docs / "PRODUCTION_EXPERT_REVIEW_NETWORK.md",
    }
    _write_json(paths["manifest"], manifest)
    _write_json(paths["profiles"], profiles)
    _write_json(paths["requests"], requests)
    _write_json(paths["findings"], findings)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(_doc(manifest), encoding="utf-8")
    return paths
