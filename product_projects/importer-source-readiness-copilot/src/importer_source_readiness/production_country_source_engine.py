"""Production country/source intelligence engine.

This module converts researched official-source requirements into executable
country-pack and source-lifecycle logic. It does not fetch the internet or
claim legal freshness; it uses the repo source registry plus dated refresh
records to decide coverage, source states, affected packets, and gated claims.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_country_source_engine_ready_reference_packs_claim_gates_closed"

COUNTRY_PACK_ORDER = ("CA-import", "IN-export", "VN-demo-origin", "GENERIC-fallback")

CANADA_REQUIRED_SOURCE_AREAS = (
    "customs_import_process",
    "tariff_orientation",
    "regulated_goods",
    "sanctions_restricted_party",
    "trade_data",
    "buyer_importer_discovery",
    "broker_directory",
    "import_controls",
)

INDIA_REQUIRED_SOURCE_AREAS = (
    "export_policy",
    "import_export_code",
    "origin_export_controls",
    "customs_reference",
)

SOURCE_STATES = (
    "not_checked",
    "checked_current_reference_only",
    "changed_minor",
    "changed_material",
    "source_unavailable",
    "stale",
    "review_required",
)

CHANGE_TYPES = (
    "cosmetic",
    "date_change",
    "source_unavailable",
    "material_regulatory_or_tariff_change",
    "new_requirement",
    "removed_requirement",
    "baseline_registered",
)

RESEARCHED_SOURCE_FACTS: tuple[dict[str, Any], ...] = (
    {
        "source_id": "cbsa-import-commercial-goods",
        "source_area": "customs_import_process",
        "usable_fact": "CBSA is the Canada commercial-import workflow route for import preparation, origin, rulings, and other government requirement routing.",
        "claim_boundary": "Routes users to official and qualified review paths; it does not approve import readiness.",
    },
    {
        "source_id": "cbsa-customs-tariff-2026",
        "source_area": "tariff_orientation",
        "usable_fact": "CBSA Customs Tariff is the Canada tariff-orientation route for HS candidate research.",
        "claim_boundary": "HS or tariff treatment remains a candidate until qualified review or authoritative ruling evidence exists.",
    },
    {
        "source_id": "cfia-airs",
        "source_area": "regulated_goods",
        "usable_fact": "CFIA AIRS is a reference route for food, plant, animal, and other CFIA-regulated import requirements.",
        "claim_boundary": "AIRS is reference-only and importers remain responsible for accurate import-time information.",
    },
    {
        "source_id": "gac-sanctions",
        "source_area": "sanctions_restricted_party",
        "usable_fact": "Global Affairs Canada is the Canada sanctions and restricted-country route.",
        "claim_boundary": "Sanctions clearance requires dated screening records and qualified review.",
    },
    {
        "source_id": "canada-sanctions",
        "source_area": "sanctions_restricted_party",
        "usable_fact": "Global Affairs Canada consolidated sanctions records support restricted-party routing.",
        "claim_boundary": "A source listing route does not prove the packet is sanctions-clear.",
    },
    {
        "source_id": "ised-trade-data-online",
        "source_area": "trade_data",
        "usable_fact": "ISED Trade Data Online supports Canada and U.S. goods-trade research reports with many partner countries.",
        "claim_boundary": "Trade data is a research signal only, not demand, margin, or buyer validation.",
    },
    {
        "source_id": "statcan-wds",
        "source_area": "trade_data",
        "usable_fact": "Statistics Canada Web Data Service routes machine-readable Canadian data tables after table and license review.",
        "claim_boundary": "A data-service route does not prove a current trade value until a dated dataset row is ingested and cited.",
    },
    {
        "source_id": "canada-cid",
        "source_area": "buyer_importer_discovery",
        "usable_fact": "Canadian Importers Database lists companies importing goods into Canada by product, city, and origin.",
        "claim_boundary": "Importer rows are lead-discovery only and never buyer validation.",
    },
    {
        "source_id": "canada-trade-commissioner-export-guide",
        "source_area": "export_policy",
        "usable_fact": "Government of Canada export guidance routes Canadian exporters to export-planning questions.",
        "claim_boundary": "General guidance does not prove a specific exporter, product, destination, or shipment is export-ready.",
    },
    {
        "source_id": "gac-export-controls",
        "source_area": "origin_export_controls",
        "usable_fact": "Global Affairs Canada export controls route controlled-goods, destination, and permit questions.",
        "claim_boundary": "Export-control routing does not prove permit status, destination permission, or compliance.",
    },
    {
        "source_id": "cbsa-licensed-customs-brokers",
        "source_area": "broker_directory",
        "usable_fact": "CBSA licensed customs broker records route users to qualified broker discovery.",
        "claim_boundary": "The product does not act as a customs broker and does not imply broker signoff.",
    },
    {
        "source_id": "gac-import-controls",
        "source_area": "import_controls",
        "usable_fact": "Global Affairs Canada import-control and permit pages route users to controlled-import questions.",
        "claim_boundary": "Import-control applicability requires current source evidence and qualified review.",
    },
    {
        "source_id": "justice-import-control-list",
        "source_area": "import_controls",
        "usable_fact": "Justice Laws source routes legal-reference checks for controlled imports.",
        "claim_boundary": "Legal interpretation and product applicability require qualified review.",
    },
    {
        "source_id": "india-dgft-foreign-trade-policy",
        "source_area": "export_policy",
        "usable_fact": "DGFT is the India foreign-trade and IEC route for export/import policy orientation.",
        "claim_boundary": "IEC, licensing, incentive, and product-specific export claims require current source and qualified review.",
    },
    {
        "source_id": "india-dgft-foreign-trade-policy",
        "source_area": "import_export_code",
        "usable_fact": "DGFT identifies IEC as the key business identification number for India export/import activity.",
        "claim_boundary": "The product can ask for IEC evidence; it cannot confirm registration or permission.",
    },
    {
        "source_id": "india-dgft-foreign-trade-policy",
        "source_area": "origin_export_controls",
        "usable_fact": "DGFT is the origin-side route for export policy, SCOMET, certificates, and export-management checks.",
        "claim_boundary": "Origin export controls require qualified review before any permission claim.",
    },
    {
        "source_id": "india-cbic-customs",
        "source_area": "customs_reference",
        "usable_fact": "CBIC is the India customs-reference route.",
        "claim_boundary": "Customs and duty treatment remains blocked until qualified review.",
    },
    {
        "source_id": "world-bank-wits",
        "source_area": "global_trade_data",
        "usable_fact": "WITS supports merchandise trade, tariff, and non-tariff-measure research.",
        "claim_boundary": "Global data supports research signals only.",
    },
    {
        "source_id": "itc-market-access-map",
        "source_area": "market_access_comparison",
        "usable_fact": "ITC Market Access Map routes tariff, market-access, and regulatory-requirement comparison.",
        "claim_boundary": "Market-access comparison is not tariff confirmation or market entry approval.",
    },
    {
        "source_id": "wco-harmonized-system",
        "source_area": "hs_code_doctrine",
        "usable_fact": "HS doctrine supports commodity-candidate and six-digit HS structure logic.",
        "claim_boundary": "HS candidates are not classification confirmation.",
    },
    {
        "source_id": "icc-incoterms-2020",
        "source_area": "responsibility_path",
        "usable_fact": "ICC Incoterms route responsibility, task, cost, and risk questions between buyer and seller.",
        "claim_boundary": "Responsibility guidance needs user confirmation and legal/freight review where applicable.",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _country_code(country: Any) -> str:
    text = _text(country).upper()
    return {
        "CANADA": "CA",
        "CA": "CA",
        "INDIA": "IN",
        "IN": "IN",
        "VIETNAM": "VN",
        "VIET NAM": "VN",
        "VN": "VN",
        "INTERNATIONAL": "INTL",
    }.get(text, text or "GENERIC")


def _country_name(country: Any) -> str:
    code = _country_code(country)
    return {
        "CA": "Canada",
        "IN": "India",
        "VN": "Vietnam",
        "INTL": "International",
        "GENERIC": "Generic",
    }.get(code, _text(country) or "Generic")


def _source_registry_by_id(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_text(source.get("id")): source for source in sources if _text(source.get("id"))}


def _source_area(source: dict[str, Any]) -> str:
    source_id = _text(source.get("id"))
    for fact in RESEARCHED_SOURCE_FACTS:
        if fact["source_id"] == source_id:
            return fact["source_area"]
    text = " ".join(_text(source.get(key)).lower() for key in ("id", "name", "evidence_role", "claim_boundary", "url"))
    if "tariff" in text or "hs" in text:
        return "tariff_orientation"
    if "cfia" in text or "airs" in text or "food" in text or "regulated" in text:
        return "regulated_goods"
    if "sanction" in text or "restricted" in text:
        return "sanctions_restricted_party"
    if "importer" in text or "buyer" in text:
        return "buyer_importer_discovery"
    if "broker" in text:
        return "broker_directory"
    if "data" in text or "trade" in text:
        return "trade_data"
    if "control" in text or "permit" in text:
        return "import_controls"
    return "official_reference"


def _facts_for_source(source_id: str) -> list[dict[str, Any]]:
    return [dict(fact) for fact in RESEARCHED_SOURCE_FACTS if fact["source_id"] == source_id]


def _refresh_rows(source_refresh_runs: Any) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not isinstance(source_refresh_runs, list):
        return rows
    for run in source_refresh_runs:
        if not isinstance(run, dict):
            continue
        for row in run.get("rows", []):
            if not isinstance(row, dict):
                continue
            url = _text(row.get("source_url"))
            if url:
                rows[url] = {
                    **row,
                    "refresh_run_id": run.get("refresh_run_id"),
                    "generated_at": run.get("generated_at"),
                    "claim_boundary": run.get("claim_boundary"),
                }
    return rows


def _source_lifecycle(source: dict[str, Any], refresh_by_url: dict[str, dict[str, Any]]) -> dict[str, Any]:
    url = _text(source.get("url"))
    refresh = refresh_by_url.get(url, {})
    has_refresh = bool(refresh)
    source_changed = bool(refresh.get("source_changed", False))
    if has_refresh and not source_changed:
        state = "checked_current_reference_only"
        change_type = "date_change"
    elif has_refresh and source_changed:
        state = "review_required"
        change_type = "material_regulatory_or_tariff_change"
    else:
        state = "not_checked"
        change_type = "baseline_registered"
    facts = _facts_for_source(_text(source.get("id")))
    source_areas = sorted({fact["source_area"] for fact in facts}) or [_source_area(source)]
    return {
        "source_id": source.get("id"),
        "name": source.get("name"),
        "jurisdiction": _country_name(source.get("jurisdiction")),
        "country_code": _country_code(source.get("jurisdiction")),
        "canonical_url": url,
        "source_area": source_areas[0],
        "source_areas": source_areas,
        "source_type": "official_or_primary_reference",
        "authority_level": "official" if _country_code(source.get("jurisdiction")) in {"CA", "IN"} or ".gc.ca" in url or "dgft.gov.in" in url else "primary_reference",
        "robots_status": "not_checked_before_automation",
        "terms_status": "not_checked_before_automation",
        "allowed_automation": "manual_or_approved_loader_only",
        "parser_method": "metadata_hash_then_source_specific_parser_when_allowed",
        "refresh_cadence": "before_packet_generation_or_paid_review",
        "source_state": state,
        "allowed_states": list(SOURCE_STATES),
        "change_type": change_type,
        "allowed_change_types": list(CHANGE_TYPES),
        "content_hash": refresh.get("content_hash", ""),
        "last_checked_at": refresh.get("generated_at", source.get("accessed_at", "")),
        "http_status": refresh.get("http_status", ""),
        "usable_facts": [fact["usable_fact"] for fact in facts] or [_text(source.get("evidence_role"))],
        "claim_boundary": "; ".join([fact["claim_boundary"] for fact in facts]) or source.get("claim_boundary", ""),
        "supports_claims": [],
        "blocked_claims": [
            "current_law_confirmed",
            "tariff_confirmed",
            "cfia_approved",
            "sanctions_clear",
            "buyer_validated",
            "supplier_verified",
            "ready_to_import",
            "ready_to_export",
        ],
        "review_required_if_material_change": True,
        "packet_impact_rule": "If source changes or is not checked for the packet date, affected packet claims stay blocked.",
    }


def _country_pack(
    *,
    pack_id: str,
    country_code: str,
    country_name: str,
    direction: str,
    required_areas: tuple[str, ...],
    source_rows: list[dict[str, Any]],
    fallback: bool = False,
    demo: bool = False,
) -> dict[str, Any]:
    matched = [
        row for row in source_rows
        if row["country_code"] in {country_code, "INTL"}
        and set(row.get("source_areas", [row["source_area"]])) & set(required_areas)
    ]
    present_areas = sorted(
        {
            area
            for row in matched
            for area in row.get("source_areas", [row["source_area"]])
            if area in set(required_areas)
        }
    )
    missing_areas = sorted(set(required_areas) - set(present_areas))
    if fallback:
        coverage_level = "generic"
    elif demo:
        coverage_level = "reference_only"
    elif missing_areas:
        coverage_level = "partial"
    else:
        coverage_level = "reference_only"
    return {
        "country_pack_id": pack_id,
        "country_code": country_code,
        "country_name": country_name,
        "direction": direction,
        "coverage_level": coverage_level,
        "source_types_required": list(required_areas),
        "source_types_present": present_areas,
        "source_types_missing": missing_areas,
        "source_count": len(matched),
        "source_ids": [row["source_id"] for row in matched],
        "claim_boundaries": [
            "country pack routes official sources only",
            "country-specific claims require source freshness and qualified review",
            "unsupported or partial paths remain research-only",
        ],
        "refresh_cadence": {
            "packet_generation": "check before generating customer packet",
            "paid_review": "check before paid/expert review",
            "material_change": "mark affected packets stale and require review",
        },
        "reviewer_required": True,
        "external_claims_opened": False,
        "next_valid_move": (
            "Attach current source snapshots and qualified review before country-specific claims."
            if coverage_level != "generic"
            else "Use generic research-only workflow until country pack sources are added."
        ),
    }


def _packet_impacts(packets: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    impacts: list[dict[str, Any]] = []
    for packet in packets:
        destination = _country_code(packet.get("destination_country"))
        origin = _country_code(packet.get("origin_country"))
        product_text = " ".join(_text(packet.get(key)).lower() for key in ("product_name", "product_category"))
        needed_areas = {"customs_import_process", "tariff_orientation", "sanctions_restricted_party"}
        if destination == "CA":
            needed_areas.update({"import_controls", "trade_data", "buyer_importer_discovery", "broker_directory"})
        if any(word in product_text for word in ("food", "seafood", "tuna", "plant", "animal")):
            needed_areas.add("regulated_goods")
        if origin == "IN":
            needed_areas.update(INDIA_REQUIRED_SOURCE_AREAS)
        matched = [
            row for row in source_rows
            if set(row.get("source_areas", [row["source_area"]])) & needed_areas
            and row["country_code"] in {destination, origin, "INTL"}
        ]
        unchecked = [row for row in matched if row["source_state"] == "not_checked"]
        review_required = [row for row in matched if row["source_state"] in {"not_checked", "review_required", "changed_material", "stale"}]
        impacts.append(
            {
                "packet_id": packet.get("packet_id"),
                "origin_country": _country_name(packet.get("origin_country")),
                "destination_country": _country_name(packet.get("destination_country")),
                "needed_source_areas": sorted(needed_areas),
                "matched_source_ids": [row["source_id"] for row in matched],
                "unchecked_source_ids": [row["source_id"] for row in unchecked],
                "review_required_source_ids": [row["source_id"] for row in review_required],
                "packet_source_state": "source_checking_or_reviewer_ready_reference_only",
                "packet_stale_if_material_change": True,
                "blocked_claims": [
                    "current_law_confirmed",
                    "tariff_confirmed",
                    "cfia_approved",
                    "sanctions_clear",
                    "ready_to_import",
                    "ready_to_export",
                ],
                "next_valid_move": "Refresh unchecked sources, preserve reference-only wording, and route the packet to scoped expert review.",
                "external_claims_opened": False,
            }
        )
    return impacts


def build_production_country_source_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    sources = _load_json(root / "data" / "official_source_registry.json", [])
    packets = _load_json(root / "data" / "customer_source_packets.json", [])
    refresh_runs = _load_json(root / "system_review_graph" / "source_refresh_runs.json", [])
    refresh_by_url = _refresh_rows(refresh_runs)
    source_rows = [_source_lifecycle(source, refresh_by_url) for source in sources]
    packs = [
        _country_pack(
            pack_id="CA-import",
            country_code="CA",
            country_name="Canada",
            direction="import",
            required_areas=CANADA_REQUIRED_SOURCE_AREAS,
            source_rows=source_rows,
        ),
        _country_pack(
            pack_id="IN-export",
            country_code="IN",
            country_name="India",
            direction="export",
            required_areas=INDIA_REQUIRED_SOURCE_AREAS,
            source_rows=source_rows,
        ),
        _country_pack(
            pack_id="VN-demo-origin",
            country_code="VN",
            country_name="Vietnam",
            direction="export",
            required_areas=("origin_export_controls", "customs_reference", "supplier_registry"),
            source_rows=source_rows,
            demo=True,
        ),
        _country_pack(
            pack_id="GENERIC-fallback",
            country_code="GENERIC",
            country_name="Generic fallback",
            direction="generic",
            required_areas=("official_reference",),
            source_rows=source_rows,
            fallback=True,
        ),
    ]
    packet_impacts = _packet_impacts(packets, source_rows)
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "country_pack_count": len(packs),
        "country_pack_order": list(COUNTRY_PACK_ORDER),
        "source_lifecycle_count": len(source_rows),
        "source_state_values": list(SOURCE_STATES),
        "source_change_type_values": list(CHANGE_TYPES),
        "researched_source_fact_count": len(RESEARCHED_SOURCE_FACTS),
        "packet_impact_count": len(packet_impacts),
        "country_packs": packs,
        "source_lifecycle": source_rows,
        "packet_source_impacts": packet_impacts,
        "official_source_registry_count": len(_source_registry_by_id(sources)),
        "source_refresh_record_count": len(refresh_by_url),
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "hosted_private_beta_ready": False,
        "live_payment_ready": False,
        "proof_boundary": (
            "This engine turns researched official-source routes into country/source logic. "
            "It does not prove current law, tariff treatment, CFIA approval, sanctions clearance, "
            "buyer validation, supplier verification, hosted readiness, or public launch approval."
        ),
    }


def render_country_source_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Country Source Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This engine converts the official-source registry and dated refresh records into country packs, source lifecycle rows, and packet source-impact decisions.",
        "",
        "## Proof Boundary",
        "",
        payload["proof_boundary"],
        "",
        "## Country Packs",
        "",
    ]
    for pack in payload["country_packs"]:
        lines.extend(
            [
                f"### {pack['country_pack_id']}",
                "",
                f"- Coverage: `{pack['coverage_level']}`",
                f"- Direction: `{pack['direction']}`",
                f"- Sources present: {', '.join(pack['source_types_present']) or 'none'}",
                f"- Sources missing: {', '.join(pack['source_types_missing']) or 'none'}",
                f"- Reviewer required: {str(pack['reviewer_required']).lower()}",
                f"- External claims opened: {str(pack['external_claims_opened']).lower()}",
                "",
            ]
        )
    lines.extend(["", "## Source Lifecycle", ""])
    for row in payload["source_lifecycle"]:
        lines.append(f"- `{row['source_id']}`: {', '.join(row.get('source_areas', [row['source_area']]))} / `{row['source_state']}`.")
    lines.extend(["", "## Packet Impacts", ""])
    for impact in payload["packet_source_impacts"]:
        lines.append(
            f"- `{impact['packet_id']}`: {impact['packet_source_state']}; next move: {impact['next_valid_move']}"
        )
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            "- External effects created: false",
            "- Claims opened: false",
            "- Public launch ready: false",
            "- Hosted private beta ready: false",
            "- Live payment ready: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_country_source_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_country_source_engine_manifest.json"
    packs_path = graph / "production_country_packs.json"
    lifecycle_path = graph / "production_source_lifecycle.json"
    doc_path = docs / "PRODUCTION_COUNTRY_SOURCE_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    packs_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_country_packs_ready_reference_only_claims_closed",
                "country_pack_count": payload["country_pack_count"],
                "country_packs": payload["country_packs"],
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    lifecycle_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_source_lifecycle_ready_reference_only_claims_closed",
                "source_lifecycle_count": payload["source_lifecycle_count"],
                "source_lifecycle": payload["source_lifecycle"],
                "packet_source_impacts": payload["packet_source_impacts"],
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_country_source_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "country_packs": packs_path,
        "source_lifecycle": lifecycle_path,
        "doc": doc_path,
    }
