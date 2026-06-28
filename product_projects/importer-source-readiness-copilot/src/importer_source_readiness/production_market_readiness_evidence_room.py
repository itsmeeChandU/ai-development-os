"""Production market-readiness evidence room.

This module converts the real-world external validation requirements into an
operator-facing evidence intake room. It does not approve launch, payments,
customs, privacy, buyer, or supplier claims. It tells the operator what real
input is missing, where returned evidence belongs, and which claims stay closed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS = "production_market_readiness_evidence_room_ready_inputs_mapped_gates_closed"
INPUT_RECORD_STATUS = "market_readiness_input_record_saved_local_pending_re_evaluation"

BLOCKED_MARKET_READY_CLAIMS = (
    "market_ready",
    "public_launch_approved",
    "hosted_private_beta_approved",
    "live_payment_activated",
    "legal_privacy_security_approved",
    "customs_trade_approved",
    "tariff_confirmed",
    "cfia_approved",
    "buyer_validated",
    "supplier_verified",
    "ready_to_ship",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _rows_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key) or ""): row for row in rows if row.get(key)}


def _split_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(row).strip() for row in value if str(row).strip()]
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


def _clean_text(value: Any, limit: int = 1000) -> str:
    text = str(value or "").replace("\x00", "").strip()
    return text[:limit]


def _source_anchors_for_gate(report: dict[str, Any], gate_id: str) -> list[dict[str, Any]]:
    anchors = []
    for source in report.get("source_anchors", []):
        if gate_id in source.get("applies_to", []):
            anchors.append(
                {
                    "source_id": source.get("source_id"),
                    "name": source.get("name"),
                    "publisher": source.get("publisher"),
                    "url": source.get("url"),
                    "checked_at": source.get("checked_at"),
                    "project_use": source.get("project_use"),
                    "source_type": source.get("source_type"),
                    "supports": "source routing and review preparation only",
                    "does_not_support": "approval, legal advice, customs advice, payment activation, or launch approval",
                }
            )
    return anchors


def _accepted_input_by_area(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    accepted: dict[str, dict[str, Any]] = {}
    for row in readiness.get("accepted_inputs", []):
        review_area = str(row.get("review_area") or row.get("gate_id") or "")
        if review_area:
            accepted[review_area] = row
    return accepted


def _missing_input_by_area(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _rows_by_key(readiness.get("missing_inputs", []), "review_area")


def _gate_input_state(gate_id: str, accepted: dict[str, dict[str, Any]], missing: dict[str, dict[str, Any]]) -> str:
    if gate_id in accepted:
        return "real_input_received_for_scope_review"
    if gate_id in missing:
        return "missing_real_input"
    return "input_state_unknown_rerun_external_validation"


def _gate_work_order(
    gate: dict[str, Any],
    template: dict[str, Any],
    missing_input: dict[str, Any],
    accepted_input: dict[str, Any],
    source_anchors: list[dict[str, Any]],
) -> dict[str, Any]:
    gate_id = str(gate.get("gate_id"))
    input_state = _gate_input_state(
        gate_id,
        {gate_id: accepted_input} if accepted_input else {},
        {gate_id: missing_input} if missing_input else {},
    )
    ready_for_area = bool(accepted_input)
    return {
        "work_order_id": f"market-readiness:{gate_id}",
        "gate_id": gate_id,
        "gate_name": gate.get("name") or template.get("plain_title") or gate_id,
        "input_state": input_state,
        "ready_for_area": ready_for_area,
        "review_area": gate_id,
        "plain_question": template.get("simple_question") or missing_input.get("simple_question") or gate.get("minimum_acceptance"),
        "who_to_ask": template.get("who_to_ask") or missing_input.get("who_to_ask") or ", ".join(gate.get("required_reviewers_or_owners", [])),
        "minimum_input": template.get("minimum_input") or missing_input.get("minimum_input") or gate.get("required_data_fields", []),
        "required_evidence": gate.get("required_evidence", []),
        "required_data_fields": gate.get("required_data_fields", []),
        "required_reviewers_or_owners": gate.get("required_reviewers_or_owners", []),
        "source_anchors": source_anchors,
        "source_anchor_count": len(source_anchors),
        "input_template": template.get("record_template", {}),
        "allowed_decisions": template.get("allowed_decisions", []),
        "drop_path": f"external_inputs/{gate_id}.json",
        "rerun_command": "python3 scripts/run_external_validation_requirements.py --input-dir external_inputs",
        "blocks_public_launch": gate.get("blocks_public_launch") is True and not ready_for_area,
        "blocks_private_beta": gate.get("blocks_private_beta") is True and not ready_for_area,
        "blocks_live_payment": gate.get("blocks_live_payment") is True and not ready_for_area,
        "blocks_trade_claims": gate.get("blocks_trade_claims") is True and not ready_for_area,
        "cannot_claim_until": gate.get("cannot_claim_until"),
        "blocking_conditions": gate.get("blocking_conditions", []),
        "safe_operator_instruction": (
            "Ask for the minimum input, save the dated response at the drop path, rerun the external validation script, "
            "then route any issues into the blocker ledger before changing launch scope."
        ),
        "blocked_claims": list(BLOCKED_MARKET_READY_CLAIMS),
        "next_valid_move": gate.get("next_valid_move") or "Collect real dated input from the named reviewer or owner.",
        "external_effects_created": False,
        "claims_opened_by_this_work_order": False,
    }


def _reviewer_brief_card(work_order: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_area": work_order["review_area"],
        "plain_title": work_order["gate_name"],
        "simple_question": work_order["plain_question"],
        "who_to_ask": work_order["who_to_ask"],
        "minimum_input": work_order["minimum_input"],
        "where_to_save_response": work_order["drop_path"],
        "what_to_send": [
            "external_validation_reviewer_brief.pdf",
            "go_live_input_requests.pdf",
            "the exact URL, commit, package hash, report, or packet scope being reviewed",
        ],
        "what_not_to_say": [
            "Please approve the whole company.",
            "The AI review already approved this.",
            "This is ready to ship unless you object.",
        ],
        "subject_line": f"Scoped review input requested: {work_order['gate_name']}",
        "claims_still_closed": work_order["blocked_claims"],
    }


def market_readiness_input_form_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    templates = _load_json(root / "system_review_graph" / "go_live_input_templates.json", {})
    return {
        "status": "market_readiness_input_form_contract_ready",
        "review_areas": [
            {
                "review_area": row.get("review_area"),
                "plain_title": row.get("plain_title"),
                "simple_question": row.get("simple_question"),
                "who_to_ask": row.get("who_to_ask"),
                "minimum_input": row.get("minimum_input", []),
            }
            for row in templates.get("templates", [])
        ],
        "allowed_decisions": templates.get("allowed_decisions", []),
        "input_folder": templates.get("input_folder", "external_inputs/"),
        "external_effects_created": False,
        "proof_boundary": "The form records returned human input locally. It does not approve launch or open claims by itself.",
    }


def build_market_readiness_input_record(
    fields: dict[str, Any],
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    contract = market_readiness_input_form_contract(repo_root)
    area_by_id = _rows_by_key(contract["review_areas"], "review_area")
    review_area = _clean_text(fields.get("review_area"), 160)
    if review_area not in area_by_id:
        raise ValueError(f"unsupported market-readiness review area: {review_area}")
    decision = _clean_text(fields.get("decision") or "need_more_evidence", 120)
    if decision not in contract["allowed_decisions"]:
        raise ValueError(f"unsupported market-readiness decision: {decision}")
    signed_at = _clean_text(fields.get("signed_at") or fields.get("decided_at"), 80)
    record = {
        "status": INPUT_RECORD_STATUS,
        "recorded_at": generated_at or _now(),
        "review_area": review_area,
        "plain_title": area_by_id[review_area].get("plain_title"),
        "reviewer_name": _clean_text(fields.get("reviewer_name"), 160),
        "reviewer_role": _clean_text(fields.get("reviewer_role"), 160),
        "scope_reviewed": _clean_text(fields.get("scope_reviewed"), 500),
        "decision": decision,
        "signed_at": signed_at,
        "top_issues": _split_lines(fields.get("top_issues")),
        "evidence_missing": _split_lines(fields.get("evidence_missing")),
        "evidence_links_or_files": _split_lines(fields.get("evidence_links_or_files")),
        "claims_the_product_must_not_make": _split_lines(fields.get("claims_the_product_must_not_make")),
        "what_would_make_this_ready": _clean_text(fields.get("what_would_make_this_ready"), 1000),
        "minimum_input_present": bool(fields.get("reviewer_name") and fields.get("scope_reviewed") and signed_at),
        "ready_decision_candidate": decision in {"ready_for_my_area", "not_applicable_for_this_launch", "go_for_public_launch"},
        "external_effects_created": False,
        "claims_opened_by_recording": False,
        "proof_boundary": (
            "This is a local record of returned input. It becomes go-live evidence only through "
            "go_live_input_readiness_report.json and the launch control plane."
        ),
    }
    return record


def save_market_readiness_input_record(fields: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    record = build_market_readiness_input_record(fields, repo_root)
    input_dir = repo_root / "external_inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    path = input_dir / f"{record['review_area']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "status": INPUT_RECORD_STATUS,
        "record": record,
        "path": path,
        "relative_path": str(path.relative_to(repo_root)),
        "external_effects_created": False,
        "claims_opened": False,
    }


def build_production_market_readiness_evidence_room(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    external_validation = _load_json(graph / "external_validation_requirements_report.json", {})
    templates = _load_json(graph / "go_live_input_templates.json", {})
    readiness = _load_json(graph / "go_live_input_readiness_report.json", {})
    launch = _load_json(graph / "production_launch_control_plane_manifest.json", {})
    continuation = _load_json(graph / "continuation_plan.json", {})

    template_by_area = _rows_by_key(templates.get("templates", []), "review_area")
    accepted_by_area = _accepted_input_by_area(readiness)
    missing_by_area = _missing_input_by_area(readiness)

    work_orders: list[dict[str, Any]] = []
    for gate in external_validation.get("gates", []):
        gate_id = str(gate.get("gate_id"))
        work_orders.append(
            _gate_work_order(
                gate=gate,
                template=template_by_area.get(gate_id, {}),
                missing_input=missing_by_area.get(gate_id, {}),
                accepted_input=accepted_by_area.get(gate_id, {}),
                source_anchors=_source_anchors_for_gate(external_validation, gate_id),
            )
        )

    gate_status_matrix = [
        {
            "gate_id": row["gate_id"],
            "gate_name": row["gate_name"],
            "input_state": row["input_state"],
            "ready_for_area": row["ready_for_area"],
            "blocks_public_launch": row["blocks_public_launch"],
            "blocks_private_beta": row["blocks_private_beta"],
            "blocks_live_payment": row["blocks_live_payment"],
            "blocks_trade_claims": row["blocks_trade_claims"],
            "source_anchor_count": row["source_anchor_count"],
            "drop_path": row["drop_path"],
            "next_valid_move": row["next_valid_move"],
        }
        for row in work_orders
    ]
    reviewer_brief_cards = [_reviewer_brief_card(row) for row in work_orders]
    missing_count = int(readiness.get("missing_input_count", len([row for row in work_orders if not row["ready_for_area"]])))
    ready_count = int(readiness.get("ready_input_count", len([row for row in work_orders if row["ready_for_area"]])))
    required_count = int(readiness.get("required_input_count", external_validation.get("gate_count", len(work_orders))))
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "evidence_room_name": "Market Readiness Evidence Room",
        "gate_count": len(work_orders),
        "required_input_count": required_count,
        "ready_input_count": ready_count,
        "missing_input_count": missing_count,
        "all_required_inputs_received": missing_count == 0 and ready_count >= required_count and required_count > 0,
        "public_launch_ready": readiness.get("public_launch_ready") is True,
        "hosted_private_beta_ready": readiness.get("hosted_private_beta_ready") is True,
        "live_payment_ready": readiness.get("live_payment_ready") is True,
        "launch_control_activation_allowed": launch.get("activation_allowed") is True,
        "exact_public_scope_approved": launch.get("exact_public_scope_approved") is True,
        "must_continue": continuation.get("must_continue") is True,
        "real_world_external_evidence_received": ready_count > 0,
        "external_effects_created": False,
        "claims_opened_by_room": False,
        "market_ready_claim_allowed": False,
        "work_orders": work_orders,
        "work_order_count": len(work_orders),
        "reviewer_brief_cards": reviewer_brief_cards,
        "reviewer_brief_card_count": len(reviewer_brief_cards),
        "gate_status_matrix": gate_status_matrix,
        "source_anchor_count": sum(row["source_anchor_count"] for row in work_orders),
        "input_folder": templates.get("input_folder", "external_inputs/"),
        "input_form_contract": market_readiness_input_form_contract(root),
        "input_capture_enabled_local": True,
        "input_capture_route": "/api/market-readiness/inputs",
        "template_status": templates.get("status", "missing"),
        "go_live_input_status": readiness.get("status", "missing"),
        "launch_control_status": launch.get("status", "missing"),
        "blocked_claims": list(BLOCKED_MARKET_READY_CLAIMS),
        "safe_next_loop": [
            "Collect the missing real-world input files in external_inputs/.",
            "Rerun scripts/run_external_validation_requirements.py --input-dir external_inputs.",
            "Rerun scripts/run_production_market_readiness_evidence_room.py.",
            "Route any returned issue into external_review_blocker_ledger.jsonl before launch scope changes.",
            "Use production_launch_control_plane_manifest.json for final activation state.",
        ],
        "proof_boundary": (
            "The evidence room organizes real go-live inputs and review work orders. It is not approval, "
            "market readiness, payment activation, customs/trade approval, legal/privacy/security approval, "
            "buyer validation, supplier verification, or public launch permission."
        ),
    }


def render_market_readiness_evidence_room_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Market Readiness Evidence Room",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Current State",
        "",
        f"- Required inputs: {payload['required_input_count']}",
        f"- Ready inputs: {payload['ready_input_count']}",
        f"- Missing inputs: {payload['missing_input_count']}",
        f"- Public launch ready: {str(payload['public_launch_ready']).lower()}",
        f"- Live payment ready: {str(payload['live_payment_ready']).lower()}",
        f"- Claims opened by room: {str(payload['claims_opened_by_room']).lower()}",
        f"- Market-ready claim allowed: {str(payload['market_ready_claim_allowed']).lower()}",
        f"- Local returned-input capture: {str(payload['input_capture_enabled_local']).lower()}",
        f"- Input capture route: `{payload['input_capture_route']}`",
        "",
        "## Work Orders",
        "",
    ]
    for row in payload["work_orders"]:
        lines.extend(
            [
                f"### {row['gate_name']}",
                "",
                f"- Input state: `{row['input_state']}`",
                f"- Ask: {row['who_to_ask']}",
                f"- Save response: `{row['drop_path']}`",
                f"- Source anchors: {row['source_anchor_count']}",
                f"- Next valid move: {row['next_valid_move']}",
                "",
            ]
        )
    lines.extend(["## Safe Next Loop", ""])
    lines.extend(f"- {row}" for row in payload["safe_next_loop"])
    lines.append("")
    return "\n".join(lines)


def write_production_market_readiness_evidence_room_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    manifest_path = graph / "production_market_readiness_evidence_room_manifest.json"
    work_orders_path = graph / "production_market_readiness_evidence_work_orders.json"
    reviewer_cards_path = graph / "production_market_readiness_reviewer_brief_cards.json"
    matrix_path = graph / "production_market_readiness_gate_status_matrix.json"
    doc_path = docs / "PRODUCTION_MARKET_READINESS_EVIDENCE_ROOM.md"

    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    work_orders_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_market_readiness_evidence_work_orders_ready",
                "work_order_count": payload["work_order_count"],
                "work_orders": payload["work_orders"],
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    reviewer_cards_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_market_readiness_reviewer_brief_cards_ready",
                "reviewer_brief_card_count": payload["reviewer_brief_card_count"],
                "reviewer_brief_cards": payload["reviewer_brief_cards"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    matrix_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_market_readiness_gate_status_matrix_ready",
                "gate_count": payload["gate_count"],
                "missing_input_count": payload["missing_input_count"],
                "ready_input_count": payload["ready_input_count"],
                "gate_status_matrix": payload["gate_status_matrix"],
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_market_readiness_evidence_room_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "work_orders": work_orders_path,
        "reviewer_cards": reviewer_cards_path,
        "matrix": matrix_path,
        "doc": doc_path,
    }
