"""Board-to-go-live readiness for the Canadian importer source product."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

REQUIRED_CANADIAN_TOOL_CATEGORIES = {
    "business_planning",
    "controlled_imports",
    "customs_accounting",
    "cybersecurity",
    "financial_planning",
    "food_import_requirements",
    "import_workflow",
    "importer_discovery",
    "permits_licences",
    "privacy",
    "qualified_reviewer_discovery",
    "restricted_party_screening",
    "tariff_classification",
    "trade_data",
}

REQUIRED_EXPERT_REVIEW_IDS = {
    "product-operator",
    "canadian-trade-compliance",
    "financial-advisor",
    "legal-privacy",
    "data-source",
    "security-ops",
}

ALLOWED_LAUNCH_CONTROL_STATUSES = {"implemented", "approval_required"}
HUMAN_APPROVAL_STATUS = "approval_required"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _unsafe_gates_closed(readiness: dict[str, Any], external: dict[str, Any]) -> bool:
    readiness_open = [
        key
        for row in readiness.get("rows", [])
        for key, value in (row.get("unsafe_counters") or {}).items()
        if int(value or 0) != 0
    ]
    external_open = [
        key
        for key, value in (external.get("unsafe_gates") or {}).items()
        if int(value or 0) != 0
    ]
    return not readiness_open and not external_open


def _canadian_tool_status(tools: list[dict[str, Any]]) -> dict[str, Any]:
    categories = {str(row.get("category") or "") for row in tools}
    malformed = [
        str(row.get("id") or "unknown")
        for row in tools
        if row.get("jurisdiction") != "CA"
        or not row.get("source_url")
        or not row.get("accessed_at")
        or not row.get("claim_boundary")
    ]
    missing = sorted(REQUIRED_CANADIAN_TOOL_CATEGORIES - categories)
    return {
        "required_categories": sorted(REQUIRED_CANADIAN_TOOL_CATEGORIES),
        "provided_categories": sorted(categories),
        "missing_categories": missing,
        "malformed_rows": malformed,
        "tool_count": len(tools),
        "ready": not missing and not malformed,
    }


def _expert_review_status(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    review_ids = {str(row.get("id") or "") for row in reviews}
    missing = sorted(REQUIRED_EXPERT_REVIEW_IDS - review_ids)
    incomplete = [
        str(row.get("id") or "unknown")
        for row in reviews
        if row.get("status") != "agent_review_complete"
        or not row.get("human_approval_gate")
        or not row.get("findings")
        or not row.get("implemented_inputs")
    ]
    return {
        "required_reviews": sorted(REQUIRED_EXPERT_REVIEW_IDS),
        "provided_reviews": sorted(review_ids),
        "missing_reviews": missing,
        "incomplete_reviews": incomplete,
        "review_count": len(reviews),
        "ready": not missing and not incomplete,
    }


def _launch_control_status(controls: list[dict[str, Any]]) -> dict[str, Any]:
    invalid = [
        str(row.get("id") or "unknown")
        for row in controls
        if row.get("status") not in ALLOWED_LAUNCH_CONTROL_STATUSES
        or not row.get("owner")
        or not row.get("evidence")
        or not row.get("next_valid_move")
    ]
    human_approval_controls = [
        row for row in controls if row.get("status") == HUMAN_APPROVAL_STATUS
    ]
    implemented_controls = [row for row in controls if row.get("status") == "implemented"]
    return {
        "invalid_controls": invalid,
        "implemented_count": len(implemented_controls),
        "human_approval_gate_count": len(human_approval_controls),
        "control_count": len(controls),
        "ready": not invalid and len(implemented_controls) >= 3 and len(human_approval_controls) >= 4,
    }


def _human_approval_gates(
    *,
    launch_controls: list[dict[str, Any]],
    expert_reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for control in launch_controls:
        if control.get("status") == HUMAN_APPROVAL_STATUS:
            gates.append(
                {
                    "id": control.get("id"),
                    "owner": control.get("owner"),
                    "source": "launch_control",
                    "gate": control.get("control"),
                    "evidence": control.get("evidence"),
                    "next_valid_move": control.get("next_valid_move"),
                    "unsafe_to_bypass": True,
                }
            )
    for review in expert_reviews:
        gates.append(
            {
                "id": f"{review.get('id')}:human-approval",
                "owner": review.get("role"),
                "source": "expert_review_simulation",
                "gate": review.get("human_approval_gate"),
                "evidence": "data/expert_review_simulations.json",
                "next_valid_move": review.get("next_valid_move"),
                "unsafe_to_bypass": True,
            }
        )
    return gates


def build_board_go_live_readiness(
    *,
    readiness: dict[str, Any],
    external: dict[str, Any],
    continuation: dict[str, Any],
    vc_pitch: dict[str, Any],
    canada_tools: list[dict[str, Any]],
    expert_reviews: list[dict[str, Any]],
    launch_controls: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    tools_status = _canadian_tool_status(canada_tools)
    expert_status = _expert_review_status(expert_reviews)
    controls_status = _launch_control_status(launch_controls)
    unsafe_closed = _unsafe_gates_closed(readiness, external)
    demo_ready = (
        readiness.get("status") == "ready_with_external_gates"
        and external.get("status") == "ready_with_external_gates"
        and continuation.get("status") == "startup_in_progress"
        and continuation.get("must_continue") is True
        and vc_pitch.get("status") == "vc_pitch_ready_with_diligence_gates"
        and unsafe_closed
    )
    board_candidate_ready = (
        demo_ready
        and tools_status["ready"]
        and expert_status["ready"]
        and controls_status["ready"]
    )
    human_approval_gates = _human_approval_gates(
        launch_controls=launch_controls,
        expert_reviews=expert_reviews,
    )

    return {
        "generated_at": generated_at or _now(),
        "status": (
            "board_go_live_candidate_with_human_approval_gates"
            if board_candidate_ready
            else "board_go_live_blocked"
        ),
        "product": "Importer Source Readiness Copilot",
        "primary_market": "Canada",
        "board_decision_scope": "private_controlled_beta_or_board_review_only",
        "implementation_complete_for_board_review": board_candidate_ready,
        "demo_ready": demo_ready,
        "unsafe_gates_closed": unsafe_closed,
        "canadian_tools_ready": tools_status["ready"],
        "simulated_expert_reviews_ready": expert_status["ready"],
        "launch_controls_ready": controls_status["ready"],
        "canadian_tool_status": tools_status,
        "expert_review_status": expert_status,
        "launch_control_status": controls_status,
        "canadian_tools": canada_tools,
        "simulated_expert_reviews": expert_reviews,
        "launch_controls": launch_controls,
        "human_approval_gates": human_approval_gates,
        "human_approval_gate_count": len(human_approval_gates),
        "board_packet_artifacts": [
            "board/board_go_live_brief.md",
            "board/expert_review_packet.md",
            "board/launch_control_checklist.md",
            "board/financial_operating_model.md",
            "system_review_graph/board_go_live_readiness_report.json",
        ],
        "allowed_next_stage": (
            "board_review_for_private_beta"
            if board_candidate_ready
            else "repair_board_readiness_inputs"
        ),
        "closed_claims": [
            "public_launch_ready",
            "production_deploy_approved",
            "customs_or_tariff_advice_ready",
            "CFIA_compliance_ready",
            "legal_advice_ready",
            "financial_advice_ready",
            "buyer_validated",
            "revenue_proven",
            "product_market_fit_proven",
            "supplier_recommendation_ready",
        ],
        "next_valid_move": (
            "Board can review the generated packet for a controlled private beta while qualified Canadian customs, legal/privacy, finance, data, security, and operator approvals remain explicit gates."
            if board_candidate_ready
            else "Repair missing Canadian tools, expert simulations, launch controls, or upstream demo proof before board review."
        ),
        "proof_boundary": (
            "This is board-to-go-live candidate evidence for Canada-focused private beta review. "
            "It is not public launch approval, legal advice, financial advice, customs/tariff advice, "
            "CFIA approval, buyer validation, revenue proof, or production deployment approval. "
            "Human experts and the board review what the AI-built system produced and approve, reject, or redirect the next stage."
        ),
    }
