"""Production decision and scoring engine.

This module turns Phase 12 into executable product logic. It does not invent a
single readiness score. Instead, it keeps the six product scores separate,
applies cap rules from packet stage, evidence strength, source freshness, and
claim-gate state, and writes durable score records with reasons and next moves.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_decision_scoring_engine_ready_no_global_readiness_score"

SCORE_IDS = (
    "market_signal_score",
    "evidence_completeness_score",
    "source_freshness_score",
    "buyer_supplier_evidence_score",
    "responsibility_clarity_score",
    "decision_safety_score",
)

THRESHOLD_CONTRACT = {
    "0-39": "blocked_or_unknown",
    "40-59": "research_or_evidence_needed",
    "60-79": "internal_review_ready_only",
    "80-100": "expert_review_ready_for_scope_only",
}

SCORE_POLICIES: dict[str, dict[str, Any]] = {
    "market_signal_score": {
        "purpose": "Shows whether a product-country lane deserves deeper validation.",
        "cap_before_external_evidence": 59,
        "claim_dependencies": ("market_signal_source_routed", "buyer_lead_route_identified", "buyer_validated"),
        "cap_rule": "Cap below 60 until dated trade dataset rows, market-access comparison, buyer evidence, and review exist.",
        "next_action": "Attach dated trade dataset rows and buyer evidence before any market conclusion.",
    },
    "evidence_completeness_score": {
        "purpose": "Shows whether packet evidence is complete enough for the current internal stage.",
        "cap_before_external_evidence": 49,
        "claim_dependencies": (
            "product_context_recorded",
            "document_field_extraction_draft",
            "origin_evidence_collected",
            "supplier_evidence_collected",
        ),
        "cap_rule": "Cap below 50 while required packet fields, documents, confirmation, or reviewer evidence are missing.",
        "next_action": "Collect missing packet fields, confirmed customer documents, and reviewer evidence.",
    },
    "source_freshness_score": {
        "purpose": "Shows whether official/reference source evidence is fresh enough for internal use.",
        "cap_before_external_evidence": 39,
        "claim_dependencies": ("hs_candidate_research_route", "tariff_route_identified", "cfia_relevance_route", "tariff_confirmed", "cfia_approved"),
        "cap_rule": "Cap below 40 when critical source evidence is stale, reference-only, not checked, or unreviewed.",
        "next_action": "Refresh official sources, store snapshots, classify changes, and route material changes to review.",
    },
    "buyer_supplier_evidence_score": {
        "purpose": "Shows buyer and supplier evidence strength without validation or verification claims.",
        "cap_before_external_evidence": 59,
        "claim_dependencies": ("buyer_lead_route_identified", "supplier_evidence_collected", "buyer_validated", "supplier_verified"),
        "cap_rule": "Cap below 60 until dated buyer interaction evidence, supplier documents, inspection/certificate evidence, and review exist.",
        "next_action": "Collect buyer reply/meeting/LOI/PO evidence and supplier registration/product/certificate evidence.",
    },
    "responsibility_clarity_score": {
        "purpose": "Shows whether importer of record, Incoterms, and role split are clear.",
        "cap_before_external_evidence": 39,
        "claim_dependencies": ("incoterms_responsibility_path", "customs_ready"),
        "cap_rule": "Cap below 40 while importer of record, Incoterms, broker path, or responsibility split are missing.",
        "next_action": "Confirm importer of record, Incoterms, broker path, freight responsibility, duties, and delivery risk.",
    },
    "decision_safety_score": {
        "purpose": "Shows whether it is safe to move beyond internal preparation.",
        "cap_before_external_evidence": 39,
        "claim_dependencies": (
            "tariff_confirmed",
            "cfia_approved",
            "buyer_validated",
            "supplier_verified",
            "customs_ready",
            "shipment_approved",
        ),
        "cap_rule": "Cap below 40 while any forbidden external claim, launch gate, payment gate, or qualified-review lane remains blocked.",
        "next_action": "Resolve claim-gate blockers and reviewer lanes before any stronger customer-visible decision.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _label(score: int | None) -> str:
    if score is None:
        return "grey"
    if score <= 39:
        return "red"
    if score <= 59:
        return "yellow"
    if score <= 79:
        return "blue"
    return "green"


def _band(score: int | None) -> str:
    if score is None:
        return "unknown"
    if score <= 39:
        return THRESHOLD_CONTRACT["0-39"]
    if score <= 59:
        return THRESHOLD_CONTRACT["40-59"]
    if score <= 79:
        return THRESHOLD_CONTRACT["60-79"]
    return THRESHOLD_CONTRACT["80-100"]


def _business_rows_by_packet(business: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        _text(row.get("packet_id")): row
        for row in business.get("packet_rows", [])
        if _text(row.get("packet_id"))
    }


def _packet_runs_by_packet(packet_engine: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        _text(row.get("packet_id")): row
        for row in packet_engine.get("packet_runs", [])
        if _text(row.get("packet_id"))
    }


def _market_packets_by_packet(market: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for run in market.get("packet_runs", []):
        packet = run.get("market_packet", {})
        packet_id = _text(packet.get("packet_id"))
        if packet_id:
            rows[packet_id] = packet
    return rows


def _claim_decisions_by_packet(claim_gate: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    rows: dict[str, dict[str, dict[str, Any]]] = {}
    for decision in claim_gate.get("claim_gate_decisions", []):
        packet_id = _text(decision.get("packet_id"))
        claim_type = _text(decision.get("claim_type"))
        if packet_id and claim_type:
            rows.setdefault(packet_id, {})[claim_type] = decision
    return rows


def _score_rows_by_id(packet_run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {_text(row.get("score")): row for row in packet_run.get("scores", []) if _text(row.get("score"))}


def _source_evidence_is_stale_or_reference(claims: dict[str, dict[str, Any]], score_id: str) -> bool:
    for claim_type in SCORE_POLICIES[score_id]["claim_dependencies"]:
        decision = claims.get(claim_type, {})
        if decision.get("stale_or_reference_only_evidence_ids"):
            return True
    return False


def _blocked_claim_dependencies(claims: dict[str, dict[str, Any]], score_id: str) -> list[str]:
    blocked = []
    for claim_type in SCORE_POLICIES[score_id]["claim_dependencies"]:
        decision = claims.get(claim_type)
        if decision and decision.get("can_show_claim") is not True:
            blocked.append(claim_type)
    return sorted(blocked)


def _claim_gate_refs(claims: dict[str, dict[str, Any]], score_id: str) -> list[str]:
    refs = []
    for claim_type in SCORE_POLICIES[score_id]["claim_dependencies"]:
        decision = claims.get(claim_type)
        if decision:
            refs.append(decision.get("claim_gate_decision_id"))
    return [ref for ref in refs if ref]


def _evidence_refs(claims: dict[str, dict[str, Any]], score_id: str) -> list[str]:
    refs: set[str] = set()
    for claim_type in SCORE_POLICIES[score_id]["claim_dependencies"]:
        for evidence in claims.get(claim_type, {}).get("evidence_trail", []):
            evidence_id = _text(evidence.get("evidence_id"))
            if evidence_id:
                refs.add(evidence_id)
    return sorted(refs)


def _raw_score(score_id: str, business_scores: dict[str, Any], market_packet: dict[str, Any]) -> int:
    raw = business_scores.get(score_id, {}).get("value")
    if score_id == "market_signal_score" and market_packet:
        market_score = market_packet.get("market_signal_score")
        if isinstance(raw, int) and isinstance(market_score, int):
            return min(raw, market_score)
        if isinstance(market_score, int):
            return market_score
    if isinstance(raw, int):
        return raw
    return 0


def _score_cap(
    score_id: str,
    packet_run: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    market_packet: dict[str, Any],
    document: dict[str, Any],
) -> tuple[int, str]:
    policy = SCORE_POLICIES[score_id]
    cap = int(policy["cap_before_external_evidence"])
    if score_id == "market_signal_score":
        cap = min(cap, int(market_packet.get("market_signal_score_cap", cap) or cap))
        if market_packet.get("can_claim_market_demand") is False:
            return cap, policy["cap_rule"]
    if score_id == "evidence_completeness_score":
        if claims.get("document_field_extraction_draft", {}).get("can_show_claim") is not True:
            return cap, "Customer document fields are missing or unconfirmed; evidence completeness remains capped."
        if document.get("real_uploads_enabled") is not True:
            return cap, "Production real-upload controls are not proven; evidence completeness remains capped."
    if score_id == "source_freshness_score" and _source_evidence_is_stale_or_reference(claims, score_id):
        return cap, policy["cap_rule"]
    if score_id == "buyer_supplier_evidence_score":
        if claims.get("buyer_validated", {}).get("can_show_claim") is not True or claims.get("supplier_verified", {}).get("can_show_claim") is not True:
            return cap, policy["cap_rule"]
    if score_id == "responsibility_clarity_score":
        if claims.get("incoterms_responsibility_path", {}).get("can_show_claim") is not True:
            return cap, policy["cap_rule"]
    if score_id == "decision_safety_score":
        if any(claims.get(claim_type, {}).get("can_show_claim") is not True for claim_type in policy["claim_dependencies"]):
            return cap, policy["cap_rule"]
    return 100, "No score cap applied for the current local evidence state."


def _score_record(
    packet_id: str,
    score_id: str,
    business_row: dict[str, Any],
    packet_run: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    market_packet: dict[str, Any],
    document: dict[str, Any],
) -> dict[str, Any]:
    business_scores = business_row.get("business_scores", {}).get("scores", {})
    packet_scores = _score_rows_by_id(packet_run)
    business_score = business_scores.get(score_id, {})
    packet_score = packet_scores.get(score_id, {})
    raw = _raw_score(score_id, business_scores, market_packet)
    cap, cap_reason = _score_cap(score_id, packet_run, claims, market_packet, document)
    value = min(raw, cap)
    blocked_dependencies = _blocked_claim_dependencies(claims, score_id)
    blocking_fields = sorted(set(packet_score.get("blocking_fields", []) + blocked_dependencies))
    if not blocking_fields and value <= 59:
        blocking_fields = blocked_dependencies
    return {
        "decision_score_id": f"decision-score:{packet_id}:{score_id}",
        "packet_id": packet_id,
        "score": score_id,
        "score_value": value,
        "raw_points": raw,
        "score_cap": cap,
        "cap_applied": raw > cap,
        "label": _label(value),
        "threshold_band": _band(value),
        "reason": business_score.get("meaning") or packet_score.get("reason") or SCORE_POLICIES[score_id]["purpose"],
        "cap_reason": business_score.get("cap_reason") or cap_reason,
        "current_cap_rule": cap_reason,
        "blocking_fields": blocking_fields,
        "blocked_claim_dependencies": blocked_dependencies,
        "required_claim_gate_decisions": _claim_gate_refs(claims, score_id),
        "supporting_evidence_refs": _evidence_refs(claims, score_id),
        "next_action": business_score.get("next_valid_move") or packet_score.get("next_action") or SCORE_POLICIES[score_id]["next_action"],
        "stage": packet_run.get("state"),
        "country_coverage": "reference_only_or_generic_until_country_pack_review",
        "reviewer_status": "qualified_review_missing_or_scoped",
        "single_global_readiness_score_used": False,
        "approval_language_blocked": True,
        "external_effects_created": False,
        "claims_opened": False,
    }


def _packet_summary(packet_id: str, records: list[dict[str, Any]], claims: dict[str, dict[str, Any]]) -> dict[str, Any]:
    labels = {record["score"]: record["label"] for record in records}
    blocked = sorted({claim for record in records for claim in record["blocked_claim_dependencies"]})
    return {
        "packet_id": packet_id,
        "score_count": len(records),
        "score_labels": labels,
        "lowest_label": "red" if "red" in labels.values() else ("yellow" if "yellow" in labels.values() else "blue"),
        "blocked_claim_dependency_count": len(blocked),
        "blocked_claim_dependencies": blocked,
        "safe_claims_showable": sorted(
            claim_type
            for claim_type, decision in claims.items()
            if decision.get("can_show_claim") is True
        ),
        "single_global_readiness_score_created": False,
        "customer_facing_summary": "Use the six separate scores and blocker reasons; do not collapse them into approval.",
        "next_valid_move": "Work the red score blockers first, then refresh source evidence and route scoped claims to reviewers.",
        "claims_opened": False,
        "external_effects_created": False,
    }


def build_production_decision_scoring_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    business = _load_json(root / "system_review_graph" / "business_logic_phase_report.json", {})
    packet_engine = _load_json(root / "system_review_graph" / "production_packet_engine_manifest.json", {})
    claim_gate = _load_json(root / "system_review_graph" / "production_evidence_claim_gate_manifest.json", {})
    market = _load_json(root / "system_review_graph" / "production_market_intelligence_manifest.json", {})
    document = _load_json(root / "system_review_graph" / "production_document_intelligence_manifest.json", {})
    business_rows = _business_rows_by_packet(business)
    packet_runs = _packet_runs_by_packet(packet_engine)
    claim_rows = _claim_decisions_by_packet(claim_gate)
    market_packets = _market_packets_by_packet(market)
    records: list[dict[str, Any]] = []
    packet_summaries: list[dict[str, Any]] = []
    for packet_id, packet_run in packet_runs.items():
        claims = claim_rows.get(packet_id, {})
        packet_records = [
            _score_record(
                packet_id,
                score_id,
                business_rows.get(packet_id, {}),
                packet_run,
                claims,
                market_packets.get(packet_id, {}),
                document,
            )
            for score_id in SCORE_IDS
        ]
        records.extend(packet_records)
        packet_summaries.append(_packet_summary(packet_id, packet_records, claims))
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "score_count": len(SCORE_IDS),
        "packet_count": len(packet_runs),
        "decision_score_record_count": len(records),
        "score_ids": list(SCORE_IDS),
        "threshold_contract": THRESHOLD_CONTRACT,
        "score_policies": [
            {
                "score": score_id,
                **SCORE_POLICIES[score_id],
            }
            for score_id in SCORE_IDS
        ],
        "decision_score_records": records,
        "packet_score_summaries": packet_summaries,
        "single_global_readiness_score_created": False,
        "combined_readiness_label_created": False,
        "approval_language_allowed": False,
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "live_payment_ready": False,
        "proof_boundary": (
            "The scoring engine explains separate capped scores for internal decision preparation. "
            "It does not approve imports, exports, tariff treatment, CFIA status, buyers, suppliers, "
            "shipments, payments, legal posture, or public launch."
        ),
    }


def render_decision_scoring_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Decision Scoring Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Summary",
        "",
        f"- Score types: {payload['score_count']}",
        f"- Score records: {payload['decision_score_record_count']}",
        "- Single global readiness score created: false",
        "- Approval language allowed: false",
        "",
        "## Score Policies",
        "",
    ]
    for policy in payload["score_policies"]:
        lines.append(f"- `{policy['score']}`: {policy['purpose']} Cap rule: {policy['cap_rule']}")
    lines.extend(["", "## Packet Scores", ""])
    for summary in payload["packet_score_summaries"]:
        lines.append(f"### {summary['packet_id']}")
        lines.append("")
        lines.append(f"- Lowest label: `{summary['lowest_label']}`")
        lines.append(f"- Blocked claim dependencies: {summary['blocked_claim_dependency_count']}")
        lines.append(f"- Next valid move: {summary['next_valid_move']}")
        lines.append("")
        for record in [row for row in payload["decision_score_records"] if row["packet_id"] == summary["packet_id"]]:
            lines.append(
                f"- `{record['score']}`: {record['score_value']}/{record['score_cap']} `{record['label']}`; "
                f"{record['reason']}"
            )
        lines.append("")
    lines.extend(
        [
            "## Closed Gates",
            "",
            "- Claims opened: false",
            "- External effects created: false",
            "- Public launch ready: false",
            "- Live payment ready: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_decision_scoring_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_decision_scoring_manifest.json"
    records_path = graph / "production_decision_score_records.json"
    policy_path = graph / "production_score_cap_policy.json"
    doc_path = docs / "PRODUCTION_DECISION_SCORING_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_decision_score_records_ready",
                "decision_score_record_count": payload["decision_score_record_count"],
                "score_ids": payload["score_ids"],
                "records": payload["decision_score_records"],
                "single_global_readiness_score_created": False,
                "approval_language_allowed": False,
                "external_effects_created": False,
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    policy_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_score_cap_policy_ready",
                "threshold_contract": payload["threshold_contract"],
                "score_policies": payload["score_policies"],
                "single_global_readiness_score_created": False,
                "approval_language_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_decision_scoring_markdown(payload), encoding="utf-8")
    return {"manifest": manifest_path, "records": records_path, "policy": policy_path, "doc": doc_path}
