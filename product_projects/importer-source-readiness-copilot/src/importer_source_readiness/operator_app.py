"""Local operator web app for Importer Source Readiness Copilot."""

from __future__ import annotations

import json
import mimetypes
import re
import shutil
from datetime import datetime, timedelta, timezone
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .document_processing import MAX_PUBLIC_PDF_PAGES, triage_pdf_upload
from .source_packet_workflow import (
    OPERATOR_WORKBENCH_STATUS,
    PUBLIC_PRODUCT_NAME,
    PUBLIC_PRODUCT_PROMISE,
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
from .product_runtime import (
    AI_PROCESSING_MODES,
    ALLOWED_EVIDENCE_TYPES,
    CSRF_TOKEN,
    FORBIDDEN_REPORT_PHRASES,
    MAX_EVIDENCE_UPLOAD_BYTES,
    PRODUCT_BOUNDARY,
    REVIEW_TEMPLATES,
    SENSITIVITY_LEVELS,
    USERS,
    actor_by_session,
    ai_policy_for_org,
    build_runtime_state,
    can_access_packet,
    default_actor,
    deployment_readiness,
    endpoint_for_mode,
    packet_org_id,
    redaction_preview_for_evidence,
    route_ai_task,
    write_runtime_artifacts,
)


API_ROUTES = {
    "/api/readiness": "system_review_graph/readiness_report.json",
    "/api/external-gates": "system_review_graph/external_gate_report.json",
    "/api/continuation": "system_review_graph/continuation_plan.json",
    "/api/vc-pitch": "system_review_graph/vc_pitch_readiness_report.json",
    "/api/board-go-live": "system_review_graph/board_go_live_readiness_report.json",
    "/api/operator-workflow": "system_review_graph/operator_workflow_report.json",
    "/api/operator-screenshots": "system_review_graph/operator_screenshot_manifest.json",
    "/api/opportunities": "system_review_graph/opportunity_scanner_report.json",
    "/api/country-coverage": "system_review_graph/country_coverage_report.json",
    "/api/billing/controls": "system_review_graph/billing_credit_controls.json",
    "/api/billing/usage": "system_review_graph/billing_usage_ledger.json",
    "/api/agent-api": "system_review_graph/agent_api_manifest.json",
    "/api/agent-api/gateway": "system_review_graph/agent_api_gateway_contract.json",
    "/api/traffic-pages": "system_review_graph/traffic_pages_manifest.json",
    "/api/transport-readiness": "system_review_graph/transport_readiness_report.json",
    "/api/stages": "system_review_graph/all_stage_readiness_report.json",
    "/api/research-plan": "system_review_graph/research_execution_plan.json",
    "/api/expert-network": "system_review_graph/expert_network_report.json",
    "/api/team-workspace": "system_review_graph/team_workspace_report.json",
    "/api/launch-operations": "system_review_graph/launch_operations_report.json",
}

STATIC_ROUTES = {
    "/operator": "system_review_graph/operator_dashboard.html",
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


def _load_graph_json(repo_root: Path, artifact_name: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    path = repo_root / "system_review_graph" / artifact_name
    if path.exists():
        payload = _load_json(path)
        if isinstance(payload, dict):
            return payload
    return default or {"status": "artifact_missing", "proof_boundary": "Run the product checks to regenerate this artifact."}


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
    write_runtime_artifacts(repo_root, workflow)
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


def _runtime_state(repo_root: Path) -> dict[str, Any]:
    workflow = _customer_workflow(repo_root)
    state_path = repo_root / "system_review_graph" / "product_runtime_state.json"
    if state_path.exists():
        payload = _load_json(state_path)
        if payload.get("status") and payload.get("users"):
            return payload
    return build_runtime_state(workflow)


def _parse_cookie(header: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for part in header.split(";"):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            cookies[key] = value
    return cookies


def _contains_script(value: str) -> bool:
    return bool(re.search(r"<\s*/?\s*script", value, flags=re.IGNORECASE))


def _truthy_form_value(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "accepted"}


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename.strip()).strip(".-")
    return cleaned[:120] or "uploaded-document.pdf"


def _parse_multipart(content_type: str, raw: bytes) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    match = re.search(r"boundary=(?P<boundary>[^;]+)", content_type)
    if not match:
        return {}, []
    boundary = match.group("boundary").strip().strip('"').encode("utf-8")
    fields: dict[str, Any] = {}
    files: list[dict[str, Any]] = []
    for part in raw.split(b"--" + boundary):
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        header_bytes, separator, data = part.partition(b"\r\n\r\n")
        if not separator:
            continue
        header_text = header_bytes.decode("utf-8", errors="replace")
        name_match = re.search(r'name="([^"]+)"', header_text)
        if not name_match:
            continue
        name = name_match.group(1)
        filename_match = re.search(r'filename="([^"]*)"', header_text)
        content_type_match = re.search(r"Content-Type:\s*([^\r\n]+)", header_text, flags=re.IGNORECASE)
        payload = data.rstrip(b"\r\n")
        if filename_match:
            filename = _safe_filename(filename_match.group(1))
            if filename:
                files.append(
                    {
                        "field_name": name,
                        "filename": filename,
                        "content_type": content_type_match.group(1).strip() if content_type_match else "application/octet-stream",
                        "content": payload,
                    }
                )
        else:
            fields[name] = payload.decode("utf-8", errors="replace")
    return fields, files


def _public_upload_manifest_path(repo_root: Path) -> Path:
    return repo_root / "system_review_graph" / "public_upload_manifest.json"


def _select_options(values: list[str], selected: str) -> str:
    return "".join(
        f"<option value='{escape(value)}'{' selected' if value == selected else ''}>{escape(value)}</option>"
        for value in values
    )


def _valid_sensitivity(value: Any) -> str:
    candidate = str(value or "internal")
    return candidate if candidate in SENSITIVITY_LEVELS else "internal"


def _valid_ai_mode(value: Any) -> str:
    candidate = str(value or "metadata_only")
    return candidate if candidate in AI_PROCESSING_MODES else "metadata_only"


def _evidence_ai_fields(fields: dict[str, Any]) -> dict[str, Any]:
    sensitivity = _valid_sensitivity(fields.get("sensitivity_level"))
    mode = _valid_ai_mode(fields.get("ai_processing_mode") or fields.get("ai_processing_permission"))
    redaction_required = str(fields.get("redaction_required") or "").lower() in {"1", "true", "yes", "on"}
    redaction_required = redaction_required or sensitivity in {"confidential", "restricted", "regulated"} or mode == "redacted"
    return {
        "sensitivity_level": sensitivity,
        "ai_processing_mode": mode,
        "ai_processing_permission": mode,
        "ai_processing_allowed": mode not in {"no_ai", "on_prem_manual"},
        "redaction_required": redaction_required,
    }


def _route_for_evidence(packet: dict[str, Any], evidence: dict[str, Any], task_type: str = "evidence_readiness_review") -> dict[str, Any]:
    return route_ai_task(
        organization_id=packet_org_id(packet),
        packet_id=str(packet.get("packet_id")),
        evidence_id=str(evidence.get("evidence_id")),
        task_type=task_type,
        document_sensitivity=str(evidence.get("sensitivity_level") or "internal"),
        requested_mode=str(evidence.get("ai_processing_mode") or "metadata_only"),
        evidence_permission=str(evidence.get("ai_processing_permission") or evidence.get("ai_processing_mode") or "metadata_only"),
    )


def _actor_from_headers(headers: Any) -> dict[str, Any]:
    token = headers.get("X-ISR-Session") or _parse_cookie(headers.get("Cookie", "")).get("isr_session")
    actor = actor_by_session(token)
    return actor or default_actor()


def _expert_actor_for_token(token: str, runtime: dict[str, Any]) -> dict[str, Any] | None:
    for grant in runtime.get("reviewer_access_grants", []):
        if grant.get("token") == token and grant.get("status") == "active":
            return {
                "id": f"expert:{token}",
                "email": "reviewer@example.local",
                "name": "Scoped Expert Reviewer",
                "role": "expert",
                "organization_id": "external-reviewer",
                "packet_ids": grant.get("packet_ids", []),
                "permissions": ["review:read:scoped", "review:finding:create:scoped"],
            }
    return None


def _visible_packets(workflow: dict[str, Any], actor: dict[str, Any]) -> list[dict[str, Any]]:
    return [packet for packet in workflow.get("packets", []) if can_access_packet(actor, packet)]


def _report_pdf_bytes(title: str, body: str) -> bytes:
    safe_title = title.replace("(", "[").replace(")", "]")
    safe_body = body.replace("(", "[").replace(")", "]").replace("\\", "/")
    stream = f"BT /F1 12 Tf 72 720 Td ({safe_title}) Tj 0 -24 Td ({safe_body[:700]}) Tj ET"
    stream_bytes = stream.encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream_bytes)} >> stream\n".encode("latin-1")
        + stream_bytes
        + b"\nendstream endobj\n",
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(data))
        data.extend(obj)
    xref = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    data.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("latin-1")
    )
    return bytes(data)


def _public_report_body(packet: dict[str, Any], report_type: str) -> str:
    summary = packet.get("public_summary") or {}
    lanes = "; ".join(
        f"{lane.get('name')}: {lane.get('status')} ({lane.get('next_valid_move')})"
        for lane in packet.get("readiness_lanes", [])
    )
    missing = ", ".join(packet.get("evidence_summary", {}).get("missing_items", [])[:8])
    questions = "; ".join(packet.get("buyer_broker_questions", [])[:6])
    report_labels = {
        "starter": "Starter Checklist",
        "draft": "Draft Trade Readiness Report",
        "buyer": "Buyer-Ready Packet",
        "broker": "Broker Review Packet",
        "missing": "Missing Evidence Checklist",
        "operator": "Operator Review Report",
        "expert": "Expert Review Packet",
    }
    label = report_labels.get(report_type, "Draft Trade Readiness Report")
    return (
        f"{label}. Product: {packet.get('product_name')}. "
        f"Trade direction: {packet.get('trade_direction')}. "
        f"Countries: {packet.get('origin_country')} to {packet.get('destination_country')}. "
        f"Status: {summary.get('status') or packet.get('readiness_status_label')}. "
        f"Main reason: {summary.get('main_reason')}. "
        f"Importer of record: {packet.get('importer_of_record')}; Incoterms: {packet.get('incoterms_if_known')}. "
        f"Evidence quality: {packet.get('evidence_summary', {}).get('summary')}. "
        f"Readiness lanes: {lanes}. Missing evidence: {missing}. "
        f"Buyer/broker questions: {questions}. "
        "Blocked claims remain blocked: no approval, tariff confirmation, CFIA clearance, legal advice, buyer validation, "
        "shipment decision, supplier recommendation, public launch, or commercial readiness claim. "
        "AI involvement: AI may structure evidence when allowed; it cannot open human gates. "
        "Boundary: draft review packet only; qualified people must review before external use."
    )


LUCIDE_PATHS = {
    "arrow-right": "<path d='M5 12h14'/><path d='m12 5 7 7-7 7'/>",
    "check": "<path d='M20 6 9 17l-5-5'/>",
    "database": "<ellipse cx='12' cy='5' rx='9' ry='3'/><path d='M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5'/><path d='M3 12c0 1.7 4 3 9 3s9-1.3 9-3'/>",
    "download": "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><path d='M7 10l5 5 5-5'/><path d='M12 15V3'/>",
    "file-text": "<path d='M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z'/><path d='M14 2v4a2 2 0 0 0 2 2h4'/><path d='M10 9H8'/><path d='M16 13H8'/><path d='M16 17H8'/>",
    "search": "<circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/>",
    "shield": "<path d='M20 13c0 5-3.5 7.5-7.7 8.9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.5a1.3 1.3 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z'/>",
    "sparkles": "<path d='M9.9 2.8 8.8 7l-4.1 1.1 4.1 1.1 1.1 4.2 1.1-4.2 4.2-1.1L11 7z'/><path d='M19 14l-.7 2.2L16 17l2.3.8L19 20l.8-2.2L22 17l-2.2-.8z'/>",
    "trash": "<path d='M3 6h18'/><path d='M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'/><path d='M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6'/><path d='M10 11v6'/><path d='M14 11v6'/>",
    "upload": "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><path d='M17 8l-5-5-5 5'/><path d='M12 3v12'/>",
}


def _icon(name: str) -> str:
    paths = LUCIDE_PATHS.get(name, "")
    return (
        "<svg class='icon' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
        f"{paths}</svg>"
    )


def _button_link(path: str, label: str, icon: str = "arrow-right", *, tone: str = "primary") -> str:
    return f"<a class='button-link button-{escape(tone)}' href='{escape(path)}'>{_icon(icon)}<span>{escape(label)}</span></a>"


def _status_badge(label: Any, tone: str = "neutral") -> str:
    return f"<span class='badge badge-{escape(tone)}'>{escape(str(label))}</span>"


def _metric_card(label: str, value: Any, detail: str = "") -> str:
    detail_html = f"<p>{escape(detail)}</p>" if detail else ""
    return f"<article class='metric'><div class='label'>{escape(label)}</div><div class='value'>{escape(str(value))}</div>{detail_html}</article>"


def _workflow_steps(active: str) -> str:
    steps = [
        ("start", "Start"),
        ("documents", "Documents"),
        ("confirm", "Confirm"),
        ("report", "Report"),
        ("review", "Review"),
    ]
    seen_active = False
    items = []
    for step_id, label in steps:
        state = "active" if step_id == active else "done" if not seen_active else "todo"
        if step_id == active:
            seen_active = True
        items.append(f"<li class='{state}'><span>{escape(label)}</span></li>")
    return f"<ol class='stepper'>{''.join(items)}</ol>"


def _render_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8f7;
      --panel: #ffffff;
      --ink: #17211f;
      --muted: #5f6b68;
      --line: #d8e0dd;
      --brand: #17665e;
      --brand-strong: #0f4944;
      --accent: #bf5b2c;
      --warn-bg: #fff6dd;
      --warn-line: #e3c46e;
      --ok-bg: #e7f7ef;
      --radius: 8px;
      --shadow: 0 18px 45px rgba(25, 45, 41, .08);
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: var(--bg); color: var(--ink); }}
    a {{ color: var(--brand); }}
    .app-shell {{ display: grid; grid-template-columns: 248px minmax(0, 1fr); min-height: 100vh; }}
    .side-nav {{ background: #102826; color: #f4fffd; padding: 22px 16px; display: flex; flex-direction: column; gap: 18px; position: sticky; top: 0; height: 100vh; }}
    .brand {{ display: flex; gap: 10px; align-items: center; font-weight: 800; letter-spacing: 0; }}
    .brand-mark {{ display: grid; place-items: center; width: 34px; height: 34px; border-radius: 8px; background: #d6fff6; color: #0f4944; }}
    .nav-group {{ display: grid; gap: 5px; }}
    .nav-label {{ color: #9cc9c2; font-size: 11px; font-weight: 800; text-transform: uppercase; margin: 8px 8px 2px; }}
    .side-nav a {{ display: flex; gap: 9px; align-items: center; color: #d9fffa; text-decoration: none; font-weight: 700; padding: 9px 10px; border-radius: 6px; }}
    .side-nav a:hover {{ background: rgba(255,255,255,.08); }}
    .topbar {{ display: none; background: #102826; color: white; padding: 12px 16px; gap: 10px; overflow-x: auto; }}
    .topbar a {{ color: #d9fffa; text-decoration: none; white-space: nowrap; font-weight: 700; }}
    main {{ width: min(1180px, 100%); padding: 26px; }}
    .page {{ display: grid; gap: 18px; }}
    .surface {{ background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); padding: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.12; letter-spacing: 0; }}
    h2 {{ margin: 24px 0 10px; font-size: 20px; letter-spacing: 0; }}
    p {{ line-height: 1.55; }}
    .lede {{ color: var(--muted); max-width: 72ch; }}
    .note {{ border: 1px solid var(--warn-line); background: var(--warn-bg); border-radius: var(--radius); padding: 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .grid-3 {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    label {{ display: block; font-weight: 800; margin: 10px 0 4px; }}
    input, textarea, select {{ width: 100%; border: 1px solid #c8d2cf; border-radius: 6px; padding: 10px; font: inherit; background: #fff; color: var(--ink); }}
    input:focus, textarea:focus, select:focus {{ outline: 3px solid rgba(23, 102, 94, .18); border-color: var(--brand); }}
    input[type="checkbox"] {{ width: auto; }}
    button, .button-link {{ display: inline-flex; align-items: center; gap: 8px; min-height: 40px; margin-top: 10px; border: 0; border-radius: 6px; background: var(--brand); color: white; padding: 10px 14px; font-weight: 800; cursor: pointer; text-decoration: none; }}
    .button-secondary {{ background: #eaf1ef; color: #173d39; }}
    .button-danger {{ background: #93312b; color: #fff; }}
    button:hover, .button-link:hover {{ filter: brightness(.96); }}
    .icon {{ width: 17px; height: 17px; flex: 0 0 auto; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; background: #fff; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; }}
    th {{ background: #edf3f1; color: #334440; font-size: 13px; }}
    .status, .badge {{ display: inline-flex; align-items: center; border: 1px solid var(--line); border-radius: 999px; padding: 5px 10px; background: #eef8f6; color: #17413d; font-size: 13px; font-weight: 800; }}
    .badge-warn {{ background: var(--warn-bg); color: #6b4b00; border-color: var(--warn-line); }}
    .badge-danger {{ background: #ffe8e2; color: #8a281e; border-color: #f1b8aa; }}
    .badge-ok {{ background: var(--ok-bg); color: #155538; border-color: #a9dbc0; }}
    .claim-list li {{ margin: 4px 0; }}
    .metric {{ border: 1px solid var(--line); border-radius: var(--radius); padding: 14px; background: #fff; min-height: 92px; }}
    .metric p {{ margin: 8px 0 0; color: var(--muted); }}
    .label {{ color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; }}
    .value {{ font-weight: 850; margin-top: 5px; overflow-wrap: anywhere; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; align-items: end; }}
    .actions form {{ margin: 0; }}
    .stepper {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; padding: 0; margin: 0; list-style: none; }}
    .stepper li {{ border: 1px solid var(--line); border-radius: 999px; padding: 8px 10px; text-align: center; font-size: 13px; font-weight: 800; background: #fff; }}
    .stepper .done {{ background: var(--ok-bg); border-color: #a9dbc0; }}
    .stepper .active {{ background: #102826; color: #fff; border-color: #102826; }}
    .split {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(280px, .8fr); gap: 16px; align-items: start; }}
    pre {{ white-space: pre-wrap; border: 1px solid var(--line); border-radius: var(--radius); padding: 14px; background: #fff; overflow: auto; }}
    .closed {{ color: #9f2f2f; font-weight: 800; }}
    @media (max-width: 900px) {{
      .app-shell {{ display: block; }}
      .side-nav {{ display: none; }}
      .topbar {{ display: flex; }}
      main {{ padding: 16px; }}
      .grid, .grid-3, .split {{ grid-template-columns: 1fr; }}
      .stepper {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<div class="topbar">
  <a href="/start">Start</a><a href="/trade-check">Documents</a><a href="/workspace">Workspace</a><a href="/operator/queue">Operator</a><a href="/admin/system-health">Health</a>
</div>
<div class="app-shell">
<nav class="side-nav" aria-label="Primary">
  <div class="brand"><span class="brand-mark">{_icon("shield")}</span><span>Trade Readiness</span></div>
  <div class="nav-group">
    <div class="nav-label">Customer Flow</div>
    <a href="/start">{_icon("sparkles")}Start</a>
    <a href="/tools">{_icon("search")}Tools</a>
    <a href="/trade-check">{_icon("upload")}Documents</a>
    <a href="/workspace">{_icon("database")}Workspace</a>
  </div>
  <div class="nav-group">
    <div class="nav-label">Review</div>
    <a href="/packets">{_icon("file-text")}Packets</a>
    <a href="/settings/ai-data-policy">{_icon("shield")}AI Policy</a>
    <a href="/operator/queue">{_icon("check")}Operator</a>
  </div>
  <div class="nav-group">
    <div class="nav-label">Admin</div>
    <a href="/admin/sources">{_icon("database")}Sources</a>
    <a href="/admin/system-health">{_icon("shield")}System Health</a>
    <a href="/support">{_icon("file-text")}Support</a>
  </div>
</nav>
<main>
<div class="page">
{body}
</div>
</main>
</div>
</body>
</html>
"""


def _render_packet_list(workflow: dict[str, Any]) -> str:
    rows = []
    for packet in workflow.get("packets", []):
        packet_id = escape(str(packet.get("packet_id")))
        rows.append(
            "<tr>"
            f"<td><a href='/packets/{packet_id}'>{escape(str(packet.get('packet_name')))}</a></td>"
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
<p><a href="/packets/new">Create a source packet</a> | <a href="/operator">Operator dashboard</a></p>
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
<form method="post" action="/packets">
  <input type="hidden" name="csrf_token" value="local-dev-csrf-token">
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
        f"<form method='post' action='/packets/{escape(packet_id)}/actions'>"
        f"<input type='hidden' name='action' value='{escape(action)}'>"
        f"<input type='hidden' name='csrf_token' value='{CSRF_TOKEN}'>"
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
        + f"<a class='button-link' href='/packets/{escape(packet_id)}/export'>Export Readiness Report</a>"
        + "</div>"
    )


def _list_items(rows: list[Any]) -> str:
    return "".join(f"<li>{escape(str(row))}</li>" for row in rows)


def _render_landing() -> str:
    body = f"""
<section class="surface split">
  <div>
    {_status_badge("Local private-beta product", "ok")}
    <h1>{escape(PUBLIC_PRODUCT_NAME)}</h1>
    <p class="lede">{escape(PUBLIC_PRODUCT_PROMISE)} Start with no documents or upload PDFs, then get a missing-evidence packet, safe summary, and next valid moves.</p>
    <div class="actions">
      {_button_link("/start", "Start without documents", "sparkles")}
      {_button_link("/trade-check", "Upload PDFs", "upload", tone="secondary")}
      {_button_link("/workspace", "Open workspace", "database", tone="secondary")}
    </div>
  </div>
  <aside class="note">{escape(PRODUCT_BOUNDARY)}</aside>
</section>
<section class="surface">
  {_workflow_steps("start")}
  <div class="grid grid-3">
    {_metric_card("Beginner Start", "No-documents mode", "Capture unknowns and get a starter checklist.")}
    {_metric_card("PDF Triage", f"PDF limit {MAX_PUBLIC_PDF_PAGES} pages", "Native text extraction or OCR-needed routing.")}
    {_metric_card("Policy Monitor", "Intelligence Hub contract", "Source snapshots, hashes, stale-packet blockers.")}
  </div>
</section>
<section class="surface">
  <h2>Boundaries</h2>
  <ul>
    <li>Does not claim import/export approval, tariff confirmation, CFIA clearance, legal advice, customs advice, supplier recommendation, buyer validation, or launch readiness.</li>
    <li>Does not replace a licensed customs broker, qualified compliance expert, lawyer, accountant, or buyer validation process.</li>
  </ul>
</section>
"""
    return _render_page(PUBLIC_PRODUCT_NAME, body)


def _render_start_page() -> str:
    body = f"""
<section class="surface">
  {_workflow_steps("start")}
  <h1>Start Trade Readiness</h1>
  <p class="lede">Use this when you know the product idea but do not yet know which documents, reviewers, buyers, or official sources are required.</p>
  <p class="note">Starter mode creates a missing-evidence packet. It does not provide advice, approval, or a shipment decision.</p>
  <form method="post" action="/api/public/starter">
    <div class="grid">
      <div><label>What are you trying to move?</label><input name="product_name" value="Organic turmeric powder"></div>
      <div><label>Product category</label><input name="product_category" value="food_import"></div>
      <div><label>Origin country</label><input name="origin_country" value="India"></div>
      <div><label>Destination country</label><input name="destination_country" value="Canada"></div>
      <div><label>Trade direction</label><select name="trade_direction">{_select_options(["export", "import", "both", "unknown"], "export")}</select></div>
      <div><label>Current stage</label><select name="current_stage">{_select_options(["idea", "supplier identified", "buyer conversation", "documents collecting", "broker review needed"], "idea")}</select></div>
    </div>
    <label>What do you already know?</label><textarea name="notes" rows="4">I want to understand what is missing before talking to buyers, brokers, or compliance experts.</textarea>
    <label>Known unknowns</label><input name="unknown_fields" value="HS code, importer of record, Incoterms, certificates, proof of origin, Canada controls">
    <label>Research depth</label><select name="research_depth_requested">{_select_options(["starter checklist", "detailed research plan", "expert-review packet"], "starter checklist")}</select>
    <label><input type="checkbox" name="accept_notice" value="accepted" checked> I understand this is a draft starter checklist and external claims remain blocked.</label>
    <button type="submit">{_icon("arrow-right")}Create Starter Packet</button>
  </form>
</section>
"""
    return _render_page("Start Trade Readiness", body)


def _render_tool_selection() -> str:
    tools = [
        ("Opportunity Scanner", "/opportunities", "Find possible opportunity signals and route them into research-gated packets."),
        ("Import Readiness Checker", "/tools/import-readiness", "Check Canada-side importer/source readiness gaps."),
        ("Export Readiness Checker", "/tools/export-readiness", "Build an Export-to-Canada packet for a foreign exporter."),
        ("Buyer/Broker Packet Builder", "/tools/buyer-broker-packet", "Prepare buyer and broker questions with blocked claims."),
        ("Trade Document Analyzer", "/trade-check", "Upload PDFs and draft extracted evidence metadata."),
        ("Document Quick Check", "/tools/document-check", "Use the same upload flow with PDF triage and user confirmation."),
        ("Missing Evidence Checker", "/trade-check", "See missing documents, reviews, and next valid moves."),
        ("Readiness PDF Generator", "/trade-check", "Download draft readiness, buyer, and broker PDFs."),
        ("Transport/Freight Forwarder Packet", "/reports/sample", "Review the freight-forwarder packet type and required questions."),
        ("Pricing And Credits", "/pricing", "Inspect local metering rules before heavy jobs run."),
        ("Expert Review Packet Generator", "/trade-check", "Package evidence for scoped qualified review."),
    ]
    cards = "".join(
        "<div class='metric'>"
        f"<div class='label'>{escape(title)}</div>"
        f"<div class='value'>{escape(summary)}</div>"
        f"<p><a class='button-link' href='{escape(path)}'>Open</a></p>"
        "</div>"
        for title, path, summary in tools
    )
    body = f"""
<h1>Choose Tool</h1>
<p class="note">{escape(PUBLIC_PRODUCT_PROMISE)} Draft checks are bounded by evidence and human review gates.</p>
<section class="grid">{cards}</section>
"""
    return _render_page("Tools", body)


def _render_public_trade_check(default_direction: str = "export") -> str:
    direction_options = _select_options(["export", "import", "both", "unknown"], default_direction)
    incoterms_options = _select_options(["unknown", "EXW", "FOB", "CIF", "DAP", "DDP"], "unknown")
    importer_options = _select_options(["unknown", "buyer", "importer", "exporter", "broker"], "unknown")
    body = f"""
<h1>Quick Trade Readiness Check</h1>
<p class="note">Upload at least one PDF. The draft report shows missing evidence and blocked claims; it is not approval, advice, or a shipment decision.</p>
<form method="post" action="/api/public/quick-check" enctype="multipart/form-data">
  <div class="grid">
    <div><label>Trade direction</label><select name="trade_direction">{direction_options}</select></div>
    <div><label>Product or category</label><input name="product_name" value="Organic turmeric powder"></div>
    <div><label>Product category</label><input name="product_category" value="food_import"></div>
    <div><label>HS code if known</label><input name="hs_code_if_known" value=""></div>
    <div><label>Origin country</label><input name="origin_country" value="India"></div>
    <div><label>Destination country</label><input name="destination_country" value="Canada"></div>
    <div><label>Exporter business name</label><input name="exporter_name" value="Example Exporter Pvt Ltd"></div>
    <div><label>Canadian buyer/importer</label><input name="buyer_name" value=""></div>
    <div><label>Importer of record</label><select name="importer_of_record">{importer_options}</select></div>
    <div><label>Incoterms if known</label><select name="incoterms_if_known">{incoterms_options}</select></div>
  </div>
  <label>Documents (PDF)</label><input type="file" name="documents" accept="application/pdf,.pdf" multiple>
  <label>Product documents already available</label><input name="product_documents" value="product spec PDF">
  <label>Commercial documents already available</label><input name="commercial_documents" value="">
  <label>Certificates / proof of origin</label><input name="certificates" value="">
  <label><input type="checkbox" name="accept_notice" value="accepted" checked> I understand this is a draft AI-assisted evidence check, files are local test artifacts, and missing evidence/approval claims stay blocked.</label>
  <button type="submit">Run Quick Check</button>
</form>
"""
    return _render_page("Quick Trade Check", body)


def _render_canadian_references(workflow: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('name')))}</td>"
        f"<td>{escape(str(row.get('jurisdiction')))}</td>"
        f"<td>{escape(str(row.get('evidence_role')))}</td>"
        f"<td>{escape(str(row.get('claim_boundary')))}</td>"
        "</tr>"
        for row in workflow.get("official_sources", [])
    )
    body = f"""
<h1>Canadian References</h1>
<p class="note">These are reference sources for review. They do not prove tariff, CFIA, permit, importer, broker, or shipment readiness by themselves.</p>
<table>
  <thead><tr><th>Source</th><th>Jurisdiction</th><th>Used For</th><th>Boundary</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
"""
    return _render_page("Canadian References", body)


def _render_opportunities(repo_root: Path, workflow: dict[str, Any]) -> str:
    opportunity = _load_graph_json(repo_root, "opportunity_scanner_report.json")
    coverage = _load_graph_json(repo_root, "country_coverage_report.json")
    signal_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('category')))}</td>"
        f"<td>{escape(str(row.get('country')))}</td>"
        f"<td>{escape(str(row.get('opportunity_signal')))}</td>"
        f"<td>{escape(str(row.get('demand_signal')))}</td>"
        f"<td>{escape(str(row.get('requirements_complexity')))}</td>"
        f"<td>{escape(str(row.get('next_step')))}</td>"
        "</tr>"
        for row in opportunity.get("signals", [])
    )
    coverage_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('country')))}</td>"
        f"<td>{escape(str(row.get('coverage_tier')))}</td>"
        f"<td>{escape(str(row.get('coverage_label')))}</td>"
        f"<td>{escape(str(row.get('source_count')))}</td>"
        f"<td>{escape(str(row.get('can_make_country_specific_claims')))}</td>"
        "</tr>"
        for row in coverage.get("countries", [])
    )
    body = f"""
<section class="surface">
  <h1>Opportunity Signals</h1>
  <p class="lede">Find possible trade-readiness opportunities, then turn them into bounded packets before making decisions.</p>
  <p class="note">{escape(str(opportunity.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
  <div class="grid grid-3">
    {_metric_card("Signals", opportunity.get("signal_count", len(opportunity.get("signals", []))), "Signal rows, not recommendations.")}
    {_metric_card("Packets", workflow.get("packet_count", len(workflow.get("packets", []))), "Local packet context available.")}
    {_metric_card("Coverage", coverage.get("status"), "Country-specific claims stay blocked.")}
  </div>
  <div class="actions">
    {_button_link("/start", "Start packet", "sparkles")}
    {_button_link("/trade-check", "Upload documents", "upload", tone="secondary")}
  </div>
</section>
<section class="surface">
  <h2>Signal Rows</h2>
  <table>
    <thead><tr><th>Category</th><th>Market</th><th>Signal</th><th>Demand Proof</th><th>Complexity</th><th>Next</th></tr></thead>
    <tbody>{signal_rows or '<tr><td colspan="6">Run scripts/run_completion_platform.py to generate opportunity rows.</td></tr>'}</tbody>
  </table>
</section>
<section class="surface">
  <h2>Country Coverage</h2>
  <table>
    <thead><tr><th>Country</th><th>Tier</th><th>Support</th><th>Sources</th><th>Can Make Claims</th></tr></thead>
    <tbody>{coverage_rows or '<tr><td colspan="5">Coverage artifact not generated yet.</td></tr>'}</tbody>
  </table>
</section>
"""
    return _render_page("Opportunity Signals", body)


def _render_country_coverage(repo_root: Path) -> str:
    coverage = _load_graph_json(repo_root, "country_coverage_report.json")
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('country')))}</td>"
        f"<td>{escape(str(row.get('coverage_tier')))}</td>"
        f"<td>{escape(str(row.get('coverage_label')))}</td>"
        f"<td>{escape(str(row.get('source_count')))}</td>"
        f"<td>{escape(str(row.get('next_valid_move')))}</td>"
        "</tr>"
        for row in coverage.get("countries", [])
    )
    packet_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('packet_id')))}</td>"
        f"<td>{escape(str(row.get('origin_country')))} -> {escape(str(row.get('destination_country')))}</td>"
        f"<td>{escape(str(row.get('product_category')))}</td>"
        f"<td>{escape(str(row.get('effective_coverage_tier')))}</td>"
        f"<td>{escape(str(row.get('coverage_status')))}</td>"
        "</tr>"
        for row in coverage.get("packet_coverage", [])
    )
    body = f"""
<section class="surface">
  <h1>Country Coverage</h1>
  <p class="lede">Coverage tiers show which countries are selectable, monitored, or template-ready inside the product.</p>
  <p class="note">{escape(str(coverage.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
</section>
<section class="surface">
  <h2>Countries</h2>
  <table><thead><tr><th>Country</th><th>Tier</th><th>Support</th><th>Sources</th><th>Next</th></tr></thead><tbody>{rows}</tbody></table>
</section>
<section class="surface">
  <h2>Packet Coverage</h2>
  <table><thead><tr><th>Packet</th><th>Lane</th><th>Category</th><th>Effective Tier</th><th>Status</th></tr></thead><tbody>{packet_rows}</tbody></table>
</section>
"""
    return _render_page("Country Coverage", body)


def _render_transport_readiness(repo_root: Path) -> str:
    transport = _load_graph_json(repo_root, "transport_readiness_report.json")
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('packet_id')))}</td>"
        f"<td>{escape(str(row.get('status')))}</td>"
        f"<td>{escape(', '.join(row.get('missing_transport_inputs', [])))}</td>"
        f"<td>{escape(str(row.get('next_valid_move')))}</td>"
        "</tr>"
        for row in transport.get("rows", [])
    )
    questions = _list_items([
        question
        for row in transport.get("rows", [])
        for question in row.get("freight_forwarder_questions", [])
    ])
    body = f"""
<section class="surface">
  <h1>Transport Readiness</h1>
  <p class="lede">Prepare shipment and freight-forwarder questions before making cost, route, or shipment claims.</p>
  <p class="note">{escape(str(transport.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
</section>
<section class="surface">
  <h2>Packet Transport Rows</h2>
  <table><thead><tr><th>Packet</th><th>Status</th><th>Missing Inputs</th><th>Next</th></tr></thead><tbody>{rows}</tbody></table>
</section>
<section class="surface">
  <h2>Freight-Forwarder Questions</h2>
  <ul>{questions}</ul>
</section>
"""
    return _render_page("Transport Readiness", body)


def _render_pricing(repo_root: Path) -> str:
    billing = _load_graph_json(repo_root, "billing_credit_controls.json")
    plan_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('id')))}</td>"
        f"<td>{escape(str(row.get('packet_limit')))}</td>"
        f"<td>{escape(str(row.get('monthly_credits')))}</td>"
        f"<td>{escape(str(row.get('heavy_jobs')))}</td>"
        "</tr>"
        for row in billing.get("plans", [])
    )
    action_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('action')))}</td>"
        f"<td>{escape(str(row.get('estimated_credits')))}</td>"
        f"<td>{escape(str(row.get('heavy_job')))}</td>"
        f"<td>{escape(str(row.get('free_plan_behavior')))}</td>"
        f"<td>{escape(str(row.get('external_charge_created')))}</td>"
        "</tr>"
        for row in billing.get("billable_actions", [])
    )
    body = f"""
<section class="surface">
  <h1>Billing And Credits</h1>
  <p class="lede">Plans, credits, and heavy-job gates are defined locally so expensive AI/OCR/API work can be controlled before execution.</p>
  <p class="note">Live checkout enabled: {escape(str(billing.get('live_checkout_enabled', False)))}. {escape(str(billing.get('proof_boundary') or 'No live payment session is created.'))}</p>
</section>
<section class="surface">
  <h2>Plans</h2>
  <table>
    <thead><tr><th>Plan</th><th>Packets</th><th>Credits</th><th>Heavy Jobs</th></tr></thead>
    <tbody>{plan_rows or '<tr><td colspan="4">Billing artifact not generated yet.</td></tr>'}</tbody>
  </table>
</section>
<section class="surface">
  <h2>Billable Actions</h2>
  <table>
    <thead><tr><th>Action</th><th>Credits</th><th>Heavy</th><th>Free Plan</th><th>External Charge</th></tr></thead>
    <tbody>{action_rows or '<tr><td colspan="5">No metered actions generated.</td></tr>'}</tbody>
  </table>
</section>
"""
    return _render_page("Billing And Credits", body)


def _render_billing_usage(repo_root: Path) -> str:
    usage = _load_graph_json(repo_root, "billing_usage_ledger.json")
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('packet_id')))}</td>"
        f"<td>{escape(str(row.get('action')))}</td>"
        f"<td>{escape(str(row.get('estimated_credits')))}</td>"
        f"<td>{escape(str(row.get('authorization_status')))}</td>"
        f"<td>{escape(str(row.get('external_charge_created')))}</td>"
        "</tr>"
        for row in usage.get("usage_rows", [])
    )
    body = f"""
<section class="surface">
  <h1>Billing Usage</h1>
  <p class="lede">Local usage rows estimate credit exposure and block heavy work before any paid or external action.</p>
  <p class="note">{escape(str(usage.get('proof_boundary') or 'No live charges are created.'))}</p>
</section>
<section class="surface">
  <table><thead><tr><th>Packet</th><th>Action</th><th>Credits</th><th>Authorization</th><th>External Charge</th></tr></thead><tbody>{rows}</tbody></table>
</section>
"""
    return _render_page("Billing Usage", body)


def _render_agent_api(repo_root: Path) -> str:
    manifest = _load_graph_json(repo_root, "agent_api_manifest.json")
    gateway = _load_graph_json(repo_root, "agent_api_gateway_contract.json")
    tools = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('tool')))}</td>"
        f"<td>{escape(str(row.get('method')))}</td>"
        f"<td>{escape(str(row.get('route')))}</td>"
        f"<td>{escape(str(row.get('scope_required')))}</td>"
        f"<td>{escape(str(row.get('billing_gate')))}</td>"
        "</tr>"
        for row in gateway.get("tools", [])
    )
    forbidden = _list_items(manifest.get("forbidden_tools", []))
    body = f"""
<section class="surface">
  <h1>Agent API</h1>
  <p class="lede">Agents can dry-run packet creation, reports, summaries, and billing quotes through scoped local tool contracts.</p>
  <p class="note">{escape(str(gateway.get('proof_boundary') or manifest.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
</section>
<section class="surface">
  <h2>Dry-Run Tools</h2>
  <table><thead><tr><th>Tool</th><th>Method</th><th>Route</th><th>Scope</th><th>Billing</th></tr></thead><tbody>{tools}</tbody></table>
</section>
<section class="surface">
  <h2>Forbidden Tools</h2>
  <ul>{forbidden}</ul>
</section>
"""
    return _render_page("Agent API", body)


def _render_stage_overview(repo_root: Path) -> str:
    stages = _load_graph_json(repo_root, "all_stage_readiness_report.json")
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('stage_id')))}</td>"
        f"<td>{escape(str(row.get('name')))}</td>"
        f"<td>{escape(str(row.get('status')))}</td>"
        f"<td>{escape(', '.join(row.get('routes', [])))}</td>"
        f"<td>{escape(str(row.get('next_valid_move')))}</td>"
        "</tr>"
        for row in stages.get("stages", [])
    )
    external = _list_items(stages.get("still_external", []))
    body = f"""
<section class="surface">
  <h1>All Product Stages</h1>
  <p class="lede">Every locally implementable stage is represented by usable routes, APIs, generated artifacts, and proof checks.</p>
  <p class="note">{escape(str(stages.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
  <div class="grid grid-3">
    {_metric_card("Stage Status", stages.get("status"), "Local stages implemented.")}
    {_metric_card("Stages", stages.get("stage_count"), "Usable local surfaces.")}
    {_metric_card("External Gates", stages.get("external_gate_count"), "Still need real approval/evidence.")}
  </div>
</section>
<section class="surface">
  <h2>Stage Runtime</h2>
  <table><thead><tr><th>ID</th><th>Stage</th><th>Status</th><th>Routes</th><th>Next</th></tr></thead><tbody>{rows}</tbody></table>
</section>
<section class="surface"><h2>Still External</h2><ul>{external}</ul></section>
"""
    return _render_page("All Product Stages", body)


def _render_research_plan(repo_root: Path) -> str:
    research = _load_graph_json(repo_root, "research_execution_plan.json")
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('packet_id')))}</td>"
        f"<td>{escape(str(row.get('research_mode')))}</td>"
        f"<td>{escape(', '.join(row.get('official_source_search', [])))}</td>"
        f"<td>{escape(', '.join(row.get('dataset_or_api_needs', [])))}</td>"
        f"<td>{escape(str(row.get('next_valid_move')))}</td>"
        "</tr>"
        for row in research.get("rows", [])
    )
    body = f"""
<section class="surface">
  <h1>Research Execution</h1>
  <p class="lede">Routes each packet to model-prior, web, official-source, dataset, and expert/user validation lanes.</p>
  <p class="note">{escape(str(research.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
</section>
<section class="surface">
  <table><thead><tr><th>Packet</th><th>Mode</th><th>Official Sources</th><th>Dataset/API Needs</th><th>Next</th></tr></thead><tbody>{rows}</tbody></table>
</section>
"""
    return _render_page("Research Execution", body)


def _render_expert_network(repo_root: Path) -> str:
    experts = _load_graph_json(repo_root, "expert_network_report.json")
    role_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('label')))}</td>"
        f"<td>{escape(str(row.get('scope')))}</td>"
        "</tr>"
        for row in experts.get("expert_roles", [])
    )
    queue_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('packet_id')))}</td>"
        f"<td>{escape(str(row.get('role_id')))}</td>"
        f"<td>{escape(str(row.get('status')))}</td>"
        f"<td>{escape(str(row.get('simulated_agent_can_approve')))}</td>"
        "</tr>"
        for row in experts.get("review_queue", [])
    )
    body = f"""
<section class="surface">
  <h1>Expert Network</h1>
  <p class="lede">Prepare scoped review packets for qualified people and keep AI simulation separate from human approval.</p>
  <p class="note">{escape(str(experts.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
</section>
<section class="surface"><h2>Roles</h2><table><thead><tr><th>Role</th><th>Scope</th></tr></thead><tbody>{role_rows}</tbody></table></section>
<section class="surface"><h2>Review Queue</h2><table><thead><tr><th>Packet</th><th>Role</th><th>Status</th><th>AI Can Approve</th></tr></thead><tbody>{queue_rows}</tbody></table></section>
"""
    return _render_page("Expert Network", body)


def _render_team_workspace(repo_root: Path) -> str:
    team = _load_graph_json(repo_root, "team_workspace_report.json")
    rows = []
    for workspace in team.get("workspaces", []):
        for approval in workspace.get("approval_board", []):
            rows.append(
                "<tr>"
                f"<td>{escape(str(workspace.get('packet_id')))}</td>"
                f"<td>{escape(str(approval.get('gate')))}</td>"
                f"<td>{escape(str(approval.get('owner')))}</td>"
                f"<td>{escape(str(approval.get('status')))}</td>"
                f"<td>{escape(str(workspace.get('next_valid_move')))}</td>"
                "</tr>"
            )
    body = f"""
<section class="surface">
  <h1>Team Workspace</h1>
  <p class="lede">Business/team roles, approval boards, and packet ownership are local coordination surfaces.</p>
  <p class="note">{escape(str(team.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
</section>
<section class="surface">
  <table><thead><tr><th>Packet</th><th>Gate</th><th>Owner</th><th>Status</th><th>Next</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
</section>
"""
    return _render_page("Team Workspace", body)


def _render_launch_operations(repo_root: Path) -> str:
    launch = _load_graph_json(repo_root, "launch_operations_report.json")
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('control')))}</td>"
        f"<td>{escape(str(row.get('status')))}</td>"
        f"<td>{escape(str(row.get('external_gate')))}</td>"
        "</tr>"
        for row in launch.get("controls", [])
    )
    entry = launch.get("private_beta_entry", {})
    body = f"""
<section class="surface">
  <h1>Launch Operations</h1>
  <p class="lede">Private-beta controls, support, rollback, monitoring, and outcome logging are specified locally.</p>
  <p class="note">{escape(str(launch.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
  <div class="grid grid-3">
    {_metric_card("Local Product Ready", entry.get("local_product_ready"), "For private review only.")}
    {_metric_card("Human Approval Required", entry.get("human_approval_required"), "No hidden launch gate.")}
    {_metric_card("Public Launch Allowed", entry.get("public_launch_allowed"), "Must stay false.")}
  </div>
</section>
<section class="surface">
  <table><thead><tr><th>Control</th><th>Status</th><th>External Gate</th></tr></thead><tbody>{rows}</tbody></table>
</section>
"""
    return _render_page("Launch Operations", body)


def _render_traffic_page(repo_root: Path, slug: str) -> str | None:
    traffic = _load_graph_json(repo_root, "traffic_pages_manifest.json")
    page = next((row for row in traffic.get("pages", []) if row.get("slug") == slug), None)
    if page is None:
        return None
    sections = _list_items(page.get("sections", []))
    body = f"""
<section class="surface">
  <h1>{escape(str(page.get('title')))}</h1>
  <p class="lede">Use this checklist page to orient the user, then route them into the actual readiness tool.</p>
  <p class="note">{escape(str(page.get('claim_boundary')))}</p>
  <div class="actions">
    {_button_link("/start", "Start without documents", "sparkles")}
    {_button_link("/trade-check", "Upload PDFs", "upload", tone="secondary")}
  </div>
</section>
<section class="surface">
  <h2>Page Sections</h2>
  <ul>{sections}</ul>
</section>
"""
    return _render_page(str(page.get("title")), body)


def _render_sample_reports(repo_root: Path) -> str:
    reports = _load_graph_json(repo_root, "public_report_types.json")
    traffic = _load_graph_json(repo_root, "traffic_pages_manifest.json")
    report_cards = "".join(
        "<div class='metric'>"
        f"<div class='label'>{escape(str(report))}</div>"
        "<div class='value'>Draft export</div>"
        "<p>Generated only from packet evidence, blockers, and proof boundaries.</p>"
        "</div>"
        for report in reports.get("reports", [])
    )
    page_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('title')))}</td>"
        f"<td>{escape(str(row.get('route')))}</td>"
        f"<td>{escape(str(row.get('claim_boundary')))}</td>"
        "</tr>"
        for row in traffic.get("pages", [])
    )
    body = f"""
<section class="surface">
  <h1>Sample Reports</h1>
  <p class="lede">Report templates are PDF-first and evidence-first. They show gaps, next moves, and blocked claims.</p>
  <p class="note">Samples are product templates, not certificates, approvals, buyer validation, or legal/customs advice.</p>
  <div class="actions">
    {_button_link("/trade-check", "Generate from packet", "file-text")}
    {_button_link("/opportunities", "View opportunities", "search", tone="secondary")}
  </div>
</section>
<section class="grid">{report_cards}</section>
<section class="surface">
  <h2>Traffic Pages</h2>
  <table>
    <thead><tr><th>Page</th><th>Route</th><th>Boundary</th></tr></thead>
    <tbody>{page_rows or '<tr><td colspan="3">Traffic pages manifest not generated yet.</td></tr>'}</tbody>
  </table>
</section>
"""
    return _render_page("Sample Reports", body)


def _render_security_public(runtime: dict[str, Any]) -> str:
    controls = runtime.get("security_controls", {})
    upload = controls.get("upload_validation", {})
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(key))}</td>"
        f"<td>{escape(json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value))}</td>"
        "</tr>"
        for key, value in controls.items()
    )
    body = f"""
<section class="surface">
  <h1>Security And Privacy</h1>
  <p class="lede">The local product uses organization scoping, generated upload names, quarantine storage, RBAC, audit events, and route-scoped file access.</p>
  <p class="note">Production TLS, secret manager, malware scanning, privacy/legal review, and hosted observability remain external gates.</p>
  <div class="grid grid-3">
    {_metric_card("Upload Limit", upload.get("max_bytes"), "Local public PDF limit.")}
    {_metric_card("Direct File Serving", upload.get("direct_file_serving"), "Uploads stay behind route checks.")}
    {_metric_card("AI Policy", controls.get("ai_data_policy"), "Organization-level controls.")}
  </div>
</section>
<section class="surface">
  <h2>Controls</h2>
  <table>
    <thead><tr><th>Control</th><th>Current Contract</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>
"""
    return _render_page("Security And Privacy", body)


def _render_source_monitoring(repo_root: Path, workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    monitor = _load_graph_json(repo_root, "intelligence_hub_policy_monitor.json")
    impact = _load_graph_json(repo_root, "policy_change_impact_report.json")
    packet_id = str(packet.get("packet_id"))
    impact_rows = [
        row for row in impact.get("packet_source_impacts", []) if str(row.get("packet_id")) == packet_id
    ]
    if not impact_rows:
        impact_rows = impact.get("packet_source_impacts", [])
    source_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('name')))}</td>"
        f"<td>{escape(str(row.get('source_id')))}</td>"
        f"<td>{escape(str(row.get('refresh_mode')))}</td>"
        f"<td>{escape(str(row.get('claim_boundary')))}</td>"
        "</tr>"
        for row in monitor.get("monitored_sources", [])[:12]
    )
    packet_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('packet_id')))}</td>"
        f"<td>{escape(str(row.get('impact_status')))}</td>"
        f"<td>{escape(', '.join(row.get('matched_source_ids', [])[:6]))}</td>"
        f"<td>{escape(str(row.get('next_valid_move')))}</td>"
        "</tr>"
        for row in impact_rows
    )
    body = f"""
<section class="surface">
  <h1>Source Monitoring</h1>
  <p class="lede">{escape(str(packet.get('packet_name')))} uses Intelligence Hub source snapshots to detect stale packet risk.</p>
  <p class="note">{escape(str(monitor.get('proof_boundary') or workflow.get('proof_boundary') or PRODUCT_BOUNDARY))}</p>
  <div class="grid grid-3">
    {_metric_card("Monitor", monitor.get("status"), "Database-style local contract.")}
    {_metric_card("Sources", monitor.get("monitored_source_count", 0), "Reference sources tracked.")}
    {_metric_card("Stale Blockers", monitor.get("stale_source_blocker_count", 0), "Review gates stay closed.")}
  </div>
  <form method="post" action="/api/public/packets/{escape(packet_id)}/refresh-official-sources"><button type="submit">Refresh Official Sources</button></form>
</section>
<section class="surface">
  <h2>Packet Impact</h2>
  <table>
    <thead><tr><th>Packet</th><th>Status</th><th>Matched Sources</th><th>Next</th></tr></thead>
    <tbody>{packet_rows or '<tr><td colspan="4">No packet impact rows generated yet.</td></tr>'}</tbody>
  </table>
</section>
<section class="surface">
  <h2>Monitored Sources</h2>
  <table>
    <thead><tr><th>Name</th><th>ID</th><th>Refresh</th><th>Boundary</th></tr></thead>
    <tbody>{source_rows or '<tr><td colspan="4">No monitored sources generated yet.</td></tr>'}</tbody>
  </table>
</section>
"""
    return _render_page("Source Monitoring", body)


def _render_safe_summary_page(packet: dict[str, Any]) -> str:
    summary = _chatgpt_safe_summary(packet)
    body = f"""
<section class="surface">
  <h1>ChatGPT-Safe Summary</h1>
  <p class="lede">Use this when drafting questions in an external AI chat without sharing uploaded file contents or private commercial details.</p>
  <p class="note">{escape(str(summary.get('proof_boundary')))}</p>
  <textarea rows="8" readonly>{escape(str(summary.get('copy_paste_summary')))}</textarea>
</section>
<section class="surface">
  <h2>Safe Questions</h2>
  <ul>{_list_items(summary.get('safe_questions', []))}</ul>
  <h2>Do Not Include</h2>
  <ul>{_list_items(summary.get('do_not_include', []))}</ul>
  <h2>Blocked Claims</h2>
  <ul>{_list_items(summary.get('blocked_claims', []))}</ul>
</section>
"""
    return _render_page("ChatGPT-Safe Summary", body)


def _render_public_result(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    packet_id = escape(str(packet.get("packet_id")))
    summary = packet.get("public_summary") or {}
    lanes = "".join(
        "<tr>"
        f"<td>{escape(str(lane.get('name')))}</td>"
        f"<td>{escape(str(lane.get('country_scope')))}</td>"
        f"<td>{escape(str(lane.get('status')))}</td>"
        f"<td>{escape(str(lane.get('next_valid_move')))}</td>"
        "</tr>"
        for lane in packet.get("readiness_lanes", [])
    )
    missing = _list_items(packet.get("evidence_summary", {}).get("missing_items", []))
    questions = _list_items(packet.get("buyer_broker_questions", []))
    actions = f"""
<div class="actions">
  <a class="button-link" href="/trade-check">Upload Documents</a>
  <a class="button-link" href="/public/packets/{packet_id}/confirm">Confirm Extracted Fields</a>
  <a class="button-link" href="/tools/canadian-references">Check Canadian References</a>
  <a class="button-link" href="/api/public/packets/{packet_id}/reports/starter.pdf">Starter Checklist</a>
  <form method="post" action="/api/public/packets/{packet_id}/refresh-official-sources"><button type="submit">Refresh Official Sources</button></form>
  <a class="button-link" href="/api/public/packets/{packet_id}/chatgpt-safe-summary">ChatGPT-Safe Summary</a>
  <a class="button-link" href="/api/public/packets/{packet_id}/reports/buyer.pdf">Generate Buyer Packet</a>
  <a class="button-link" href="/api/public/packets/{packet_id}/reports/broker.pdf">Generate Broker Review Packet</a>
  <a class="button-link" href="/api/public/packets/{packet_id}/reports/missing.pdf">Missing Evidence PDF</a>
  <a class="button-link" href="/api/public/packets/{packet_id}/reports/draft.pdf">Export Readiness Report</a>
  <form method="post" action="/api/public/packets/{packet_id}/delete-files"><button type="submit">Delete Uploaded Files</button></form>
</div>
"""
    body = f"""
<h1>{escape(str(summary.get('title') or 'Trade Readiness Packet'))}</h1>
<p><span class="status">{escape(str(summary.get('status') or packet.get('readiness_status_label')))}</span></p>
<p class="note">{escape(str(packet.get('safe_summary')))}</p>
{_workflow_steps("report")}
{actions}
<section class="grid">
  <div class="metric"><div class="label">Product</div><div class="value">{escape(str(packet.get('product_name')))}</div></div>
  <div class="metric"><div class="label">Trade direction</div><div class="value">{escape(str(packet.get('trade_direction')))}</div></div>
  <div class="metric"><div class="label">Countries</div><div class="value">{escape(str(packet.get('origin_country')))} -> {escape(str(packet.get('destination_country')))}</div></div>
  <div class="metric"><div class="label">Main reason</div><div class="value">{escape(str(summary.get('main_reason')))}</div></div>
  <div class="metric"><div class="label">Evidence</div><div class="value">{escape(str(packet.get('evidence_summary', {}).get('summary')))}</div></div>
  <div class="metric"><div class="label">Next valid move</div><div class="value">{escape(str(summary.get('next_valid_move')))}</div></div>
  <div class="metric"><div class="label">Confirmation</div><div class="value">{escape(str(packet.get('confirmation_status') or 'not_confirmed'))}</div></div>
  <div class="metric"><div class="label">Beginner mode</div><div class="value">{escape(str(packet.get('beginner_mode') or False))}</div></div>
</section>
<h2>Readiness Lanes</h2>
<table>
  <thead><tr><th>Lane</th><th>Scope</th><th>Status</th><th>Next</th></tr></thead>
  <tbody>{lanes}</tbody>
</table>
<h2>Missing Evidence</h2>
<ul>{missing}</ul>
<h2>Buyer / Broker Questions</h2>
<ul>{questions}</ul>
<h2>Blocked Claims</h2>
<ul>{_list_items(packet.get('blocked_claims_display', []))}</ul>
<p class="note">Create a free account to save history, add reviewers, and keep an operator workspace. Public quick checks are draft-only and should delete or expire uploaded files.</p>
<p><a class="button-link" href="/signup">Create Account</a> <a class="button-link" href="/support">Request Review</a></p>
"""
    return _render_page("Trade Readiness Result", body)


def _chatgpt_safe_summary(packet: dict[str, Any]) -> dict[str, Any]:
    evidence = packet.get("evidence_summary", {})
    return {
        "status": "chatgpt_safe_summary_ready",
        "packet_id": packet.get("packet_id"),
        "copy_paste_summary": (
            f"I am preparing a draft trade-readiness packet for {packet.get('product_name')} from "
            f"{packet.get('origin_country')} to {packet.get('destination_country')}. "
            f"Known status: {packet.get('customer_visible_status_label')}. "
            f"Evidence attached: {evidence.get('attached', 0)}; missing items: {evidence.get('missing', 0)}. "
            "Please help organize questions and missing evidence only. Do not provide legal, customs, tariff, CFIA, "
            "supplier, buyer, shipment, or launch approval claims."
        ),
        "do_not_include": [
            "uploaded file contents",
            "prices, bank details, private buyer/supplier data",
            "personal information",
            "claims that tariff, CFIA, legal, customs, buyer, or shipment readiness is approved",
        ],
        "safe_questions": packet.get("buyer_broker_questions", [])[:8],
        "blocked_claims": packet.get("blocked_claims_display", []),
        "next_valid_move": packet.get("next_valid_move"),
        "proof_boundary": "This summary is safe for drafting questions. It is not a substitute for expert review or current official source proof.",
    }


def _render_public_confirm(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    packet_id = escape(str(packet.get("packet_id")))
    evidence_rows = packet.get("evidence_items", [])
    field_rows = []
    for evidence in evidence_rows:
        extracted = evidence.get("extracted_fields") or {}
        if not extracted:
            continue
        field_rows.append(
            "<tr>"
            f"<td>{escape(str(evidence.get('title')))}</td>"
            f"<td>{escape(str(evidence.get('extraction_status') or evidence.get('ledger_status')))}</td>"
            f"<td>{escape(str(evidence.get('extraction_confidence') or 'low'))}</td>"
            f"<td>{escape(json.dumps(extracted, sort_keys=True))}</td>"
            "</tr>"
        )
    body = f"""
<section class="surface">
  {_workflow_steps("confirm")}
  <h1>Confirm Extracted Fields</h1>
  <p class="lede">Review the draft metadata before it becomes packet context. Unknown or wrong fields should remain blockers.</p>
  <p class="note">Confirmation does not verify document authenticity or open customs, tariff, legal, CFIA, buyer, supplier, shipment, or launch claims.</p>
  <form method="post" action="/api/public/packets/{packet_id}/confirm">
    <div class="grid">
      <div><label>Product</label><input name="product_name" value="{escape(str(packet.get('product_name') or ''))}"></div>
      <div><label>HS code if known</label><input name="hs_code_value" value="{escape(str(packet.get('hs_code_value') or ''))}"></div>
      <div><label>Origin</label><input name="origin_country" value="{escape(str(packet.get('origin_country') or ''))}"></div>
      <div><label>Destination</label><input name="destination_country" value="{escape(str(packet.get('destination_country') or ''))}"></div>
      <div><label>Importer of record</label><select name="importer_of_record">{_select_options(["unknown", "buyer", "importer", "exporter", "broker"], str(packet.get('importer_of_record') or 'unknown'))}</select></div>
      <div><label>Incoterms</label><select name="incoterms_if_known">{_select_options(["unknown", "EXW", "FOB", "CIF", "DAP", "DDP"], str(packet.get('incoterms_if_known') or 'unknown'))}</select></div>
    </div>
    <label>Confirmation notes</label><textarea name="confirmation_notes" rows="3">User confirmed visible metadata only. Missing evidence and expert review remain required.</textarea>
    <label><input type="checkbox" name="fields_confirmed" value="accepted" checked> I confirm these draft fields are suitable for internal packet context.</label>
    <button type="submit">{_icon("check")}Save Confirmation</button>
  </form>
</section>
<section class="surface">
  <h2>Extracted Metadata</h2>
  <table>
    <thead><tr><th>Document</th><th>Status</th><th>Confidence</th><th>Fields</th></tr></thead>
    <tbody>{''.join(field_rows) or '<tr><td colspan="4">No extracted fields yet. Upload PDFs or use starter mode.</td></tr>'}</tbody>
  </table>
</section>
"""
    return _render_page("Confirm Extracted Fields", body)


def _render_workspace(workflow: dict[str, Any], runtime: dict[str, Any]) -> str:
    packets = workflow.get("packets", [])
    blocked = sum(1 for packet in packets if packet.get("blocker_count", 0) > 0)
    rows = "".join(
        "<tr>"
        f"<td><a href='/public/packets/{escape(str(packet.get('packet_id')))}/result'>{escape(str(packet.get('packet_name')))}</a></td>"
        f"<td>{escape(str(packet.get('product_name')))}</td>"
        f"<td>{escape(str(packet.get('customer_visible_status_label')))}</td>"
        f"<td>{escape(str(packet.get('confirmation_status') or 'not_confirmed'))}</td>"
        f"<td>{escape(str(packet.get('next_valid_move')))}</td>"
        "</tr>"
        for packet in packets
    )
    body = f"""
<section class="surface">
  <h1>Saved Packet Workspace</h1>
  <p class="lede">Local workspace for packets, reports, source monitoring, and review lanes. Production accounts, hosting, and privacy/security review remain external gates.</p>
  <div class="grid grid-3">
    {_metric_card("Packets", len(packets), "Saved in local JSON and SQLite artifacts.")}
    {_metric_card("Blocked", blocked, "External claims stay closed.")}
    {_metric_card("Runtime", runtime.get("status"), "Private-beta candidate with human gates.")}
  </div>
  <div class="actions">
    {_button_link("/start", "Create starter packet", "sparkles")}
    {_button_link("/trade-check", "Upload PDFs", "upload", tone="secondary")}
    {_button_link("/admin/sources", "Source monitor", "database", tone="secondary")}
  </div>
</section>
<section class="surface">
  <h2>Packets</h2>
  <table>
    <thead><tr><th>Packet</th><th>Product</th><th>Status</th><th>Confirmation</th><th>Next</th></tr></thead>
    <tbody>{rows or '<tr><td colspan="5">No saved packets yet.</td></tr>'}</tbody>
  </table>
</section>
"""
    return _render_page("Saved Workspace", body)


def _render_login_signup(mode: str) -> str:
    action = "/api/auth/signup" if mode == "signup" else "/api/auth/login"
    title = "Create Account" if mode == "signup" else "Log In"
    body = f"""
<h1>{title}</h1>
<p class="note">Local private-beta auth uses seeded demo sessions. Real external hosting must wire a production identity provider and secrets manager.</p>
<form method="post" action="{action}">
  <input type="hidden" name="csrf_token" value="{CSRF_TOKEN}">
  <label>Email</label><input name="email" value="customer@example.local">
  <label>Name</label><input name="name" value="Local Customer">
  <label>Organization</label><input name="organization_name" value="Importer Demo Co.">
  <button type="submit">{title}</button>
</form>
<p>Demo sessions: customer@example.local, operator@example.local, admin@example.local, other@example.local.</p>
"""
    return _render_page(title, body)


def _render_onboarding() -> str:
    body = """
<h1>Onboarding</h1>
<p class="note">The first win is a source packet. Keep the first packet narrow and evidence-backed.</p>
<form method="get" action="/packets/new">
  <label>User type</label>
  <select name="user_type"><option>Importer / founder</option><option>Sourcing operator</option><option>Consultant</option><option>Broker/compliance reviewer</option><option>Internal operator</option></select>
  <label>What are you trying to decide?</label>
  <select name="goal"><option>What evidence is missing?</option><option>Can I continue researching this source?</option><option>What should I ask a broker/reviewer?</option><option>Can I prepare a readiness report?</option></select>
  <button type="submit">Create first packet</button>
</form>
"""
    return _render_page("Onboarding", body)


def _render_customer_dashboard(workflow: dict[str, Any], actor: dict[str, Any]) -> str:
    packets = _visible_packets(workflow, actor)
    blocked_count = sum(1 for packet in packets if packet.get("blocker_count", 0) > 0)
    missing = sum(int((packet.get("evidence_summary") or {}).get("missing", 0)) for packet in packets)
    rows = []
    for packet in packets:
        packet_id = escape(str(packet.get("packet_id")))
        blockers = packet.get("top_blockers", [])
        main = blockers[0].get("title") if blockers else "Internal review"
        rows.append(
            "<tr>"
            f"<td><a href='/packets/{packet_id}'>{escape(str(packet.get('packet_name')))}</a></td>"
            f"<td>{escape(str(packet.get('product_name')))}</td>"
            f"<td>{escape(str(packet.get('destination_country')))}</td>"
            f"<td>{escape(str(packet.get('customer_visible_status_label')))}</td>"
            f"<td>{escape(str(main))}</td>"
            f"<td>{escape(str((packet.get('evidence_summary') or {}).get('summary')))}</td>"
            f"<td>{escape(str(packet.get('next_valid_move')))}</td>"
            "</tr>"
        )
    body = f"""
<h1>Your Source Packets</h1>
<p class="note">Signed in as {escape(str(actor.get('email')))}. Customer pages show plain-English packet, evidence, blockers, next steps, reports, and review requests.</p>
<section class="grid">
  <div class="metric"><div class="label">Packets total</div><div class="value">{len(packets)}</div></div>
  <div class="metric"><div class="label">Blocked packets</div><div class="value">{blocked_count}</div></div>
  <div class="metric"><div class="label">Reports ready</div><div class="value">{len(packets)}</div></div>
  <div class="metric"><div class="label">Evidence missing</div><div class="value">{missing}</div></div>
</section>
<p><a class="button-link" href="/packets/new">Create packet</a></p>
<table>
  <thead><tr><th>Packet</th><th>Product</th><th>Destination</th><th>Status</th><th>Main blocker</th><th>Evidence</th><th>Next action</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="7">Create your first source packet to see what evidence is missing before moving forward.</td></tr>'}</tbody>
</table>
"""
    return _render_page("Dashboard", body)


def _render_packet_reviews(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    runtime = build_runtime_state(workflow)
    requests = [row for row in runtime["review_requests"] if row["packet_id"] == packet.get("packet_id")]
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('review_type')))}</td>"
        f"<td>{escape(str(row.get('reviewer_role')))}</td>"
        f"<td>{escape(str(row.get('status')))}</td>"
        f"<td><a href='/review/{escape(str(row.get('token')))}'>Scoped review link</a></td>"
        "</tr>"
        for row in requests
    )
    body = f"""
<h1>Reviews - {escape(str(packet.get('packet_name')))}</h1>
<p class="note">Review requests are scoped. Expert findings can only affect claims within the review scope.</p>
<table>
  <thead><tr><th>Type</th><th>Reviewer role</th><th>Status</th><th>Scoped link</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
"""
    return _render_page("Packet Reviews", body)


def _render_packet_ai_reviews(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    runs = [run for run in workflow.get("ai_review_runs", []) if run.get("packet_id") == packet.get("packet_id")]
    cards = []
    for run in runs:
        routes = run.get("model_route_decisions", [])
        cards.append(
            "<div class='metric'>"
            f"<div class='label'>{escape(str(run.get('review_type')))}</div>"
            f"<div class='value'>{escape(str(run.get('status')))}</div>"
            f"<p>Mode: {escape(str(run.get('model_mode')))}; endpoint: {escape(str(run.get('model_name_or_endpoint')))}; redaction: {escape(str(run.get('redaction_applied')))}</p>"
            f"<p>Routes: {len(routes)}; findings: {len(run.get('findings', []))}; human review required: {escape(str(run.get('human_review_required')))}; can open gate: {escape(str(run.get('can_open_gate')))}</p>"
            "</div>"
        )
    body = f"""
<h1>AI Reviews</h1>
<p class="note">AI simulated reviews help identify missing evidence and risky claims. They do not replace qualified human review and cannot open external approval gates.</p>
<section class="grid">{''.join(cards)}</section>
"""
    return _render_page("AI Reviews", body)


def _render_packet_reports(workflow: dict[str, Any], packet: dict[str, Any]) -> str:
    runtime = build_runtime_state(workflow)
    exports = [row for row in runtime["report_exports"] if row["packet_id"] == packet.get("packet_id")]
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('report_type')))}</td>"
        f"<td>{escape(str(row.get('format')))}</td>"
        f"<td>{escape(str(row.get('status')))}</td>"
        f"<td>{escape(str(row.get('ai_involvement_disclosure')))}</td>"
        f"<td><a href='/api/reports/{escape(str(row.get('id')))}/download'>Download</a></td>"
        "</tr>"
        for row in exports
    )
    body = f"""
<h1>Reports</h1>
<p class="note">Reports are draft readiness artifacts. The app never exports approval, compliance, or import-ready certificates.</p>
<table>
  <thead><tr><th>Report</th><th>Format</th><th>Status</th><th>AI Disclosure</th><th>Action</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
"""
    return _render_page("Reports", body)


def _render_packet_settings(packet: dict[str, Any]) -> str:
    body = f"""
<h1>Packet Settings</h1>
<p>{escape(str(packet.get('packet_name')))}</p>
<p class="note">Deleting customer data is tracked as a deletion request and audit event. Retention rules must be reviewed before hosted use.</p>
<p><a href="/settings/ai-data-policy">AI data policy</a> | <a href="/privacy">Privacy</a> | <a href="/terms">Terms</a> | <a href="/data-retention">Data retention</a></p>
<form method="post" action="/api/packets/{escape(str(packet.get('packet_id')))}/delete-request">
  <input type="hidden" name="csrf_token" value="{CSRF_TOKEN}">
  <button type="submit">Request data deletion</button>
</form>
"""
    return _render_page("Packet Settings", body)


def _render_ai_data_policy(runtime: dict[str, Any], actor: dict[str, Any]) -> str:
    policy = ai_policy_for_org(str(actor.get("organization_id") or "org-importer-demo"))
    endpoints = runtime.get("model_endpoints", [])
    endpoint_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('id')))}</td>"
        f"<td>{escape(str(row.get('mode')))}</td>"
        f"<td>{escape(str(row.get('model_name')))}</td>"
        f"<td>{escape(str(row.get('health_check_status')))}</td>"
        f"<td>{escape(str(row.get('retention_policy')))}</td>"
        "</tr>"
        for row in endpoints
    )
    requirement_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('id')))}</td>"
        f"<td>{escape(str(row.get('name')))}</td>"
        f"<td>{escape(str(row.get('status')))}</td>"
        f"<td>{escape(str(row.get('boundary')))}</td>"
        "</tr>"
        for row in runtime.get("requirements_traceability", [])
    )
    body = f"""
<h1>AI Data Policy</h1>
<p class="note">Organization policy controls whether evidence can use AI, which model route is allowed, what must be redacted, and what falls back to manual review.</p>
<section class="grid">
  <div class="metric"><div class="label">Default mode</div><div class="value">{escape(str(policy.get('default_mode')))}</div></div>
  <div class="metric"><div class="label">Allowed modes</div><div class="value">{escape(', '.join(policy.get('allowed_modes', [])))}</div></div>
  <div class="metric"><div class="label">Allowed sensitivity</div><div class="value">{escape(', '.join(policy.get('allowed_sensitivity', [])))}</div></div>
  <div class="metric"><div class="label">No-AI fallback</div><div class="value">{escape(str(policy.get('no_ai_fallback')))}</div></div>
</section>
<h2>Endpoint Contracts</h2>
<table>
  <thead><tr><th>ID</th><th>Mode</th><th>Model</th><th>Status</th><th>Retention</th></tr></thead>
  <tbody>{endpoint_rows}</tbody>
</table>
<h2>Requirement Traceability</h2>
<table>
  <thead><tr><th>ID</th><th>Requirement</th><th>Status</th><th>Boundary</th></tr></thead>
  <tbody>{requirement_rows}</tbody>
</table>
"""
    return _render_page("AI Data Policy", body)


def _render_static_policy_page(kind: str) -> str:
    pages = {
        "privacy": (
            "Privacy Notice",
            "Evidence, packet metadata, audit events, AI route decisions, and deletion requests are stored locally for review. Hosted use still requires qualified privacy/legal review.",
        ),
        "terms": (
            "Terms",
            "The product provides source-readiness organization, blocker tracking, and draft reports. It does not provide legal, customs, tariff, CFIA, financial, supplier, buyer, or launch advice.",
        ),
        "ai-use": (
            "AI Use",
            "AI is optional and policy-routed. Simulated AI reviewers can suggest blockers and next moves, but cannot open gates or replace qualified people.",
        ),
        "data-retention": (
            "Data Retention",
            "Local artifacts are retained for auditability. Customer deletion requests are logged and must be reviewed before hosted deployment.",
        ),
    }
    title, message = pages[kind]
    body = f"""
<h1>{escape(title)}</h1>
<p class="note">{escape(message)}</p>
<p><a href="/settings/ai-data-policy">AI data policy</a> | <a href="/support">Support</a></p>
"""
    return _render_page(title, body)


def _render_account(actor: dict[str, Any]) -> str:
    body = f"""
<h1>Account</h1>
<table>
  <tbody>
    <tr><th>User</th><td>{escape(str(actor.get('name')))}</td></tr>
    <tr><th>Email</th><td>{escape(str(actor.get('email')))}</td></tr>
    <tr><th>Role</th><td>{escape(str(actor.get('role')))}</td></tr>
    <tr><th>Organization</th><td>{escape(str(actor.get('organization_id')))}</td></tr>
  </tbody>
</table>
"""
    return _render_page("Account", body)


def _render_support() -> str:
    body = f"""
<h1>Support</h1>
<p class="note">{escape(PRODUCT_BOUNDARY)}</p>
<h2>Before private beta use</h2>
<ul>
  <li>Review privacy notice and terms.</li>
  <li>Use packet exports as draft internal readiness artifacts only.</li>
  <li>Escalate customs, tariff, CFIA, legal, supplier, buyer, and launch questions to qualified people.</li>
</ul>
<p>Support contact process: create an operator review request from the packet, then export the expert-review packet.</p>
"""
    return _render_page("Support", body)


def _render_admin_index(runtime: dict[str, Any]) -> str:
    body = f"""
<h1>Admin</h1>
<p class="note">Admin surfaces manage users, organizations, official sources, claim rules, review templates, audit, and system health.</p>
<section class="grid">
  <div class="metric"><div class="label">Users</div><div class="value">{len(runtime.get('users', []))}</div></div>
  <div class="metric"><div class="label">Organizations</div><div class="value">{len(runtime.get('organizations', []))}</div></div>
  <div class="metric"><div class="label">Claim rules</div><div class="value">{len(runtime.get('claim_rules', []))}</div></div>
  <div class="metric"><div class="label">Audit events</div><div class="value">{len(runtime.get('audit_events', []))}</div></div>
</section>
<p><a href="/admin/users">Users</a> | <a href="/admin/organizations">Organizations</a> | <a href="/admin/claim-rules">Claim rules</a> | <a href="/admin/review-templates">Review templates</a> | <a href="/admin/audit">Audit</a> | <a href="/admin/system-health">System health</a></p>
"""
    return _render_page("Admin", body)


def _render_simple_table(title: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{escape(str(row.get(column, '')))}</td>" for column in columns) + "</tr>"
        for row in rows
    )
    headers = "".join(f"<th>{escape(column.replace('_', ' ').title())}</th>" for column in columns)
    body = f"""
<h1>{escape(title)}</h1>
<table><thead><tr>{headers}</tr></thead><tbody>{body_rows or f'<tr><td colspan="{len(columns)}">No rows.</td></tr>'}</tbody></table>
"""
    return _render_page(title, body)


def _render_audit(runtime: dict[str, Any]) -> str:
    events = runtime.get("audit_events", [])
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('created_at')))}</td>"
        f"<td>{escape(str(row.get('actor_type')))}</td>"
        f"<td>{escape(str(row.get('event_type')))}</td>"
        f"<td>{escape(str(row.get('entity_type')))}</td>"
        f"<td>{escape(str(row.get('entity_id')))}</td>"
        "</tr>"
        for row in events
    )
    body = f"""
<h1>Audit</h1>
<p class="note">Audit events include packet creation, evidence uploads/deletions, source refreshes, AI review runs, review findings, report exports, permission changes, and deletion requests.</p>
<table>
  <thead><tr><th>Timestamp</th><th>Actor</th><th>Event</th><th>Entity</th><th>ID</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
"""
    return _render_page("Audit", body)


def _render_system_health(runtime: dict[str, Any]) -> str:
    deploy = runtime.get("deployment", deployment_readiness())
    checklist = runtime.get("private_beta_checklist", [])
    rows = "".join(
        f"<tr><td>{escape(str(row.get('item')))}</td><td>{escape(str(row.get('status')))}</td></tr>"
        for row in checklist
    )
    body = f"""
<h1>System Health</h1>
<p><span class="status">{escape(str(deploy.get('status')))}</span></p>
<p class="note">{escape(str(deploy.get('proof_boundary')))}</p>
<h2>Private Beta Checklist</h2>
<table><thead><tr><th>Control</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>
"""
    return _render_page("System Health", body)


def _render_review_page(workflow: dict[str, Any], token: str, view: str) -> str:
    runtime = build_runtime_state(workflow)
    request = next((row for row in runtime["review_requests"] if row.get("token") == token), None)
    if request is None:
        return _render_page("Review Not Found", "<h1>Review Not Found</h1><p>This scoped review token is not active.</p>")
    packet = _packet_lookup(workflow).get(str(request["packet_id"]))
    if packet is None:
        return _render_page("Review Not Found", "<h1>Review Not Found</h1><p>Packet was not found.</p>")
    if view == "evidence":
        return _render_packet_evidence(packet)
    if view in {"questions", "submit"}:
        questions = _list_items(request.get("questions", []))
        body = f"""
<h1>Submit Scoped Finding</h1>
<p class="note">Scope: {escape(str(request.get('scope')))}</p>
<h2>Questions For Reviewer</h2>
<ul>{questions}</ul>
<form method="post" action="/review/{escape(token)}/submit">
  <input type="hidden" name="csrf_token" value="{CSRF_TOKEN}">
  <label>Decision</label><select name="decision"><option>blocked</option><option>needs_more_evidence</option><option>scoped_review_complete</option><option>not_within_scope</option></select>
  <label>Evidence reviewed IDs</label><input name="evidence_reviewed_ids" value="{escape(','.join(str(row.get('evidence_id')) for row in packet.get('evidence_items', [])))}">
  <label>Conditions</label><textarea name="conditions" rows="3">Scoped finding only; no general approval.</textarea>
  <label>Notes</label><textarea name="notes" rows="4"></textarea>
  <button type="submit">Submit scoped finding</button>
</form>
"""
        return _render_page("Submit Scoped Finding", body)
    claims = _list_items(packet.get("blocked_claims_display", []))
    body = f"""
<h1>Review request: {escape(str(request.get('review_type')))}</h1>
<p><strong>Packet:</strong> {escape(str(packet.get('packet_name')))}</p>
<p class="note">Scope: {escape(str(request.get('scope')))}</p>
<h2>Blocked Claims</h2>
<ul>{claims}</ul>
<h2>Out Of Scope</h2>
<ul>{_list_items(request.get('out_of_scope', []))}</ul>
<p><a class="button-link" href="/review/{escape(token)}/evidence">Evidence</a> <a class="button-link" href="/review/{escape(token)}/questions">Questions</a></p>
"""
    return _render_page("Expert Review", body)


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
<p><a href="/packets/{escape(str(packet.get('packet_id')))}/evidence">Evidence</a> | <a href="/packets/{escape(str(packet.get('packet_id')))}/blockers">Blockers</a> | <a href="/packets/{escape(str(packet.get('packet_id')))}/readiness">Readiness report</a> | <a href="/packets/{escape(str(packet.get('packet_id')))}/source-monitoring">Source monitoring</a> | <a href="/packets/{escape(str(packet.get('packet_id')))}/safe-summary">Safe summary</a> | <a href="/packets/{escape(str(packet.get('packet_id')))}/ai-reviews">AI reviews</a> | <a href="/packets/{escape(str(packet.get('packet_id')))}/reviews">Human reviews</a> | <a href="/packets/{escape(str(packet.get('packet_id')))}/reports">Reports</a> | <a href="/operator/queue">Operator queue</a></p>
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
        route = _route_for_evidence(packet, evidence)
        redaction = redaction_preview_for_evidence(evidence)
        rows.append(
            "<tr>"
            f"<td>{escape(str(evidence.get('evidence_id')))}</td>"
            f"<td><a href='{escape(str(evidence.get('source_url')))}'>{escape(str(evidence.get('evidence_type')))}</a></td>"
            f"<td>{escape(str(evidence.get('ledger_status')))}</td>"
            f"<td>{escape(str(evidence.get('rights_status')))}</td>"
            f"<td>{escape(str(evidence.get('freshness_status')))}</td>"
            f"<td>{escape(str(evidence.get('sensitivity_level')))}</td>"
            f"<td>{escape(str(evidence.get('ai_processing_mode')))}</td>"
            f"<td>{escape(str(route.get('allowed')))}</td>"
            f"<td>{escape(str(redaction.get('redaction_status')))}</td>"
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
  <div class="metric"><div class="label">AI Allowed</div><div class="value">{escape(str(summary.get('ai_allowed')))}</div></div>
  <div class="metric"><div class="label">Redaction Required</div><div class="value">{escape(str(summary.get('redaction_required')))}</div></div>
</section>
<h2>Upload Evidence</h2>
<form method="post" action="/packets/{escape(str(packet.get('packet_id')))}/actions">
  <input type="hidden" name="action" value="upload_evidence">
  <input type="hidden" name="csrf_token" value="{CSRF_TOKEN}">
  <label>Evidence type</label><input name="evidence_type" value="customer_uploaded_reference">
  <label>Source URL</label><input name="source_url" value="">
  <label>Sensitivity</label><select name="sensitivity_level">{_select_options(SENSITIVITY_LEVELS, 'internal')}</select>
  <label>AI processing mode</label><select name="ai_processing_mode">{_select_options(AI_PROCESSING_MODES, 'metadata_only')}</select>
  <label><input type="checkbox" name="redaction_required" value="true"> Redaction required</label>
  <label>Claim supported</label><input name="claim_supported" value="Customer-uploaded evidence for internal review">
  <button type="submit">Upload Evidence</button>
</form>
<table>
  <thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Rights</th><th>Freshness</th><th>Sensitivity</th><th>AI Mode</th><th>AI Allowed</th><th>Redaction</th><th>Claim Supported</th><th>Review Required</th><th>Boundary</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="12">No evidence.</td></tr>'}</tbody>
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
    runtime = _runtime_state(repo_root)
    return {
        "product": PUBLIC_PRODUCT_NAME,
        "internal_engine": "Importer Source Readiness Copilot",
        "surface": "local_customer_operator_expert_application",
        "public_surface": "public_quick_check_ready_local_with_external_gates",
        "runtime_status": runtime.get("status"),
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
        "auth_status": runtime.get("security_controls", {}).get("authentication"),
        "rbac_status": runtime.get("security_controls", {}).get("rbac"),
        "deployment_status": runtime.get("deployment", {}).get("status"),
        "allowed_use": workflow.get("allowed_use"),
        "not_allowed_use": workflow.get("not_allowed_use", []),
        "routes": sorted(
            [
                *API_ROUTES,
                *STATIC_ROUTES,
                "/",
                "/start",
                "/tools",
                "/trade-check",
                "/tools/import-readiness",
                "/tools/export-readiness",
                "/tools/buyer-broker-packet",
                "/tools/document-check",
                "/tools/canadian-references",
                "/opportunities",
                "/country-coverage",
                "/transport-readiness",
                "/reports/sample",
                "/pricing",
                "/billing",
                "/billing/usage",
                "/agent-api",
                "/stages",
                "/research-plan",
                "/expert-network",
                "/team-workspace",
                "/launch-operations",
                "/ai-data-policy",
                "/security",
                "/public/packets/:id/result",
                "/public/packets/:id/confirm",
                "/workspace",
                "/api/public/starter",
                "/api/public/quick-check",
                "/api/public/packets/:id/refresh-official-sources",
                "/api/public/packets/:id/confirm",
                "/api/public/packets/:id/chatgpt-safe-summary",
                "/api/public/packets/:id/reports/starter.pdf",
                "/api/public/packets/:id/reports/draft.pdf",
                "/api/public/packets/:id/reports/missing.pdf",
                "/api/public/packets/:id/reports/buyer.pdf",
                "/api/public/packets/:id/reports/broker.pdf",
                "/api/public/packets/:id/delete-files",
                "/api/billing/usage",
                "/api/agent-api/gateway",
                "/api/stages",
                "/api/research-plan",
                "/api/expert-network",
                "/api/team-workspace",
                "/api/launch-operations",
                "/api/agent-tools/:tool",
                "/login",
                "/signup",
                "/onboarding",
                "/dashboard",
                "/packets",
                "/packets/new",
                "/packets/:id",
                "/packets/:id/evidence",
                "/packets/:id/blockers",
                "/packets/:id/readiness",
                "/packets/:id/ai-reviews",
                "/packets/:id/reviews",
                "/packets/:id/reports",
                "/packets/:id/source-monitoring",
                "/packets/:id/safe-summary",
                "/packets/:id/settings",
                "/settings/ai-data-policy",
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
                "/review/:token",
                "/review/:token/evidence",
                "/review/:token/questions",
                "/review/:token/submit",
                "/admin",
                "/admin/sources",
                "/admin/gates",
                "/admin/users",
                "/admin/organizations",
                "/admin/claim-rules",
                "/admin/review-templates",
                "/admin/audit",
                "/admin/system-health",
                "/account",
                "/support",
                "/privacy",
                "/terms",
                "/ai-use",
                "/data-retention",
                "/api/orgs/current/ai-policy",
                "/api/orgs/current/ai-policy/test-model-endpoint",
                "/api/evidence/:evidenceId/ai-permission",
            ]
        ),
        "proof_boundary": (
            "This local app includes a draft public quick-check surface and internal "
            "operator workspace. It is not customs/tariff advice, supplier recommendation, "
            "legal or financial advice, shipment approval, or launch approval."
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
            actor = _actor_from_headers(self.headers)
            workflow = _customer_workflow(repo_root)
            runtime = _runtime_state(repo_root)

            if path == "/api":
                self._send_json(_index_payload(repo_root))
                return
            if path in {"/healthz", "/readyz", "/api/system-health"}:
                self._send_json(self._system_health_payload())
                return
            if path.startswith("/api/"):
                self._handle_api_get(path, actor)
                return
            if path == "/api/customer-workflow":
                self._send_json(workflow)
                return
            if path in API_ROUTES:
                self._send_file(API_ROUTES[path], "application/json; charset=utf-8")
                return
            if path == "/":
                self._send_html(_render_landing())
                return
            if path == "/start":
                self._send_html(_render_start_page())
                return
            if path == "/tools":
                self._send_html(_render_tool_selection())
                return
            if path in {"/trade-check", "/tools/import-readiness", "/tools/export-readiness", "/tools/buyer-broker-packet", "/tools/document-check"}:
                default_direction = "import" if path == "/tools/import-readiness" else "export"
                self._send_html(_render_public_trade_check(default_direction))
                return
            if path == "/tools/canadian-references":
                self._send_html(_render_canadian_references(workflow))
                return
            if path == "/opportunities":
                self._send_html(_render_opportunities(repo_root, workflow))
                return
            if path == "/country-coverage":
                self._send_html(_render_country_coverage(repo_root))
                return
            if path == "/transport-readiness":
                self._send_html(_render_transport_readiness(repo_root))
                return
            if path == "/reports/sample":
                self._send_html(_render_sample_reports(repo_root))
                return
            if path in {"/pricing", "/billing"}:
                self._send_html(_render_pricing(repo_root))
                return
            if path == "/billing/usage":
                self._send_html(_render_billing_usage(repo_root))
                return
            if path == "/agent-api":
                self._send_html(_render_agent_api(repo_root))
                return
            if path == "/stages":
                self._send_html(_render_stage_overview(repo_root))
                return
            if path == "/research-plan":
                self._send_html(_render_research_plan(repo_root))
                return
            if path == "/expert-network":
                self._send_html(_render_expert_network(repo_root))
                return
            if path == "/team-workspace":
                self._send_html(_render_team_workspace(repo_root))
                return
            if path == "/launch-operations":
                self._send_html(_render_launch_operations(repo_root))
                return
            if path.startswith("/tools/"):
                traffic_html = _render_traffic_page(repo_root, path.removeprefix("/tools/").strip("/"))
                if traffic_html is not None:
                    self._send_html(traffic_html)
                    return
            if path == "/ai-data-policy":
                self._send_html(_render_ai_data_policy(runtime, actor))
                return
            if path == "/security":
                self._send_html(_render_security_public(runtime))
                return
            if path.startswith("/public/packets/") and path.endswith("/result"):
                packet_id = path.removeprefix("/public/packets/").removesuffix("/result").strip("/")
                packet = _packet_lookup(workflow).get(packet_id)
                if packet is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                    return
                self._send_html(_render_public_result(workflow, packet))
                return
            if path.startswith("/public/packets/") and path.endswith("/confirm"):
                packet_id = path.removeprefix("/public/packets/").removesuffix("/confirm").strip("/")
                packet = _packet_lookup(workflow).get(packet_id)
                if packet is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                    return
                self._send_html(_render_public_confirm(workflow, packet))
                return
            if path == "/login":
                self._send_html(_render_login_signup("login"))
                return
            if path == "/signup":
                self._send_html(_render_login_signup("signup"))
                return
            if path == "/onboarding":
                self._send_html(_render_onboarding())
                return
            if path == "/dashboard":
                self._send_html(_render_customer_dashboard(workflow, actor))
                return
            if path == "/workspace":
                self._send_html(_render_workspace(workflow, runtime))
                return
            if path == "/account":
                self._send_html(_render_account(actor))
                return
            if path == "/support":
                self._send_html(_render_support())
                return
            if path == "/settings/ai-data-policy":
                self._send_html(_render_ai_data_policy(runtime, actor))
                return
            if path in {"/privacy", "/terms", "/ai-use", "/data-retention"}:
                self._send_html(_render_static_policy_page(path.removeprefix("/")))
                return
            if path in STATIC_ROUTES:
                self._send_file(STATIC_ROUTES[path], "text/html; charset=utf-8")
                return
            if path in {"/source-packets", "/packets"}:
                self._send_html(_render_packet_list(workflow))
                return
            if path in {"/source-packets/new", "/packets/new"}:
                self._send_html(_render_packet_form())
                return
            if path == "/admin":
                self._send_html(_render_admin_index(runtime))
                return
            if path == "/admin/users":
                self._send_html(_render_simple_table("Users", runtime.get("users", []), ["id", "email", "name", "role", "organization_id"]))
                return
            if path == "/admin/organizations":
                self._send_html(_render_simple_table("Organizations", runtime.get("organizations", []), ["id", "name", "type"]))
                return
            if path == "/admin/claim-rules":
                self._send_html(_render_simple_table("Claim Rules", runtime.get("claim_rules", []), ["claim_type", "display_name", "default_status", "requires_human_review"]))
                return
            if path == "/admin/review-templates":
                self._send_html(_render_simple_table("Review Templates", runtime.get("review_templates", []), ["id", "name", "reviewer_role", "scope"]))
                return
            if path == "/admin/audit":
                self._send_html(_render_audit(runtime))
                return
            if path == "/admin/system-health":
                self._send_html(_render_system_health(runtime))
                return
            if path == "/admin/sources":
                self._send_html(_render_admin_sources(workflow))
                return
            if path == "/admin/gates":
                self._send_html(_render_admin_gates(workflow))
                return
            if path == "/operator/queue":
                self._send_file("system_review_graph/operator_dashboard.html", "text/html; charset=utf-8")
                return
            if path in {"/operator/packets", "/operator/blockers", "/operator/reviews", "/operator/reports", "/operator/sources", "/operator/gates"}:
                self._send_file("system_review_graph/operator_dashboard.html", "text/html; charset=utf-8")
                return
            if path.startswith("/operator/packets/"):
                packet_id = path.removeprefix("/operator/packets/").strip("/")
                self._send_packet_route(packet_id, "", actor)
                return
            if path.startswith("/review/"):
                suffix = path.removeprefix("/review/").strip("/")
                parts = suffix.split("/")
                token = parts[0]
                view = parts[1] if len(parts) > 1 else ""
                self._send_html(_render_review_page(workflow, token, view))
                return
            if path.startswith("/source-packets/") or path.startswith("/packets/"):
                suffix = path.removeprefix("/source-packets/") if path.startswith("/source-packets/") else path.removeprefix("/packets/")
                suffix = suffix.strip("/")
                parts = suffix.split("/")
                packet_id = parts[0]
                view = parts[1] if len(parts) > 1 else ""
                self._send_packet_route(packet_id, view, actor)
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
            actor = _actor_from_headers(self.headers)
            if path.startswith("/api/"):
                self._handle_api_post(path, actor)
                return
            if path.startswith("/review/") and path.endswith("/submit"):
                token = path.removeprefix("/review/").removesuffix("/submit").strip("/")
                self._handle_review_submit(token)
                return
            if path not in {"/source-packets", "/packets"}:
                if (path.startswith("/source-packets/") or path.startswith("/packets/")) and path.endswith("/actions"):
                    if path.startswith("/source-packets/"):
                        packet_id = path.removeprefix("/source-packets/").removesuffix("/actions").strip("/")
                    else:
                        packet_id = path.removeprefix("/packets/").removesuffix("/actions").strip("/")
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
            if fields.get("csrf_token") not in {"", None, CSRF_TOKEN}:
                self.send_error(HTTPStatus.FORBIDDEN, "Invalid CSRF token")
                return
            packet = packet_from_submission({**fields, "organization_id": actor.get("organization_id")})
            if not can_access_packet(actor, packet):
                self.send_error(HTTPStatus.FORBIDDEN, "Packet is outside this organization")
                return
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
            self.send_header("Location", f"/packets/{packet['packet_id']}/readiness")
            self.end_headers()

        def do_PATCH(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            actor = _actor_from_headers(self.headers)
            if path.startswith("/api/"):
                self._handle_api_patch(path, actor)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown operator app route")

        def _read_fields(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_EVIDENCE_UPLOAD_BYTES:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Request too large")
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            content_type = self.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return json.loads(raw or "{}")
            parsed_fields = parse_qs(raw, keep_blank_values=True)
            return {key: values[-1] for key, values in parsed_fields.items()}

        def _append_audit(self, event: dict[str, Any]) -> None:
            path = repo_root / "system_review_graph" / "customer_action_log.json"
            _append_json_list(path, event)

        def _handle_api_patch(self, path: str, actor: dict[str, Any]) -> None:
            fields = self._read_fields()
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat()
            if path.startswith("/api/evidence/") and path.endswith("/ai-permission"):
                evidence_id = path.removeprefix("/api/evidence/").removesuffix("/ai-permission").strip("/")
                packets, evidence_rows = _load_mutable_customer_rows(repo_root)
                workflow = build_customer_workflow(
                    source_packets=packets,
                    evidence_items=evidence_rows,
                    official_sources=_load_json(repo_root / "data" / "official_source_registry.json"),
                )
                packet_lookup = _packet_lookup(workflow)
                target = next((row for row in evidence_rows if str(row.get("evidence_id")) == evidence_id), None)
                if target is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Evidence not found")
                    return
                packet = packet_lookup.get(str(target.get("packet_id")))
                if packet is None or not can_access_packet(actor, packet):
                    self.send_error(HTTPStatus.FORBIDDEN, "Evidence is outside this organization")
                    return
                ai_fields = _evidence_ai_fields(fields)
                updated_rows = []
                updated_evidence: dict[str, Any] = {}
                for row in evidence_rows:
                    if str(row.get("evidence_id")) == evidence_id:
                        updated_evidence = {**row, **ai_fields, "ai_permission_updated_at": now, "ai_permission_updated_by": actor.get("id")}
                        updated_rows.append(updated_evidence)
                    else:
                        updated_rows.append(row)
                rebuilt = _write_customer_workflow(repo_root, packets, updated_rows)
                rebuilt_packet = _packet_lookup(rebuilt).get(str(packet.get("packet_id"))) or packet
                rebuilt_evidence = next(
                    (row for row in rebuilt_packet.get("evidence_items", []) if str(row.get("evidence_id")) == evidence_id),
                    updated_evidence,
                )
                route = _route_for_evidence(rebuilt_packet, rebuilt_evidence, "evidence_permission_update")
                self._append_audit(
                    {
                        "event_id": f"{evidence_id}:ai-permission-updated:{now}",
                        "packet_id": rebuilt_packet.get("packet_id"),
                        "organization_id": packet_org_id(rebuilt_packet),
                        "event_type": "ai_permission_updated",
                        "actor_user_id": actor.get("id"),
                        "after_json": ai_fields,
                        "created_at": now,
                    }
                )
                self._send_json({"status": "ai_permission_updated", "evidence": rebuilt_evidence, "route_decision": route})
                return
            self.send_error(HTTPStatus.NOT_FOUND, "API route not found")

        def _system_health_payload(self) -> dict[str, Any]:
            runtime = _runtime_state(repo_root)
            store = repo_root / "system_review_graph" / "customer_workflow.sqlite"
            return {
                "status": "ok",
                "product": PUBLIC_PRODUCT_NAME,
                "internal_engine": "Importer Source Readiness Copilot",
                "runtime_status": runtime.get("status"),
                "deployment_status": runtime.get("deployment", {}).get("status"),
                "store_exists": store.exists(),
                "routes_ready": True,
                "unsafe_gates_closed": True,
                "proof_boundary": runtime.get("deployment", {}).get("proof_boundary"),
            }

        def _public_packet(self, packet_id: str) -> dict[str, Any] | None:
            workflow = _customer_workflow(repo_root)
            return _packet_lookup(workflow).get(packet_id)

        def _handle_public_starter(self, actor: dict[str, Any]) -> None:
            fields = self._read_fields()
            if not _truthy_form_value(fields.get("accept_notice")):
                self.send_error(HTTPStatus.BAD_REQUEST, "Starter notice must be accepted")
                return
            if any(_contains_script(str(value)) for value in fields.values()):
                self.send_error(HTTPStatus.BAD_REQUEST, "Metadata contains unsafe HTML")
                return
            product_name = fields.get("product_name") or "Starter trade packet"
            packet = packet_from_submission(
                {
                    **fields,
                    "packet_name": fields.get("packet_name") or f"{product_name} starter checklist",
                    "organization_id": actor.get("organization_id") or "org-importer-demo",
                    "user_type": fields.get("user_type") or "beginner",
                    "beginner_mode": True,
                    "offline_evidence_only": True,
                    "source_type": "beginner_starter",
                    "product_documents": "",
                    "commercial_documents": "",
                    "certificates": "",
                    "proof_of_origin": "",
                    "intended_use": "Beginner no-documents starter checklist for missing trade-readiness evidence.",
                }
            )
            evidence = {
                **evidence_from_submission(packet),
                "evidence_id": f"evidence-{packet['packet_id']}-starter-intake",
                "title": "Beginner starter intake",
                "description": fields.get("notes") or "No documents provided yet.",
                "evidence_type": "customer_uploaded_reference",
                "source_url": "",
                "rights_status": "blocked",
                "freshness_status": "needs_current_refresh_before_claims",
                "claim_supported": "User provided starter context only.",
                "claim_boundary": "Starter context identifies missing evidence and questions only.",
            }
            packets, evidence_rows = _load_mutable_customer_rows(repo_root)
            packets = [row for row in packets if str(row.get("packet_id")) != str(packet["packet_id"])]
            evidence_rows = [row for row in evidence_rows if str(row.get("packet_id")) != str(packet["packet_id"])]
            packets.append(packet)
            evidence_rows.append(evidence)
            _write_customer_workflow(repo_root, packets, evidence_rows)
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/public/packets/{packet['packet_id']}/result")
            self.end_headers()

        def _handle_public_quick_check(self, actor: dict[str, Any]) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_EVIDENCE_UPLOAD_BYTES:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Upload too large")
                return
            raw = self.rfile.read(length)
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                fields, files = _parse_multipart(content_type, raw)
            else:
                parsed_fields = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
                fields = {key: values[-1] for key, values in parsed_fields.items()}
                files = []
            if not _truthy_form_value(fields.get("accept_notice")):
                self.send_error(HTTPStatus.BAD_REQUEST, "AI/data notice must be accepted for quick check")
                return
            if any(_contains_script(str(value)) for value in fields.values()):
                self.send_error(HTTPStatus.BAD_REQUEST, "Metadata contains unsafe HTML")
                return
            pdf_files = [
                file
                for file in files
                if str(file.get("filename", "")).lower().endswith(".pdf")
                and (
                    bytes(file.get("content") or b"").startswith(b"%PDF")
                    or str(file.get("content_type") or "").lower() == "application/pdf"
                )
            ]
            if not pdf_files:
                self.send_error(HTTPStatus.BAD_REQUEST, "Upload at least one PDF document")
                return
            now = datetime.now(timezone.utc).replace(microsecond=0)
            expires_at = (now + timedelta(hours=24)).isoformat()
            document_names = ", ".join(str(file["filename"]) for file in pdf_files)
            packet = packet_from_submission(
                {
                    **fields,
                    "packet_name": fields.get("packet_name") or f"{fields.get('product_name') or 'Trade'} readiness quick check",
                    "organization_id": actor.get("organization_id") or "org-importer-demo",
                    "user_type": fields.get("user_type") or "foreign_exporter",
                    "offline_evidence_only": True,
                    "product_documents": fields.get("product_documents") or document_names,
                    "commercial_documents": fields.get("commercial_documents") or document_names,
                    "source_type": "public_quick_check",
                    "intended_use": "Draft public quick check for missing trade-readiness evidence.",
                }
            )
            packet_id = str(packet["packet_id"])
            upload_dir = repo_root / "system_review_graph" / "public_uploads" / packet_id / "quarantine"
            upload_dir.mkdir(parents=True, exist_ok=True)
            saved_files: list[dict[str, Any]] = []
            evidence_rows: list[dict[str, Any]] = []
            for index, file in enumerate(pdf_files, start=1):
                original_filename = _safe_filename(str(file["filename"]))
                filename = f"document-{index:03d}.pdf"
                content = bytes(file.get("content") or b"")
                triage = triage_pdf_upload(original_filename, content, content_type=str(file.get("content_type") or "application/pdf"))
                if triage["extraction_status"] == "blocked_page_limit":
                    self.send_error(HTTPStatus.BAD_REQUEST, f"{original_filename} exceeds the {MAX_PUBLIC_PDF_PAGES}-page local quick-check limit")
                    return
                saved_path = upload_dir / filename
                saved_path.write_bytes(content)
                document_type = fields.get("document_type") or original_filename.rsplit(".", 1)[0].replace("-", " ").replace("_", " ")
                relative_path = saved_path.relative_to(repo_root).as_posix()
                saved_files.append(
                    {
                        "filename": filename,
                        "original_filename": original_filename,
                        "relative_path": relative_path,
                        "content_type": file.get("content_type") or "application/pdf",
                        "size_bytes": saved_path.stat().st_size,
                        "sha256": triage["sha256"],
                        "extraction_status": triage["extraction_status"],
                        "extraction_confidence": triage["extraction_confidence"],
                        "has_native_text": triage["has_native_text"],
                        "ocr_recommended": triage["ocr_recommended"],
                        "user_confirmation_required": True,
                        "expires_at": expires_at,
                    }
                )
                evidence_rows.append(
                    {
                        "evidence_id": f"evidence-{packet_id}-public-upload-{index}",
                        "packet_id": packet_id,
                        "organization_id": packet_org_id(packet),
                        "title": f"Uploaded PDF - {filename}",
                        "description": "Public quick-check PDF uploaded for draft evidence extraction.",
                        "evidence_type": "customer_uploaded_document",
                        "document_type": document_type,
                        "source_url": "",
                        "file_path": relative_path,
                        "source_owner": fields.get("exporter_name") or "public quick-check user",
                        "uploaded_by": "public_quick_check",
                        "created_at": now.isoformat(),
                        "accessed_at": now.isoformat(),
                        "last_verified_at": "",
                        "expires_at": expires_at,
                        "content_hash": triage["sha256"],
                        "original_filename": original_filename,
                        "storage_status": "quarantined_local_generated_name",
                        "direct_file_serving": False,
                        "page_count_estimate": triage["page_count_estimate"],
                        "extraction_status": triage["extraction_status"],
                        "extraction_confidence": triage["extraction_confidence"],
                        "has_native_text": triage["has_native_text"],
                        "ocr_recommended": triage["ocr_recommended"],
                        "native_text_excerpt": triage["native_text_excerpt"],
                        "user_confirmation_required": True,
                        "user_confirmed_at": "",
                        "rights_status": "unknown",
                        "freshness_status": "needs_current_refresh_before_claims",
                        "claim_supported": "Document was provided for draft readiness review.",
                        "claim_boundary": "Uploaded document metadata supports only draft review until qualified review and source freshness exist.",
                        "sensitivity_level": "confidential",
                        "ai_processing_mode": "redacted",
                        "ai_processing_permission": "redacted",
                        "ai_processing_allowed": True,
                        "redaction_required": True,
                        "review_required": True,
                        "human_review_status": "not_reviewed",
                        "extracted_fields": {
                            "document_type": document_type,
                            "filename": filename,
                            "original_filename": original_filename,
                            "product": packet.get("product_name"),
                            "supplier_or_exporter": packet.get("exporter_name") or packet.get("supplier_name"),
                            "buyer_or_importer": packet.get("buyer_name") or packet.get("importer_name"),
                            "origin_country": packet.get("origin_country"),
                            "destination_country": packet.get("destination_country"),
                            "hs_code": packet.get("hs_code_value"),
                            "expiry_date": "not_extracted",
                            "signatures_or_stamps": "not_extracted_in_local_quick_check",
                        },
                    }
                )
            packets, current_evidence = _load_mutable_customer_rows(repo_root)
            packets = [row for row in packets if str(row.get("packet_id")) != packet_id]
            current_evidence = [row for row in current_evidence if str(row.get("packet_id")) != packet_id]
            packets.append(packet)
            current_evidence.extend(evidence_rows)
            rebuilt = _write_customer_workflow(repo_root, packets, current_evidence)
            manifest_path = _public_upload_manifest_path(repo_root)
            manifest = {"status": "public_upload_manifest_ready", "packets": []}
            if manifest_path.exists():
                manifest = _load_json(manifest_path)
            manifest.setdefault("packets", [])
            manifest["packets"] = [row for row in manifest["packets"] if str(row.get("packet_id")) != packet_id]
            manifest["packets"].append(
                {
                    "packet_id": packet_id,
                    "created_at": now.isoformat(),
                    "expires_at": expires_at,
                    "file_count": len(saved_files),
                    "files": saved_files,
                    "delete_route": f"/api/public/packets/{packet_id}/delete-files",
                    "retention_notice": "Public quick-check uploads are local draft artifacts and should be deleted or expired after processing.",
                }
            )
            write_json(manifest, manifest_path)
            write_runtime_artifacts(repo_root, rebuilt)
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/public/packets/{packet_id}/result")
            self.end_headers()

        def _handle_public_packet_post(self, path: str) -> None:
            suffix = path.removeprefix("/api/public/packets/").strip("/")
            parts = suffix.split("/")
            packet_id = parts[0]
            action = "/".join(parts[1:])
            packet = self._public_packet(packet_id)
            if packet is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                return
            if action == "delete-files":
                upload_dir = repo_root / "system_review_graph" / "public_uploads" / packet_id
                if upload_dir.exists():
                    shutil.rmtree(upload_dir)
                manifest_path = _public_upload_manifest_path(repo_root)
                if manifest_path.exists():
                    manifest = _load_json(manifest_path)
                    manifest["packets"] = [
                        {**row, "deleted_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "files": []}
                        if str(row.get("packet_id")) == packet_id
                        else row
                        for row in manifest.get("packets", [])
                    ]
                    write_json(manifest, manifest_path)
                self._send_json({"status": "public_upload_files_deleted", "packet_id": packet_id})
                return
            if action == "refresh-official-sources":
                packets, evidence_rows = _load_mutable_customer_rows(repo_root)
                evidence_rows, refresh_report = refresh_packet_sources(
                    packet_id=packet_id,
                    evidence_items=evidence_rows,
                    actor="public_quick_check",
                )
                write_json(refresh_report, repo_root / "system_review_graph" / f"source_refresh_report_{packet_id}.json")
                _write_customer_workflow(repo_root, packets, evidence_rows)
                self._send_json(refresh_report)
                return
            if action == "confirm":
                fields = self._read_fields()
                if not _truthy_form_value(fields.get("fields_confirmed")):
                    self.send_error(HTTPStatus.BAD_REQUEST, "Field confirmation is required")
                    return
                if any(_contains_script(str(value)) for value in fields.values()):
                    self.send_error(HTTPStatus.BAD_REQUEST, "Confirmation contains unsafe HTML")
                    return
                now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
                packets, evidence_rows = _load_mutable_customer_rows(repo_root)
                updated_packets = []
                for row in packets:
                    if str(row.get("packet_id")) == packet_id:
                        updated_packets.append(
                            {
                                **row,
                                "product_name": fields.get("product_name") or row.get("product_name"),
                                "hs_code_value": fields.get("hs_code_value") or row.get("hs_code_value"),
                                "origin_country": fields.get("origin_country") or row.get("origin_country"),
                                "destination_country": fields.get("destination_country") or row.get("destination_country"),
                                "importer_of_record": fields.get("importer_of_record") or row.get("importer_of_record"),
                                "incoterms_if_known": fields.get("incoterms_if_known") or row.get("incoterms_if_known"),
                                "confirmation_status": "user_confirmed_draft_fields",
                                "confirmation_notes": fields.get("confirmation_notes") or "",
                                "confirmed_at": now,
                            }
                        )
                    else:
                        updated_packets.append(row)
                updated_evidence = [
                    {
                        **row,
                        "user_confirmed_at": now,
                        "confirmation_status": "user_confirmed_draft_fields",
                    }
                    if str(row.get("packet_id")) == packet_id
                    else row
                    for row in evidence_rows
                ]
                rebuilt = _write_customer_workflow(repo_root, updated_packets, updated_evidence)
                self._send_json({"status": "public_packet_fields_confirmed", "packet": _packet_lookup(rebuilt).get(packet_id)})
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Public packet action not found")

        def _handle_api_get(self, path: str, actor: dict[str, Any]) -> None:
            workflow = _customer_workflow(repo_root)
            runtime = _runtime_state(repo_root)
            packets = _visible_packets(workflow, actor)
            packet_lookup = {str(packet.get("packet_id")): packet for packet in workflow.get("packets", [])}

            if path in API_ROUTES:
                self._send_file(API_ROUTES[path], "application/json; charset=utf-8")
                return
            if path.startswith("/api/agent-tools/"):
                tool_name = path.removeprefix("/api/agent-tools/").strip("/")
                gateway = _load_graph_json(repo_root, "agent_api_gateway_contract.json")
                tool = next((row for row in gateway.get("tools", []) if row.get("tool") == tool_name), None)
                if tool is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Agent tool not found")
                    return
                self._send_json(
                    {
                        "status": "agent_tool_dry_run_ready",
                        "tool": tool,
                        "actor": actor.get("role"),
                        "external_effects_created": False,
                        "can_open_claim_gate": False,
                        "proof_boundary": gateway.get("proof_boundary"),
                    }
                )
                return
            if path == "/api/customer-workflow":
                self._send_json(workflow)
                return
            if path == "/api/auth/me":
                self._send_json({"authenticated": True, "user": actor})
                return
            if path == "/api/orgs/current":
                org = next((row for row in runtime["organizations"] if row["id"] == actor.get("organization_id")), {})
                self._send_json({"organization": org})
                return
            if path == "/api/orgs/current/members":
                members = [
                    row
                    for row in runtime["memberships"]
                    if row.get("organization_id") == actor.get("organization_id") or actor.get("role") == "admin"
                ]
                self._send_json({"members": members})
                return
            if path == "/api/orgs/current/ai-policy":
                policy = ai_policy_for_org(str(actor.get("organization_id") or "org-importer-demo"))
                self._send_json(
                    {
                        "policy": policy,
                        "model_endpoints": runtime.get("model_endpoints", []),
                        "router": runtime.get("ai_model_router", {}),
                        "manual_no_ai_workflow": runtime.get("manual_no_ai_workflow", {}),
                        "redaction_pipeline": runtime.get("redaction_pipeline", {}),
                        "proof_boundary": "Policy response exposes product controls only; it does not prove hosted privacy/legal approval.",
                    }
                )
                return
            if path == "/api/packets":
                self._send_json({"packets": packets})
                return
            if path == "/api/sources":
                self._send_json({"sources": workflow.get("official_sources", [])})
                return
            if path == "/api/audit":
                visible_ids = {str(packet.get("packet_id")) for packet in packets}
                events = [
                    row
                    for row in runtime.get("audit_events", [])
                    if actor.get("role") in {"admin", "operator"} or row.get("entity_id") in visible_ids
                ]
                self._send_json({"events": events})
                return
            if path == "/api/system-health":
                self._send_json(self._system_health_payload())
                return
            if path.startswith("/api/public/packets/") and "/reports/" in path:
                suffix = path.removeprefix("/api/public/packets/").strip("/")
                packet_id, _, report_file = suffix.partition("/reports/")
                report_type = report_file.removesuffix(".pdf")
                packet = packet_lookup.get(packet_id)
                if packet is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                    return
                title = {
                    "draft": "Draft Trade Readiness Report",
                    "buyer": "Buyer-Ready Packet",
                    "broker": "Broker Review Packet",
                    "missing": "Missing Evidence Checklist",
                    "operator": "Operator Review Report",
                    "expert": "Expert Review Packet",
                }.get(report_type, "Draft Trade Readiness Report")
                self._send_bytes(_report_pdf_bytes(title, _public_report_body(packet, report_type)), "application/pdf")
                return
            if path.startswith("/api/public/packets/") and path.endswith("/chatgpt-safe-summary"):
                packet_id = path.removeprefix("/api/public/packets/").removesuffix("/chatgpt-safe-summary").strip("/")
                packet = packet_lookup.get(packet_id)
                if packet is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                    return
                self._send_json(_chatgpt_safe_summary(packet))
                return
            if path.startswith("/api/external-review/"):
                token = path.removeprefix("/api/external-review/").strip("/")
                request = next((row for row in runtime["review_requests"] if row.get("token") == token), None)
                if request is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Review token not found")
                    return
                packet = packet_lookup.get(str(request["packet_id"]))
                self._send_json({"review_request": request, "packet": packet})
                return
            if path.startswith("/api/reports/") and path.endswith("/download"):
                report_id = path.removeprefix("/api/reports/").removesuffix("/download").strip("/")
                report = next((row for row in runtime["report_exports"] if row.get("id") == report_id), None)
                if report is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Report not found")
                    return
                packet = packet_lookup.get(str(report.get("packet_id")))
                if packet is None or not can_access_packet(actor, packet):
                    self.send_error(HTTPStatus.FORBIDDEN, "Report outside this organization")
                    return
                if report.get("format") == "pdf":
                    body = f"{packet.get('packet_name')} - {packet.get('customer_visible_status_label')}. {packet.get('safe_summary')}"
                    self._send_bytes(_report_pdf_bytes("Customer Readiness Report", body), "application/pdf")
                else:
                    self._send_json({"report": report, "packet": packet, "boundary": PRODUCT_BOUNDARY})
                return
            if path.startswith("/api/packets/"):
                parts = path.removeprefix("/api/packets/").strip("/").split("/")
                packet_id = parts[0]
                packet = packet_lookup.get(packet_id)
                if packet is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                    return
                if not can_access_packet(actor, packet):
                    self.send_error(HTTPStatus.FORBIDDEN, "Packet is outside this organization")
                    return
                view = parts[1] if len(parts) > 1 else ""
                if view == "":
                    self._send_json({"packet": packet})
                elif view == "evidence":
                    self._send_json({"evidence": packet.get("evidence_items", [])})
                elif view == "blockers":
                    self._send_json({"blockers": packet.get("blockers", []), "groups": packet.get("blocker_groups", [])})
                elif view == "claims":
                    self._send_json({"claims": [row for row in runtime["claims"] if row.get("packet_id") == packet_id]})
                elif view == "gates":
                    self._send_json({"gates": [row for row in runtime["claims"] if row.get("packet_id") == packet_id]})
                elif view == "ai-reviews":
                    self._send_json({"ai_reviews": [row for row in workflow.get("ai_review_runs", []) if row.get("packet_id") == packet_id]})
                elif view == "review-requests":
                    self._send_json({"review_requests": [row for row in runtime["review_requests"] if row.get("packet_id") == packet_id]})
                elif view == "reports":
                    self._send_json({"reports": [row for row in runtime["report_exports"] if row.get("packet_id") == packet_id]})
                elif view == "audit":
                    self._send_json({"events": [row for row in runtime["audit_events"] if row.get("entity_id") == packet_id]})
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, "Packet API route not found")
                return
            self.send_error(HTTPStatus.NOT_FOUND, "API route not found")

        def _handle_api_post(self, path: str, actor: dict[str, Any]) -> None:
            if path.startswith("/api/agent-tools/"):
                tool_name = path.removeprefix("/api/agent-tools/").strip("/")
                fields = self._read_fields()
                gateway = _load_graph_json(repo_root, "agent_api_gateway_contract.json")
                tool = next((row for row in gateway.get("tools", []) if row.get("tool") == tool_name), None)
                if tool is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Agent tool not found")
                    return
                self._send_json(
                    {
                        "status": "agent_tool_dry_run_executed",
                        "tool": tool_name,
                        "packet_id": fields.get("packet_id") or "packet-frozen-tuna-canada-001",
                        "dry_run": True,
                        "external_effects_created": False,
                        "credits_charged": 0,
                        "can_open_claim_gate": False,
                        "next_valid_move": "Use generated packet/report locally and collect human evidence before external claims.",
                    }
                )
                return
            if path == "/api/public/starter":
                self._handle_public_starter(actor)
                return
            if path == "/api/public/quick-check":
                self._handle_public_quick_check(actor)
                return
            if path.startswith("/api/public/packets/"):
                self._handle_public_packet_post(path)
                return
            fields = self._read_fields()
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat()
            if path in {"/api/auth/login", "/api/auth/signup"}:
                email = str(fields.get("email") or "customer@example.local")
                user = next((row for row in USERS if row["email"] == email), USERS[0])
                payload = {"authenticated": True, "user": user, "csrf_token": CSRF_TOKEN}
                data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Set-Cookie", f"isr_session={user['session_token']}; HttpOnly; SameSite=Lax")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return
            if path == "/api/auth/logout":
                self.send_response(HTTPStatus.NO_CONTENT)
                self.send_header("Set-Cookie", "isr_session=; Max-Age=0; HttpOnly; SameSite=Lax")
                self.end_headers()
                return
            if path == "/api/orgs/current/ai-policy/test-model-endpoint":
                policy = ai_policy_for_org(str(actor.get("organization_id") or "org-importer-demo"))
                mode = _valid_ai_mode(fields.get("mode") or policy.get("default_mode"))
                endpoint = endpoint_for_mode(mode, policy)
                allowed = mode in policy.get("allowed_modes", [])
                self._send_json(
                    {
                        "status": "endpoint_contract_ready" if allowed and (endpoint or mode in {"no_ai", "metadata_only", "on_prem_manual"}) else "endpoint_contract_blocked",
                        "mode": mode,
                        "allowed_by_policy": allowed,
                        "endpoint": endpoint or {},
                        "live_call_made": False,
                        "next_valid_move": "Configure and test real provider credentials in staging before hosted customer use.",
                    }
                )
                return
            if path == "/api/packets":
                packet = packet_from_submission({**fields, "organization_id": actor.get("organization_id")})
                evidence = evidence_from_submission(packet)
                packets, evidence_rows = _load_mutable_customer_rows(repo_root)
                packets.append(packet)
                evidence_rows.append(evidence)
                _write_customer_workflow(repo_root, packets, evidence_rows)
                self._send_json({"packet": packet, "next": f"/packets/{packet['packet_id']}"})
                return
            if path.startswith("/api/external-review/") and path.endswith("/findings"):
                token = path.removeprefix("/api/external-review/").removesuffix("/findings").strip("/")
                self._record_review_finding(token, fields, now)
                return
            if path.startswith("/api/packets/"):
                parts = path.removeprefix("/api/packets/").strip("/").split("/")
                packet_id = parts[0]
                action = parts[1] if len(parts) > 1 else ""
                workflow = _customer_workflow(repo_root)
                packet = _packet_lookup(workflow).get(packet_id)
                if packet is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                    return
                if not can_access_packet(actor, packet):
                    self.send_error(HTTPStatus.FORBIDDEN, "Packet is outside this organization")
                    return
                if action == "evidence":
                    if fields.get("evidence_type") not in ALLOWED_EVIDENCE_TYPES:
                        self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported evidence type")
                        return
                    if any(_contains_script(str(value)) for value in fields.values()):
                        self.send_error(HTTPStatus.BAD_REQUEST, "Evidence metadata contains unsafe HTML")
                        return
                    ai_fields = _evidence_ai_fields(fields)
                    packets, evidence_rows = _load_mutable_customer_rows(repo_root)
                    evidence_rows.append(
                        {
                            "evidence_id": f"evidence-{packet_id}-api-{len(evidence_rows) + 1}",
                            "packet_id": packet_id,
                            "organization_id": packet_org_id(packet),
                            "title": fields.get("title") or fields.get("claim_supported") or "Customer uploaded evidence",
                            "description": fields.get("description") or "",
                            "evidence_type": fields.get("evidence_type"),
                            "source_url": fields.get("source_url") or "",
                            "source_owner": actor.get("email"),
                            "uploaded_by": actor.get("id"),
                            "created_at": now,
                            "rights_status": "unknown",
                            "freshness_status": "needs_current_refresh_before_claims",
                            "claim_supported": fields.get("claim_supported") or "Customer-uploaded evidence.",
                            "claim_boundary": "Customer-uploaded evidence is internal review material until refreshed and reviewed.",
                            "review_required": True,
                            "human_review_status": "not_reviewed",
                            **ai_fields,
                        }
                    )
                    _write_customer_workflow(repo_root, packets, evidence_rows)
                    self._send_json({"status": "evidence_uploaded", "packet_id": packet_id})
                    return
                if action == "refresh-sources":
                    packets, evidence_rows = _load_mutable_customer_rows(repo_root)
                    evidence_rows, refresh_report = refresh_packet_sources(packet_id=packet_id, evidence_items=evidence_rows, actor=str(actor.get("id")))
                    write_json(refresh_report, repo_root / "system_review_graph" / f"source_refresh_report_{packet_id}.json")
                    _write_customer_workflow(repo_root, packets, evidence_rows)
                    self._send_json(refresh_report)
                    return
                if action == "ai-reviews" or action == "analyze":
                    run = build_ai_review_run(workflow, packet_id)
                    _append_json_list(repo_root / "system_review_graph" / "customer_ai_review_runs.json", run)
                    self._send_json(run)
                    return
                if action == "delete-request":
                    self._append_audit(
                        {
                            "event_id": f"{packet_id}:data-deletion-requested:{now}",
                            "packet_id": packet_id,
                            "organization_id": packet_org_id(packet),
                            "event_type": "data_deletion_requested",
                            "actor_user_id": actor.get("id"),
                            "created_at": now,
                        }
                    )
                    self._send_json({"status": "deletion_request_recorded", "packet_id": packet_id})
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Packet API action not found")
                return
            self.send_error(HTTPStatus.NOT_FOUND, "API route not found")

        def _record_review_finding(self, token: str, fields: dict[str, Any], now: str) -> None:
            workflow = _customer_workflow(repo_root)
            runtime = build_runtime_state(workflow)
            request = next((row for row in runtime["review_requests"] if row.get("token") == token), None)
            if request is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Review token not found")
                return
            packet_id = str(request["packet_id"])
            finding = {
                "id": f"finding-{packet_id}-{now.replace(':', '').replace('+', 'Z')}",
                "review_request_id": request["id"],
                "packet_id": packet_id,
                "reviewer_name": request.get("reviewer_name"),
                "reviewer_role": request.get("reviewer_role"),
                "reviewer_organization": "External scoped reviewer",
                "finding_type": request.get("review_type"),
                "decision": fields.get("decision") or "needs_more_evidence",
                "scope": request.get("scope"),
                "conditions": fields.get("conditions") or "",
                "blocked_claims": ["tariff_classification_claim", "food_safety_claim"],
                "approved_claims_scoped": [] if fields.get("decision") != "scoped_review_complete" else ["allowed_scoped_human_review"],
                "evidence_reviewed_ids": [item.strip() for item in str(fields.get("evidence_reviewed_ids") or "").split(",") if item.strip()],
                "notes": fields.get("notes") or "",
                "created_at": now,
                "expires_at": request.get("due_at"),
            }
            _append_json_list(repo_root / "system_review_graph" / "human_review_findings.json", finding)
            self._append_audit(
                {
                    "event_id": f"{packet_id}:review-finding-submitted:{now}",
                    "packet_id": packet_id,
                    "event_type": "review_finding_submitted",
                    "entity_type": "HumanReviewFinding",
                    "entity_id": finding["id"],
                    "after_json": finding,
                    "created_at": now,
                }
            )
            self._send_json({"status": "finding_recorded_scoped", "finding": finding})

        def _handle_review_submit(self, token: str) -> None:
            fields = self._read_fields()
            if fields.get("csrf_token") != CSRF_TOKEN:
                self.send_error(HTTPStatus.FORBIDDEN, "Invalid CSRF token")
                return
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat()
            self._record_review_finding(token, fields, now)

        def _handle_packet_action(self, packet_id: str) -> None:
            actor = _actor_from_headers(self.headers)
            length = int(self.headers.get("Content-Length") or 0)
            if length > 65536:
                self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Packet action too large")
                return
            raw = self.rfile.read(length).decode("utf-8")
            fields = {key: values[-1] for key, values in parse_qs(raw, keep_blank_values=True).items()}
            if fields.get("csrf_token") != CSRF_TOKEN:
                self.send_error(HTTPStatus.FORBIDDEN, "Invalid CSRF token")
                return
            action = str(fields.get("action") or "")
            packets, evidence_rows = _load_mutable_customer_rows(repo_root)
            workflow_for_access = build_customer_workflow(
                source_packets=packets,
                evidence_items=evidence_rows,
                official_sources=_load_json(repo_root / "data" / "official_source_registry.json"),
            )
            packet_for_access = _packet_lookup(workflow_for_access).get(packet_id)
            if packet_for_access is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Packet not found")
                return
            if not can_access_packet(actor, packet_for_access):
                self.send_error(HTTPStatus.FORBIDDEN, "Packet is outside this organization")
                return
            redirect = f"/packets/{packet_id}"
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
                redirect = f"/packets/{packet_id}/evidence"
            elif action == "upload_evidence":
                evidence_type = fields.get("evidence_type") or "customer_uploaded_reference"
                if evidence_type not in ALLOWED_EVIDENCE_TYPES:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported evidence type")
                    return
                if any(_contains_script(str(value)) for value in fields.values()):
                    self.send_error(HTTPStatus.BAD_REQUEST, "Evidence metadata contains unsafe HTML")
                    return
                ai_fields = _evidence_ai_fields(fields)
                evidence_rows.append(
                    {
                        "evidence_id": f"evidence-{packet_id}-customer-{len(evidence_rows) + 1}",
                        "packet_id": packet_id,
                        "organization_id": packet_org_id(packet_for_access),
                        "title": fields.get("title") or fields.get("claim_supported") or "Customer uploaded evidence",
                        "description": fields.get("description") or "",
                        "evidence_type": evidence_type,
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
                        **ai_fields,
                    }
                )
                _append_json_list(
                    action_log,
                    {"event_id": f"{packet_id}:upload-evidence:{now}", "packet_id": packet_id, "event_type": "upload_evidence", "created_at": now},
                )
                redirect = f"/packets/{packet_id}/evidence"
            elif action == "run_ai_review":
                workflow = build_customer_workflow(
                    source_packets=packets,
                    evidence_items=evidence_rows,
                    official_sources=_load_json(repo_root / "data" / "official_source_registry.json"),
                )
                run = build_ai_review_run(workflow, packet_id)
                _append_json_list(repo_root / "system_review_graph" / "customer_ai_review_runs.json", run)
                redirect = f"/packets/{packet_id}/ai-reviews"
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
                redirect = f"/packets/{packet_id}/expert-review-packet"
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
                redirect = f"/packets/{packet_id}/blockers"
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
                redirect = f"/packets/{packet_id}/blockers"
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

        def _send_bytes(self, data: bytes, content_type: str) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_scoped_file(self, base: Path, relative_path: str, content_type: str | None) -> None:
            if relative_path.startswith("public_uploads/") or "/public_uploads/" in relative_path:
                self.send_error(HTTPStatus.FORBIDDEN, "Public upload files are quarantined and not directly served")
                return
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

        def _send_packet_route(self, packet_id: str, view: str, actor: dict[str, Any]) -> None:
            workflow = _customer_workflow(repo_root)
            packet = _packet_lookup(workflow).get(packet_id)
            if packet is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Source packet not found")
                return
            if not can_access_packet(actor, packet):
                self.send_error(HTTPStatus.FORBIDDEN, "Packet is outside this organization")
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
            if view == "ai-reviews":
                self._send_html(_render_packet_ai_reviews(workflow, packet))
                return
            if view == "reviews":
                self._send_html(_render_packet_reviews(workflow, packet))
                return
            if view == "reports":
                self._send_html(_render_packet_reports(workflow, packet))
                return
            if view == "source-monitoring":
                self._send_html(_render_source_monitoring(repo_root, workflow, packet))
                return
            if view == "safe-summary":
                self._send_html(_render_safe_summary_page(packet))
                return
            if view == "settings":
                self._send_html(_render_packet_settings(packet))
                return
            if view == "expert-review-packet":
                self._send_html(_render_expert_packet(workflow, packet))
                return
            if view == "export":
                self._send_json(
                    {
                        "packet_id": packet.get("packet_id"),
                        "summary": packet.get("safe_summary"),
                        "status": packet.get("customer_visible_status_label"),
                        "customer_stage_status": workflow.get("customer_stage_status"),
                        "private_beta_status": workflow.get("private_beta_readiness", {}).get("status"),
                        "evidence_summary": packet.get("evidence_summary"),
                        "missing_evidence": packet.get("evidence_summary", {}).get("missing_items", []),
                        "blocker_groups": packet.get("blocker_groups", []),
                        "top_blockers": packet.get("top_blockers", []),
                        "blocked_claims": packet.get("blocked_claims_display"),
                        "next_valid_moves": [row.get("next_valid_move") for row in packet.get("blocker_groups", [])],
                        "ai_review_runs": workflow.get("ai_review_runs", []),
                        "private_beta_readiness": workflow.get("private_beta_readiness"),
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
