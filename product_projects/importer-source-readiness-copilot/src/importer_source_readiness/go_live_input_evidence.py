"""Strict returned-input evidence validation for go-live review.

Returned human inputs are useful only when they include scope, identity,
qualification, dates, and attached proof references. This module evaluates that
evidence without opening any public-launch, payment, customs, buyer, supplier,
privacy, security, or legal claim gates.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATUS = "go_live_returned_input_evidence_ready_claims_closed"
READY_INPUT_DECISIONS = {"ready_for_my_area", "not_applicable_for_this_launch", "go_for_public_launch"}

REVIEW_AREA_ORDER = [
    "real_external_expert_reviews",
    "legal_privacy_security_approval",
    "qualified_customs_trade_review",
    "hosted_staging_production_proof",
    "live_payment_activation",
    "real_users_private_beta_outcomes",
    "buyer_supplier_validation",
    "public_go_no_go_approval",
]

EVIDENCE_RULES: dict[str, dict[str, Any]] = {
    "real_external_expert_reviews": {
        "plain_title": "Outside Expert Review",
        "ready_decisions": {"ready_for_my_area"},
        "reviewer_role_terms": ["reviewer", "expert", "security", "privacy", "legal", "operations", "trade", "payment", "ux", "product"],
        "required_evidence_categories": [
            "review_scope",
            "qualified_reviewer_findings",
            "signed_decision",
            "package_or_commit_reference",
        ],
    },
    "legal_privacy_security_approval": {
        "plain_title": "Legal, Privacy, And Security",
        "ready_decisions": {"ready_for_my_area"},
        "reviewer_role_terms": ["privacy", "legal", "security", "compliance", "counsel", "appsec"],
        "required_evidence_categories": [
            "privacy_notice_or_data_map",
            "security_review_or_scan",
            "ai_data_policy",
            "signed_approval",
        ],
    },
    "qualified_customs_trade_review": {
        "plain_title": "Customs And Trade Language",
        "ready_decisions": {"ready_for_my_area", "not_applicable_for_this_launch"},
        "reviewer_role_terms": ["customs", "broker", "trade", "compliance", "cfia", "freight", "logistics"],
        "required_evidence_categories": [
            "reviewer_credential",
            "country_product_scope",
            "official_source_snapshot",
            "approved_blocked_claim_language",
        ],
        "not_applicable_evidence_categories": [
            "launch_scope_excludes_trade_claims",
            "owner_decision",
            "future_review_trigger",
        ],
    },
    "hosted_staging_production_proof": {
        "plain_title": "Hosted Staging Or Production",
        "ready_decisions": {"ready_for_my_area"},
        "reviewer_role_terms": ["devops", "sre", "operations", "deployment", "infrastructure", "platform"],
        "required_evidence_categories": [
            "live_url_or_environment",
            "commit_or_build",
            "smoke_test_result",
            "monitoring_or_logs",
            "rollback_or_backup",
        ],
    },
    "live_payment_activation": {
        "plain_title": "Payments",
        "ready_decisions": {"ready_for_my_area", "not_applicable_for_this_launch"},
        "reviewer_role_terms": ["payment", "billing", "stripe", "tax", "accounting", "support", "finance"],
        "required_evidence_categories": [
            "stripe_live_or_disabled_scope",
            "webhook_test",
            "tax_refund_support_policy",
            "billing_claim_language",
        ],
        "not_applicable_evidence_categories": [
            "launch_scope_excludes_live_payments",
            "owner_decision",
            "future_activation_condition",
        ],
    },
    "real_users_private_beta_outcomes": {
        "plain_title": "Real User Feedback",
        "ready_decisions": {"ready_for_my_area"},
        "reviewer_role_terms": ["ux", "user", "research", "product", "customer", "beta"],
        "required_evidence_categories": [
            "participant_records",
            "task_results",
            "claim_comprehension",
            "issues_and_changes",
        ],
    },
    "buyer_supplier_validation": {
        "plain_title": "Buyer Or Supplier Validation",
        "ready_decisions": {"ready_for_my_area", "not_applicable_for_this_launch"},
        "reviewer_role_terms": ["founder", "commercial", "sales", "buyer", "supplier", "customer", "market", "partnership"],
        "required_evidence_categories": [
            "counterparty_evidence",
            "problem_validation",
            "permission_scope",
            "screening_or_risk_notes",
        ],
        "not_applicable_evidence_categories": [
            "launch_scope_excludes_validation_claims",
            "owner_decision",
            "future_validation_trigger",
        ],
    },
    "public_go_no_go_approval": {
        "plain_title": "Final Go Live Decision",
        "ready_decisions": {"go_for_public_launch"},
        "reviewer_role_terms": ["owner", "founder", "launch", "operator", "accountable"],
        "required_evidence_categories": [
            "all_gate_summary",
            "release_scope",
            "risk_acceptance",
            "support_and_rollback_owner",
            "signed_go_no_go",
        ],
    },
}

_HEX_RE = re.compile(r"^[a-fA-F0-9]{7,64}$")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return [value]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _field_present(record: dict[str, Any], names: tuple[str, ...]) -> bool:
    return any(bool(_text(record.get(name))) for name in names)


def _missing_identity_fields(record: dict[str, Any]) -> list[str]:
    checks = [
        (("reviewer_name", "approver"), "reviewer or accountable owner name"),
        (("reviewer_role", "approver_role", "qualification_basis", "credential"), "reviewer role or qualification"),
        (("scope_reviewed", "launch_scope", "scope"), "scope reviewed"),
        (("signed_at", "decided_at"), "signed or decided date"),
        (("decision",), "decision"),
    ]
    return [label for fields, label in checks if not _field_present(record, fields)]


def _role_text(record: dict[str, Any]) -> str:
    parts = [
        record.get("reviewer_role"),
        record.get("approver_role"),
        record.get("qualification_basis"),
        record.get("credential"),
        record.get("reviewer_name"),
        record.get("approver"),
    ]
    return " ".join(_text(part).lower() for part in parts if _text(part))


def _role_matches(record: dict[str, Any], terms: list[str]) -> bool:
    haystack = _role_text(record)
    return any(term.lower() in haystack for term in terms)


def _reference_status(reference: str, repo_root: Path | None) -> tuple[bool, str]:
    ref = reference.strip()
    if not ref:
        return False, "empty_reference"
    if _URL_RE.search(ref):
        return True, "url_reference_not_fetched"
    if ref.startswith(("sha256:", "commit:", "package:", "s3://", "gs://")):
        return True, "structured_external_reference"
    if _HEX_RE.fullmatch(ref):
        return True, "commit_or_digest_reference"
    path = Path(ref)
    if path.is_absolute():
        return path.exists(), "local_file_present" if path.exists() else "local_file_missing"
    if repo_root is not None:
        candidate = repo_root / path
        return candidate.exists(), "local_file_present" if candidate.exists() else "local_file_missing"
    if "/" in ref or "." in Path(ref).name:
        return False, "local_file_unchecked"
    return False, "plain_text_not_evidence_reference"


def _evidence_references(record: dict[str, Any], repo_root: Path | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    artifacts = record.get("evidence_artifacts") or record.get("attached_evidence") or {}
    if isinstance(artifacts, dict):
        for category, value in artifacts.items():
            for item in _as_list(value):
                reference = _text(item)
                usable, status = _reference_status(reference, repo_root)
                refs.append(
                    {
                        "category": _text(category),
                        "reference": reference,
                        "usable": usable,
                        "reference_status": status,
                    }
                )
    elif isinstance(artifacts, list):
        for item in artifacts:
            if isinstance(item, dict):
                category = _text(item.get("category") or item.get("type") or item.get("evidence_category"))
                reference = _text(item.get("reference") or item.get("path") or item.get("url") or item.get("file"))
            else:
                category = ""
                reference = _text(item)
            usable, status = _reference_status(reference, repo_root)
            refs.append(
                {
                    "category": category,
                    "reference": reference,
                    "usable": usable,
                    "reference_status": status,
                }
            )
    for item in _as_list(record.get("evidence_links_or_files")):
        reference = _text(item)
        usable, status = _reference_status(reference, repo_root)
        refs.append(
            {
                "category": "",
                "reference": reference,
                "usable": usable,
                "reference_status": status,
            }
        )
    return refs


def _category_tokens(category: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", category.lower()) if len(token) > 3}


def _category_is_fulfilled(category: str, references: list[dict[str, Any]]) -> bool:
    tokens = _category_tokens(category)
    for ref in references:
        if ref.get("usable") is not True:
            continue
        ref_category = _text(ref.get("category")).lower()
        ref_text = f"{ref_category} {_text(ref.get('reference')).lower()}"
        if ref_category == category:
            return True
        if tokens and all(token in ref_text for token in tokens):
            return True
    return False


def required_categories_for_decision(review_area: str, decision: str) -> list[str]:
    rule = EVIDENCE_RULES.get(review_area, {})
    if decision == "not_applicable_for_this_launch":
        return list(rule.get("not_applicable_evidence_categories") or rule.get("required_evidence_categories") or [])
    return list(rule.get("required_evidence_categories") or [])


def validate_go_live_input_record(
    record: dict[str, Any],
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    review_area = _text(record.get("review_area"))
    rule = EVIDENCE_RULES.get(review_area)
    if rule is None:
        return {
            "generated_at": generated_at,
            "review_area": review_area or "missing",
            "plain_title": "",
            "status": "unknown_review_area",
            "accepted_for_area": False,
            "missing_input_fields": ["supported review area"],
            "missing_evidence_categories": [],
            "evidence_reference_count": 0,
            "usable_evidence_reference_count": 0,
            "claims_opened_by_validation": False,
            "external_effects_created": False,
        }

    decision = _text(record.get("decision"))
    missing_fields = _missing_identity_fields(record)
    ready_decisions = set(rule.get("ready_decisions", []))
    ready_decision_candidate = decision in ready_decisions
    evidence_missing = [str(item) for item in _as_list(record.get("evidence_missing")) if _text(item)]
    references = _evidence_references(record, repo_root)
    usable_reference_count = sum(1 for ref in references if ref.get("usable") is True)
    required_categories = required_categories_for_decision(review_area, decision)
    missing_categories = [
        category for category in required_categories if not _category_is_fulfilled(category, references)
    ]
    role_match = _role_matches(record, list(rule.get("reviewer_role_terms", [])))

    if missing_fields:
        status = "received_but_incomplete_identity"
    elif not ready_decision_candidate:
        status = "received_not_ready"
    elif evidence_missing:
        status = "received_needs_more_evidence"
    elif not role_match:
        status = "received_unqualified_reviewer"
    elif missing_categories:
        status = "received_without_required_evidence"
    else:
        status = "accepted_for_area_with_attached_evidence"

    accepted = status == "accepted_for_area_with_attached_evidence"
    return {
        "generated_at": generated_at,
        "review_area": review_area,
        "plain_title": rule["plain_title"],
        "status": status,
        "decision": decision,
        "ready_decision_candidate": ready_decision_candidate,
        "accepted_for_area": accepted,
        "reviewer_name": record.get("reviewer_name") or record.get("approver") or "",
        "reviewer_role": record.get("reviewer_role") or record.get("approver_role") or record.get("credential") or "",
        "scope_reviewed": record.get("scope_reviewed") or record.get("launch_scope") or record.get("scope") or "",
        "signed_at": record.get("signed_at") or record.get("decided_at") or "",
        "source_file": record.get("source_file") or "",
        "missing_input_fields": missing_fields,
        "reviewer_role_terms_required": list(rule.get("reviewer_role_terms", [])),
        "reviewer_role_matched": role_match,
        "required_evidence_categories": required_categories,
        "missing_evidence_categories": missing_categories,
        "evidence_reference_count": len(references),
        "usable_evidence_reference_count": usable_reference_count,
        "evidence_references": references,
        "evidence_missing": evidence_missing,
        "top_issues": [str(item) for item in _as_list(record.get("top_issues")) if _text(item)],
        "claims_the_product_must_not_make": [
            str(item) for item in _as_list(record.get("claims_the_product_must_not_make")) if _text(item)
        ],
        "next_valid_move": _next_valid_move(status, rule["plain_title"]),
        "claims_opened_by_validation": False,
        "external_effects_created": False,
    }


def _next_valid_move(status: str, title: str) -> str:
    if status == "accepted_for_area_with_attached_evidence":
        return "Keep this evidence attached and wait for every other required area plus final owner approval."
    if status == "received_but_incomplete_identity":
        return f"Ask the {title} reviewer or owner to add identity, qualification, scope, decision, and signed date."
    if status == "received_not_ready":
        return f"Resolve the {title} decision before this area can count as accepted."
    if status == "received_needs_more_evidence":
        return f"Collect the missing {title} evidence listed by the reviewer."
    if status == "received_unqualified_reviewer":
        return f"Route the {title} record to a reviewer or owner with matching qualifications."
    if status == "received_without_required_evidence":
        return f"Attach the required {title} evidence references before accepting this area."
    return "Move the record to a supported review area and rerun validation."


def _selected_validation(validations: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in validations if row.get("accepted_for_area") is True]
    candidates = accepted or validations
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: str(row.get("signed_at") or row.get("generated_at") or row.get("source_file") or ""),
    )[-1]


def build_go_live_returned_input_evidence_manifest(
    records: list[dict[str, Any]],
    generated_at: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    validations_by_area: dict[str, list[dict[str, Any]]] = {area: [] for area in REVIEW_AREA_ORDER}
    invalid_records: list[dict[str, Any]] = []
    for record in records:
        validation = validate_go_live_input_record(record, repo_root=repo_root, generated_at=generated_at)
        area = str(validation.get("review_area") or "")
        if area in validations_by_area:
            validations_by_area[area].append(validation)
        else:
            invalid_records.append(validation)

    rows: list[dict[str, Any]] = []
    for area in REVIEW_AREA_ORDER:
        selected = _selected_validation(validations_by_area[area])
        rule = EVIDENCE_RULES[area]
        if selected is None:
            rows.append(
                {
                    "review_area": area,
                    "plain_title": rule["plain_title"],
                    "status": "not_received",
                    "accepted_for_area": False,
                    "decision": "",
                    "source_file": f"external_inputs/{area}.json",
                    "missing_input_fields": ["returned input record"],
                    "missing_evidence_categories": required_categories_for_decision(area, "ready_for_my_area"),
                    "evidence_reference_count": 0,
                    "usable_evidence_reference_count": 0,
                    "record_count_for_area": 0,
                    "next_valid_move": "Collect a dated returned-input record with attached evidence for this area.",
                    "claims_opened_by_validation": False,
                    "external_effects_created": False,
                }
            )
            continue
        rows.append(
            {
                **selected,
                "record_count_for_area": len(validations_by_area[area]),
            }
        )

    accepted_areas = {row["review_area"] for row in rows if row.get("accepted_for_area") is True}
    final_row = next((row for row in rows if row["review_area"] == "public_go_no_go_approval"), {})
    public_launch_ready = (
        len(accepted_areas) == len(REVIEW_AREA_ORDER)
        and final_row.get("decision") == "go_for_public_launch"
    )
    live_payment_row = next((row for row in rows if row["review_area"] == "live_payment_activation"), {})
    return {
        "status": STATUS,
        "generated_at": generated_at,
        "review_area_count": len(REVIEW_AREA_ORDER),
        "input_record_count": len(records),
        "accepted_area_count": len(accepted_areas),
        "not_received_area_count": sum(1 for row in rows if row["status"] == "not_received"),
        "incomplete_area_count": sum(1 for row in rows if row["status"] == "received_but_incomplete_identity"),
        "not_ready_area_count": sum(1 for row in rows if row["status"] == "received_not_ready"),
        "needs_more_evidence_area_count": sum(1 for row in rows if row["status"] == "received_needs_more_evidence"),
        "unqualified_area_count": sum(1 for row in rows if row["status"] == "received_unqualified_reviewer"),
        "missing_evidence_area_count": sum(1 for row in rows if row["status"] == "received_without_required_evidence"),
        "invalid_record_count": len(invalid_records),
        "all_areas_accepted_with_evidence": len(accepted_areas) == len(REVIEW_AREA_ORDER),
        "public_launch_ready_by_evidence": public_launch_ready,
        "hosted_private_beta_ready_by_evidence": all(
            area in accepted_areas
            for area in (
                "real_external_expert_reviews",
                "legal_privacy_security_approval",
                "hosted_staging_production_proof",
            )
        ),
        "live_payment_ready_by_evidence": (
            "live_payment_activation" in accepted_areas
            and live_payment_row.get("decision") != "not_applicable_for_this_launch"
        ),
        "buyer_supplier_validation_ready_by_evidence": (
            "buyer_supplier_validation" in accepted_areas
            and next((row for row in rows if row["review_area"] == "buyer_supplier_validation"), {}).get("decision")
            != "not_applicable_for_this_launch"
        ),
        "validation_rows": rows,
        "invalid_records": invalid_records,
        "claims_opened_by_evidence_validation": False,
        "external_effects_created": False,
        "proof_boundary": (
            "This validates whether returned inputs include scoped, dated, qualified evidence references. "
            "It does not approve public launch, hosted beta, payments, customs/trade claims, privacy/legal/security, "
            "buyer validation, or supplier verification by itself."
        ),
        "next_valid_move": (
            "Run the launch control plane and require final owner approval for the exact scope."
            if public_launch_ready
            else "Collect missing, qualified, scoped, dated evidence for the areas that are not accepted."
        ),
    }


def render_go_live_returned_input_evidence_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Go Live Returned Input Evidence",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Summary",
        "",
        f"- Accepted with evidence: {payload['accepted_area_count']} of {payload['review_area_count']}",
        f"- Not received: {payload['not_received_area_count']}",
        f"- Incomplete identity/scope/date: {payload['incomplete_area_count']}",
        f"- Missing evidence: {payload['missing_evidence_area_count']}",
        f"- Unqualified reviewer/owner: {payload['unqualified_area_count']}",
        f"- Public launch ready by evidence: {str(payload['public_launch_ready_by_evidence']).lower()}",
        f"- Claims opened by validation: {str(payload['claims_opened_by_evidence_validation']).lower()}",
        "",
        "## Validation Matrix",
        "",
        "| Area | Status | Evidence | Next valid move |",
        "| --- | --- | ---: | --- |",
    ]
    for row in payload["validation_rows"]:
        lines.append(
            "| `{}` | `{}` | {} | {} |".format(
                row["review_area"],
                row["status"],
                row["usable_evidence_reference_count"],
                row["next_valid_move"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_go_live_returned_input_evidence_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "go_live_returned_input_evidence_manifest.json"
    matrix_path = graph / "go_live_returned_input_validation_matrix.json"
    doc_path = docs / "GO_LIVE_RETURNED_INPUT_EVIDENCE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    matrix_path.write_text(
        json.dumps(
            {
                "status": "go_live_returned_input_validation_matrix_ready_claims_closed",
                "generated_at": payload["generated_at"],
                "review_area_count": payload["review_area_count"],
                "accepted_area_count": payload["accepted_area_count"],
                "validation_rows": payload["validation_rows"],
                "claims_opened": False,
                "external_effects_created": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    doc_path.write_text(render_go_live_returned_input_evidence_markdown(payload), encoding="utf-8")
    return {"manifest": manifest_path, "matrix": matrix_path, "doc": doc_path}
