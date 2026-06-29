"""Returned external-review intake and gate mapping.

Reviewer packets and blank templates are not evidence. This module defines the
record shape for real returned reviewer decisions, validates returned files, and
exports blocker rows without opening private-beta, launch, trade, payment, or
legal gates by itself.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .external_review import FINDING_FIELDS, REVIEW_ROLES, ReviewRole


STATUS = "external_review_returned_findings_intake_ready_real_reviews_required_claims_closed"
CONTRACT_STATUS = "external_review_returned_finding_contract_ready_claims_closed"
MATRIX_STATUS = "external_review_returned_review_matrix_ready_claims_closed"
BLOCKER_EXPORT_STATUS = "external_review_returned_blocker_export_ready_claims_closed"

ALLOWED_DECISIONS = (
    "approve_within_scope",
    "block",
    "needs_more_evidence",
    "out_of_scope",
    "wrong_reviewer_type",
)

REQUIRED_EVIDENCE_CATEGORIES = (
    "reviewer_identity",
    "credential_or_qualification",
    "scope_reviewed",
    "package_or_commit_reference",
    "signed_decision",
    "findings_or_no_findings_rationale",
)

ROLE_QUALIFICATION_TERMS: dict[str, tuple[str, ...]] = {
    "ux-product": ("ux", "product", "usability", "research", "customer"),
    "security-public-upload": ("security", "appsec", "upload", "file", "risk"),
    "privacy-legal": ("privacy", "legal", "counsel", "compliance", "pipeda"),
    "ai-safety": ("ai", "safety", "prompt", "model", "redaction"),
    "devops-production-readiness": ("devops", "sre", "production", "platform", "infrastructure"),
    "trade-boundary-customs-language": ("trade", "customs", "broker", "cfia", "compliance"),
    "freight-logistics": ("freight", "logistics", "forwarder", "transport", "incoterms"),
    "report-language": ("report", "language", "copy", "content", "compliance"),
    "billing-payment": ("billing", "payment", "stripe", "tax", "finance"),
}


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


def _role_by_id() -> dict[str, ReviewRole]:
    return {role.role_id: role for role in REVIEW_ROLES}


def _role_by_name() -> dict[str, ReviewRole]:
    return {role.reviewer_role.lower(): role for role in REVIEW_ROLES}


def _record_role(record: dict[str, Any]) -> ReviewRole | None:
    role_id = _text(record.get("role_id") or record.get("review_role_id"))
    if role_id in _role_by_id():
        return _role_by_id()[role_id]
    reviewer_role = _text(record.get("reviewer_role")).lower()
    return _role_by_name().get(reviewer_role)


def _field_present(record: dict[str, Any], names: tuple[str, ...]) -> bool:
    return any(bool(_text(record.get(name))) for name in names)


def _missing_identity_fields(record: dict[str, Any]) -> list[str]:
    checks = (
        (("role_id", "review_role_id", "reviewer_role"), "supported reviewer role"),
        (("reviewer_name", "reviewer"), "reviewer name"),
        (("reviewer_role", "reviewer_title", "qualification_basis", "credential"), "reviewer role or qualification"),
        (("scope_reviewed", "scope"), "scope reviewed"),
        (("package_or_commit_ref", "package_ref", "commit_ref"), "package or commit reference"),
        (("signed_at", "reviewed_at", "decided_at"), "signed or reviewed date"),
        (("decision",), "decision"),
    )
    return [label for names, label in checks if not _field_present(record, names)]


def _qualification_matches(role: ReviewRole, record: dict[str, Any]) -> bool:
    haystack = " ".join(
        _text(record.get(field)).lower()
        for field in ("reviewer_role", "reviewer_title", "qualification_basis", "credential", "reviewer_name")
        if _text(record.get(field))
    )
    return any(term in haystack for term in ROLE_QUALIFICATION_TERMS.get(role.role_id, ()))


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


def _missing_evidence_categories(record: dict[str, Any]) -> list[str]:
    present = _evidence_categories(record)
    return [category for category in REQUIRED_EVIDENCE_CATEGORIES if category not in present]


def _finding_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in _as_list(record.get("findings")):
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _invalid_finding_rows(role: ReviewRole, record: dict[str, Any]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for index, finding in enumerate(_finding_rows(record), start=1):
        missing = sorted(set(FINDING_FIELDS) - set(finding))
        role_mismatch = _text(finding.get("reviewer_role")) not in {"", role.reviewer_role}
        severity = _text(finding.get("severity"))
        if missing or role_mismatch or severity not in {"P0", "P1", "P2", "P3"}:
            invalid.append(
                {
                    "index": index,
                    "finding_id": finding.get("finding_id") or f"finding-{index}",
                    "missing_fields": missing,
                    "role_mismatch": role_mismatch,
                    "severity": severity,
                }
            )
    return invalid


def _unresolved_blocking_findings(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for finding in _finding_rows(record):
        severity = _text(finding.get("severity"))
        status = _text(finding.get("status") or "open").lower()
        blocks = finding.get("blocks_private_beta") is True or finding.get("blocks_public_launch") is True
        if severity in {"P0", "P1"} and blocks and status not in {"resolved", "accepted_risk_for_scope"}:
            rows.append(finding)
    return rows


def validate_returned_external_review_record(
    record: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    role = _record_role(record)
    decision = _text(record.get("decision"))
    missing_fields = _missing_identity_fields(record)
    missing_categories = _missing_evidence_categories(record)
    invalid_findings: list[dict[str, Any]] = []
    qualification_matched = False
    unresolved_blocking: list[dict[str, Any]] = []

    if role is not None:
        qualification_matched = _qualification_matches(role, record)
        invalid_findings = _invalid_finding_rows(role, record)
        unresolved_blocking = _unresolved_blocking_findings(record)

    if role is None:
        status = "received_unknown_reviewer_role"
    elif missing_fields:
        status = "received_missing_identity_scope_or_decision"
    elif decision not in ALLOWED_DECISIONS:
        status = "received_unknown_decision"
    elif not qualification_matched:
        status = "received_unqualified_reviewer"
    elif missing_categories:
        status = "received_missing_required_evidence"
    elif invalid_findings:
        status = "received_invalid_finding_rows"
    elif decision == "approve_within_scope" and unresolved_blocking:
        status = "accepted_qualified_review_with_blocking_findings"
    elif decision == "approve_within_scope":
        status = "accepted_qualified_review_no_blocking_findings"
    elif decision in {"block", "needs_more_evidence"}:
        status = "accepted_qualified_review_with_blocking_findings"
    else:
        status = "received_not_accepted_for_scope"

    accepted = status.startswith("accepted_qualified_review")
    scope_approval = status == "accepted_qualified_review_no_blocking_findings"
    return {
        "generated_at": generated_at,
        "status": status,
        "review_id": record.get("review_id") or record.get("id") or "",
        "role_id": role.role_id if role else _text(record.get("role_id") or record.get("review_role_id")),
        "reviewer_role": role.reviewer_role if role else _text(record.get("reviewer_role")),
        "wave": role.wave if role else None,
        "reviewer_name": record.get("reviewer_name") or record.get("reviewer") or "",
        "qualification_basis": record.get("qualification_basis") or record.get("credential") or "",
        "scope_reviewed": record.get("scope_reviewed") or record.get("scope") or "",
        "package_or_commit_ref": record.get("package_or_commit_ref") or record.get("package_ref") or record.get("commit_ref") or "",
        "signed_at": record.get("signed_at") or record.get("reviewed_at") or record.get("decided_at") or "",
        "decision": decision,
        "source_file": record.get("source_file") or "",
        "missing_input_fields": missing_fields,
        "required_evidence_categories": list(REQUIRED_EVIDENCE_CATEGORIES),
        "missing_evidence_categories": missing_categories,
        "qualification_matched": qualification_matched,
        "finding_count": len(_finding_rows(record)),
        "invalid_finding_count": len(invalid_findings),
        "invalid_findings": invalid_findings,
        "unresolved_blocking_finding_count": len(unresolved_blocking),
        "unresolved_blocking_findings": unresolved_blocking,
        "accepted_for_review_evidence": accepted,
        "scope_approval_recorded": scope_approval,
        "blocks_private_beta": (role.blocks_private_beta if role else True) and not scope_approval,
        "blocks_public_launch": (role.blocks_public_launch if role else True) and not scope_approval,
        "claims_opened_by_validation": False,
        "external_effects_created": False,
        "next_valid_move": _next_valid_move(status, role),
    }


def _next_valid_move(status: str, role: ReviewRole | None) -> str:
    label = role.reviewer_role if role else "the reviewer"
    if status == "accepted_qualified_review_no_blocking_findings":
        return f"Keep the scoped {label} approval attached, then wait for every other required review and final owner approval."
    if status == "accepted_qualified_review_with_blocking_findings":
        return f"Convert the {label} findings into owned fixes or explicit blockers and rerun proof."
    if status == "received_unknown_reviewer_role":
        return "Move this record to one of the supported reviewer roles and rerun intake."
    if status == "received_missing_identity_scope_or_decision":
        return f"Ask {label} to add identity, qualification, scope, package or commit reference, date, and decision."
    if status == "received_unknown_decision":
        return f"Ask {label} to use one of the allowed scoped decision values."
    if status == "received_unqualified_reviewer":
        return f"Route the record to a reviewer whose role or credentials match {label}."
    if status == "received_missing_required_evidence":
        return f"Attach the required evidence references before counting the {label} review."
    if status == "received_invalid_finding_rows":
        return f"Fix the {label} finding rows so every finding follows the required schema."
    return f"Keep {label} closed for this scope and collect the right reviewer decision."


def build_returned_external_review_contract(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": CONTRACT_STATUS,
        "generated_at": generated_at,
        "review_role_count": len(REVIEW_ROLES),
        "allowed_decisions": list(ALLOWED_DECISIONS),
        "required_evidence_categories": list(REQUIRED_EVIDENCE_CATEGORIES),
        "finding_fields": list(FINDING_FIELDS),
        "reviewer_roles": [
            {
                "role_id": role.role_id,
                "reviewer_role": role.reviewer_role,
                "wave": role.wave,
                "blocks_private_beta": role.blocks_private_beta,
                "blocks_public_launch": role.blocks_public_launch,
                "drop_path": f"external_review_findings/returned/{role.role_id}.json",
                "qualification_terms": list(ROLE_QUALIFICATION_TERMS.get(role.role_id, ())),
                "scope": role.scope,
            }
            for role in REVIEW_ROLES
        ],
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "This contract describes acceptable returned-review evidence. It is not itself a review or approval.",
    }


def _load_returned_review_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    returned_dir = repo_root / "external_review_findings" / "returned"
    if returned_dir.exists():
        for path in sorted(returned_dir.glob("*.json")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                payload["source_file"] = str(path.relative_to(repo_root))
                records.append(payload)
            elif isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        item["source_file"] = str(path.relative_to(repo_root))
                        records.append(item)
    aggregate = _load_json(repo_root / "external_inputs" / "real_external_expert_reviews.json", {})
    if isinstance(aggregate, dict):
        for item in _as_list(aggregate.get("review_records")):
            if isinstance(item, dict):
                item.setdefault("source_file", "external_inputs/real_external_expert_reviews.json")
                records.append(item)
    return records


def _selected_validation(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in rows if row.get("accepted_for_review_evidence") is True]
    candidates = accepted or rows
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: str(row.get("signed_at") or row.get("generated_at") or row.get("source_file") or ""))[-1]


def _matrix_rows(validations: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    by_role: dict[str, list[dict[str, Any]]] = {role.role_id: [] for role in REVIEW_ROLES}
    for row in validations:
        if row.get("role_id") in by_role:
            by_role[str(row["role_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for role in REVIEW_ROLES:
        selected = _selected_validation(by_role[role.role_id])
        if selected is None:
            rows.append(
                {
                    "generated_at": generated_at,
                    "role_id": role.role_id,
                    "reviewer_role": role.reviewer_role,
                    "wave": role.wave,
                    "status": "not_received",
                    "decision": "",
                    "accepted_for_review_evidence": False,
                    "scope_approval_recorded": False,
                    "record_count_for_role": 0,
                    "unresolved_blocking_finding_count": 0,
                    "blocks_private_beta": role.blocks_private_beta,
                    "blocks_public_launch": role.blocks_public_launch,
                    "source_file": f"external_review_findings/returned/{role.role_id}.json",
                    "next_valid_move": role.next_valid_move,
                    "claims_opened_by_validation": False,
                    "external_effects_created": False,
                }
            )
            continue
        rows.append({**selected, "record_count_for_role": len(by_role[role.role_id])})
    return rows


def _blocker_rows(matrix_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    role_map = _role_by_id()
    for row in matrix_rows:
        role = role_map.get(str(row.get("role_id")))
        if role is None:
            continue
        if row.get("scope_approval_recorded") is True and row.get("unresolved_blocking_finding_count", 0) == 0:
            continue
        if row.get("status") == "not_received":
            rows.append(
                {
                    "id": role.blocker_id,
                    "finding_id": role.blocker_id,
                    "module": "external_review_intake",
                    "reviewer_role": role.reviewer_role,
                    "severity": role.severity_floor,
                    "affected_stage": role.affected_stage,
                    "affected_file_or_artifact": row.get("source_file"),
                    "issue": f"Returned {role.reviewer_role} decision has not been received.",
                    "owner": role.owner,
                    "required_fix": role.required_decision,
                    "retest_command": role.retest_command,
                    "blocks_private_beta": role.blocks_private_beta,
                    "blocks_public_launch": role.blocks_public_launch,
                    "evidence": "external_review_returned_findings_manifest.json records no accepted returned review for this role.",
                    "gate": "closed",
                    "next_valid_move": row["next_valid_move"],
                    "unsafe_to_bypass": True,
                    "created_at": generated_at,
                    "source_report": "system_review_graph/external_review_returned_findings_manifest.json",
                }
            )
            continue
        for index, finding in enumerate(row.get("unresolved_blocking_findings", []), start=1):
            finding_id = _text(finding.get("finding_id") or f"{role.role_id}-returned-{index}")
            rows.append(
                {
                    "id": f"RETURNED-{finding_id}",
                    "finding_id": finding_id,
                    "module": "external_review_intake",
                    "reviewer_role": role.reviewer_role,
                    "severity": finding.get("severity") or role.severity_floor,
                    "affected_stage": finding.get("affected_stage") or role.affected_stage,
                    "affected_file_or_artifact": finding.get("affected_file_or_artifact") or row.get("source_file"),
                    "issue": finding.get("issue") or "Returned reviewer finding blocks this scope.",
                    "owner": finding.get("owner") or role.owner,
                    "required_fix": finding.get("required_fix") or role.required_decision,
                    "retest_command": finding.get("retest_command") or role.retest_command,
                    "blocks_private_beta": finding.get("blocks_private_beta") is True,
                    "blocks_public_launch": finding.get("blocks_public_launch") is True,
                    "evidence": row.get("source_file") or "returned external review record",
                    "gate": "closed",
                    "next_valid_move": row["next_valid_move"],
                    "unsafe_to_bypass": True,
                    "created_at": generated_at,
                    "source_report": "system_review_graph/external_review_returned_findings_manifest.json",
                }
            )
    return rows


def build_returned_external_review_intake(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    records = _load_returned_review_records(root)
    validations = [validate_returned_external_review_record(record, generated_at) for record in records]
    matrix_rows = _matrix_rows(validations, generated_at)
    blocker_rows = _blocker_rows(matrix_rows, generated_at)
    accepted_count = sum(1 for row in matrix_rows if row.get("accepted_for_review_evidence") is True)
    scope_approval_count = sum(1 for row in matrix_rows if row.get("scope_approval_recorded") is True)
    wave_1_rows = [row for row in matrix_rows if row.get("wave") == 1]
    wave_2_rows = [row for row in matrix_rows if row.get("wave") == 2]
    wave_3_rows = [row for row in matrix_rows if row.get("wave") == 3]
    wave_1_scope_ready = all(row.get("scope_approval_recorded") is True for row in wave_1_rows)
    wave_2_scope_ready = all(row.get("scope_approval_recorded") is True for row in wave_2_rows)
    wave_3_scope_ready = all(row.get("scope_approval_recorded") is True for row in wave_3_rows)
    return {
        "status": STATUS,
        "generated_at": generated_at,
        "review_role_count": len(REVIEW_ROLES),
        "returned_record_count": len(records),
        "accepted_review_evidence_count": accepted_count,
        "scope_approval_count": scope_approval_count,
        "pending_review_count": len(REVIEW_ROLES) - accepted_count,
        "unresolved_blocking_finding_count": sum(row.get("unresolved_blocking_finding_count", 0) for row in matrix_rows),
        "blocker_export_count": len(blocker_rows),
        "wave_1_scope_ready_by_evidence": wave_1_scope_ready,
        "wave_2_scope_ready_by_evidence": wave_2_scope_ready,
        "wave_3_scope_ready_by_evidence": wave_3_scope_ready,
        "hosted_private_beta_ready_by_review_evidence": False,
        "public_launch_ready_by_review_evidence": False,
        "live_payment_ready_by_review_evidence": False,
        "claims_opened_by_intake": False,
        "external_effects_created": False,
        "contract": build_returned_external_review_contract(generated_at),
        "review_matrix": {
            "status": MATRIX_STATUS,
            "generated_at": generated_at,
            "review_role_count": len(REVIEW_ROLES),
            "accepted_review_evidence_count": accepted_count,
            "scope_approval_count": scope_approval_count,
            "rows": matrix_rows,
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
        "next_valid_move": (
            "Save real returned reviewer decisions under external_review_findings/returned/, rerun intake, "
            "then fix or explicitly block every returned P0/P1 before changing beta or launch scope."
        ),
        "proof_boundary": (
            "This intake evaluates returned external review records. It cannot create reviewer evidence, "
            "cannot qualify a reviewer by itself, and cannot open private-beta, public-launch, legal, "
            "customs, security, privacy, payment, buyer, or supplier claims without the launch control plane."
        ),
    }


def render_returned_external_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Returned External Review Intake",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Current Result",
        "",
        f"- Returned review records: {payload['returned_record_count']}",
        f"- Accepted review evidence: {payload['accepted_review_evidence_count']} of {payload['review_role_count']}",
        f"- Scope approvals: {payload['scope_approval_count']}",
        f"- Pending reviews: {payload['pending_review_count']}",
        f"- Hosted private beta ready by review evidence: {str(payload['hosted_private_beta_ready_by_review_evidence']).lower()}",
        f"- Public launch ready by review evidence: {str(payload['public_launch_ready_by_review_evidence']).lower()}",
        f"- Claims opened by intake: {str(payload['claims_opened_by_intake']).lower()}",
        "",
        "## Where Returned Reviews Go",
        "",
        "`external_review_findings/returned/{role_id}.json`",
        "",
        "## Review Matrix",
        "",
        "| Role | Status | Decision | Next valid move |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["review_matrix"]["rows"]:
        lines.append(
            f"| {row['reviewer_role']} | `{row['status']}` | `{row.get('decision', '')}` | {row['next_valid_move']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def write_returned_external_review_intake_artifacts(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    graph = root / "system_review_graph"
    docs = root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    payload = build_returned_external_review_intake(root, generated_at)
    (graph / "external_review_returned_finding_contract.json").write_text(
        _render_json(payload["contract"]),
        encoding="utf-8",
    )
    (graph / "external_review_returned_findings_manifest.json").write_text(
        _render_json({key: value for key, value in payload.items() if key not in {"contract", "review_matrix", "blocker_export"}}),
        encoding="utf-8",
    )
    (graph / "external_review_returned_review_matrix.json").write_text(
        _render_json(payload["review_matrix"]),
        encoding="utf-8",
    )
    (graph / "external_review_returned_blocker_export.jsonl").write_text(
        _render_jsonl(payload["blocker_export"]["rows"]),
        encoding="utf-8",
    )
    (docs / "EXTERNAL_REVIEW_RETURNED_FINDINGS.md").write_text(
        render_returned_external_review_markdown(payload),
        encoding="utf-8",
    )
    return {
        "status": payload["status"],
        "returned_record_count": payload["returned_record_count"],
        "accepted_review_evidence_count": payload["accepted_review_evidence_count"],
        "pending_review_count": payload["pending_review_count"],
        "blocker_export_count": payload["blocker_export_count"],
        "claims_opened_by_intake": payload["claims_opened_by_intake"],
        "public_launch_ready_by_review_evidence": payload["public_launch_ready_by_review_evidence"],
        "generated_at": generated_at,
    }
