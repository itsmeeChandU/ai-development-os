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
INPUT_LEDGER_STATUS = "production_market_readiness_input_ledger_ready_claims_closed"
READY_INPUT_DECISIONS = {"ready_for_my_area", "not_applicable_for_this_launch", "go_for_public_launch"}

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


def _input_records_from_folder(input_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    if not input_dir.exists():
        return records, invalid_records
    for path in sorted(input_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            invalid_records.append(
                {
                    "source_file": path.name,
                    "status": "invalid_json",
                    "error": str(exc),
                    "missing_fields": ["valid JSON input record"],
                    "next_valid_move": "Replace the file with a valid returned-input JSON record.",
                    "claims_opened_by_ledger": False,
                    "external_effects_created": False,
                }
            )
            continue
        if not isinstance(payload, dict):
            invalid_records.append(
                {
                    "source_file": path.name,
                    "status": "invalid_json",
                    "error": "JSON input must be an object",
                    "missing_fields": ["object-shaped JSON input record"],
                    "next_valid_move": "Replace the file with the matching returned-input JSON template.",
                    "claims_opened_by_ledger": False,
                    "external_effects_created": False,
                }
            )
            continue
        payload["source_file"] = path.name
        records.append(payload)
    return records, invalid_records


def _record_missing_fields(record: dict[str, Any]) -> list[str]:
    missing = []
    if not (record.get("reviewer_name") or record.get("approver")):
        missing.append("reviewer or accountable owner name")
    if not (record.get("reviewer_role") or record.get("approver_role")):
        missing.append("reviewer role or qualification")
    if not (record.get("scope_reviewed") or record.get("launch_scope")):
        missing.append("scope reviewed")
    if not (record.get("signed_at") or record.get("decided_at")):
        missing.append("signed or decided date")
    if not record.get("decision"):
        missing.append("decision")
    return missing


def _record_is_accepted(record: dict[str, Any]) -> bool:
    return not _record_missing_fields(record) and str(record.get("decision") or "") in READY_INPUT_DECISIONS


def _selected_input_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [record for record in records if _record_is_accepted(record)]
    if accepted:
        return sorted(accepted, key=lambda row: str(row.get("recorded_at") or row.get("signed_at") or row.get("source_file") or ""))[-1]
    if records:
        return sorted(records, key=lambda row: str(row.get("recorded_at") or row.get("signed_at") or row.get("source_file") or ""))[-1]
    return None


def _input_ledger_row(template: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    review_area = str(template.get("review_area"))
    selected = _selected_input_record(records)
    if selected is None:
        who_to_ask = str(template.get("who_to_ask") or "the responsible reviewer or owner").strip().rstrip(".")
        return {
            "review_area": review_area,
            "plain_title": template.get("plain_title"),
            "status": "not_received",
            "decision": "",
            "source_file": f"external_inputs/{review_area}.json",
            "reviewer_name": "",
            "reviewer_role": "",
            "signed_at": "",
            "scope_reviewed": "",
            "record_count_for_area": 0,
            "minimum_input_present": False,
            "ready_decision_candidate": False,
            "accepted_for_area": False,
            "missing_fields": ["returned input record"],
            "next_valid_move": f"Send the scoped request to {who_to_ask}, then save the dated response.",
            "claims_opened_by_ledger": False,
            "external_effects_created": False,
        }

    decision = str(selected.get("decision") or "")
    missing_fields = _record_missing_fields(selected)
    ready_decision = decision in READY_INPUT_DECISIONS
    accepted = not missing_fields and ready_decision
    if accepted:
        status = "accepted_for_area"
        next_valid_move = "Keep this scoped input attached, then wait for every other area and final owner approval before launch."
    elif decision == "need_more_evidence" or selected.get("evidence_missing"):
        status = "received_needs_more_evidence"
        next_valid_move = "Collect the missing evidence listed in the returned input and keep the area blocked."
    elif missing_fields:
        status = "received_but_incomplete"
        next_valid_move = "Ask the reviewer or owner to add the missing fields before counting this area as ready."
    else:
        status = "received_not_ready"
        next_valid_move = "Resolve the reviewer decision before this area can be accepted."
    return {
        "review_area": review_area,
        "plain_title": template.get("plain_title"),
        "status": status,
        "decision": decision,
        "source_file": selected.get("source_file"),
        "reviewer_name": selected.get("reviewer_name") or selected.get("approver") or "",
        "reviewer_role": selected.get("reviewer_role") or selected.get("approver_role") or "",
        "signed_at": selected.get("signed_at") or selected.get("decided_at") or "",
        "scope_reviewed": selected.get("scope_reviewed") or selected.get("launch_scope") or "",
        "record_count_for_area": len(records),
        "minimum_input_present": not missing_fields,
        "ready_decision_candidate": ready_decision,
        "accepted_for_area": accepted,
        "missing_fields": missing_fields,
        "top_issues": _split_lines(selected.get("top_issues")),
        "evidence_missing": _split_lines(selected.get("evidence_missing")),
        "claims_the_product_must_not_make": _split_lines(selected.get("claims_the_product_must_not_make")),
        "next_valid_move": next_valid_move,
        "claims_opened_by_ledger": False,
        "external_effects_created": False,
    }


def build_market_readiness_input_ledger(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    templates = _load_json(graph / "go_live_input_templates.json", {})
    input_dir = root / "external_inputs"
    records, invalid_records = _input_records_from_folder(input_dir)
    records_by_area: dict[str, list[dict[str, Any]]] = {
        str(row.get("review_area")): [] for row in templates.get("templates", [])
    }
    unassigned_records: list[dict[str, Any]] = []
    for record in records:
        area = str(record.get("review_area") or "")
        if area in records_by_area:
            records_by_area[area].append(record)
        else:
            unassigned_records.append(
                {
                    "source_file": record.get("source_file"),
                    "review_area": area or "missing",
                    "status": "unknown_review_area",
                    "missing_fields": ["supported review area"],
                    "next_valid_move": "Move the record to one of the supported market-readiness review areas.",
                    "claims_opened_by_ledger": False,
                    "external_effects_created": False,
                }
            )

    rows = [
        _input_ledger_row(template, records_by_area.get(str(template.get("review_area")), []))
        for template in templates.get("templates", [])
    ]
    accepted_count = len([row for row in rows if row["status"] == "accepted_for_area"])
    not_received_count = len([row for row in rows if row["status"] == "not_received"])
    incomplete_count = len([row for row in rows if row["status"] == "received_but_incomplete"])
    needs_more_evidence_count = len([row for row in rows if row["status"] == "received_needs_more_evidence"])
    invalid_count = len(invalid_records) + len(unassigned_records)
    final_row = next((row for row in rows if row["review_area"] == "public_go_no_go_approval"), {})
    return {
        "generated_at": _now(),
        "status": INPUT_LEDGER_STATUS,
        "review_area_count": len(rows),
        "input_record_count": len(records),
        "accepted_area_count": accepted_count,
        "not_received_area_count": not_received_count,
        "incomplete_area_count": incomplete_count,
        "needs_more_evidence_area_count": needs_more_evidence_count,
        "invalid_record_count": invalid_count,
        "all_areas_accepted": accepted_count == len(rows) and bool(rows),
        "public_launch_ready_by_ledger": accepted_count == len(rows) and final_row.get("decision") == "go_for_public_launch",
        "input_folder": "external_inputs/",
        "ledger_rows": rows,
        "invalid_records": invalid_records + unassigned_records,
        "blocked_claims": list(BLOCKED_MARKET_READY_CLAIMS),
        "claims_opened_by_ledger": False,
        "external_effects_created": False,
        "next_valid_move": (
            "Collect and record the missing real inputs."
            if accepted_count < len(rows)
            else "Run the launch control plane and require final owner approval for the exact scope."
        ),
        "proof_boundary": (
            "The ledger validates returned input completeness for operators. It does not approve launch, "
            "payments, customs/trade claims, legal/privacy/security claims, buyer validation, or supplier verification."
        ),
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
    input_ledger = build_market_readiness_input_ledger(root)
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
        "input_ledger": input_ledger,
        "input_ledger_status": input_ledger["status"],
        "input_ledger_route": "/api/market-readiness/input-ledger",
        "input_capture_enabled_local": True,
        "input_capture_route": "/api/market-readiness/inputs",
        "template_status": templates.get("status", "missing"),
        "go_live_input_status": readiness.get("status", "missing"),
        "launch_control_status": launch.get("status", "missing"),
        "blocked_claims": list(BLOCKED_MARKET_READY_CLAIMS),
        "safe_next_loop": [
            "Collect the missing real-world input files in external_inputs/.",
            "Use production_market_readiness_input_ledger.json to inspect incomplete or unaccepted returned inputs.",
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
        f"- Input ledger route: `{payload['input_ledger_route']}`",
        "",
        "## Returned Input Ledger",
        "",
        f"- Accepted areas: {payload['input_ledger']['accepted_area_count']}",
        f"- Not received areas: {payload['input_ledger']['not_received_area_count']}",
        f"- Needs more evidence: {payload['input_ledger']['needs_more_evidence_area_count']}",
        f"- Incomplete areas: {payload['input_ledger']['incomplete_area_count']}",
        f"- Claims opened by ledger: {str(payload['input_ledger']['claims_opened_by_ledger']).lower()}",
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
    input_ledger_path = graph / "production_market_readiness_input_ledger.json"
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
    input_ledger_path.write_text(json.dumps(payload["input_ledger"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    doc_path.write_text(render_market_readiness_evidence_room_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "work_orders": work_orders_path,
        "reviewer_cards": reviewer_cards_path,
        "matrix": matrix_path,
        "input_ledger": input_ledger_path,
        "doc": doc_path,
    }
