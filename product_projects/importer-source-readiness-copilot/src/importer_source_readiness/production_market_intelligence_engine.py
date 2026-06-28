"""Production market intelligence engine.

This module turns market-intelligence requirements into executable local
records. It maps product/country packets to approved research sources and
metric slots, but it refuses to invent trade values, demand, profitability, or
buyer validation without real dataset rows and buyer evidence.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_market_intelligence_engine_ready_source_routed_no_demand_claims"

MARKET_METRICS = (
    "hs_candidate_route",
    "destination_import_value",
    "three_to_five_year_trend",
    "top_origin_countries",
    "unit_value_range",
    "market_concentration",
    "import_replacement_signal",
    "market_access_barriers",
    "buyer_importer_lead_routes",
)

MARKET_SOURCE_MAP = {
    "hs_candidate_route": ("wco-harmonized-system", "cbsa-customs-tariff-2026"),
    "destination_import_value": ("ised-trade-data-online", "world-bank-wits", "itc-trade-map"),
    "three_to_five_year_trend": ("ised-trade-data-online", "world-bank-wits", "itc-trade-map"),
    "top_origin_countries": ("ised-trade-data-online", "world-bank-wits", "itc-trade-map"),
    "unit_value_range": ("world-bank-wits", "itc-trade-map"),
    "market_concentration": ("ised-trade-data-online", "world-bank-wits", "itc-trade-map"),
    "import_replacement_signal": ("ised-trade-data-online", "world-bank-wits", "itc-trade-map"),
    "market_access_barriers": ("itc-market-access-map", "cbsa-customs-tariff-2026", "cfia-airs", "gac-import-controls"),
    "buyer_importer_lead_routes": ("canada-cid",),
}

MARKET_BLOCKED_CLAIMS = (
    "profitable_market",
    "guaranteed_demand",
    "buyer_validated",
    "confirmed_market_size",
    "tariff_advantage_confirmed",
    "market_entry_approved",
    "price_or_margin_confirmed",
)

METRIC_LIMITATIONS = {
    "hs_candidate_route": "HS routing supports candidate research only; classification is not confirmed.",
    "destination_import_value": "Import value requires a dated dataset row before any value can be shown.",
    "three_to_five_year_trend": "Trend requires multi-year dataset rows; growth is not demand proof.",
    "top_origin_countries": "Competitor-country rows are market context, not buyer demand.",
    "unit_value_range": "Unit values are rough trade-data signals, not pricing or margin guarantees.",
    "market_concentration": "Concentration is a research signal only and needs dataset rows.",
    "import_replacement_signal": "Import replacement is a hypothesis until local production and buyer evidence exist.",
    "market_access_barriers": "Tariff/access/regulatory routes require qualified review before external claims.",
    "buyer_importer_lead_routes": "Importer directories are lead sources only and never buyer validation.",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _source_registry_by_id(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_text(source.get("id")): source for source in sources if _text(source.get("id"))}


def _country(value: Any) -> str:
    text = _text(value)
    return {"CA": "Canada", "IN": "India", "VN": "Vietnam"}.get(text.upper(), text or "Generic")


def _source_routes(metric: str, source_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    routes = []
    for source_id in MARKET_SOURCE_MAP[metric]:
        source = source_by_id.get(source_id)
        if not source:
            routes.append(
                {
                    "source_id": source_id,
                    "status": "missing_from_registry",
                    "claim_boundary": "Missing source route blocks this metric.",
                }
            )
            continue
        routes.append(
            {
                "source_id": source_id,
                "name": source.get("name"),
                "url": source.get("url"),
                "jurisdiction": _country(source.get("jurisdiction")),
                "status": "source_route_ready_reference_only",
                "access_mode": "manual_dataset_or_source_specific_connector_required",
                "license_status": "not_checked_for_automated_ingestion",
                "claim_boundary": source.get("claim_boundary"),
            }
        )
    return routes


def _dataset_connectors(source_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    source_ids = sorted({source_id for ids in MARKET_SOURCE_MAP.values() for source_id in ids})
    connectors = []
    for source_id in source_ids:
        source = source_by_id.get(source_id, {})
        connectors.append(
            {
                "dataset_connector_id": f"market-dataset:{source_id}",
                "source_id": source_id,
                "source_name": source.get("name", source_id),
                "canonical_url": source.get("url", ""),
                "access_mode": "manual_download_or_api_after_terms_review",
                "license_status": "not_checked_for_production_ingestion",
                "credential_status": "not_configured",
                "ingestion_ready": False,
                "live_fetch_allowed": False,
                "required_before_value_claim": True,
                "next_valid_move": "Confirm terms/license, configure connector or manual import, then attach dated dataset rows.",
            }
        )
    return connectors


def _packet_market_signals(packet: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    packet_id = _text(packet.get("packet_id"))
    signals = []
    for metric in MARKET_METRICS:
        routes = _source_routes(metric, source_by_id)
        signal_level = "insufficient_data"
        if all(route.get("status") == "source_route_ready_reference_only" for route in routes):
            signal_level = "weak_research_signal"
        signals.append(
            {
                "market_signal_id": f"market-signal:{packet_id}:{metric}",
                "packet_id": packet_id,
                "metric": metric,
                "product_name": packet.get("product_name"),
                "origin_country": _country(packet.get("origin_country")),
                "destination_country": _country(packet.get("destination_country")),
                "hs_candidate": packet.get("hs_code_value", ""),
                "source_routes": routes,
                "source_route_count": len(routes),
                "signal_level": signal_level,
                "confidence": "research_plan",
                "value_status": "not_ingested_dataset_required",
                "value": "",
                "period": "",
                "limitation": METRIC_LIMITATIONS[metric],
                "next_validation": "Attach dated dataset rows, buyer evidence, and reviewer findings before stronger claims.",
                "supports_claims": [],
                "blocked_claims": list(MARKET_BLOCKED_CLAIMS),
                "external_effects_created": False,
                "claims_opened": False,
            }
        )
    return signals


def _market_packet(packet: dict[str, Any], signals: list[dict[str, Any]]) -> dict[str, Any]:
    route_ready = sum(1 for signal in signals if signal["signal_level"] == "weak_research_signal")
    score_cap = 59
    score = min(score_cap, int((route_ready / max(len(signals), 1)) * 45))
    return {
        "packet_id": packet.get("packet_id"),
        "status": "market_packet_ready_research_only",
        "signal_count": len(signals),
        "source_routed_metric_count": route_ready,
        "market_signal_score": score,
        "market_signal_score_cap": score_cap,
        "score_label": "grey" if score < 20 else "yellow",
        "score_reason": "Score is capped because no dated trade dataset rows, buyer evidence, or reviewer findings are attached.",
        "blocked_claims": list(MARKET_BLOCKED_CLAIMS),
        "can_claim_market_demand": False,
        "can_claim_profitability": False,
        "can_claim_buyer_validation": False,
        "next_valid_move": "Ingest dated market dataset rows and attach buyer evidence before any market conclusion.",
    }


def build_production_market_intelligence_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    packets = _load_json(root / "data" / "customer_source_packets.json", [])
    sources = _load_json(root / "data" / "official_source_registry.json", [])
    source_by_id = _source_registry_by_id(sources)
    connectors = _dataset_connectors(source_by_id)
    packet_runs = []
    all_signals = []
    for packet in packets:
        signals = _packet_market_signals(packet, source_by_id)
        all_signals.extend(signals)
        packet_runs.append(
            {
                "packet_id": packet.get("packet_id"),
                "market_packet": _market_packet(packet, signals),
                "signals": signals,
            }
        )
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "metric_count": len(MARKET_METRICS),
        "market_metrics": list(MARKET_METRICS),
        "market_signal_count": len(all_signals),
        "packet_count": len(packet_runs),
        "dataset_connector_count": len(connectors),
        "dataset_connectors": connectors,
        "packet_runs": packet_runs,
        "signals": all_signals,
        "blocked_claims": list(MARKET_BLOCKED_CLAIMS),
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "live_payment_ready": False,
        "proof_boundary": (
            "Market intelligence is source-routed research logic only. It does not "
            "prove demand, market size, profitability, buyer validation, tariff "
            "advantage, or market-entry approval without real dataset rows, buyer "
            "evidence, and qualified review."
        ),
    }


def render_market_intelligence_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Market Intelligence Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This engine creates source-routed market signal records without inventing data values or demand claims.",
        "",
        "## Proof Boundary",
        "",
        payload["proof_boundary"],
        "",
        "## Metrics",
        "",
    ]
    for metric in payload["market_metrics"]:
        lines.append(f"- `{metric}`")
    lines.extend(["", "## Packet Runs", ""])
    for run in payload["packet_runs"]:
        market_packet = run["market_packet"]
        lines.extend(
            [
                f"### {run['packet_id']}",
                "",
                f"- Status: `{market_packet['status']}`",
                f"- Signal count: {market_packet['signal_count']}",
                f"- Source-routed metrics: {market_packet['source_routed_metric_count']}",
                f"- Market signal score: {market_packet['market_signal_score']} / cap {market_packet['market_signal_score_cap']}",
                "- Can claim demand: false",
                "- Can claim profitability: false",
                "- Can claim buyer validation: false",
                f"- Next valid move: {market_packet['next_valid_move']}",
                "",
            ]
        )
    lines.extend(["", "## Dataset Connectors", ""])
    for connector in payload["dataset_connectors"]:
        lines.append(f"- `{connector['source_id']}`: ingestion ready `{str(connector['ingestion_ready']).lower()}`.")
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            "- External effects created: false",
            "- Claims opened: false",
            "- Public launch ready: false",
            "- Live payment ready: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_market_intelligence_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_market_intelligence_manifest.json"
    signals_path = graph / "production_market_signals.json"
    connectors_path = graph / "production_market_dataset_connectors.json"
    doc_path = docs / "PRODUCTION_MARKET_INTELLIGENCE_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    signals_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_market_signals_ready_research_only",
                "signal_count": payload["market_signal_count"],
                "signals": payload["signals"],
                "blocked_claims": payload["blocked_claims"],
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    connectors_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_market_dataset_connectors_registered_not_ingesting",
                "dataset_connector_count": payload["dataset_connector_count"],
                "dataset_connectors": payload["dataset_connectors"],
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_market_intelligence_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "signals": signals_path,
        "connectors": connectors_path,
        "doc": doc_path,
    }
