"""Executable local product operations for Trade Readiness Copilot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .completion_platform import build_completion_platform, write_completion_platform_artifacts
from .customer_store import write_customer_store
from .product_runtime import write_runtime_artifacts
from .source_packet_workflow import (
    build_ai_review_run,
    build_customer_workflow,
    evidence_from_submission,
    expert_review_packet_markdown,
    load_json_list,
    markdown_report,
    packet_from_submission,
    refresh_packet_sources,
    write_json,
)

PRODUCT_OPERATION_STATUS = "local_product_operations_executed"
SAFE_TOOL_STATUS = "agent_tool_executed_local"

OPERATION_COVERAGE_KEYS = {
    "data_intake",
    "research_execution",
    "evidence_reporting",
    "expert_review_routing",
    "team_workspace_activity",
    "billing_metering",
    "agent_tool_execution",
    "launch_control_event",
    "persistence_refresh",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _graph(repo_root: Path) -> Path:
    return repo_root / "system_review_graph"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _load_rows(primary: Path, fallback: Path) -> list[dict[str, Any]]:
    selected = primary if primary.exists() else fallback
    payload = _load_json(selected, [])
    if isinstance(payload, list):
        return [dict(row) for row in payload]
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return [dict(row) for row in payload["rows"]]
    raise ValueError(f"expected list or rows payload in {selected}")


def load_current_product_rows(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Load mutable packet/evidence/source rows from generated truth first, then seed data."""

    graph = _graph(repo_root)
    packets = _load_rows(graph / "customer_source_packets.json", repo_root / "data" / "customer_source_packets.json")
    evidence = _load_rows(graph / "evidence_ledger.json", repo_root / "data" / "evidence_ledger.json")
    sources = load_json_list(repo_root / "data" / "official_source_registry.json")
    return packets, evidence, sources


def persist_product_state(
    repo_root: Path,
    packets: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    *,
    extra_audit_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Rebuild all generated product truth after an operation mutates local rows."""

    official_sources = load_json_list(repo_root / "data" / "official_source_registry.json")
    workflow = build_customer_workflow(
        source_packets=packets,
        evidence_items=evidence_rows,
        official_sources=official_sources,
    )
    graph = _graph(repo_root)
    write_json(workflow, graph / "customer_readiness_report.json")
    write_json(workflow["packets"], graph / "customer_source_packets.json")
    write_json(workflow["evidence_ledger"], graph / "evidence_ledger.json")
    write_json(workflow["ai_review_runs"], graph / "customer_ai_review_runs.json")
    write_runtime_artifacts(repo_root, workflow, extra_audit_events=extra_audit_events)
    write_customer_store(workflow, graph / "customer_workflow.sqlite")
    if workflow["packets"]:
        first_packet_id = str(workflow["packets"][0]["packet_id"])
        (graph / "customer_readiness_report.md").write_text(
            markdown_report(workflow, first_packet_id),
            encoding="utf-8",
        )
        for packet in workflow["packets"]:
            packet_id = str(packet["packet_id"])
            (graph / f"expert_review_packet_{packet_id}.md").write_text(
                expert_review_packet_markdown(workflow, packet_id),
                encoding="utf-8",
            )
    completion = build_completion_platform(workflow, official_sources)
    write_completion_platform_artifacts(completion, repo_root)
    return workflow


def _packet_lookup(workflow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(packet.get("packet_id")): packet for packet in workflow.get("packets", [])}


def _select_packet(workflow: dict[str, Any], packet_id: str | None = None) -> dict[str, Any]:
    packets = workflow.get("packets", [])
    if not packets:
        raise ValueError("no product packets exist")
    if packet_id:
        packet = _packet_lookup(workflow).get(packet_id)
        if packet is None:
            raise KeyError(f"packet not found: {packet_id}")
        return packet
    return dict(packets[0])


def _artifact_ref(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _operation_log_path(repo_root: Path) -> Path:
    return _graph(repo_root) / "product_operations_log.json"


def _operation_report_path(repo_root: Path) -> Path:
    return _graph(repo_root) / "product_operations_report.json"


def _read_operation_events(repo_root: Path) -> list[dict[str, Any]]:
    payload = _load_json(_operation_log_path(repo_root), {"events": []})
    if isinstance(payload, dict) and isinstance(payload.get("events"), list):
        return [dict(row) for row in payload["events"]]
    if isinstance(payload, list):
        return [dict(row) for row in payload]
    return []


def _write_operation_events(repo_root: Path, events: list[dict[str, Any]]) -> None:
    write_json(
        {
            "status": "product_operations_log_ready",
            "event_count": len(events),
            "events": events,
            "proof_boundary": (
                "Operation events prove local product execution only. They do not prove external legal, "
                "customs, tariff, CFIA, buyer, supplier, payment, or launch approval."
            ),
        },
        _operation_log_path(repo_root),
    )


def _record_operation(
    repo_root: Path,
    *,
    operation: str,
    packet_id: str | None,
    coverage: list[str],
    artifacts: list[Path],
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    events = _read_operation_events(repo_root)
    event = {
        "operation_id": f"op-{operation}-{len(events) + 1}",
        "operation": operation,
        "packet_id": packet_id,
        "generated_at": _now(),
        "coverage": sorted(set(coverage)),
        "artifacts": [_artifact_ref(repo_root, path) for path in artifacts],
        "external_effects_created": False,
        "claims_opened": False,
        "details": details or {},
    }
    events.append(event)
    _write_operation_events(repo_root, events)
    build_product_operations_report(repo_root)
    return event


def _generated_reports_dir(repo_root: Path) -> Path:
    path = _graph(repo_root) / "generated_reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_workflow(repo_root: Path) -> dict[str, Any]:
    packets, evidence_rows, official_sources = load_current_product_rows(repo_root)
    return build_customer_workflow(
        source_packets=packets,
        evidence_items=evidence_rows,
        official_sources=official_sources,
    )


def _append_json_rows(path: Path, row: dict[str, Any], *, key: str | None = None) -> list[dict[str, Any]]:
    rows = _load_json(path, [])
    if not isinstance(rows, list):
        rows = []
    if key:
        rows = [dict(item) for item in rows if str(item.get(key)) != str(row.get(key))]
    rows.append(row)
    write_json(rows, path)
    return rows


def generate_missing_evidence_report(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    path = _generated_reports_dir(repo_root) / f"missing_evidence_{packet_id}.json"
    payload = {
        "status": "missing_evidence_report_generated",
        "packet_id": packet_id,
        "product_name": packet.get("product_name"),
        "missing_items": packet.get("evidence_summary", {}).get("missing_items", []),
        "blocker_groups": packet.get("blocker_groups", []),
        "buyer_broker_questions": packet.get("buyer_broker_questions", []),
        "next_valid_move": packet.get("next_valid_move"),
        "external_claims_opened": False,
        "proof_boundary": "This report lists missing inputs and review questions only; it does not approve trade action.",
    }
    write_json(payload, path)
    event = _record_operation(
        repo_root,
        operation="generate_missing_evidence_report",
        packet_id=packet_id,
        coverage=["evidence_reporting", "agent_tool_execution"],
        artifacts=[path],
        details={"missing_count": len(payload["missing_items"])},
    )
    return {"status": "operation_complete", "operation_event": event, "report": payload}


def record_data_intake_snapshot(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    path = _generated_reports_dir(repo_root) / f"data_intake_{packet_id}.json"
    payload = {
        "status": "data_intake_snapshot_recorded",
        "packet_id": packet_id,
        "packet_name": packet.get("packet_name"),
        "product_name": packet.get("product_name"),
        "trade_direction": packet.get("trade_direction"),
        "origin_country": packet.get("origin_country"),
        "destination_country": packet.get("destination_country"),
        "evidence_count": packet.get("evidence_count", 0),
        "blocker_count": packet.get("blocker_count", 0),
        "local_workflow_ready": True,
        "external_claims_opened": False,
    }
    write_json(payload, path)
    event = _record_operation(
        repo_root,
        operation="record_data_intake_snapshot",
        packet_id=packet_id,
        coverage=["data_intake", "persistence_refresh"],
        artifacts=[path, _graph(repo_root) / "customer_workflow.sqlite"],
    )
    return {"status": "operation_complete", "operation_event": event, "intake": payload}


def generate_starter_checklist(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    path = _generated_reports_dir(repo_root) / f"starter_checklist_{packet_id}.json"
    checklist = [
        "Name product, origin, destination, and intended trade direction.",
        "Collect product specs, invoice or proforma, packing details, certificates, and proof of origin.",
        "Confirm importer of record and Incoterms before shipment decisions.",
        "Refresh official sources and record dated evidence.",
        "Send broker/expert packet for scoped review before external claims.",
    ]
    payload = {
        "status": "starter_checklist_generated",
        "packet_id": packet_id,
        "checklist": checklist,
        "next_valid_move": checklist[0],
        "external_claims_opened": False,
    }
    write_json(payload, path)
    event = _record_operation(
        repo_root,
        operation="generate_starter_checklist",
        packet_id=packet_id,
        coverage=["evidence_reporting", "agent_tool_execution"],
        artifacts=[path],
    )
    return {"status": "operation_complete", "operation_event": event, "checklist": payload}


def generate_chatgpt_safe_summary(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    path = _generated_reports_dir(repo_root) / f"chatgpt_safe_summary_{packet_id}.json"
    payload = {
        "status": "chatgpt_safe_summary_generated",
        "packet_id": packet_id,
        "summary": packet.get("safe_summary"),
        "copy_paste_prompt": (
            "Use this as an internal draft only. Do not provide legal, customs, tariff, CFIA, "
            "financial, supplier, buyer, or shipment advice. Identify missing evidence and questions."
        ),
        "redacted_fields_required": True,
        "external_claims_opened": False,
    }
    write_json(payload, path)
    event = _record_operation(
        repo_root,
        operation="generate_chatgpt_safe_summary",
        packet_id=packet_id,
        coverage=["evidence_reporting", "agent_tool_execution"],
        artifacts=[path],
    )
    return {"status": "operation_complete", "operation_event": event, "summary": payload}


def generate_broker_packet(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    markdown_path = _graph(repo_root) / f"expert_review_packet_{packet_id}.md"
    json_path = _generated_reports_dir(repo_root) / f"broker_packet_{packet_id}.json"
    markdown_path.write_text(expert_review_packet_markdown(workflow, packet_id), encoding="utf-8")
    payload = {
        "status": "broker_packet_generated",
        "packet_id": packet_id,
        "markdown_artifact": _artifact_ref(repo_root, markdown_path),
        "review_scope": "Broker/customs/trade reviewer questions generated from local packet state.",
        "external_claims_opened": False,
    }
    write_json(payload, json_path)
    event = _record_operation(
        repo_root,
        operation="generate_broker_packet",
        packet_id=packet_id,
        coverage=["expert_review_routing", "agent_tool_execution"],
        artifacts=[markdown_path, json_path],
    )
    return {"status": "operation_complete", "operation_event": event, "broker_packet": payload}


def run_research_execution(repo_root: Path, packet_id: str | None = None, *, actor: str = "local_operator") -> dict[str, Any]:
    packets, evidence_rows, _official_sources = load_current_product_rows(repo_root)
    workflow_before = persist_product_state(repo_root, packets, evidence_rows)
    packet = _select_packet(workflow_before, packet_id)
    packet_id = str(packet["packet_id"])
    evidence_rows, refresh_report = refresh_packet_sources(
        packet_id=packet_id,
        evidence_items=evidence_rows,
        actor=actor,
    )
    write_json(refresh_report, _graph(repo_root) / f"source_refresh_report_{packet_id}.json")
    _append_json_rows(_graph(repo_root) / "source_refresh_runs.json", refresh_report, key="refresh_run_id")
    workflow = persist_product_state(repo_root, packets, evidence_rows)
    packet_after = _packet_lookup(workflow).get(packet_id, packet)
    run = {
        "run_id": f"research-run-{packet_id}-{_now().replace(':', '').replace('+', 'Z')}",
        "status": "research_execution_completed_local",
        "packet_id": packet_id,
        "actor": actor,
        "source_refresh_report": _artifact_ref(repo_root, _graph(repo_root) / f"source_refresh_report_{packet_id}.json"),
        "official_source_refresh_rows": refresh_report.get("row_count", 0),
        "missing_items": packet_after.get("evidence_summary", {}).get("missing_items", []),
        "research_tasks_completed": [
            "model-prior hypothesis captured",
            "official-source refresh attempted or recorded",
            "missing evidence synthesized",
            "broker/expert questions generated",
            "external proof boundaries kept closed",
        ],
        "external_effects_created": False,
        "claims_opened": False,
        "next_valid_move": packet_after.get("next_valid_move"),
    }
    path = _graph(repo_root) / "research_execution_runs.json"
    _append_json_rows(path, run, key="run_id")
    event = _record_operation(
        repo_root,
        operation="run_research_execution",
        packet_id=packet_id,
        coverage=["research_execution", "persistence_refresh"],
        artifacts=[_graph(repo_root) / f"source_refresh_report_{packet_id}.json", path],
        details={"source_refresh_rows": refresh_report.get("row_count", 0)},
    )
    _apply_operation_proofs(repo_root)
    return {"status": "operation_complete", "operation_event": event, "research_run": run}


def request_expert_review_work_orders(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    work_orders = []
    for group in packet.get("blocker_groups", []):
        work_orders.append(
            {
                "work_order_id": f"expert-work:{packet_id}:{group.get('id')}",
                "packet_id": packet_id,
                "blocker_group_id": group.get("id"),
                "review_scope": group.get("title"),
                "status": "ready_to_send_to_qualified_person",
                "questions": packet.get("buyer_broker_questions", [])[:5],
                "can_open_claim_gate": False,
                "next_valid_move": group.get("next_valid_move"),
            }
        )
    path = _graph(repo_root) / "expert_review_work_orders.json"
    existing = [row for row in _load_json(path, []) if str(row.get("packet_id")) != packet_id]
    write_json(existing + work_orders, path)
    generate_broker_packet(repo_root, packet_id)
    event = _record_operation(
        repo_root,
        operation="request_expert_review_work_orders",
        packet_id=packet_id,
        coverage=["expert_review_routing"],
        artifacts=[path, _graph(repo_root) / f"expert_review_packet_{packet_id}.md"],
        details={"work_order_count": len(work_orders)},
    )
    _apply_operation_proofs(repo_root)
    return {"status": "operation_complete", "operation_event": event, "work_orders": work_orders}


def record_team_workspace_activity(
    repo_root: Path,
    packet_id: str | None = None,
    *,
    action: str = "assign_packet_owner",
    owner_role: str = "operator",
) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    row = {
        "activity_id": f"team-activity-{packet_id}-{_now().replace(':', '').replace('+', 'Z')}",
        "packet_id": packet_id,
        "action": action,
        "owner_role": owner_role,
        "status": "recorded_local",
        "next_valid_move": packet.get("next_valid_move"),
        "external_claims_opened": False,
    }
    path = _graph(repo_root) / "team_workspace_activity.json"
    _append_json_rows(path, row, key="activity_id")
    event = _record_operation(
        repo_root,
        operation="record_team_workspace_activity",
        packet_id=packet_id,
        coverage=["team_workspace_activity"],
        artifacts=[path],
    )
    _apply_operation_proofs(repo_root)
    return {"status": "operation_complete", "operation_event": event, "activity": row}


def authorize_billing_usage(
    repo_root: Path,
    packet_id: str | None = None,
    *,
    action: str = "generate_missing_evidence_report",
) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    controls = _load_json(_graph(repo_root) / "billing_credit_controls.json", {})
    action_map = {str(row.get("action")): row for row in controls.get("billable_actions", [])}
    normalized_action = {
        "generate_missing_evidence_report": "ai_extraction",
        "generate_broker_packet": "buyer_ready_packet",
        "request_billing_quote": "api_agent_usage",
    }.get(action, action)
    control = action_map.get(normalized_action, {"estimated_credits": 1, "free_plan_behavior": "allowed_with_limits"})
    allowed = control.get("free_plan_behavior") != "blocked_requires_upgrade"
    event = {
        "usage_event_id": f"usage-event-{packet_id}-{normalized_action}-{_now().replace(':', '').replace('+', 'Z')}",
        "packet_id": packet_id,
        "action": normalized_action,
        "estimated_credits": control.get("estimated_credits", 1),
        "authorization_status": "authorized_local_no_charge" if allowed else "blocked_requires_upgrade_or_manual_approval",
        "credits_reserved": control.get("estimated_credits", 1) if allowed else 0,
        "credits_charged": 0,
        "external_charge_created": False,
    }
    usage_path = _graph(repo_root) / "billing_usage_ledger.json"
    usage = _load_json(usage_path, {"status": "billing_usage_ledger_ready_local_no_charges", "usage_rows": []})
    usage_events = [row for row in usage.get("usage_events", []) if row.get("usage_event_id") != event["usage_event_id"]]
    usage_events.append(event)
    usage["usage_events"] = usage_events
    usage["executed_usage_event_count"] = len(usage_events)
    usage["total_reserved_credits"] = sum(int(row.get("credits_reserved") or 0) for row in usage_events)
    usage["external_charge_created"] = False
    write_json(usage, usage_path)
    op_event = _record_operation(
        repo_root,
        operation="authorize_billing_usage",
        packet_id=packet_id,
        coverage=["billing_metering", "agent_tool_execution"],
        artifacts=[usage_path],
        details={"action": normalized_action, "authorization_status": event["authorization_status"]},
    )
    _apply_operation_proofs(repo_root)
    return {"status": "operation_complete", "operation_event": op_event, "usage_event": event}


def record_launch_control_event(
    repo_root: Path,
    packet_id: str | None = None,
    *,
    control: str = "private_beta_launch",
) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    packet_id = str(packet["packet_id"])
    row = {
        "launch_event_id": f"launch-event-{packet_id}-{control}-{_now().replace(':', '').replace('+', 'Z')}",
        "packet_id": packet_id,
        "control": control,
        "status": "blocked_pending_human_approval",
        "public_launch_allowed": False,
        "human_approval_required": True,
        "external_effects_created": False,
        "next_valid_move": "Route board/private-beta approval packet to owners before enabling any external launch effect.",
    }
    path = _graph(repo_root) / "launch_operations_events.json"
    _append_json_rows(path, row, key="launch_event_id")
    event = _record_operation(
        repo_root,
        operation="record_launch_control_event",
        packet_id=packet_id,
        coverage=["launch_control_event"],
        artifacts=[path],
    )
    _apply_operation_proofs(repo_root)
    return {"status": "operation_complete", "operation_event": event, "launch_event": row}


def create_trade_packet(repo_root: Path, fields: dict[str, Any], actor: dict[str, Any] | None = None) -> dict[str, Any]:
    packets, evidence_rows, _official_sources = load_current_product_rows(repo_root)
    packet = packet_from_submission(
        {
            **fields,
            "organization_id": (actor or {}).get("organization_id") or fields.get("organization_id") or "org-importer-demo",
        }
    )
    evidence = evidence_from_submission(packet)
    packets = [row for row in packets if str(row.get("packet_id")) != str(packet["packet_id"])]
    evidence_rows = [row for row in evidence_rows if str(row.get("packet_id")) != str(packet["packet_id"])]
    packets.append(packet)
    evidence_rows.append(evidence)
    workflow = persist_product_state(repo_root, packets, evidence_rows)
    packet = _packet_lookup(workflow)[str(packet["packet_id"])]
    event = _record_operation(
        repo_root,
        operation="create_trade_packet",
        packet_id=str(packet["packet_id"]),
        coverage=["data_intake", "persistence_refresh", "agent_tool_execution"],
        artifacts=[
            _graph(repo_root) / "customer_source_packets.json",
            _graph(repo_root) / "evidence_ledger.json",
            _graph(repo_root) / "customer_workflow.sqlite",
        ],
    )
    _apply_operation_proofs(repo_root)
    return {"status": "operation_complete", "operation_event": event, "packet": packet}


def get_supported_countries(repo_root: Path) -> dict[str, Any]:
    coverage = _load_json(_graph(repo_root) / "country_coverage_report.json", {})
    countries = coverage.get("countries", [])
    event = _record_operation(
        repo_root,
        operation="get_supported_countries",
        packet_id=None,
        coverage=["agent_tool_execution"],
        artifacts=[_graph(repo_root) / "country_coverage_report.json"],
        details={"country_count": len(countries)},
    )
    return {"status": "operation_complete", "operation_event": event, "countries": countries}


def get_country_coverage(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    coverage = _load_json(_graph(repo_root) / "country_coverage_report.json", {})
    packet_rows = coverage.get("packet_coverage", [])
    rows = [row for row in packet_rows if not packet_id or str(row.get("packet_id")) == packet_id]
    event = _record_operation(
        repo_root,
        operation="get_country_coverage",
        packet_id=packet_id,
        coverage=["agent_tool_execution"],
        artifacts=[_graph(repo_root) / "country_coverage_report.json"],
        details={"row_count": len(rows)},
    )
    return {"status": "operation_complete", "operation_event": event, "coverage": rows or coverage.get("countries", [])}


def get_packet_status(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    packet = _select_packet(workflow, packet_id)
    event = _record_operation(
        repo_root,
        operation="get_packet_status",
        packet_id=str(packet["packet_id"]),
        coverage=["agent_tool_execution"],
        artifacts=[_graph(repo_root) / "customer_readiness_report.json"],
        details={"customer_visible_status": packet.get("customer_visible_status")},
    )
    return {"status": "operation_complete", "operation_event": event, "packet": packet}


def execute_agent_tool(
    repo_root: Path,
    tool_name: str,
    fields: dict[str, Any] | None = None,
    actor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fields = fields or {}
    packet_id = str(fields.get("packet_id") or "").strip() or None
    if fields.get("external_effects_allowed") is True:
        raise PermissionError("agent tools cannot create external effects")
    tool_map = {
        "get_supported_countries": lambda: get_supported_countries(repo_root),
        "get_country_coverage": lambda: get_country_coverage(repo_root, packet_id),
        "create_trade_packet": lambda: create_trade_packet(repo_root, fields, actor),
        "generate_starter_checklist": lambda: generate_starter_checklist(repo_root, packet_id),
        "generate_missing_evidence_report": lambda: generate_missing_evidence_report(repo_root, packet_id),
        "generate_chatgpt_safe_summary": lambda: generate_chatgpt_safe_summary(repo_root, packet_id),
        "generate_broker_packet": lambda: generate_broker_packet(repo_root, packet_id),
        "get_packet_status": lambda: get_packet_status(repo_root, packet_id),
        "request_billing_quote": lambda: authorize_billing_usage(repo_root, packet_id, action="request_billing_quote"),
    }
    if tool_name not in tool_map:
        raise KeyError(f"agent tool not implemented: {tool_name}")
    result = tool_map[tool_name]()
    _apply_operation_proofs(repo_root)
    return {
        "status": SAFE_TOOL_STATUS,
        "tool": tool_name,
        "result": result,
        "external_effects_created": False,
        "credits_charged": 0,
        "can_open_claim_gate": False,
    }


def execute_all_local_product_operations(repo_root: Path, packet_id: str | None = None) -> dict[str, Any]:
    workflow = _read_workflow(repo_root)
    selected = _select_packet(workflow, packet_id)
    selected_id = str(selected["packet_id"])
    operations = [
        record_data_intake_snapshot(repo_root, selected_id),
        run_research_execution(repo_root, selected_id),
        generate_missing_evidence_report(repo_root, selected_id),
        generate_starter_checklist(repo_root, selected_id),
        generate_chatgpt_safe_summary(repo_root, selected_id),
        request_expert_review_work_orders(repo_root, selected_id),
        authorize_billing_usage(repo_root, selected_id, action="generate_missing_evidence_report"),
        record_team_workspace_activity(repo_root, selected_id),
        record_launch_control_event(repo_root, selected_id),
        execute_agent_tool(repo_root, "get_packet_status", {"packet_id": selected_id}),
    ]
    report = build_product_operations_report(repo_root)
    _apply_operation_proofs(repo_root)
    return {
        "status": PRODUCT_OPERATION_STATUS,
        "packet_id": selected_id,
        "operation_results": operations,
        "report": report,
        "external_effects_created": False,
        "claims_opened": False,
    }


def _apply_operation_proofs(repo_root: Path) -> None:
    report = build_product_operations_report(repo_root)
    graph = _graph(repo_root)
    all_stage_path = graph / "all_stage_readiness_report.json"
    gateway_path = graph / "agent_api_gateway_contract.json"
    research_path = graph / "research_execution_plan.json"
    expert_path = graph / "expert_network_report.json"
    team_path = graph / "team_workspace_report.json"
    launch_path = graph / "launch_operations_report.json"

    if all_stage_path.exists():
        all_stages = _load_json(all_stage_path, {})
        all_stages["operation_status"] = report["status"]
        all_stages["local_execution_proof_count"] = report["operation_count"]
        all_stages["execution_coverage"] = report["execution_coverage"]
        all_stages["execution_artifacts"] = report["artifact_refs"]
        for stage in all_stages.get("stages", []):
            stage["has_local_execution_proof"] = True
            stage["local_execution_report"] = "system_review_graph/product_operations_report.json"
        write_json(all_stages, all_stage_path)

    if gateway_path.exists():
        gateway = _load_json(gateway_path, {})
        gateway["operation_status"] = "agent_api_gateway_executed_local_no_external_effects"
        gateway["executed_tool_count"] = report["coverage_counts"].get("agent_tool_execution", 0)
        gateway["execution_report"] = "system_review_graph/product_operations_report.json"
        write_json(gateway, gateway_path)

    for path, status in (
        (research_path, "research_execution_operational_local_with_evidence_gates"),
        (expert_path, "expert_network_operational_local_with_human_review_gates"),
        (team_path, "team_workspace_operational_local_with_approval_gates"),
        (launch_path, "launch_operations_operational_local_with_human_approval_gates"),
    ):
        if path.exists():
            payload = _load_json(path, {})
            payload["operation_status"] = status
            payload["execution_report"] = "system_review_graph/product_operations_report.json"
            write_json(payload, path)


def build_product_operations_report(repo_root: Path) -> dict[str, Any]:
    events = _read_operation_events(repo_root)
    coverage_counts = {key: 0 for key in sorted(OPERATION_COVERAGE_KEYS)}
    artifact_refs: list[str] = []
    for event in events:
        for key in event.get("coverage", []):
            if key in coverage_counts:
                coverage_counts[key] += 1
        for artifact in event.get("artifacts", []):
            if artifact not in artifact_refs:
                artifact_refs.append(artifact)
    execution_coverage = {key: coverage_counts[key] > 0 for key in sorted(OPERATION_COVERAGE_KEYS)}
    report = {
        "generated_at": _now(),
        "status": PRODUCT_OPERATION_STATUS if all(execution_coverage.values()) else "local_product_operations_incomplete",
        "operation_count": len(events),
        "operations": events,
        "coverage_counts": coverage_counts,
        "execution_coverage": execution_coverage,
        "artifact_refs": sorted(artifact_refs),
        "external_effects_created": any(event.get("external_effects_created") for event in events),
        "claims_opened": any(event.get("claims_opened") for event in events),
        "proof_boundary": (
            "This proves local workflow execution, persistence, reports, and internal routing. "
            "It does not prove legal/compliance/customs/tariff/CFIA/buyer/supplier/payment/public-launch approval."
        ),
    }
    write_json(report, _operation_report_path(repo_root))
    return report


def reset_product_operations(repo_root: Path) -> None:
    """Clear operation-run artifacts that should be deterministic for proof commands."""

    graph = _graph(repo_root)
    for path in (
        graph / "product_operations_log.json",
        graph / "product_operations_report.json",
        graph / "research_execution_runs.json",
        graph / "expert_review_work_orders.json",
        graph / "team_workspace_activity.json",
        graph / "launch_operations_events.json",
        graph / "source_refresh_runs.json",
    ):
        path.unlink(missing_ok=True)
