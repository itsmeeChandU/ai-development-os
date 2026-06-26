"""Operator workbench queue for the importer source readiness product."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_TOOL_CATEGORIES = {
    "customs_accounting",
    "food_import_requirements",
    "import_workflow",
    "importer_discovery",
    "qualified_reviewer_discovery",
    "restricted_party_screening",
    "tariff_classification",
}

MODULE_TOOL_CATEGORIES = {
    "country_import_rules": {"import_workflow"},
    "country_export_rules": {"controlled_imports"},
    "data_freshness": {"trade_data", "importer_discovery"},
    "food_safety": {"food_import_requirements"},
    "legal_compliance": {"privacy", "qualified_reviewer_discovery"},
    "launch_readiness": {"business_planning", "cybersecurity", "financial_planning", "privacy"},
    "official_source_review": {"import_workflow", "trade_data"},
    "restricted_party_screening": {"restricted_party_screening"},
    "tariff_classification": {"tariff_classification", "qualified_reviewer_discovery"},
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _tool_refs(tools: list[dict[str, Any]], categories: set[str]) -> list[dict[str, Any]]:
    refs = []
    for tool in tools:
        if str(tool.get("category") or "") not in categories:
            continue
        refs.append(
            {
                "id": tool.get("id"),
                "name": tool.get("name"),
                "category": tool.get("category"),
                "source_url": tool.get("source_url"),
                "claim_boundary": tool.get("claim_boundary"),
            }
        )
    return refs


def _source_priority(row: dict[str, Any]) -> int:
    if row.get("status") == "blocked_unsafe":
        return 100
    blocker_count = len(row.get("blockers") or [])
    if blocker_count >= 5:
        return 78
    if blocker_count:
        return 65
    return 30


def _external_priority(row: dict[str, Any]) -> int:
    module = str(row.get("module") or "")
    if module in {"launch_readiness", "legal_compliance", "tariff_classification", "food_safety"}:
        return 86
    if module in {"restricted_party_screening", "country_import_rules", "country_export_rules"}:
        return 82
    return 72


def _closed_claims(*reports: dict[str, Any]) -> list[str]:
    claims: set[str] = set()
    for report in reports:
        claims.update(str(claim) for claim in report.get("closed_claims", []))
    return sorted(claims)


def _unsafe_gates_closed(readiness: dict[str, Any], external: dict[str, Any]) -> bool:
    for row in readiness.get("rows", []):
        for value in (row.get("unsafe_counters") or {}).values():
            if int(value or 0) != 0:
                return False
    for value in (external.get("unsafe_gates") or {}).values():
        if int(value or 0) != 0:
            return False
    return True


def build_operator_workflow(
    *,
    readiness: dict[str, Any],
    external: dict[str, Any],
    continuation: dict[str, Any],
    board: dict[str, Any],
    canada_tools: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the operator's next-action queue from generated truth reports."""

    work_queue: list[dict[str, Any]] = []

    for row in readiness.get("rows", []):
        blockers = row.get("blockers") or []
        work_queue.append(
            {
                "id": f"source:{row.get('product_slug') or row.get('queue_id')}",
                "type": "source_card_review",
                "priority": _source_priority(row),
                "status": row.get("status"),
                "owner": "operator",
                "label": row.get("source_name") or row.get("product_slug"),
                "product_slug": row.get("product_slug"),
                "queue_id": row.get("queue_id"),
                "country": row.get("country"),
                "hs_code": row.get("hs_code"),
                "blocker_count": len(blockers),
                "blocked_modules": sorted({str(blocker.get("module")) for blocker in blockers}),
                "next_valid_move": row.get("next_valid_move"),
                "evidence": "system_review_graph/readiness_report.json",
                "proof_command": "python3 scripts/run_readiness.py && python3 scripts/check_product.py",
                "canadian_tool_refs": _tool_refs(canada_tools, SOURCE_TOOL_CATEGORIES),
                "claim_boundary": "Internal operator review only; this row does not prove supplier, buyer, customs, tariff, or launch readiness.",
            }
        )

    for row in external.get("blockers", []):
        module = str(row.get("module") or "")
        work_queue.append(
            {
                "id": f"gate:{row.get('id')}",
                "type": "external_evidence_gate",
                "priority": _external_priority(row),
                "status": "blocked_external_input",
                "owner": row.get("owner"),
                "label": row.get("issue"),
                "module": module,
                "evidence": row.get("evidence"),
                "next_valid_move": row.get("next_valid_move"),
                "proof_command": "python3 scripts/run_external_gates.py && python3 scripts/check_product.py",
                "canadian_tool_refs": _tool_refs(canada_tools, MODULE_TOOL_CATEGORIES.get(module, set())),
                "claim_boundary": "Requires dated evidence or qualified review before any external claim can open.",
            }
        )

    for lane in continuation.get("lanes", []):
        work_queue.append(
            {
                "id": f"lane:{lane.get('id')}",
                "type": "continuation_lane",
                "priority": 76 if lane.get("status") == "blocked_external_input" else 54,
                "status": lane.get("status"),
                "owner": lane.get("owner"),
                "label": lane.get("title"),
                "blocker_count": lane.get("blocker_count", 0),
                "required_evidence": lane.get("required_evidence", []),
                "next_valid_move": lane.get("next_valid_move"),
                "proof_command": lane.get("proof_command"),
                "claim_boundary": "Continuation lane must collect evidence before completion claims change.",
            }
        )

    for gate in board.get("human_approval_gates", []):
        work_queue.append(
            {
                "id": f"approval:{gate.get('id')}",
                "type": "human_approval_gate",
                "priority": 90,
                "status": "approval_required",
                "owner": gate.get("owner"),
                "label": gate.get("gate"),
                "evidence": gate.get("evidence"),
                "next_valid_move": gate.get("next_valid_move"),
                "proof_command": "Attach dated approval evidence, then rerun python3 scripts/check_product.py.",
                "claim_boundary": "AI simulation is not final approval; a responsible human owner must approve or reject this gate.",
            }
        )

    work_queue.sort(key=lambda row: (-int(row.get("priority") or 0), str(row.get("id") or "")))
    counts = Counter(str(row["type"]) for row in work_queue)
    unsafe_closed = _unsafe_gates_closed(readiness, external)
    operator_can_use_now = (
        unsafe_closed
        and readiness.get("status") == "ready_with_external_gates"
        and external.get("status") == "ready_with_external_gates"
        and continuation.get("status") == "startup_in_progress"
    )

    return {
        "generated_at": generated_at or _now(),
        "status": "operator_workflow_ready_internal" if operator_can_use_now else "operator_workflow_blocked",
        "display_status": "Operator workbench usable for internal review" if operator_can_use_now else "Operator workbench blocked",
        "product": "Importer Source Readiness Copilot",
        "primary_market": "Canada",
        "operator_can_use_now": operator_can_use_now,
        "allowed_use": "internal_source_readiness_review_and_board_private_beta_decisioning",
        "not_allowed_use": [
            "customs_or_tariff_advice",
            "supplier_recommendation",
            "buyer_validation_claim",
            "public_launch_claim",
            "legal_or_financial_advice",
            "production_deployment_approval",
        ],
        "work_queue_count": len(work_queue),
        "work_queue_counts_by_type": dict(sorted(counts.items())),
        "top_next_valid_move": (
            str(work_queue[0].get("next_valid_move"))
            if work_queue
            else "No work queue rows; rerun product proof or attach new evidence."
        ),
        "unsafe_gates_closed": unsafe_closed,
        "closed_claims": _closed_claims(continuation, board),
        "work_queue": work_queue,
        "canadian_tool_count": len(canada_tools),
        "canadian_tools": _tool_refs(canada_tools, {str(tool.get("category") or "") for tool in canada_tools}),
        "proof_boundary": (
            "This workflow is an operator workbench for internal review. It coordinates generated reports, "
            "Canadian reference tools, continuation lanes, and human approval gates; it does not prove "
            "external-world readiness, customs/tariff correctness, buyer demand, legal/financial approval, "
            "supplier quality, or production launch approval."
        ),
    }


def write_operator_workflow(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
