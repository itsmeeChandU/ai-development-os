"""Investor pitch readiness for the importer source readiness product."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

REQUIRED_EVIDENCE_TYPES = {
    "market_scale",
    "official_trade_data",
    "regulatory_workflow",
    "compliance_complexity",
}

DILIGENCE_LANES = [
    {
        "id": "vc-buyer-discovery",
        "owner": "product",
        "required_evidence": "10 to 15 dated importer, broker, operator, or sourcing lead conversations.",
        "next_valid_move": "Run buyer discovery and attach notes or no-fit evidence before claiming demand.",
    },
    {
        "id": "vc-design-partner",
        "owner": "founder",
        "required_evidence": "At least one written design-partner or pilot-intent artifact.",
        "next_valid_move": "Convert warm operator interest into a dated pilot-intent or rejection note.",
    },
    {
        "id": "vc-compliance-review",
        "owner": "compliance",
        "required_evidence": "Qualified customs, food safety, and claims-language review.",
        "next_valid_move": "Have a qualified reviewer inspect the country matrix and pitch claims.",
    },
    {
        "id": "vc-data-rights",
        "owner": "data",
        "required_evidence": "Source-rights, refresh cadence, and allowed-use proof for official and commercial sources.",
        "next_valid_move": "Document data rights and repeatable refresh proof before scaling beyond fixtures.",
    },
    {
        "id": "vc-business-model",
        "owner": "founder",
        "required_evidence": "Pricing hypothesis, ICP, sales motion, and first 90-day experiment plan.",
        "next_valid_move": "Validate willingness to pay during buyer discovery and update the pitch packet.",
    },
    {
        "id": "vc-legal-financing",
        "owner": "founder",
        "required_evidence": "Entity, IP, cap table, financing terms, and securities-law review.",
        "next_valid_move": "Confirm fundraising terms with counsel before sending investor documents.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _unsafe_gates_closed(report: dict[str, Any], external: dict[str, Any]) -> bool:
    unsafe_rows = [
        row
        for row in report.get("rows", [])
        for value in (row.get("unsafe_counters") or {}).values()
        if int(value or 0) != 0
    ]
    external_unsafe = [
        key
        for key, value in (external.get("unsafe_gates") or {}).items()
        if int(value or 0) != 0
    ]
    return not unsafe_rows and not external_unsafe


def _evidence_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_types = {str(row.get("type") or "") for row in rows}
    missing = sorted(REQUIRED_EVIDENCE_TYPES - evidence_types)
    malformed = [
        str(row.get("id") or "unknown")
        for row in rows
        if not row.get("source_url") or not row.get("claim_boundary") or not row.get("accessed_at")
    ]
    return {
        "required_types": sorted(REQUIRED_EVIDENCE_TYPES),
        "provided_types": sorted(evidence_types),
        "missing_types": missing,
        "malformed_rows": malformed,
        "source_count": len(rows),
        "ready": not missing and not malformed,
    }


def build_vc_pitch_readiness(
    *,
    readiness: dict[str, Any],
    external: dict[str, Any],
    continuation: dict[str, Any],
    investor_evidence: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    evidence = _evidence_status(investor_evidence)
    demo_ready = (
        readiness.get("status") == "ready_with_external_gates"
        and external.get("status") == "ready_with_external_gates"
        and _unsafe_gates_closed(readiness, external)
    )
    continuation_ready = (
        continuation.get("status") == "startup_in_progress"
        and continuation.get("must_continue") is True
        and int(continuation.get("lane_count") or 0) >= 5
    )
    pitch_ready = demo_ready and continuation_ready and evidence["ready"]

    return {
        "generated_at": generated_at or _now(),
        "status": "vc_pitch_ready_with_diligence_gates" if pitch_ready else "vc_pitch_blocked",
        "pitch_mode": "private_investor_conversation",
        "product": "Importer Source Readiness Copilot",
        "one_line": (
            "A blocked-safe operator copilot that turns importer/exporter source packets "
            "into readiness status, evidence lanes, and next valid moves before teams overclaim."
        ),
        "demo_ready": demo_ready,
        "continuation_ready": continuation_ready,
        "evidence_ready": evidence["ready"],
        "evidence_status": evidence,
        "readiness_status": readiness.get("status"),
        "external_gate_status": external.get("status"),
        "startup_continuation_status": continuation.get("status"),
        "continuation_lane_count": continuation.get("lane_count"),
        "open_external_blockers": int(readiness.get("blocker_count") or 0)
        + int(external.get("blocker_count") or 0),
        "investor_sources": investor_evidence,
        "pitch_claims": [
            {
                "id": "problem",
                "claim": (
                    "Import/export source work has real proof gaps across official sources, "
                    "country rules, buyer validation, contracts, and qualified review."
                ),
                "evidence": [
                    "system_review_graph/readiness_report.json",
                    "system_review_graph/external_gate_report.json",
                    "data/investor_evidence.json",
                ],
                "boundary": "Problem framing only; not legal, customs, tariff, supplier, or buyer advice.",
            },
            {
                "id": "product",
                "claim": (
                    "The local product loop can demonstrate blocked-safe source-card evaluation, "
                    "operator dashboard output, continuation lanes, and proof gates."
                ),
                "evidence": [
                    "system_review_graph/operator_dashboard.html",
                    "system_review_graph/continuation_plan.json",
                    "python3 scripts/check_product.py",
                ],
                "boundary": "Demo readiness only; not external operational readiness.",
            },
            {
                "id": "wedge",
                "claim": (
                    "The wedge is internal operator readiness for import/export source packets "
                    "before teams make public, commercial, supplier, or compliance claims."
                ),
                "evidence": ["investor/demo_script.md", "investor/diligence_room_index.md"],
                "boundary": "Strategy hypothesis pending buyer discovery and design partners.",
            },
        ],
        "draft_funding_ask": {
            "amount_usd": 500000,
            "instrument": "draft pre-seed SAFE or equivalent, subject to counsel",
            "runway_months": 12,
            "use_of_funds": [
                "buyer discovery and design-partner pilots",
                "qualified compliance review and claim-boundary design",
                "source-rights, refresh, and data integration",
                "operator UI and workflow automation",
                "security, audit, and GitHub/SRG/code-review graph integration",
            ],
            "boundary": "Draft planning assumption only; not an offering document or legal/financial advice.",
        },
        "diligence_lanes": [
            {
                **lane,
                "status": "open_diligence_gate",
                "unsafe_to_bypass": True,
            }
            for lane in DILIGENCE_LANES
        ],
        "closed_claims": [
            "public_launch_ready",
            "fully_operational",
            "revenue_proven",
            "product_market_fit_proven",
            "qualified_compliance_ready",
            "customs_or_tariff_advice_ready",
            "supplier_recommendation_ready",
            "buyer_validated",
        ],
        "demo_script": [
            "Run python3 scripts/check_product.py and show PASS output.",
            "Open system_review_graph/operator_dashboard.html.",
            "Show readiness_report.json and external_gate_report.json blockers.",
            "Show continuation_plan.json to prove the product knows what must continue.",
            "Show investor/vc_pitch_deck.md and diligence_room_index.md for the VC conversation.",
        ],
        "next_valid_move": (
            "Use the pitch packet for private VC conversations while opening buyer discovery, "
            "design-partner, compliance, data-rights, business-model, and financing diligence lanes."
            if pitch_ready
            else "Fix missing investor evidence, demo proof, or continuation lanes before pitching."
        ),
        "proof_boundary": (
            "This report supports an honest private VC pitch. It does not prove traction, revenue, "
            "legal/compliance approval, supplier readiness, customs/tariff advice, public launch "
            "readiness, or external operational readiness."
        ),
    }
