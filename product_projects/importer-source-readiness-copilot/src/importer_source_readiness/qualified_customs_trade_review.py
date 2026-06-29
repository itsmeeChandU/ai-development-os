"""Qualified customs/trade review proof intake.

Country packs and source routes help prepare a packet, but they are not
qualified customs, tariff, CFIA, sanctions, or shipment advice. This module
validates returned customs/trade review evidence for the exact product lane and
keeps approval-style claims closed unless a future workflow with lawful scope
and explicit qualified proof supports that wording.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATUS = "qualified_customs_trade_review_intake_ready_real_review_evidence_required_claims_closed"
CONTRACT_STATUS = "qualified_customs_trade_review_contract_ready_claims_closed"
GATE_MATRIX_STATUS = "qualified_customs_trade_review_gate_matrix_ready_claims_closed"
BLOCKER_EXPORT_STATUS = "qualified_customs_trade_review_blocker_export_ready_claims_closed"

ALLOWED_DECISIONS = (
    "approve_preparation_language_for_scope",
    "approve_demo_reference_only",
    "not_applicable_for_this_launch",
    "keep_blocked",
    "needs_more_evidence",
)

REQUIRED_REVIEWER_ROLES = (
    "customs_trade_reviewer",
)

REGULATED_GOODS_REVIEWER_ROLE = "regulated_goods_reviewer"

ROLE_ALIASES = {
    "licensed_customs_broker": ("customs_trade_reviewer",),
    "qualified_trade_compliance_reviewer": ("customs_trade_reviewer",),
    "trade_compliance_specialist": ("customs_trade_reviewer",),
    "customs_broker_or_trade_compliance_specialist": ("customs_trade_reviewer",),
    "cfia_food_import_reviewer": ("regulated_goods_reviewer",),
    "food_import_compliance_reviewer": ("regulated_goods_reviewer",),
}

REVIEW_SCOPE_TYPES = (
    "canada_import_preparation",
    "canada_import_food_or_regulated_goods_preparation",
    "origin_export_to_canada_preparation",
    "buyer_broker_packet_language_review",
)

DEMO_SCOPE_TYPES = (
    "demo_reference_only",
    "launch_scope_excludes_trade_claims",
)

REQUIRED_PROOF_CATEGORIES: tuple[dict[str, str], ...] = (
    {
        "category": "review_scope_product_lane",
        "label": "Review scope, product, and lane",
        "why": "The reviewer must know the product, origin, destination, direction, intended use, and exact packet scope.",
    },
    {
        "category": "reviewer_identity_qualification_scope",
        "label": "Reviewer identity, qualification, and scope",
        "why": "Customs/trade review needs a named qualified reviewer and a scope limitation tied to the reviewed packet.",
    },
    {
        "category": "cbsa_importer_obligations_review",
        "label": "CBSA importer obligations review",
        "why": "Business/RM account, importer responsibility, accounting, and other government requirement routing must be reviewed for the lane.",
    },
    {
        "category": "broker_boundary_importer_responsibility",
        "label": "Broker boundary and importer responsibility",
        "why": "The product must not act as a customs broker and must preserve importer responsibility language.",
    },
    {
        "category": "hs_candidate_classification_boundary",
        "label": "HS candidate and classification boundary",
        "why": "HS candidates can support research only; classification and tariff treatment need qualified review or authoritative evidence.",
    },
    {
        "category": "customs_tariff_treatment_review",
        "label": "Customs tariff/treatment review",
        "why": "Tariff source routes, duty treatment, and tariff wording must be checked before any stronger statement is allowed.",
    },
    {
        "category": "origin_preference_document_review",
        "label": "Origin, preference, and origin-document review",
        "why": "Origin or preferential treatment language needs origin evidence and reviewer scope, not just origin country text.",
    },
    {
        "category": "regulated_goods_cfia_airs_review",
        "label": "Regulated goods and CFIA/AIRS review",
        "why": "Food, seafood, plant, animal, and other regulated-product routes need dated CFIA/AIRS or reviewer evidence.",
    },
    {
        "category": "sanctions_import_export_controls_review",
        "label": "Sanctions and import/export controls review",
        "why": "Restricted countries, parties, controls, and prohibited-goods issues need dated source checks and reviewer notes.",
    },
    {
        "category": "required_documents_accounting_review",
        "label": "Required documents and accounting review",
        "why": "Commercial invoice, packing list, origin, permits/certificates, accounting, and record requirements need a scoped evidence list.",
    },
    {
        "category": "incoterms_importer_of_record_responsibility",
        "label": "Incoterms, importer of record, and responsibility path",
        "why": "Responsibility for import, export, customs, freight, documents, and broker review must be explicit.",
    },
    {
        "category": "allowed_blocked_claim_language",
        "label": "Allowed and blocked claim language",
        "why": "The reviewer must state which preparation language is allowed and which approval-style claims remain blocked.",
    },
    {
        "category": "unresolved_findings_next_actions",
        "label": "Unresolved findings and next actions",
        "why": "Open customs/trade findings need severity, owner, next action, and review-before-use status.",
    },
    {
        "category": "reviewer_signed_scope_decision",
        "label": "Reviewer signed scope decision",
        "why": "A dated decision is required before the finding can count as returned qualified review evidence.",
    },
)

DEMO_SCOPE_CATEGORIES = (
    "launch_scope_excludes_trade_claims",
    "owner_decision",
    "future_review_trigger",
)

SOURCE_ANCHORS: tuple[dict[str, str], ...] = (
    {
        "source_id": "cbsa-import-commercial-goods",
        "name": "Importing commercial goods into Canada",
        "publisher": "Canada Border Services Agency",
        "url": "https://www.cbsa-asfc.gc.ca/import/menu-eng.html",
        "checked_at": "2026-06-29",
        "product_use": "Importer workflow, business/import account, tariff, origin, rulings, accounting, and other government requirement routing.",
    },
    {
        "source_id": "cbsa-licensed-customs-brokers",
        "name": "Licensed customs brokers",
        "publisher": "Canada Border Services Agency",
        "url": "https://www.cbsa-asfc.gc.ca/services/cb-cd/cb-cd-eng.html",
        "checked_at": "2026-06-29",
        "product_use": "Broker boundary, importer responsibility, and licensed-broker review lane anchor.",
    },
    {
        "source_id": "cbsa-customs-tariff-2026",
        "name": "Canadian Customs Tariff 2026",
        "publisher": "Canada Border Services Agency",
        "url": "https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/2026/menu-eng.html",
        "checked_at": "2026-06-29",
        "product_use": "Tariff source routing and HS/tariff candidate review anchor.",
    },
    {
        "source_id": "cfia-airs",
        "name": "Automated Import Reference System",
        "publisher": "Canadian Food Inspection Agency",
        "url": "https://inspection.canada.ca/en/importing-food-plants-animals/airs",
        "checked_at": "2026-06-29",
        "product_use": "CFIA-regulated food, plant, animal, and commodity requirement routing anchor.",
    },
    {
        "source_id": "gac-sanctions",
        "name": "Canadian sanctions",
        "publisher": "Global Affairs Canada",
        "url": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/current-actuelles.aspx",
        "checked_at": "2026-06-29",
        "product_use": "Sanctions, restricted-country, and restricted-party warning route anchor.",
    },
    {
        "source_id": "gac-import-export-controls",
        "name": "Export and import controls",
        "publisher": "Global Affairs Canada",
        "url": "https://www.international.gc.ca/controls-controles/index.aspx",
        "checked_at": "2026-06-29",
        "product_use": "Import/export controls and permits route anchor.",
    },
    {
        "source_id": "wco-harmonized-system",
        "name": "Harmonized System",
        "publisher": "World Customs Organization",
        "url": "https://www.wcoomd.org/en/topics/nomenclature/overview/what-is-the-harmonized-system.aspx",
        "checked_at": "2026-06-29",
        "product_use": "HS six-digit candidate and classification-boundary anchor.",
    },
    {
        "source_id": "icc-incoterms-2020",
        "name": "Incoterms 2020",
        "publisher": "International Chamber of Commerce",
        "url": "https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/",
        "checked_at": "2026-06-29",
        "product_use": "Responsibility, costs, risk, and seller/buyer task split anchor.",
    },
    {
        "source_id": "india-dgft-iec",
        "name": "Importer Exporter Code",
        "publisher": "Directorate General of Foreign Trade",
        "url": "https://www.dgft.gov.in/CP/?opt=iec-profile-management",
        "checked_at": "2026-06-29",
        "product_use": "India origin/exporter identity and export-readiness routing anchor.",
    },
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _evidence_categories(record: dict[str, Any]) -> set[str]:
    categories: set[str] = set()
    evidence = record.get("evidence_artifacts") or record.get("attached_evidence") or {}
    if isinstance(evidence, dict):
        for category, value in evidence.items():
            if _text(category) and any(_text(item) for item in _as_list(value)):
                categories.add(_text(category))
    elif isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                category = _text(item.get("category") or item.get("type") or item.get("evidence_category"))
                reference = _text(item.get("reference") or item.get("path") or item.get("url") or item.get("file"))
                if category and reference:
                    categories.add(category)
    return categories


def _reviewer_roles(record: dict[str, Any]) -> set[str]:
    roles: set[str] = set()
    for value in _as_list(record.get("reviewer_roles") or record.get("reviewer_role")):
        role = _text(value).lower()
        if not role:
            continue
        if role in ROLE_ALIASES:
            roles.update(ROLE_ALIASES[role])
        else:
            roles.add(role)
    return roles


def _missing_identity_fields(record: dict[str, Any]) -> list[str]:
    checks = (
        (("review_scope_id", "review_scope_name"), "review scope id or name"),
        (("review_scope_type",), "review scope type"),
        (("origin_country",), "origin country"),
        (("destination_country",), "destination country"),
        (("product_or_hs_description", "product_description"), "product or HS description"),
        (("reviewer_name",), "reviewer name"),
        (("reviewer_qualification", "qualification_summary"), "reviewer qualification"),
        (("reviewed_at", "signed_at", "checked_at"), "reviewed or signed date"),
        (("build_or_commit_ref", "commit_ref", "build_ref"), "build or commit reference"),
        (("decision",), "decision"),
    )
    missing = []
    for names, label in checks:
        if not any(_text(record.get(name)) for name in names):
            missing.append(label)
    return missing


def _regulated_review_required(record: dict[str, Any]) -> bool:
    if record.get("regulated_goods_review_required") is True:
        return True
    text = " ".join(
        _text(record.get(key)).lower()
        for key in ("review_scope_type", "product_or_hs_description", "product_description", "product_category")
    )
    return any(token in text for token in ("food", "seafood", "fish", "plant", "animal", "cfia", "regulated"))


def _required_categories_for_decision(decision: str) -> tuple[str, ...]:
    if decision in {"approve_demo_reference_only", "not_applicable_for_this_launch"}:
        return DEMO_SCOPE_CATEGORIES
    return tuple(item["category"] for item in REQUIRED_PROOF_CATEGORIES)


def validate_qualified_customs_trade_review_record(
    record: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    missing_fields = _missing_identity_fields(record)
    decision = _text(record.get("decision"))
    review_scope_type = _text(record.get("review_scope_type"))
    roles = _reviewer_roles(record)
    missing_roles = [role for role in REQUIRED_REVIEWER_ROLES if role not in roles]
    regulated_required = _regulated_review_required(record)
    if regulated_required and REGULATED_GOODS_REVIEWER_ROLE not in roles:
        missing_roles.append(REGULATED_GOODS_REVIEWER_ROLE)
    required_categories = _required_categories_for_decision(decision)
    attached_categories = _evidence_categories(record)
    missing_categories = [category for category in required_categories if category not in attached_categories]
    review_scope = review_scope_type in REVIEW_SCOPE_TYPES
    demo_scope = review_scope_type in DEMO_SCOPE_TYPES

    if missing_fields:
        status = "received_missing_customs_trade_identity"
    elif decision not in ALLOWED_DECISIONS:
        status = "received_unknown_customs_trade_decision"
    elif decision == "approve_preparation_language_for_scope" and not review_scope:
        status = "received_preparation_approval_without_supported_scope"
    elif decision in {"approve_demo_reference_only", "not_applicable_for_this_launch"} and not demo_scope:
        status = "received_demo_or_not_applicable_without_demo_scope"
    elif decision == "approve_preparation_language_for_scope" and missing_roles:
        status = "received_missing_required_customs_trade_reviewer_roles"
    elif not (review_scope or demo_scope):
        status = "received_unsupported_customs_trade_scope"
    elif missing_categories:
        status = "received_missing_required_customs_trade_evidence"
    elif decision == "approve_preparation_language_for_scope":
        status = "accepted_qualified_customs_trade_preparation_scope_evidence"
    elif decision in {"approve_demo_reference_only", "not_applicable_for_this_launch"}:
        status = "accepted_customs_trade_demo_or_no_claim_scope_evidence"
    else:
        status = "received_customs_trade_not_ready"

    accepted = status in {
        "accepted_qualified_customs_trade_preparation_scope_evidence",
        "accepted_customs_trade_demo_or_no_claim_scope_evidence",
    }
    reviewed_by_evidence = status == "accepted_qualified_customs_trade_preparation_scope_evidence"
    return {
        "generated_at": generated_at,
        "status": status,
        "review_scope_id": record.get("review_scope_id") or record.get("review_scope_name") or "",
        "review_scope_type": review_scope_type,
        "origin_country": record.get("origin_country") or "",
        "destination_country": record.get("destination_country") or "",
        "product_or_hs_description": record.get("product_or_hs_description") or record.get("product_description") or "",
        "regulated_goods_review_required": regulated_required,
        "reviewer_name": record.get("reviewer_name") or "",
        "reviewer_roles": sorted(roles),
        "missing_reviewer_roles": sorted(set(missing_roles)),
        "reviewer_qualification": record.get("reviewer_qualification") or record.get("qualification_summary") or "",
        "reviewed_at": record.get("reviewed_at") or record.get("signed_at") or record.get("checked_at") or "",
        "build_or_commit_ref": record.get("build_or_commit_ref") or record.get("commit_ref") or record.get("build_ref") or "",
        "decision": decision,
        "source_file": record.get("source_file") or "",
        "missing_input_fields": missing_fields,
        "required_evidence_categories": list(required_categories),
        "missing_evidence_categories": missing_categories,
        "accepted_for_customs_trade_review_evidence": accepted,
        "customs_trade_reviewed_by_evidence": reviewed_by_evidence,
        "tariff_confirmed_by_review_evidence": False,
        "cfia_approved_by_review_evidence": False,
        "customs_ready_by_review_evidence": False,
        "shipment_ready_by_review_evidence": False,
        "public_launch_ready_by_review_evidence": False,
        "claims_opened_by_validation": False,
        "external_effects_created": False,
        "next_valid_move": _next_valid_move(status),
    }


def _next_valid_move(status: str) -> str:
    if status == "accepted_qualified_customs_trade_preparation_scope_evidence":
        return "Keep scoped customs/trade review attached for preparation language only; approval-style customs, tariff, CFIA, and shipment claims stay blocked."
    if status == "accepted_customs_trade_demo_or_no_claim_scope_evidence":
        return "Use this only for demo/reference or no-trade-claim scope; collect scoped qualified review before any stronger trade wording."
    if status == "received_missing_customs_trade_identity":
        return "Add scope, lane, product, reviewer, qualification, date, build reference, and decision."
    if status == "received_unknown_customs_trade_decision":
        return "Use one of the allowed customs/trade decisions and rerun validation."
    if status == "received_preparation_approval_without_supported_scope":
        return "Use a supported customs/trade review scope for preparation-language approval."
    if status == "received_demo_or_not_applicable_without_demo_scope":
        return "Use demo_reference_only or launch_scope_excludes_trade_claims for demo/no-claim decisions."
    if status == "received_missing_required_customs_trade_reviewer_roles":
        return "Attach qualified customs/trade reviewer coverage and regulated-goods reviewer coverage when CFIA/regulated goods are in scope."
    if status == "received_unsupported_customs_trade_scope":
        return "Use a supported Canada import, regulated-goods, origin-export, broker-packet, or demo/no-claim review scope."
    if status == "received_missing_required_customs_trade_evidence":
        return "Attach every required customs/trade evidence category before counting qualified review proof."
    return "Resolve customs/trade review evidence issues and keep tariff, CFIA, customs, shipment, and launch claims closed."


def build_qualified_customs_trade_review_contract(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": CONTRACT_STATUS,
        "generated_at": generated_at,
        "allowed_decisions": list(ALLOWED_DECISIONS),
        "required_reviewer_roles": list(REQUIRED_REVIEWER_ROLES),
        "regulated_goods_reviewer_role": REGULATED_GOODS_REVIEWER_ROLE,
        "review_scope_types": list(REVIEW_SCOPE_TYPES),
        "demo_scope_types": list(DEMO_SCOPE_TYPES),
        "required_evidence_categories": list(REQUIRED_PROOF_CATEGORIES),
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "demo_scope_evidence_categories": list(DEMO_SCOPE_CATEGORIES),
        "source_anchors": list(SOURCE_ANCHORS),
        "source_anchor_count": len(SOURCE_ANCHORS),
        "drop_paths": [
            "external_inputs/qualified_customs_trade_review.json",
            "external_inputs/qualified_customs_trade_reviews/*.json",
        ],
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "This contract defines scoped customs/trade review evidence for preparation-language review only. It does not confirm tariff treatment, approve CFIA/admissibility, act as a customs broker, approve shipment, or approve public launch.",
    }


def _load_review_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    single = _load_json(repo_root / "external_inputs" / "qualified_customs_trade_review.json", {})
    if isinstance(single, dict) and single:
        single["source_file"] = "external_inputs/qualified_customs_trade_review.json"
        records.append(single)
    proof_dir = repo_root / "external_inputs" / "qualified_customs_trade_reviews"
    if proof_dir.exists():
        for path in sorted(proof_dir.glob("*.json")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                payload["source_file"] = str(path.relative_to(repo_root))
                records.append(payload)
    return records


def _selected_validation(validations: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in validations if row.get("accepted_for_customs_trade_review_evidence") is True]
    candidates = accepted or validations
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: str(row.get("reviewed_at") or row.get("generated_at") or row.get("source_file") or ""))[-1]


def _gate_rows(selected: dict[str, Any] | None, generated_at: str) -> list[dict[str, Any]]:
    rows = []
    selected_required = set(selected.get("required_evidence_categories", [])) if selected else set()
    selected_missing = set(selected.get("missing_evidence_categories", [])) if selected else set()
    for item in REQUIRED_PROOF_CATEGORIES:
        category = item["category"]
        in_scope = selected is None or category in selected_required
        missing = selected is None or (in_scope and category in selected_missing)
        rows.append(
            {
                "generated_at": generated_at,
                "gate_id": f"qualified_customs_trade:{category}",
                "category": category,
                "label": item["label"],
                "status": "missing_real_customs_trade_review_evidence" if missing else "evidence_attached_for_review",
                "blocks_customs_trade_review": missing,
                "blocks_tariff_claims": True,
                "blocks_cfia_claims": True,
                "blocks_customs_ready_claims": True,
                "blocks_shipment_claims": True,
                "blocks_public_launch": True,
                "why": item["why"],
                "claims_opened_by_gate": False,
                "external_effects_created": False,
            }
        )
    return rows


def _blocker_rows(gate_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows = []
    for row in gate_rows:
        if row["blocks_customs_trade_review"] is not True:
            continue
        rows.append(
            {
                "id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "finding_id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "module": "qualified_customs_trade_review",
                "reviewer_role": "Qualified Customs/Trade Review",
                "severity": "P0",
                "affected_stage": "qualified_customs_trade_review",
                "affected_file_or_artifact": "system_review_graph/qualified_customs_trade_review_manifest.json",
                "issue": f"Qualified customs/trade review proof missing: {row['label']}.",
                "owner": "customs/trade reviewer",
                "required_fix": row["why"],
                "retest_command": "python3 scripts/check_product.py",
                "blocks_private_beta": True,
                "blocks_public_launch": True,
                "evidence": "qualified_customs_trade_review_manifest.json records missing scoped customs/trade review evidence.",
                "gate": "closed",
                "next_valid_move": "Attach real scoped customs/trade review proof or a no-trade-claim launch decision and rerun qualified review intake.",
                "unsafe_to_bypass": True,
                "created_at": generated_at,
                "source_report": "system_review_graph/qualified_customs_trade_review_manifest.json",
            }
        )
    return rows


def build_qualified_customs_trade_review_intake(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    records = _load_review_records(root)
    validations = [validate_qualified_customs_trade_review_record(record, generated_at) for record in records]
    selected = _selected_validation(validations)
    gate_rows = _gate_rows(selected, generated_at)
    blocker_rows = _blocker_rows(gate_rows, generated_at)
    accepted_count = sum(1 for row in validations if row["accepted_for_customs_trade_review_evidence"] is True)
    reviewed_by_evidence = selected is not None and selected.get("customs_trade_reviewed_by_evidence") is True
    return {
        "status": STATUS,
        "generated_at": generated_at,
        "review_record_count": len(records),
        "accepted_review_record_count": accepted_count,
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "attached_evidence_category_count": 0
        if selected is None
        else len(selected.get("required_evidence_categories", [])) - len(selected.get("missing_evidence_categories", [])),
        "missing_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES)
        if selected is None
        else len(selected.get("missing_evidence_categories", [])),
        "gate_count": len(gate_rows),
        "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_customs_trade_review"] is True),
        "blocker_export_count": len(blocker_rows),
        "selected_validation": selected or {},
        "validations": validations,
        "customs_trade_reviewed_by_evidence": reviewed_by_evidence,
        "tariff_confirmed_by_review_evidence": False,
        "cfia_approved_by_review_evidence": False,
        "customs_ready_by_review_evidence": False,
        "shipment_ready_by_review_evidence": False,
        "public_launch_ready_by_review_evidence": False,
        "claims_opened_by_intake": False,
        "external_effects_created": False,
        "contract": build_qualified_customs_trade_review_contract(generated_at),
        "gate_matrix": {
            "status": GATE_MATRIX_STATUS,
            "generated_at": generated_at,
            "gate_count": len(gate_rows),
            "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_customs_trade_review"] is True),
            "rows": gate_rows,
            "claims_opened": False,
            "external_effects_created": False,
        },
        "blocker_export": {
            "status": BLOCKER_EXPORT_STATUS,
            "generated_at": generated_at,
            "blocker_count": len(blocker_rows),
            "rows": blocker_rows,
            "claims_opened": False,
            "external_effects_created": False,
        },
        "next_valid_move": "Attach scoped qualified customs/trade review proof or a no-trade-claim decision, then rerun qualified review intake.",
        "proof_boundary": (
            "This validates scoped customs/trade review evidence only. It does not confirm tariff treatment, "
            "approve CFIA/admissibility, act as a customs broker, approve shipment, or approve public launch."
        ),
    }


def render_qualified_customs_trade_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Qualified Customs Trade Review Proof",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Current Result",
        "",
        f"- Review records received: {payload['review_record_count']}",
        f"- Accepted review records: {payload['accepted_review_record_count']}",
        f"- Missing evidence categories: {payload['missing_evidence_category_count']}",
        f"- Customs/trade reviewed by evidence: {str(payload['customs_trade_reviewed_by_evidence']).lower()}",
        f"- Tariff confirmed by review evidence: {str(payload['tariff_confirmed_by_review_evidence']).lower()}",
        f"- CFIA approved by review evidence: {str(payload['cfia_approved_by_review_evidence']).lower()}",
        f"- Customs ready by review evidence: {str(payload['customs_ready_by_review_evidence']).lower()}",
        f"- Shipment ready by review evidence: {str(payload['shipment_ready_by_review_evidence']).lower()}",
        f"- Claims opened by intake: {str(payload['claims_opened_by_intake']).lower()}",
        "",
        "## Drop Paths",
        "",
        "- `external_inputs/qualified_customs_trade_review.json`",
        "- `external_inputs/qualified_customs_trade_reviews/*.json`",
        "",
        "## Gate Matrix",
        "",
        "| Evidence | Status | Blocks Review |",
        "| --- | --- | --- |",
    ]
    for row in payload["gate_matrix"]["rows"]:
        lines.append(f"| {row['label']} | `{row['status']}` | `{str(row['blocks_customs_trade_review']).lower()}` |")
    lines.extend(["", "## Source Anchors", ""])
    for source in payload["contract"]["source_anchors"]:
        lines.append(f"- {source['publisher']}: {source['name']} ({source['url']})")
    lines.append("")
    return "\n".join(lines)


def _render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def write_qualified_customs_trade_review_artifacts(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    graph = root / "system_review_graph"
    docs = root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    payload = build_qualified_customs_trade_review_intake(root, generated_at)
    (graph / "qualified_customs_trade_review_contract.json").write_text(_render_json(payload["contract"]), encoding="utf-8")
    manifest_payload = {key: value for key, value in payload.items() if key not in {"contract", "gate_matrix", "blocker_export"}}
    (graph / "qualified_customs_trade_review_manifest.json").write_text(_render_json(manifest_payload), encoding="utf-8")
    (graph / "qualified_customs_trade_review_gate_matrix.json").write_text(_render_json(payload["gate_matrix"]), encoding="utf-8")
    (graph / "qualified_customs_trade_review_blocker_export.jsonl").write_text(
        _render_jsonl(payload["blocker_export"]["rows"]),
        encoding="utf-8",
    )
    (docs / "QUALIFIED_CUSTOMS_TRADE_REVIEW_PROOF.md").write_text(
        render_qualified_customs_trade_review_markdown(payload),
        encoding="utf-8",
    )
    return {
        "status": payload["status"],
        "review_record_count": payload["review_record_count"],
        "accepted_review_record_count": payload["accepted_review_record_count"],
        "blocked_gate_count": payload["blocked_gate_count"],
        "blocker_export_count": payload["blocker_export_count"],
        "customs_trade_reviewed_by_evidence": payload["customs_trade_reviewed_by_evidence"],
        "tariff_confirmed_by_review_evidence": payload["tariff_confirmed_by_review_evidence"],
        "claims_opened_by_intake": payload["claims_opened_by_intake"],
        "generated_at": generated_at,
    }
