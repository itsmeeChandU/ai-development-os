"""Render a static operator dashboard for source readiness."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from .source_packet_workflow import CUSTOMER_PROTOTYPE_STATUS, SAFE_DISPLAY_STATUS


def _rows(blockers: list[dict[str, Any]]) -> str:
    if not blockers:
        return "<tr><td colspan='5'>No blockers.</td></tr>"
    return "\n".join(
        "<tr>"
        f"<td>{escape(str(row['id']))}</td>"
        f"<td>{escape(str(row['module']))}</td>"
        f"<td>{escape(str(row['owner']))}</td>"
        f"<td>{escape(str(row['issue']))}</td>"
        f"<td>{escape(str(row['next_valid_move']))}</td>"
        "</tr>"
        for row in blockers
    )


def _display_value(value: Any) -> str:
    return str(value).replace("_", " ")


def _friendly_status(value: Any) -> str:
    if value == "ready_with_external_gates":
        return SAFE_DISPLAY_STATUS
    if value == "operator_workflow_ready_internal":
        return "Operator workbench usable for internal review"
    return _display_value(value)


def _work_queue_rows(workflow: dict[str, Any] | None) -> str:
    if not workflow:
        return "<tr><td colspan='6'>No operator workflow report found.</td></tr>"
    queue = workflow.get("work_queue", [])
    if not queue:
        return "<tr><td colspan='6'>No operator queue rows.</td></tr>"
    rows = []
    for row in queue[:18]:
        refs = row.get("canadian_tool_refs") or []
        ref_html = ", ".join(
            f"<a href='{escape(str(ref.get('source_url')))}'>{escape(str(ref.get('id')))}</a>"
            for ref in refs[:4]
        )
        if len(refs) > 4:
            ref_html += f" +{len(refs) - 4}"
        rows.append(
            "<tr>"
            f"<td><strong>{escape(str(row.get('priority')))}</strong></td>"
            f"<td>{escape(_display_value(row.get('type')))}</td>"
            f"<td>{escape(str(row.get('owner')))}</td>"
            f"<td>{escape(_display_value(row.get('status')))}</td>"
            f"<td>{escape(str(row.get('next_valid_move')))}</td>"
            f"<td>{ref_html or 'n/a'}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _render_operator_workflow(workflow: dict[str, Any] | None) -> str:
    status = "missing workflow"
    count = 0
    can_use = "unknown"
    boundary = "Operator workflow report is required for day-to-day use."
    if workflow:
        status = str(workflow.get("display_status") or _friendly_status(workflow.get("status") or status))
        count = int(workflow.get("work_queue_count") or 0)
        can_use = "yes" if workflow.get("operator_can_use_now") else "no"
        boundary = str(workflow.get("proof_boundary") or boundary)
    return f"""
  <section class="operator-workflow" aria-labelledby="operator-workflow-title">
    <div class="section-heading">
      <div>
        <h2 id="operator-workflow-title">Operator Work Queue</h2>
        <p>{escape(boundary)}</p>
      </div>
      <div class="workflow-summary">
        <span>{escape(status)}</span>
        <strong>{count}</strong>
        <em>usable now: {escape(can_use)}</em>
      </div>
    </div>
    <table>
      <thead><tr><th>Priority</th><th>Type</th><th>Owner</th><th>Status</th><th>Next Valid Move</th><th>Canada Tools</th></tr></thead>
      <tbody>{_work_queue_rows(workflow)}</tbody>
    </table>
  </section>
"""


def _screenshot_cards(manifest: dict[str, Any] | None) -> str:
    if not manifest:
        return """
      <div class="empty-state">
        <div class="empty-title">No screenshot manifest found</div>
        <p>The current proof run did not publish operator screenshot metadata.</p>
      </div>
"""
    screenshots = manifest.get("screenshots", [])
    if not screenshots:
        return f"""
      <div class="empty-state">
        <div class="empty-title">No operator screenshots in this proof run</div>
        <p>{escape(str(manifest.get("next_valid_move", "Generate screenshots and rerun the product check.")))}</p>
      </div>
"""
    cards = []
    for row in screenshots:
        title = escape(str(row.get("title") or row.get("file_name") or "Operator screenshot"))
        src = escape(str(row.get("dashboard_src") or row.get("artifact_path") or ""))
        artifact_path = escape(str(row.get("artifact_path") or ""))
        media_type = escape(str(row.get("media_type") or "image"))
        captured_at = escape(str(row.get("captured_at") or "unknown"))
        sha = escape(str(row.get("sha256") or "")[:12])
        size = escape(str(row.get("size_bytes") or 0))
        boundary = escape(str(row.get("claim_boundary") or "Visual review aid only."))
        cards.append(
            "<article class='screenshot-card'>"
            f"<a href='{src}' aria-label='Open {title}'><img src='{src}' alt='{title}' loading='lazy'></a>"
            "<div class='screenshot-body'>"
            f"<h3>{title}</h3>"
            f"<p class='path'>{artifact_path}</p>"
            "<dl>"
            f"<div><dt>Captured</dt><dd>{captured_at}</dd></div>"
            f"<div><dt>Media</dt><dd>{media_type}</dd></div>"
            f"<div><dt>Bytes</dt><dd>{size}</dd></div>"
            f"<div><dt>SHA</dt><dd>{sha}</dd></div>"
            "</dl>"
            f"<p class='boundary'>{boundary}</p>"
            "</div>"
            "</article>"
        )
    return "\n".join(cards)


def _render_screenshot_gallery(manifest: dict[str, Any] | None) -> str:
    status = "missing manifest"
    count = 0
    boundary = "Screenshot artifacts are visual review aids only."
    if manifest:
        status = _display_value(manifest.get("status") or status)
        count = int(manifest.get("screenshot_count") or 0)
        boundary = str(manifest.get("proof_boundary") or boundary)
    return f"""
  <section class="screenshots" aria-labelledby="operator-screenshots-title">
    <div class="section-heading">
      <div>
        <h2 id="operator-screenshots-title">Operator Screenshots</h2>
        <p>{escape(boundary)}</p>
      </div>
      <div class="screenshot-summary">
        <span>{escape(status)}</span>
        <strong>{count}</strong>
      </div>
    </div>
    <div class="screenshot-grid">
{_screenshot_cards(manifest)}
    </div>
  </section>
"""


def _customer_packet_rows(customer_workflow: dict[str, Any] | None) -> str:
    if not customer_workflow:
        return "<tr><td colspan='6'>No customer source-packet workflow generated.</td></tr>"
    packets = customer_workflow.get("packets", [])
    if not packets:
        return "<tr><td colspan='6'>No customer source packets found.</td></tr>"
    rows = []
    for packet in packets:
        rows.append(
            "<tr>"
            f"<td><a href='/packets/{escape(str(packet.get('packet_id')))}'>{escape(str(packet.get('packet_name')))}</a></td>"
            f"<td>{escape(str(packet.get('product_name')))}</td>"
            f"<td>{escape(str(packet.get('customer_visible_status_label')))}</td>"
            f"<td>{escape(str((packet.get('evidence_summary') or {}).get('summary')))}</td>"
            f"<td>{escape(str(packet.get('blocker_count')))}</td>"
            f"<td>{escape(str(packet.get('next_valid_move')))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _render_customer_workflow(customer_workflow: dict[str, Any] | None) -> str:
    status = "missing customer workflow"
    count = 0
    boundary = "Customer source-packet workflow has not been generated."
    if customer_workflow:
        status = str(customer_workflow.get("display_status") or customer_workflow.get("status") or status)
        count = int(customer_workflow.get("packet_count") or 0)
        boundary = str(customer_workflow.get("proof_boundary") or boundary)
    return f"""
  <section class="customer-workflow" aria-labelledby="customer-workflow-title">
    <div class="section-heading">
      <div>
        <h2 id="customer-workflow-title">Customer Source Packet Workflow</h2>
        <p>{escape(boundary)}</p>
      </div>
      <div class="workflow-summary">
        <span>{escape(status)}</span>
        <strong>{count}</strong>
        <em><a href="/packets/new">new packet</a></em>
      </div>
    </div>
    <table>
      <thead><tr><th>Packet</th><th>Product</th><th>Status</th><th>Evidence</th><th>Blockers</th><th>Next Valid Move</th></tr></thead>
      <tbody>{_customer_packet_rows(customer_workflow)}</tbody>
    </table>
  </section>
"""


def _top_blocker_cards(customer_workflow: dict[str, Any] | None) -> str:
    if not customer_workflow:
        return ""
    groups = customer_workflow.get("top_blockers", [])
    cards = []
    for group in groups[:6]:
        cards.append(
            "<article class='blocker-card'>"
            f"<span>{escape(str(group.get('stage')))}</span>"
            f"<h3>{escape(str(group.get('title')))}</h3>"
            f"<p>{escape(str(group.get('next_valid_move')))}</p>"
            "</article>"
        )
    return "\n".join(cards)


def _render_private_beta_path(customer_workflow: dict[str, Any] | None) -> str:
    if not customer_workflow:
        return ""
    private_beta = customer_workflow.get("private_beta_readiness", {})
    ready = "".join(f"<li>{escape(str(row))}</li>" for row in private_beta.get("ready", []))
    blocked = _top_blocker_cards(customer_workflow)
    return f"""
  <section class="private-beta" aria-labelledby="private-beta-title">
    <div class="section-heading">
      <div>
        <h2 id="private-beta-title">Path To Private Beta</h2>
        <p>{escape(str(private_beta.get("next_valid_move") or "Private beta is blocked until evidence and controls are complete."))}</p>
      </div>
      <div class="workflow-summary">
        <span>{escape(str(private_beta.get("display_status") or "Private beta blocked"))}</span>
        <strong>{escape(str(len(private_beta.get("blocked", []))))}</strong>
        <em>blocked gates</em>
      </div>
    </div>
    <div class="blocker-grid">{blocked}</div>
    <h3>Ready</h3>
    <ul>{ready}</ul>
  </section>
"""


def render_dashboard(
    readiness: dict[str, Any],
    external: dict[str, Any],
    screenshot_manifest: dict[str, Any] | None = None,
    operator_workflow: dict[str, Any] | None = None,
    customer_workflow: dict[str, Any] | None = None,
) -> str:
    readiness_blockers = readiness.get("blockers", [])
    external_blockers = external.get("blockers", [])
    total_blockers = len(readiness_blockers) + len(external_blockers)
    sources = "\n".join(
        "<li>"
        f"<a href='{escape(str(row['url']))}'>{escape(str(row['name']))}</a>"
        f" - accessed {escape(str(row['accessed_at']))}; {escape(str(row['claim_boundary']))}"
        "</li>"
        for row in external.get("official_sources", [])
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Importer Source Readiness Copilot</title>
  <style>
    :root {{ color-scheme: light dark; --ink: #172026; --muted: #52616f; --line: #ccd5df; --panel: #f7f9fb; --panel-strong: #eef3f7; --warn: #fff7df; --warn-line: #ead28a; --danger: #9f2f2f; --accent: #1d6b65; --accent-soft: #dff3ef; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: var(--ink); background: #fbfcfd; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px; }}
    h1, h2, h3 {{ margin: 0 0 8px; }}
    h1 {{ font-size: 34px; line-height: 1.1; }}
    h2 {{ font-size: 22px; margin-top: 30px; }}
    h3 {{ font-size: 16px; }}
    p {{ line-height: 1.5; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 20px 0; }}
    .metric {{ border: 1px solid var(--line); border-radius: 6px; padding: 14px; background: var(--panel); }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .value {{ font-size: 20px; line-height: 1.2; font-weight: 700; margin-top: 6px; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; margin: 14px 0 28px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #dce3ea; padding: 9px; vertical-align: top; }}
    th {{ background: var(--panel-strong); }}
    .closed {{ color: var(--danger); font-weight: 700; }}
    .note {{ background: var(--warn); border: 1px solid var(--warn-line); padding: 12px; border-radius: 6px; }}
    .section-heading {{ display: flex; justify-content: space-between; gap: 18px; align-items: start; margin-top: 28px; }}
    .section-heading p {{ color: var(--muted); margin: 0; max-width: 820px; }}
    .screenshot-summary {{ min-width: 132px; border: 1px solid var(--line); background: #fff; border-radius: 6px; padding: 10px 12px; text-align: right; }}
    .screenshot-summary span {{ display: block; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
    .screenshot-summary strong {{ display: block; font-size: 28px; }}
    .workflow-summary {{ min-width: 158px; border: 1px solid var(--line); background: var(--accent-soft); border-radius: 6px; padding: 10px 12px; text-align: right; }}
    .workflow-summary span {{ display: block; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
    .workflow-summary strong {{ display: block; font-size: 28px; }}
    .workflow-summary em {{ display: block; color: var(--accent); font-size: 12px; font-style: normal; font-weight: 700; }}
    .blocker-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }}
    .blocker-card {{ border: 1px solid var(--line); border-left: 4px solid var(--danger); border-radius: 6px; background: #fff; padding: 12px; }}
    .blocker-card span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 4px; }}
    .blocker-card p {{ color: var(--muted); margin: 0; }}
    .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-top: 16px; }}
    .screenshot-card {{ border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: #fff; }}
    .screenshot-card img {{ display: block; width: 100%; aspect-ratio: 16 / 10; object-fit: contain; background: #111820; border-bottom: 1px solid var(--line); }}
    .screenshot-body {{ padding: 13px; }}
    .path {{ color: var(--muted); font-size: 12px; margin: 0 0 10px; overflow-wrap: anywhere; }}
    dl {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 0 0 10px; }}
    dt {{ color: var(--muted); font-size: 11px; text-transform: uppercase; }}
    dd {{ margin: 1px 0 0; font-size: 12px; overflow-wrap: anywhere; }}
    .boundary {{ border-top: 1px solid #e6ebf0; color: var(--muted); font-size: 12px; margin: 10px 0 0; padding-top: 10px; }}
    .empty-state {{ grid-column: 1 / -1; border: 1px dashed var(--line); border-radius: 6px; padding: 18px; background: #fff; }}
    .empty-title {{ font-weight: 700; margin-bottom: 4px; }}
    @media (max-width: 860px) {{
      main {{ padding: 22px; }}
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .section-heading {{ display: block; }}
      .screenshot-summary {{ text-align: left; margin-top: 12px; }}
    }}
    @media (max-width: 560px) {{
      .grid {{ grid-template-columns: 1fr; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>Importer Source Readiness Copilot</h1>
  <p class="note">Local product logic is complete. External claims remain closed until the listed evidence gates are satisfied by dated official sources, contracts, buyers, and qualified review.</p>
  <section class="grid">
    <div class="metric"><div class="label">Status</div><div class="value">{escape(SAFE_DISPLAY_STATUS)}</div></div>
    <div class="metric"><div class="label">Current Product Stage</div><div class="value">{escape(CUSTOMER_PROTOTYPE_STATUS)}</div></div>
    <div class="metric"><div class="label">Source rows</div><div class="value">{escape(str(readiness["row_count"]))}</div></div>
    <div class="metric"><div class="label">Total blockers</div><div class="value">{total_blockers}</div></div>
  </section>
{_render_customer_workflow(customer_workflow)}
{_render_private_beta_path(customer_workflow)}
{_render_operator_workflow(operator_workflow)}
{_render_screenshot_gallery(screenshot_manifest)}
  <h2>Readiness Blockers</h2>
  <table>
    <thead><tr><th>ID</th><th>Module</th><th>Owner</th><th>Issue</th><th>Next Valid Move</th></tr></thead>
    <tbody>{_rows(readiness_blockers)}</tbody>
  </table>
  <h2>External Gate Blockers</h2>
  <table>
    <thead><tr><th>ID</th><th>Module</th><th>Owner</th><th>Issue</th><th>Next Valid Move</th></tr></thead>
    <tbody>{_rows(external_blockers)}</tbody>
  </table>
  <h2>Official Source Registry</h2>
  <ul>{sources}</ul>
  <h2>Unsafe Gates</h2>
  <p class="closed">All unsafe gates are closed: no external sends, paid actions, customs/tariff claims, import/export advice claims, or supplier recommendations were made.</p>
</main>
</body>
</html>
"""


def write_dashboard(
    readiness: dict[str, Any],
    external: dict[str, Any],
    path: Path,
    screenshot_manifest: dict[str, Any] | None = None,
    operator_workflow: dict[str, Any] | None = None,
    customer_workflow: dict[str, Any] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_dashboard(readiness, external, screenshot_manifest, operator_workflow, customer_workflow),
        encoding="utf-8",
    )
    return path
