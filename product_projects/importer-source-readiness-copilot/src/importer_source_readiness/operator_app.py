"""Local operator web app for Importer Source Readiness Copilot."""

from __future__ import annotations

import json
import mimetypes
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .source_packet_workflow import (
    OPERATOR_WORKBENCH_STATUS,
    build_customer_workflow,
    build_ai_review_run,
    evidence_from_submission,
    expert_review_packet_markdown,
    load_json_list,
    markdown_report,
    packet_from_submission,
    refresh_packet_sources,
    write_json,
)
from .customer_store import write_customer_store


API_ROUTES = {
    "/api/readiness": "system_review_graph/readiness_report.json",
    "/api/external-gates": "system_review_graph/external_gate_report.json",
    "/api/continuation": "system_review_graph/continuation_plan.json",
    "/api/vc-pitch": "system_review_graph/vc_pitch_readiness_report.json",
    "/api/board-go-live": "system_review_graph/board_go_live_readiness_report.json",
    "/api/operator-workflow": "system_review_graph/operator_workflow_report.json",
    "/api/operator-screenshots": "system_review_graph/operator_screenshot_manifest.json",
}

STATIC_ROUTES = {
    "/": "system_review_graph/operator_dashboard.html",
    "/dashboard": "system_review_graph/operator_dashboard.html",
    "/operator_dashboard.html": "system_review_graph/operator_dashboard.html",
}


def _safe_join(root: Path, relative_path: str) -> Path | None:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _safe_join_under(base: Path, relative_path: str) -> Path | None:
    base = base.resolve()
    candidate = (base / relative_path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_list_or_rows(path: Path, fallback: Path) -> list[dict[str, Any]]:
    selected = path if path.exists() else fallback
    payload = json.loads(selected.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    raise ValueError(f"expected list or rows in {selected}")


def _customer_workflow(repo_root: Path) -> dict[str, Any]:
    report_path = repo_root / "system_review_graph" / "customer_readiness_report.json"
    if report_path.exists():
        payload = _load_json(report_path)
        if payload.get("customer_stage_status") and payload.get("private_beta_readiness"):
            return payload
    return build_customer_workflow(
        source_packets=load_json_list(repo_root / "data" / "customer_source_packets.json"),
        evidence_items=load_json_list(repo_root / "data" / "evidence_ledger.json"),
        official_sources=_load_json(repo_root / "data" / "official_source_registry.json"),
    )


def _write_customer_workflow(repo_root: Path, packets: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    workflow = build_customer_workflow(
        source_packets=packets,
        evidence_items=evidence,
        official_sources=_load_json(repo_root / "data" / "official_source_registry.json"),
    )
    write_json(workflow, repo_root / "system_review_graph" / "customer_readiness_report.json")
    write_json(workflow["packets"], repo_root / "system_review_graph" / "customer_source_packets.json")
    write_json(workflow["evidence_ledger"], repo_root / "system_review_graph" / "evidence_ledger.json")
    write_json(workflow["ai_review_runs"], repo_root / "system_review_graph" / "customer_ai_review_runs.json")
    write_customer_store(workflow, repo_root / "system_review_graph" / "customer_workflow.sqlite")
    if workflow["packets"]:
        packet_id = workflow["packets"][-1]["packet_id"]
        (repo_root / "system_review_graph" / "customer_readiness_report.md").write_text(
            markdown_report(workflow, packet_id),
            encoding="utf-8",
        )
        (repo_root / "system_review_graph" / f"expert_review_packet_{packet_id}.md").write_text(
            expert_review_packet_markdown(workflow, packet_id),
            encoding="utf-8",
        )
    return workflow


def _append_json_list(path: Path, row: dict[str, Any]) -> None:
    rows = []
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows = payload
    rows.append(row)
    write_json(rows, path)


def _load_mutable_customer_rows(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packets = _load_list_or_rows(
        repo_root / "system_review_graph" / "customer_source_packets.json",
        repo_root / "data" / "customer_source_packets.json",
    )
    evidence_rows = _load_list_or_rows(
        repo_root / "system_review_graph" / "evidence_ledger.json",
        repo_root / "data" / "evidence_ledger.json",
    )
    return packets, evidence_rows


def _packet_lookup(workflow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(packet.get("packet_id")): packet for packet in workflow.get("packets", [])}


def _render_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #fbfcfd; color: #172026; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 28px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{ margin-top: 26px; }}
    p {{ line-height: 1.5; }}
    a {{ color: #155f59; }}
    .note {{ border: 1px solid #ead28a; background: #fff7df; border-radius: 6px; padding: 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    label {{ display: block; font-weight: 700; margin: 10px 0 4px; }}
    input, textarea, select {{ box-sizing: border-box; width: 100%; border: 1px solid #ccd5df; border-radius: 5px; padding: 9px; font: inherit; }}
    button, .button-link {{ display: inline-block; margin-top: 10px; border: 0; border-radius: 5px; background: #1d6b65; color: white; padding: 10px 14px; font-weight: 700; cursor: pointer; text-decoration: none; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #dce3ea; padding: 9px; vertical-align: top; }}
    th {{ background: #eef3f7; }}
    .status {{ display: inline-block; border: 1px solid #ccd5df; border-radius: 999px; padding: 4px 9px; background: #eef8f6; font-size: 13px; }}
    .claim-list li {{ margin: 4px 0; }}
    .metric {{ border: 1px solid #ccd5df; border-radius: 6px; padding: 12px; background: #fff; }}
    .label {{ color: #52616f; font-size: 12px; }}
    .value {{ font-weight: 700; margin-top: 4px; overflow-wrap: anywhere; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; align-items: end; }}
    .actions form {{ margin: 0; }}
    pre {{ white-space: pre-wrap; border: 1px solid #ccd5df; border-radius: 6px; padding: 14px; background: #fff; overflow: auto; }}
    .closed {{ color: #9f2f2f; font-weight: 700; }}
    @media (max-width: 760px) {{ main {{ padding: 20px; }} .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def _render_packet_list(workflow: dict[str, Any]) -> str:
    rows = []
    for packet in workflow.get("packets", []):
        packet_id = escape(str(packet.get("packet_id")))
        rows.append(
            "<tr>"
            f"<td><a href='/source-packets/{packet_id}'>{escape(str(packet.get('packet_name')))}</a></td>"
            f"<td>{escape(str(packet.get('product_name')))}</td>"
            f"<td><span class='status'>{escape(str(packet.get('customer_visible_status_label')))}</span></td>"
            f"<td>{escape(str((packet.get('evidence_summary') or {}).get('summary')))}</td>"
            f"<td>{escape(str(packet.get('blocker_count')))}</td>"
            f"<td>{escape(str(packet.get('next_valid_move')))}</td>"
            "</tr>"
        )
    body = f"""
<h1>Customer Source Packets</h1>
<p><span class="status">{escape(str(workflow.get("display_status")))}</span></p>
<p class="note">{escape(str(workflow.get("proof_boundary")))}</p>
<p><a href="/source-packets/new">Create a source packet</a> | <a href="/">Operator dashboard</a></p>
<table>
  <thead><tr><th>Packet</th><th>Product</th><th>Status</th><th>Evidence</th><th>Blockers</th><th>Next Valid Move</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="6">No packets.</td></tr>'}</tbody>
</table>
"""
    return _render_page("Source Packets", body)


def _render_packet_form() -> str:
    body = """
<h1>Create Source Packet</h1>
<p class="note">Local intake creates an internal readiness packet. It does not provide customs, tariff, legal, CFIA, supplier, buyer, or launch approval.</p>
<form method="post" action="/source-packets">
  <div class="grid">
    <div><label>Packet name</label><input name="packet_name" value="Frozen tuna Canada source packet"></div>
    <div><label>Product name</label><input name="product_name" value="Frozen tuna fillet"></div>
    <div><label>Product category</label><input name="product_category" value="food_import"></div>
    <div><label>HS code if known</label><input name="hs_code_value" value="0304870000"></div>
    <div><label>Origin country</label><input name="origin_country" value="Vietnam"></div>
    <div><label>Destination country</label><input name="destination_country" value="Canada"></div>
    <div><label>Supplier name</label><input name="supplier_name" value="Example Seafood Supplier"></div>
    <div><label>Supplier country</label><input name="supplier_country" value="Vietnam"></div>
  </div>
  <label>Source URL</label><input name="source_url" value="https://ised-isde.canada.ca/site/ised/en/research-and-business-intelligence/canadian-importers-database">
  <label>Intended use</label><textarea name="intended_use" rows="4">Assess whether this source packet is ready for internal importer/source-readiness review.</textarea>
  <label>Notes</label><textarea name="notes" rows="4">Customer-submitted source packet. Claims remain blocked until evidence, review, contracts, screening, and launch gates are closed.</textarea>
  <button type="submit">Generate Readiness Report</button>
</form>
"""
    return _render_page("Create Source Packet", body)


def _action_form(packet_id: str, action: str, label: str, extra: str = "") -> str:
    return (
        f"<form method='post' action='/source-packets/{escape(packet_id)}/actions'>"
        f"<input type='hidden' name='action' value='{escape(action)}'>"
        f"{extra}"
        f"<button type='submit'>{escape(label)}</button>"
        "</form>"
    )


def _render_action_bar(packet: dict[str, Any]) -> str:
    packet_id = str(packet.get("packet_id"))
    return (
        "<div class='actions'>"
        + _action_form(packet_id, "refresh_sources", "Refresh Official Sources")
        + _action_form(packet_id, "request_operator_review", "Request Operator Review")
        + _action_form(packet_id, "run_ai_review", "Run AI Review")
        + _action_form(packet_id, "generate_expert_packet", "Generate Expert Review Packet")
        + f"<a class='button-link' href='/source-packets/{escape(packet_id)}/export'>Export Readiness Report</a>"
        + "</div>"
    )


def _list_items(rows: list[Any]) -> str:
    return "".join(f"<li>{escape(str(row))}</li>" for row in rows)


def _blocker_group_rows(groups: list[dict[str, Any]]) -> str:
    if not groups:
        return "<tr><td colspan='5'>No grouped blockers.</td></tr>"
    return "".join(
        "<tr>"
        f"<td>{escape(str(row.get('stage')))}</td>"
        f"<td>{escape(str(row.get('title')))}</td>"
        f"<td>{escape(str(row.get('owner_role')))}</td>"
        f"<td>{escape(str(row.get('blocker_count')))}</td>"
        f"<td>{escape(str(row.get('next_valid_move')))}</td>"
        "</tr>"
        for row in groups
    )


def _render_packet_detail(packet: dict[str, Any]) -> str:
    evidence_summary = packet.get("evidence_summary") or {}
    top_blockers = _blocker_group_rows(packet.get("top_blockers", []))
    allowed = _list_items(packet.get("allowed_actions", []))
    not_allowed = _list_items(packet.get("not_allowed_actions", []))
    body = f"""
<h1>{escape(str(packet.get('packet_name')))}</h1>
<p><span class="status">{escape(str(packet.get('customer_visible_status_label')))}</span></p>
<p class="note">{escape(str(packet.get('safe_summary')))}</p>
{_render_action_bar(packet)}
<p><a href="/source-packets/{escape(str(packet.get('packet_id')))}/evidence">Evidence</a> | <a href="/source-packets/{escape(str(packet.get('packet_id')))}/blockers">Blockers</a> | <a href="/source-packets/{escape(str(packet.get('packet_id')))}/readiness-report">Readiness report</a> | <a href="/source-packets/{escape(str(packet.get('packet_id')))}/expert-review-packet">Expert review packet</a> | <a href="/operator/queue">Operator queue</a></p>
<section class="grid">
  <div class="metric"><div class="label">Readiness</div><div class="value">{escape(str(packet.get('readiness_status_label')))}</div></div>
  <div class="metric"><div class="label">Evidence</div><div class="value">{escape(str(evidence_summary.get('summary')))}</div></div>
  <div class="metric"><div class="label">Blockers</div><div class="value">{escape(str(packet.get('blocker_count')))}</div></div>
  <div class="metric"><div class="label">Next</div><div class="value">{escape(str(packet.get('next_valid_move')))}</div></div>
</section>
<table>
  <tbody>
    <tr><th>Product</th><td>{escape(str(packet.get('product_name')))}</td></tr>
    <tr><th>Category</th><td>{escape(str(packet.get('product_category')))}</td></tr>
    <tr><th>Origin</th><td>{escape(str(packet.get('origin_country')))}</td></tr>
    <tr><th>Destination</th><td>{escape(str(packet.get('destination_country')))}</td></tr>
    <tr><th>Supplier</th><td>{escape(str(packet.get('supplier_name')))}</td></tr>
    <tr><th>HS code if known</th><td>{escape(str(packet.get('hs_code_value')))}</td></tr>
    <tr><th>Customer status</th><td>{escape(str(packet.get('customer_visible_status')))}</td></tr>
    <tr><th>Next valid move</th><td>{escape(str(packet.get('next_valid_move')))}</td></tr>
  </tbody>
</table>
<h2>Why Blocked</h2>
<table>
  <thead><tr><th>Stage</th><th>Group</th><th>Owner Role</th><th>Items</th><th>Next Valid Move</th></tr></thead>
  <tbody>{top_blockers}</tbody>
</table>
<div class="grid">
  <div><h2>Allowed</h2><ul>{allowed}</ul></div>
  <div><h2>Not Allowed</h2><ul>{not_allowed}</ul></div>
</div>
"""
    return _render_page(str(packet.get("packet_name")), body)


def _render_packet_evidence(packet: dict[str, Any]) -> str:
    summary = packet.get("evidence_summary") or {}
    rows = []
    for evidence in packet.get("evidence_items", []):
        rows.append(
            "<tr>"
            f"<td>{escape(str(evidence.get('evidence_id')))}</td>"
            f"<td><a href='{escape(str(evidence.get('source_url')))}'>{escape(str(evidence.get('evidence_type')))}</a></td>"
            f"<td>{escape(str(evidence.get('ledger_status')))}</td>"
            f"<td>{escape(str(evidence.get('rights_status')))}</td>"
            f"<td>{escape(str(evidence.get('freshness_status')))}</td>"
            f"<td>{escape(str(evidence.get('claim_supported')))}</td>"
            f"<td>{escape(str(evidence.get('review_required')))}</td>"
            f"<td>{escape(str(evidence.get('claim_boundary')))}</td>"
            "</tr>"
        )
    body = f"""
<h1>Evidence - {escape(str(packet.get('packet_name')))}</h1>
<p class="note">No evidence means no claim. Stale, reference-only, or AI-only evidence keeps claims blocked.</p>
<section class="grid">
  <div class="metric"><div class="label">Attached</div><div class="value">{escape(str(summary.get('attached')))}</div></div>
  <div class="metric"><div class="label">Accepted</div><div class="value">{escape(str(summary.get('accepted')))}</div></div>
  <div class="metric"><div class="label">Stale</div><div class="value">{escape(str(summary.get('stale')))}</div></div>
  <div class="metric"><div class="label">Missing</div><div class="value">{escape(str(summary.get('missing')))}</div></div>
</section>
<h2>Upload Evidence</h2>
<form method="post" action="/source-packets/{escape(str(packet.get('packet_id')))}/actions">
  <input type="hidden" name="action" value="upload_evidence">
  <label>Evidence type</label><input name="evidence_type" value="customer_uploaded_reference">
  <label>Source URL</label><input name="source_url" value="">
  <label>Claim supported</label><input name="claim_supported" value="Customer-uploaded evidence for internal review">
  <button type="submit">Upload Evidence</button>
</form>
<table>
  <thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Rights</th><th>Freshness</th><th>Claim Supported</th><th>Review Required</th><th>Boundary</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="8">No evidence.</td></tr>'}</tbody>
</table>
"""
    return _render_page("Packet Evidence", body)


def _render_packet_readiness(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    claims = "".join(f"<li>{escape(str(claim))}</li>" for claim in packet.get("blocked_claims_display", []))
    missing = _list_items(packet.get("evidence_summary", {}).get("missing_items", []))
    blockers = _blocker_group_rows(packet.get("blocker_groups", []))
    body = f"""
<h1>Readiness Report</h1>
<p><strong>{escape(str(packet.get('packet_name')))}</strong></p>
<p><span class="status">{escape(str(packet.get('display_status')))}</span></p>
<p class="note">{escape(str(packet.get('safe_summary')))}</p>
<h2>Evidence Summary</h2>
<p>{escape(str(packet.get('evidence_summary', {}).get('summary')))}</p>
<h2>Missing Evidence</h2>
<ul>{missing}</ul>
<h2>Blocked Claims</h2>
<ul class="claim-list">{claims}</ul>
<h2>Blockers</h2>
<table>
  <thead><tr><th>Stage</th><th>Group</th><th>Owner Role</th><th>Items</th><th>Next Valid Move</th></tr></thead>
  <tbody>{blockers}</tbody>
</table>
<h2>Boundary</h2>
<p>{escape(str(workflow.get('proof_boundary')))}</p>
"""
    return _render_page("Readiness Report", body)


def _render_packet_blockers(packet: dict[str, Any]) -> str:
    detailed = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('group_title')))}</td>"
        f"<td>{escape(str(row.get('issue')))}</td>"
        f"<td>{escape(str(row.get('evidence_required')))}</td>"
        f"<td>{escape(str(row.get('next_valid_move')))}</td>"
        "<td>"
        + _action_form(str(packet.get("packet_id")), "request_review", "Request review", f"<input type='hidden' name='blocker_id' value='{escape(str(row.get('id')))}'>")
        + _action_form(str(packet.get("packet_id")), "resolve_blocker", "Resolve", f"<input type='hidden' name='blocker_id' value='{escape(str(row.get('id')))}'>")
        + "</td>"
        "</tr>"
        for row in packet.get("blockers", [])
    )
    body = f"""
<h1>Blockers - {escape(str(packet.get('packet_name')))}</h1>
<p class="note">Blockers cannot close without attached evidence. Resolve attempts without evidence are logged but rejected.</p>
<table>
  <thead><tr><th>Group</th><th>Issue</th><th>Evidence Required</th><th>Next Valid Move</th><th>Actions</th></tr></thead>
  <tbody>{detailed or '<tr><td colspan="5">No blockers.</td></tr>'}</tbody>
</table>
"""
    return _render_page("Packet Blockers", body)


def _render_expert_packet(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    markdown = expert_review_packet_markdown(workflow, str(packet.get("packet_id")))
    return _render_page(
        "Expert Review Packet",
        f"<h1>Expert Review Packet</h1><pre>{escape(markdown)}</pre>",
    )


def _render_admin_sources(workflow: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('name')))}</td>"
        f"<td>{escape(str(row.get('jurisdiction')))}</td>"
        f"<td>{escape(str(row.get('evidence_role')))}</td>"
        f"<td>{escape(str(row.get('accessed_at')))}</td>"
        f"<td>refresh required before claims</td>"
        f"<td>{escape(str(row.get('claim_boundary')))}</td>"
        "</tr>"
        for row in workflow.get("official_sources", [])
    )
    body = f"""
<h1>Official Source Registry</h1>
<p class="note">Official sources are reference inputs. Claims stay closed until source refresh and qualified review exist.</p>
<table>
  <thead><tr><th>Source</th><th>Jurisdiction</th><th>Used For</th><th>Accessed At</th><th>Freshness</th><th>Claim Boundary</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
"""
    return _render_page("Official Sources", body)


def _render_admin_gates(workflow: dict[str, Any]) -> str:
    private_beta = workflow.get("private_beta_readiness", {})
    ready = _list_items(private_beta.get("ready", []))
    blocked = _blocker_group_rows(private_beta.get("blocked", []))
    body = f"""
<h1>Private Beta Gates</h1>
<p><span class="status">{escape(str(private_beta.get('display_status')))}</span></p>
<h2>Ready</h2>
<ul>{ready}</ul>
<h2>Blocked</h2>
<table>
  <thead><tr><th>Stage</th><th>Gate</th><th>Owner Role</th><th>Items</th><th>Next Valid Move</th></tr></thead>
  <tbody>{blocked}</tbody>
</table>
<p class="closed">Unsafe gates are closed by default.</p>
"""
    return _render_page("Private Beta Gates", body)


def _index_payload(repo_root: Path) -> dict[str, Any]:
    workflow = _load_json(repo_root / "system_review_graph" / "operator_workflow_report.json")
    continuation = _load_json(repo_root / "system_review_graph" / "continuation_plan.json")
    board = _load_json(repo_root / "system_review_graph" / "board_go_live_readiness_report.json")
    customer = _customer_workflow(repo_root)
    return {
        "product": "Importer Source Readiness Copilot",
        "surface": "local_operator_application",
        "operator_status": workflow.get("status"),
        "operator_display_status": workflow.get("display_status") or OPERATOR_WORKBENCH_STATUS,
        "operator_can_use_now": workflow.get("operator_can_use_now"),
        "work_queue_count": workflow.get("work_queue_count"),
        "customer_workflow_status": customer.get("status"),
        "customer_stage_status": customer.get("customer_stage_status"),
        "private_beta_status": customer.get("private_beta_status"),
        "customer_packet_count": customer.get("packet_count"),
        "startup_status": continuation.get("status"),
        "board_status": board.get("status"),
        "allowed_use": workflow.get("allowed_use"),
        "not_allowed_use": workflow.get("not_allowed_use", []),
        "routes": sorted(
            [
                *API_ROUTES,
                *STATIC_ROUTES,
                "/source-packets",
                "/source-packets/new",
                "/source-packets/:id",
                "/source-packets/:id/evidence",
                "/source-packets/:id/blockers",
                "/source-packets/:id/readiness-report",
                "/source-packets/:id/expert-review-packet",
                "/source-packets/:id/export",
                "/operator/queue",
                "/operator/packets/:id",
                "/admin/sources",
                "/admin/gates",
            ]
        ),
        "proof_boundary": (
            "This local app is the internal operator surface. It is not a public "
            "customer app, customs/tariff advice, supplier recommendation, legal "
            "or financial advice, or launch approval."
        ),
    }


def build_operator_app_handler(repo_root: Path) -> type[BaseHTTPRequestHandler]:
    repo_root = repo_root.resolve()

    class OperatorAppHandler(BaseHTTPRequestHandler):
        server_version = "ImporterSourceReadinessOperatorApp/0.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = unquote(parsed.path)

            if path == "/api":
                self._send_json(_index_payload(repo_root))
                return
            if path == "/api/customer-workflow":
                self._send_json(_customer_workflow(repo_root))
                return
            if path in API_ROUTES:
                self._send_file(API_ROUTES[path], "application/json; charset=utf-8")
                return
            if path in STATIC_ROUTES:
                self._send_file(STATIC_ROUTES[path], "text/html; charset=utf-8")
                return
            if path == "/source-packets":
                self._send_html(_render_packet_list(_customer_workflow(repo_root)))
                return
            if path == "/source-packets/new":
                self._send_html(_render_packet_form())
                return
            if path == "/admin/sources":
                self._send_html(_render_admin_sources(_customer_workflow(repo_root)))
                return
            if path == "/admin/gates":
                self._send_html(_render_admin_gates(_customer_workflow(repo_root)))
                return
            if path == "/operator/queue":
                self._send_file("system_review_graph/operator_dashboard.html", "text/html; charset=utf-8")
                return
            if path.startswith("/operator/packets/"):
                packet_id = path.removeprefix("/operator/packets/").strip("/")
                self._send_packet_route(packet_id, "")
                return
            if path.startswith("/source-packets/"):
                suffix = path.removeprefix("/source-packets/").strip("/")
                parts = suffix.split("/")
                packet_id = parts[0]
                view = parts[1] if len(parts) > 1 else ""
                self._send_packet_route(packet_id, view)
                return
            if path.startswith("/operator_screenshots/"):
                self._send_scoped_file(
                    repo_root / "system_review_graph" / "operator_screenshots",
                    path.removeprefix("/operator_screenshots/"),
                    None,
                )
                return
            if path.startswith("/system_review_graph/"):
                self._send_scoped_file(
                    repo_root / "system_review_graph",
                    path.removeprefix("/system_review_graph/"),
                    None,
                )
                return

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown operator app route")

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            if path != "/source-packets":
                if path.startswith("/source-packets/") and path.endswith("/actions"):
                    packet_id = path.removeprefix("/source-packets/").removesuffix("/actions").strip("/")
                    self._handle_packet_action(packet_id)
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown operator app route")
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length > 65536:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Source packet too large")
                return
            raw = self.rfile.read(length).decode("utf-8")
            content_type = self.headers.get("Content-Type", "")
            if "application/json" in content_type:
                fields = json.loads(raw or "{}")
            else:
                parsed_fields = parse_qs(raw, keep_blank_values=True)
                fields = {key: values[-1] for key, values in parsed_fields.items()}
            packet = packet_from_submission(fields)
            evidence = evidence_from_submission(packet)
            packets = _load_list_or_rows(
                repo_root / "system_review_graph" / "customer_source_packets.json",
                repo_root / "data" / "customer_source_packets.json",
            )
            evidence_rows = _load_list_or_rows(
                repo_root / "system_review_graph" / "evidence_ledger.json",
                repo_root / "data" / "evidence_ledger.json",
            )
            packets = [row for row in packets if str(row.get("packet_id")) != str(packet["packet_id"])]
            evidence_rows = [
                row
                for row in evidence_rows
                if str(row.get("evidence_id")) != str(evidence["evidence_id"])
            ]
            packets.append(packet)
            evidence_rows.append(evidence)
            _write_customer_workflow(repo_root, packets, evidence_rows)
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/source-packets/{packet['packet_id']}/readiness-report")
            self.end_headers()

        def _handle_packet_action(self, packet_id: str) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 65536:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Packet action too large")
                return
            raw = self.rfile.read(length).decode("utf-8")
            fields = {key: values[-1] for key, values in parse_qs(raw, keep_blank_values=True).items()}
            action = str(fields.get("action") or "")
            packets, evidence_rows = _load_mutable_customer_rows(repo_root)
            redirect = f"/source-packets/{packet_id}"
            action_log = repo_root / "system_review_graph" / "customer_action_log.json"
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat()

            if action == "refresh_sources":
                evidence_rows, refresh_report = refresh_packet_sources(
                    packet_id=packet_id,
                    evidence_items=evidence_rows,
                    actor="local_operator",
                )
                write_json(refresh_report, repo_root / "system_review_graph" / f"source_refresh_report_{packet_id}.json")
                _append_json_list(repo_root / "system_review_graph" / "source_refresh_runs.json", refresh_report)
                redirect = f"/source-packets/{packet_id}/evidence"
            elif action == "upload_evidence":
                evidence_rows.append(
                    {
                        "evidence_id": f"evidence-{packet_id}-customer-{len(evidence_rows) + 1}",
                        "packet_id": packet_id,
                        "evidence_type": fields.get("evidence_type") or "customer_uploaded_reference",
                        "source_url": fields.get("source_url") or "",
                        "file_path": "",
                        "source_owner": "customer",
                        "uploaded_by": "local-customer",
                        "created_at": now,
                        "accessed_at": "",
                        "last_verified_at": "",
                        "expires_at": "",
                        "rights_status": "unknown",
                        "freshness_status": "needs_current_refresh_before_claims",
                        "claim_supported": fields.get("claim_supported") or "Customer-uploaded evidence for internal review.",
                        "claim_boundary": "Customer-uploaded evidence is internal review material until refreshed and reviewed.",
                        "review_required": True,
                        "human_review_status": "not_reviewed",
                        "reviewed_by": "",
                        "reviewed_at": "",
                    }
                )
                _append_json_list(
                    action_log,
                    {"event_id": f"{packet_id}:upload-evidence:{now}", "packet_id": packet_id, "event_type": "upload_evidence", "created_at": now},
                )
                redirect = f"/source-packets/{packet_id}/evidence"
            elif action == "run_ai_review":
                workflow = build_customer_workflow(
                    source_packets=packets,
                    evidence_items=evidence_rows,
                    official_sources=_load_json(repo_root / "data" / "official_source_registry.json"),
                )
                run = build_ai_review_run(workflow, packet_id)
                _append_json_list(repo_root / "system_review_graph" / "customer_ai_review_runs.json", run)
                redirect = f"/source-packets/{packet_id}/readiness-report"
            elif action == "generate_expert_packet":
                workflow = build_customer_workflow(
                    source_packets=packets,
                    evidence_items=evidence_rows,
                    official_sources=_load_json(repo_root / "data" / "official_source_registry.json"),
                )
                (repo_root / "system_review_graph" / f"expert_review_packet_{packet_id}.md").write_text(
                    expert_review_packet_markdown(workflow, packet_id),
                    encoding="utf-8",
                )
                redirect = f"/source-packets/{packet_id}/expert-review-packet"
            elif action in {"request_operator_review", "request_review"}:
                _append_json_list(
                    action_log,
                    {
                        "event_id": f"{packet_id}:request-review:{fields.get('blocker_id', 'packet')}:{now}",
                        "packet_id": packet_id,
                        "blocker_id": fields.get("blocker_id", ""),
                        "event_type": "request_review",
                        "created_at": now,
                        "claim_boundary": "Review request does not open external claims.",
                    },
                )
                redirect = f"/source-packets/{packet_id}/blockers"
            elif action == "resolve_blocker":
                _append_json_list(
                    action_log,
                    {
                        "event_id": f"{packet_id}:resolve-rejected:{fields.get('blocker_id', 'packet')}:{now}",
                        "packet_id": packet_id,
                        "blocker_id": fields.get("blocker_id", ""),
                        "event_type": "resolve_rejected_missing_evidence",
                        "created_at": now,
                        "claim_boundary": "Blocker resolution requires attached evidence before closure.",
                    },
                )
                redirect = f"/source-packets/{packet_id}/blockers"
            _write_customer_workflow(repo_root, packets, evidence_rows)
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", redirect)
            self.end_headers()

        def _send_html(self, html: str) -> None:
            data = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_scoped_file(self, base: Path, relative_path: str, content_type: str | None) -> None:
            path = _safe_join_under(base, relative_path)
            if path is None or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Artifact not found")
                return
            data = path.read_bytes()
            guessed_type = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", guessed_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_file(self, relative_path: str, content_type: str | None) -> None:
            path = _safe_join(repo_root, relative_path)
            if path is None or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Artifact not found")
                return
            data = path.read_bytes()
            guessed_type = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", guessed_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_packet_route(self, packet_id: str, view: str) -> None:
            workflow = _customer_workflow(repo_root)
            packet = _packet_lookup(workflow).get(packet_id)
            if packet is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Source packet not found")
                return
            if view in {"", "detail"}:
                self._send_html(_render_packet_detail(packet))
                return
            if view == "evidence":
                self._send_html(_render_packet_evidence(packet))
                return
            if view == "blockers":
                self._send_html(_render_packet_blockers(packet))
                return
            if view in {"readiness", "readiness-report"}:
                self._send_html(_render_packet_readiness(workflow, packet))
                return
            if view == "expert-review-packet":
                self._send_html(_render_expert_packet(workflow, packet))
                return
            if view == "export":
                self._send_json(
                    {
                        "summary": packet.get("safe_summary"),
                        "status": packet.get("customer_visible_status_label"),
                        "evidence_summary": packet.get("evidence_summary"),
                        "missing_evidence": packet.get("evidence_summary", {}).get("missing_items", []),
                        "blocked_claims": packet.get("blocked_claims_display"),
                        "next_valid_moves": [row.get("next_valid_move") for row in packet.get("blocker_groups", [])],
                        "official_references": workflow.get("official_sources", []),
                        "review_required": True,
                        "proof_boundary": workflow.get("proof_boundary"),
                    }
                )
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Source packet route not found")

    return OperatorAppHandler


def make_server(repo_root: Path, host: str, port: int) -> ThreadingHTTPServer:
    handler = build_operator_app_handler(repo_root)
    return ThreadingHTTPServer((host, port), handler)
