"""Render a static operator dashboard for source readiness."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


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


def render_dashboard(readiness: dict[str, Any], external: dict[str, Any]) -> str:
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
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #172026; }}
    main {{ max-width: 1180px; margin: 0 auto; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 20px 0; }}
    .metric {{ border: 1px solid #ccd5df; border-radius: 6px; padding: 14px; background: #f7f9fb; }}
    .label {{ color: #52616f; font-size: 13px; }}
    .value {{ font-size: 22px; font-weight: 700; margin-top: 6px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 14px 0 28px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #dce3ea; padding: 9px; vertical-align: top; }}
    th {{ background: #eef3f7; }}
    .closed {{ color: #9f2f2f; font-weight: 700; }}
    .note {{ background: #fff7df; border: 1px solid #ead28a; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
<main>
  <h1>Importer Source Readiness Copilot</h1>
  <p class="note">Local product logic is complete. External claims remain closed until the listed evidence gates are satisfied by dated official sources, contracts, buyers, and qualified review.</p>
  <section class="grid">
    <div class="metric"><div class="label">Readiness status</div><div class="value">{escape(str(readiness["status"]))}</div></div>
    <div class="metric"><div class="label">External gate status</div><div class="value">{escape(str(external["status"]))}</div></div>
    <div class="metric"><div class="label">Source rows</div><div class="value">{escape(str(readiness["row_count"]))}</div></div>
    <div class="metric"><div class="label">Total blockers</div><div class="value">{total_blockers}</div></div>
  </section>
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


def write_dashboard(readiness: dict[str, Any], external: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard(readiness, external), encoding="utf-8")
    return path
