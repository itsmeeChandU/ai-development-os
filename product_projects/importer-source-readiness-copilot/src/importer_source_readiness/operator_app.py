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
    build_customer_workflow,
    evidence_from_submission,
    load_json_list,
    markdown_report,
    packet_from_submission,
    write_json,
)


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
        return _load_json(report_path)
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
    if workflow["packets"]:
        packet_id = workflow["packets"][-1]["packet_id"]
        (repo_root / "system_review_graph" / "customer_readiness_report.md").write_text(
            markdown_report(workflow, packet_id),
            encoding="utf-8",
        )
    return workflow


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
    button {{ margin-top: 16px; border: 0; border-radius: 5px; background: #1d6b65; color: white; padding: 10px 14px; font-weight: 700; cursor: pointer; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #dce3ea; padding: 9px; vertical-align: top; }}
    th {{ background: #eef3f7; }}
    .status {{ display: inline-block; border: 1px solid #ccd5df; border-radius: 999px; padding: 4px 9px; background: #eef8f6; font-size: 13px; }}
    .claim-list li {{ margin: 4px 0; }}
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
            f"<td><span class='status'>{escape(str(packet.get('customer_visible_status')))}</span></td>"
            f"<td>{escape(str(packet.get('evidence_count')))}</td>"
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


def _render_packet_detail(packet: dict[str, Any]) -> str:
    body = f"""
<h1>{escape(str(packet.get('packet_name')))}</h1>
<p><span class="status">{escape(str(packet.get('display_status')))}</span></p>
<p class="note">{escape(str(packet.get('safe_summary')))}</p>
<p><a href="/source-packets/{escape(str(packet.get('packet_id')))}/evidence">Evidence</a> | <a href="/source-packets/{escape(str(packet.get('packet_id')))}/readiness-report">Readiness report</a> | <a href="/source-packets/{escape(str(packet.get('packet_id')))}/export">JSON export</a> | <a href="/operator/queue">Operator queue</a></p>
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
"""
    return _render_page(str(packet.get("packet_name")), body)


def _render_packet_evidence(packet: dict[str, Any]) -> str:
    rows = []
    for evidence in packet.get("evidence_items", []):
        rows.append(
            "<tr>"
            f"<td>{escape(str(evidence.get('evidence_id')))}</td>"
            f"<td><a href='{escape(str(evidence.get('source_url')))}'>{escape(str(evidence.get('evidence_type')))}</a></td>"
            f"<td>{escape(str(evidence.get('ledger_status')))}</td>"
            f"<td>{escape(str(evidence.get('rights_status')))}</td>"
            f"<td>{escape(str(evidence.get('freshness_status')))}</td>"
            f"<td>{escape(str(evidence.get('claim_boundary')))}</td>"
            "</tr>"
        )
    body = f"""
<h1>Evidence - {escape(str(packet.get('packet_name')))}</h1>
<p class="note">No evidence means no claim. Stale, reference-only, or AI-only evidence keeps claims blocked.</p>
<table>
  <thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Rights</th><th>Freshness</th><th>Boundary</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="6">No evidence.</td></tr>'}</tbody>
</table>
"""
    return _render_page("Packet Evidence", body)


def _render_packet_readiness(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    claims = "".join(f"<li>{escape(str(claim))}</li>" for claim in packet.get("blocked_claims", []))
    blockers = "".join(
        f"<tr><td>{escape(str(row.get('severity')))}</td><td>{escape(str(row.get('module')))}</td><td>{escape(str(row.get('issue')))}</td><td>{escape(str(row.get('next_valid_move')))}</td></tr>"
        for row in packet.get("blockers", [])
    )
    body = f"""
<h1>Readiness Report</h1>
<p><strong>{escape(str(packet.get('packet_name')))}</strong></p>
<p><span class="status">{escape(str(packet.get('display_status')))}</span></p>
<p class="note">{escape(str(packet.get('safe_summary')))}</p>
<h2>Blocked Claims</h2>
<ul class="claim-list">{claims}</ul>
<h2>Blockers</h2>
<table>
  <thead><tr><th>Severity</th><th>Module</th><th>Issue</th><th>Next Valid Move</th></tr></thead>
  <tbody>{blockers or '<tr><td colspan="4">No blockers for internal review.</td></tr>'}</tbody>
</table>
<h2>Boundary</h2>
<p>{escape(str(workflow.get('proof_boundary')))}</p>
"""
    return _render_page("Readiness Report", body)


def _index_payload(repo_root: Path) -> dict[str, Any]:
    workflow = _load_json(repo_root / "system_review_graph" / "operator_workflow_report.json")
    continuation = _load_json(repo_root / "system_review_graph" / "continuation_plan.json")
    board = _load_json(repo_root / "system_review_graph" / "board_go_live_readiness_report.json")
    customer = _customer_workflow(repo_root)
    return {
        "product": "Importer Source Readiness Copilot",
        "surface": "local_operator_application",
        "operator_status": workflow.get("status"),
        "operator_can_use_now": workflow.get("operator_can_use_now"),
        "work_queue_count": workflow.get("work_queue_count"),
        "customer_workflow_status": customer.get("status"),
        "customer_packet_count": customer.get("packet_count"),
        "startup_status": continuation.get("status"),
        "board_status": board.get("status"),
        "allowed_use": workflow.get("allowed_use"),
        "not_allowed_use": workflow.get("not_allowed_use", []),
        "routes": sorted([*API_ROUTES, *STATIC_ROUTES, "/source-packets", "/source-packets/new", "/operator/queue"]),
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
            if view in {"readiness", "readiness-report"}:
                self._send_html(_render_packet_readiness(workflow, packet))
                return
            if view == "export":
                self._send_json({"packet": packet, "proof_boundary": workflow.get("proof_boundary")})
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Source packet route not found")

    return OperatorAppHandler


def make_server(repo_root: Path, host: str, port: int) -> ThreadingHTTPServer:
    handler = build_operator_app_handler(repo_root)
    return ThreadingHTTPServer((host, port), handler)
