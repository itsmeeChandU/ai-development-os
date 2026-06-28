"""Continuation planning for externally gated product work."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


LANE_DEFINITIONS = [
    {
        "id": "buyer-validation",
        "title": "Buyer and operator validation",
        "owner": "product",
        "modules": ["buyer_validation"],
        "required_evidence": [
            "dated buyer, importer, broker, or operator interviews",
            "no-fit, no-budget, or willingness-to-pay notes",
            "operator workflow gaps found during real review",
        ],
        "proof_command": "Attach evidence to data/evidence_packets.json and rerun python3 scripts/check_product.py.",
    },
    {
        "id": "qualified-compliance-review",
        "title": "Qualified compliance review",
        "owner": "compliance",
        "modules": ["legal_compliance", "expert_review", "tariff_classification", "food_safety"],
        "required_evidence": [
            "qualified customs, food safety, or legal review notes",
            "reviewer identity, date, scope, and claim boundary",
            "approved or rejected language for operator-facing claims",
        ],
        "proof_command": "Update country matrix and evidence packets, then rerun python3 scripts/check_product.py.",
    },
    {
        "id": "country-matrix-review",
        "title": "Country import/export requirements",
        "owner": "compliance",
        "modules": ["country_import_rules", "country_export_rules", "official_source_review"],
        "required_evidence": [
            "dated official-source links for each country and product category",
            "import/export rule review with claim boundaries",
            "country matrix row owner and last-checked date",
        ],
        "proof_command": "Update data/country_requirements_matrix.json and rerun python3 scripts/run_external_gates.py.",
    },
    {
        "id": "source-rights-freshness",
        "title": "Source rights and data freshness",
        "owner": "data",
        "modules": ["data_freshness"],
        "required_evidence": [
            "source rights and allowed-use notes",
            "repeatable refresh proof with date and source lineage",
            "freshness SLA or explicit fixture-only boundary",
        ],
        "proof_command": "Update source registry/evidence packets and rerun python3 scripts/check_product.py.",
    },
    {
        "id": "contract-terms",
        "title": "Commercial and source contracts",
        "owner": "operations",
        "modules": ["commercial_contract"],
        "required_evidence": [
            "written source, supplier, buyer, or data-use terms",
            "liability, support, termination, and rights boundaries",
            "commercial owner acceptance",
        ],
        "proof_command": "Attach contract evidence to data/evidence_packets.json and rerun python3 scripts/check_product.py.",
    },
    {
        "id": "restricted-party-screening",
        "title": "Restricted-party screening",
        "owner": "compliance",
        "modules": ["restricted_party_screening"],
        "required_evidence": [
            "dated screening result for relevant parties",
            "screening source, jurisdiction, and reviewer",
            "clear pass/fail decision and escalation path",
        ],
        "proof_command": "Update country matrix/evidence packets and rerun python3 scripts/run_external_gates.py.",
    },
    {
        "id": "launch-approval",
        "title": "Launch and public-claim approval",
        "owner": "operator",
        "modules": ["launch_readiness"],
        "required_evidence": [
            "approved public copy and support workflow",
            "release owner signoff",
            "explicit proof that buyer, compliance, contract, and data lanes are closed",
        ],
        "proof_command": "Rerun python3 scripts/check_product.py after all upstream evidence lanes are closed.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _collect_blockers(readiness: dict[str, Any], external: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for source_report, rows in (
        ("readiness_report", readiness.get("blockers", [])),
        ("external_gate_report", external.get("blockers", [])),
    ):
        for row in rows:
            blocker = dict(row)
            blocker["source_report"] = source_report
            blockers.append(blocker)
    return blockers


def _summarize_blocker(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "module": row.get("module"),
        "issue": row.get("issue"),
        "owner": row.get("owner"),
        "evidence": row.get("evidence"),
        "gate": row.get("gate"),
        "next_valid_move": row.get("next_valid_move"),
        "source_report": row.get("source_report"),
    }


def _lane_next_valid_move(lane: dict[str, Any], blockers: list[dict[str, Any]]) -> str:
    if blockers:
        first_move = str(blockers[0].get("next_valid_move") or "").strip()
        if first_move:
            return first_move
    return (
        f"Collect the required evidence for {lane['id']}, attach it to the product data files, "
        "and rerun the product proof gate."
    )


def build_continuation_plan(
    *,
    readiness: dict[str, Any],
    external: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    blockers = _collect_blockers(readiness, external)
    blockers_by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for blocker in blockers:
        blockers_by_module[str(blocker.get("module") or "unknown")].append(blocker)

    lanes: list[dict[str, Any]] = []
    for lane in LANE_DEFINITIONS:
        lane_blockers = [
            blocker
            for module in lane["modules"]
            for blocker in blockers_by_module.get(module, [])
        ]
        if not lane_blockers and not blockers:
            continue
        lanes.append(
            {
                "id": lane["id"],
                "title": lane["title"],
                "owner": lane["owner"],
                "status": "blocked_external_input" if lane_blockers else "pending_evidence_review",
                "source_modules": lane["modules"],
                "blocker_count": len(lane_blockers),
                "blockers": [_summarize_blocker(row) for row in lane_blockers],
                "required_evidence": lane["required_evidence"],
                "next_valid_move": _lane_next_valid_move(lane, lane_blockers),
                "proof_command": lane["proof_command"],
                "unsafe_to_bypass": bool(lane_blockers),
            }
        )

    readiness_status = str(readiness.get("status") or "")
    external_status = str(external.get("status") or "")
    blocker_count = len(blockers)
    must_continue = (
        blocker_count > 0
        or readiness_status == "ready_with_external_gates"
        or external_status == "ready_with_external_gates"
    )
    not_done_reasons = []
    if readiness_status == "ready_with_external_gates":
        not_done_reasons.append("readiness report is internally usable but externally gated")
    if external_status == "ready_with_external_gates":
        not_done_reasons.append("external gate report still has missing evidence")
    if blocker_count:
        not_done_reasons.append(f"{blocker_count} blocker rows require external evidence or qualified review")

    return {
        "generated_at": generated_at or _now(),
        "status": "startup_in_progress" if must_continue else "externally_operational_candidate",
        "software_loop_status": "complete" if readiness_status != "blocked_unsafe" else "blocked_unsafe",
        "local_operator_status": "operator_ready_internal" if readiness_status != "blocked_unsafe" else "unsafe_blocked",
        "readiness_status": readiness_status,
        "external_gate_status": external_status,
        "must_continue": must_continue,
        "lane_count": len(lanes),
        "blocker_count": blocker_count,
        "lanes": lanes,
        "not_done_reasons": not_done_reasons,
        "next_valid_move": (
            "Continue through the evidence lanes before claiming the startup, product, "
            "launch, supplier, customs, tariff, buyer, or commercial flow is done."
            if must_continue
            else "All local and external gates are clear; run a final launch approval review."
        ),
        "proof_boundary": (
            "Local software completion is not startup completion. "
            "ready_with_external_gates means continue with evidence lanes before "
            "operational, launch, legal, customs, supplier, buyer, or commercial claims."
        ),
        "closed_claims": [
            "fully_operational",
            "launch_ready",
            "buyer_validated",
            "qualified_compliance_ready",
            "customs_or_tariff_advice_ready",
            "supplier_recommendation_ready",
            "commercially_ready",
        ],
    }
