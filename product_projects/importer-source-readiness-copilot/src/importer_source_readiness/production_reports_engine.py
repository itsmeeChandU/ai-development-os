"""Production reports and deliverables engine.

Phase 15 makes reports a first-class product surface. Reports are generated
from packet, evidence, source, claim-gate, score, and expert-review artifacts.
Every export keeps blocked claims visible and carries citations, version,
watermark, and review status.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_reports_engine_ready_cited_exports_blocked_claims_visible"
WATERMARK = "DRAFT - NOT APPROVAL"
REVIEW_STATUS = "not_reviewed"

REPORT_TYPES: tuple[dict[str, Any], ...] = (
    {
        "report_type": "starter_trade_readiness_packet",
        "title": "Starter Trade Readiness Packet",
        "audience": "beginner exporter or importer",
        "purpose": "Show the known product/lane context, missing fields, official source routes, and next safe move.",
        "packet_view": "starter_packet",
    },
    {
        "report_type": "market_opportunity_brief",
        "title": "Market Opportunity Brief",
        "audience": "exporter, operator, or advisor",
        "purpose": "Summarize source-routed market signals without demand, profitability, or buyer-validation claims.",
        "packet_view": "market_research_packet",
    },
    {
        "report_type": "buyer_ready_packet",
        "title": "Buyer-Ready Packet",
        "audience": "possible buyer, importer, or sales reviewer",
        "purpose": "Prepare buyer-facing context, questions, evidence level, and blocked buyer-validation language.",
        "packet_view": "buyer_ready_packet",
    },
    {
        "report_type": "supplier_document_request",
        "title": "Supplier Document Request",
        "audience": "supplier, sourcing operator, or supplier reviewer",
        "purpose": "List supplier evidence requested and separate collected evidence from supplier verification.",
        "packet_view": "supplier_request_packet",
    },
    {
        "report_type": "broker_review_packet",
        "title": "Broker Review Packet",
        "audience": "customs broker, trade reviewer, or freight reviewer",
        "purpose": "Package customs, tariff, CFIA, responsibility, and unresolved review questions for scoped human review.",
        "packet_view": "broker_review_packet",
    },
    {
        "report_type": "missing_evidence_report",
        "title": "Missing Evidence Report",
        "audience": "customer, operator, or reviewer",
        "purpose": "Show missing documents, missing confirmations, stale source evidence, and next collection steps.",
        "packet_view": "operator_packet",
    },
    {
        "report_type": "blocked_claims_report",
        "title": "Blocked Claims Report",
        "audience": "compliance reviewer, operator, or launch owner",
        "purpose": "List each blocked claim, why it is blocked, and what evidence or review is required.",
        "packet_view": "blocked_claims_packet",
    },
    {
        "report_type": "country_source_map",
        "title": "Country Source Map",
        "audience": "operator, advisor, or reviewer",
        "purpose": "Show country-pack coverage, source routes, refresh state, and claim boundaries.",
        "packet_view": "operator_packet",
    },
    {
        "report_type": "source_freshness_report",
        "title": "Source Freshness Report",
        "audience": "operator, source reviewer, or expert reviewer",
        "purpose": "Show source snapshot freshness, source lifecycle state, and packet stale-review needs.",
        "packet_view": "operator_packet",
    },
    {
        "report_type": "expert_review_summary",
        "title": "Expert Review Summary",
        "audience": "reviewer, operator, or launch owner",
        "purpose": "Summarize scoped reviewer lanes, pending findings, credential needs, and review gate impacts.",
        "packet_view": "broker_review_packet",
    },
    {
        "report_type": "executive_decision_report",
        "title": "Executive Decision Report",
        "audience": "founder, manager, advisor, or launch owner",
        "purpose": "Summarize scores, blockers, source/evidence state, external gates, and the next safe decision.",
        "packet_view": "executive_decision_packet",
    },
    {
        "report_type": "audit_export",
        "title": "Audit Export",
        "audience": "operator, compliance reviewer, or enterprise admin",
        "purpose": "Export report generation inputs, evidence citations, source citations, review status, and audit rows.",
        "packet_view": "operator_packet",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _packet_id(packet: dict[str, Any]) -> str:
    return str(packet.get("packet_id") or "packet-frozen-tuna-canada-001")


def _packets(repo_root: Path) -> list[dict[str, Any]]:
    customer = _load_json(repo_root / "system_review_graph" / "customer_readiness_report.json", {})
    packets = customer.get("packets", [])
    if packets:
        return packets
    return [{"packet_id": "packet-frozen-tuna-canada-001"}]


def _source_rows(repo_root: Path) -> list[dict[str, Any]]:
    anchors = _load_json(repo_root / "system_review_graph" / "production_research_anchors.json", {})
    sources = anchors.get("sources", anchors if isinstance(anchors, list) else [])
    registry = _load_json(repo_root / "data" / "official_source_registry.json", [])
    if isinstance(registry, dict):
        registry = registry.get("sources", [])
    rows = []
    seen: set[str] = set()
    for row in list(sources) + list(registry):
        source_id = str(row.get("id") or row.get("source_id") or "")
        if source_id and source_id not in seen:
            seen.add(source_id)
            rows.append(row)
    return rows


def _evidence_rows(repo_root: Path, packet: dict[str, Any]) -> list[dict[str, Any]]:
    packet_rows = packet.get("evidence_items", [])
    ledger = _load_json(repo_root / "system_review_graph" / "evidence_ledger.json", {})
    ledger_rows = ledger.get("rows", []) if isinstance(ledger, dict) else []
    rows = packet_rows or ledger_rows
    if rows:
        return rows
    return [{"evidence_id": f"evidence:{_packet_id(packet)}:context", "type": "user_input", "quality": "draft"}]


def _claim_rows(repo_root: Path, packet_id: str) -> list[dict[str, Any]]:
    claim_gate = _load_json(repo_root / "system_review_graph" / "production_evidence_claim_gate_manifest.json", {})
    rows = claim_gate.get("claim_gate_decisions", [])
    filtered = [row for row in rows if str(row.get("packet_id") or packet_id) == packet_id]
    return filtered or rows


def _score_rows(repo_root: Path, packet_id: str) -> list[dict[str, Any]]:
    scoring = _load_json(repo_root / "system_review_graph" / "production_decision_scoring_manifest.json", {})
    rows = scoring.get("decision_score_records", [])
    return [row for row in rows if str(row.get("packet_id") or packet_id) == packet_id] or rows


def _review_rows(repo_root: Path, packet_id: str) -> list[dict[str, Any]]:
    expert = _load_json(repo_root / "system_review_graph" / "production_expert_review_network_manifest.json", {})
    rows = expert.get("review_requests", [])
    return [row for row in rows if str(row.get("packet_id") or packet_id) == packet_id] or rows


def _source_citations(sources: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    citations = []
    for row in sources[:limit]:
        source_id = str(row.get("id") or row.get("source_id") or "")
        citations.append(
            {
                "source_id": source_id,
                "source_name": row.get("source_name") or row.get("name") or source_id,
                "url": row.get("url", ""),
                "checked_on": row.get("checked_on") or row.get("last_checked") or "",
                "claim_boundary": row.get("claim_boundary") or row.get("use_boundary") or "Reference source; current applicability needs review.",
            }
        )
    return citations


def _evidence_citations(evidence_rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    citations = []
    for row in evidence_rows[:limit]:
        evidence_id = str(row.get("evidence_id") or row.get("id") or row.get("source_id") or "")
        citations.append(
            {
                "evidence_id": evidence_id,
                "type": row.get("type") or row.get("evidence_type") or row.get("source_type") or "evidence",
                "provenance": row.get("provenance") or row.get("source") or row.get("quality") or "local_artifact",
                "freshness": row.get("freshness") or row.get("quality") or "unknown",
                "claim_boundary": row.get("claim_boundary") or "Evidence supports preparation only until confirmed and reviewed.",
            }
        )
    return citations


def _blocked_claims(claim_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in claim_rows:
        can_show = row.get("can_show_claim")
        level = row.get("claim_level")
        blocked = can_show is False or str(level or "").startswith("blocked") or row.get("forbidden_external_claim") is True
        if blocked:
            rows.append(
                {
                    "claim_type": row.get("claim_type") or row.get("claim"),
                    "label": row.get("label") or row.get("claim_text") or row.get("claim_type"),
                    "reason": row.get("blocked_reason") or row.get("blocked_wording") or row.get("reason") or "Claim remains blocked until stronger evidence exists.",
                    "next_valid_move": row.get("next_valid_move") or "Attach required evidence and scoped review before stronger wording.",
                }
            )
    if rows:
        return rows
    return [
        {
            "claim_type": "external_claims",
            "label": "External claims",
            "reason": "No external claim can be shown without evidence and review.",
            "next_valid_move": "Keep report language at preparation level.",
        }
    ]


def _summary_points(
    packet: dict[str, Any],
    report_type: dict[str, Any],
    score_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
) -> list[str]:
    packet_id = _packet_id(packet)
    points = [
        f"Packet: {packet_id}",
        f"Audience: {report_type['audience']}",
        f"Purpose: {report_type['purpose']}",
        f"Watermark: {WATERMARK}",
        f"Review status: {REVIEW_STATUS}",
    ]
    if score_rows:
        red_scores = [str(row.get("score_id") or row.get("score")) for row in score_rows if row.get("label") == "red"]
        points.append(f"Red or blocked score lanes: {', '.join(red_scores) if red_scores else 'none in local fixture'}")
    if review_rows:
        points.append(f"Scoped review requests attached: {len(review_rows)}")
    points.append("Blocked claims remain visible in this report.")
    return points


def _report_record(
    repo_root: Path,
    packet: dict[str, Any],
    report_type: dict[str, Any],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    packet_id = _packet_id(packet)
    evidence = _evidence_rows(repo_root, packet)
    claims = _claim_rows(repo_root, packet_id)
    scores = _score_rows(repo_root, packet_id)
    reviews = _review_rows(repo_root, packet_id)
    blocked = _blocked_claims(claims)
    source_citations = _source_citations(sources)
    evidence_citations = _evidence_citations(evidence)
    report_type_id = report_type["report_type"]
    base_path = f"system_review_graph/production_reports/{packet_id}/{report_type_id}"
    pdf_path = f"output/pdf/production_reports/{packet_id}/{report_type_id}.pdf"
    return {
        "report_id": f"production-report:{packet_id}:{report_type_id}:v1",
        "packet_id": packet_id,
        "report_type": report_type_id,
        "title": report_type["title"],
        "audience": report_type["audience"],
        "purpose": report_type["purpose"],
        "packet_view": report_type["packet_view"],
        "version": "v1-local",
        "watermark": WATERMARK,
        "review_status": REVIEW_STATUS,
        "formats": ["json", "html", "pdf"],
        "json_path": f"{base_path}.json",
        "html_preview_path": f"{base_path}.html",
        "pdf_export_path": pdf_path,
        "source_citations": source_citations,
        "evidence_citations": evidence_citations,
        "citation_count": len(source_citations) + len(evidence_citations),
        "blocked_claims": blocked,
        "blocked_claim_count": len(blocked),
        "blocked_claim_section_included": True,
        "can_hide_blocked_claims": False,
        "score_references": [
            {
                "score": row.get("score_id") or row.get("score"),
                "label": row.get("label"),
                "reason": row.get("reason"),
                "next_action": row.get("next_action"),
            }
            for row in scores
        ],
        "review_request_refs": [row.get("review_request_id") for row in reviews],
        "summary_points": _summary_points(packet, report_type, scores, reviews),
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "Report exports organize packet evidence and review work; they do not approve trade action or remove blocked claims.",
    }


def _html_report(record: dict[str, Any]) -> str:
    blocked = "".join(
        f"<li><strong>{html.escape(str(row.get('label')))}</strong>: {html.escape(str(row.get('reason')))}</li>"
        for row in record["blocked_claims"]
    )
    sources = "".join(
        f"<li>{html.escape(str(row.get('source_name')))} - {html.escape(str(row.get('url')))}</li>"
        for row in record["source_citations"]
    )
    evidence = "".join(
        f"<li>{html.escape(str(row.get('evidence_id')))} - {html.escape(str(row.get('type')))}</li>"
        for row in record["evidence_citations"]
    )
    points = "".join(f"<li>{html.escape(point)}</li>" for point in record["summary_points"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(record['title'])}</title>
</head>
<body>
  <header>
    <h1>{html.escape(record['title'])}</h1>
    <p>{html.escape(record['watermark'])} | Version {html.escape(record['version'])} | Review {html.escape(record['review_status'])}</p>
  </header>
  <main>
    <h2>Summary</h2>
    <ul>{points}</ul>
    <h2>Blocked Claims</h2>
    <ul>{blocked}</ul>
    <h2>Source Citations</h2>
    <ul>{sources}</ul>
    <h2>Evidence Citations</h2>
    <ul>{evidence}</ul>
  </main>
</body>
</html>
"""


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_report(record: dict[str, Any]) -> bytes:
    lines = [
        record["title"],
        f"{record['watermark']} | {record['version']} | {record['review_status']}",
        f"Packet: {record['packet_id']}",
        f"Audience: {record['audience']}",
        "Blocked claims remain visible.",
    ]
    lines.extend([f"- {row['label']}: {row['reason']}" for row in record["blocked_claims"][:8]])
    text_lines = []
    y = 760
    for line in lines[:26]:
        text_lines.append(f"BT /F1 10 Tf 50 {y} Td ({_pdf_escape(str(line)[:95])}) Tj ET")
        y -= 22
    stream = "\n".join(text_lines).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("ascii") + stream + b"\nendstream endobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def _write_report_files(repo_root: Path, record: dict[str, Any]) -> dict[str, Path]:
    json_path = repo_root / record["json_path"]
    html_path = repo_root / record["html_preview_path"]
    pdf_path = repo_root / record["pdf_export_path"]
    json_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(_html_report(record), encoding="utf-8")
    pdf_path.write_bytes(_pdf_report(record))
    return {"json": json_path, "html": html_path, "pdf": pdf_path}


def build_production_reports_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    packets = _packets(root)
    sources = _source_rows(root)
    records = [
        _report_record(root, packet, report_type, sources)
        for packet in packets
        for report_type in REPORT_TYPES
    ]
    export_rows = []
    citation_rows = []
    for record in records:
        for fmt, path_key in (("json", "json_path"), ("html", "html_preview_path"), ("pdf", "pdf_export_path")):
            export_rows.append(
                {
                    "report_id": record["report_id"],
                    "packet_id": record["packet_id"],
                    "report_type": record["report_type"],
                    "format": fmt,
                    "path": record[path_key],
                    "status": "export_ready_local",
                    "watermark": record["watermark"],
                    "review_status": record["review_status"],
                    "blocked_claim_section_included": True,
                    "claims_opened": False,
                    "external_effects_created": False,
                }
            )
        for citation in record["source_citations"]:
            citation_rows.append({"report_id": record["report_id"], "citation_type": "source", **citation})
        for citation in record["evidence_citations"]:
            citation_rows.append({"report_id": record["report_id"], "citation_type": "evidence", **citation})
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "packet_count": len(packets),
        "report_type_count": len(REPORT_TYPES),
        "report_record_count": len(records),
        "export_record_count": len(export_rows),
        "citation_record_count": len(citation_rows),
        "report_types": list(REPORT_TYPES),
        "report_records": records,
        "export_records": export_rows,
        "citation_records": citation_rows,
        "watermark": WATERMARK,
        "review_status": REVIEW_STATUS,
        "blocked_claim_sections_required": True,
        "can_hide_blocked_claims": False,
        "html_preview_supported": True,
        "pdf_export_supported": True,
        "json_export_supported": True,
        "version_history_supported": True,
        "claims_opened": False,
        "external_effects_created": False,
        "public_launch_ready": False,
        "live_payment_ready": False,
        "proof_boundary": "Reports are shareable preparation artifacts with citations and blocked claims; they are not approval, legal advice, customs advice, buyer validation, supplier verification, payment activation, or launch approval.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _doc(manifest: dict[str, Any]) -> str:
    report_lines = "\n".join(
        f"- {row['title']}: {row['purpose']}"
        for row in manifest["report_types"]
    )
    return f"""# Production Reports Engine

Status: `{manifest['status']}`

The reports engine exports every Trade Readiness Packet as cited JSON, HTML,
and PDF deliverables. Each report keeps blocked claims visible, carries a
draft watermark, and records review status.

## Report Types

{report_lines}

## Counts

- Packets: {manifest['packet_count']}
- Report types: {manifest['report_type_count']}
- Report records: {manifest['report_record_count']}
- Export records: {manifest['export_record_count']}
- Citation records: {manifest['citation_record_count']}

Report records are generated as report types per packet. In a multi-packet
workspace, export counts increase without opening new claims.

## Gate Boundary

- Blocked-claim sections required: {str(manifest['blocked_claim_sections_required']).lower()}
- Claims opened: {str(manifest['claims_opened']).lower()}
- External effects created: {str(manifest['external_effects_created']).lower()}
- Public launch ready: {str(manifest['public_launch_ready']).lower()}

Reports organize evidence for decisions and expert review. They do not approve
trade action or remove unresolved claims.
"""


def write_production_reports_engine_artifacts(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Path]:
    root = repo_root or Path(__file__).resolve().parents[2]
    srg = root / "system_review_graph"
    docs = root / "docs"
    written_report_paths: list[dict[str, str]] = []
    for record in manifest["report_records"]:
        paths = _write_report_files(root, record)
        written_report_paths.append({fmt: str(path.relative_to(root)) for fmt, path in paths.items()})
    catalog = {
        "status": "production_report_catalog_ready",
        "report_types": manifest["report_types"],
    }
    exports = {
        "status": "production_report_exports_ready_cited",
        "export_records": manifest["export_records"],
        "written_report_paths": written_report_paths,
    }
    citations = {
        "status": "production_report_citations_ready",
        "citation_records": manifest["citation_records"],
    }
    paths = {
        "manifest": srg / "production_reports_engine_manifest.json",
        "catalog": srg / "production_report_catalog.json",
        "exports": srg / "production_report_exports.json",
        "citations": srg / "production_report_citations.json",
        "doc": docs / "PRODUCTION_REPORTS_ENGINE.md",
    }
    _write_json(paths["manifest"], manifest)
    _write_json(paths["catalog"], catalog)
    _write_json(paths["exports"], exports)
    _write_json(paths["citations"], citations)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(_doc(manifest), encoding="utf-8")
    return paths
