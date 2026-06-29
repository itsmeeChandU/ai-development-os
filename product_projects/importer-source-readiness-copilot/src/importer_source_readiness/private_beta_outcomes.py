"""Private-beta outcome contract and evidence evaluator.

The smoke-test plan says which beta wave should happen. This module defines
what a real session record must contain before it can count as private-beta
evidence. Internal demos, simulated sessions, and incomplete user notes remain
useful for product work, but they do not open launch gates.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATUS = "private_beta_outcome_contract_ready_real_users_required_claims_closed"
SCHEMA_STATUS = "private_beta_session_evidence_schema_ready_claims_closed"
GATE_MATRIX_STATUS = "private_beta_outcome_gate_matrix_ready_claims_closed"

REQUIRED_SEGMENTS: tuple[dict[str, Any], ...] = (
    {
        "segment": "beginner_user_no_documents",
        "required_count": 2,
        "plain_description": "Beginner exporter or importer who does not yet have trade documents.",
    },
    {
        "segment": "document_holding_import_or_export_user",
        "required_count": 2,
        "plain_description": "Business user who has at least one trade document to inspect.",
    },
    {
        "segment": "operator_or_consultant_style_user",
        "required_count": 1,
        "plain_description": "Advisor, operator, consultant, or internal reviewer style user who can assess workflow fit.",
    },
)

OPTIONAL_SEGMENTS: tuple[dict[str, Any], ...] = (
    {
        "segment": "reviewer_broker_or_freight_forwarder_style_user",
        "required_count": 0,
        "plain_description": "Customs broker, freight forwarder, or reviewer style user. Useful before launch, not counted in the five-user minimum.",
    },
)

TASKS: tuple[dict[str, Any], ...] = (
    {
        "task_id": "beginner_starter_flow",
        "label": "Start a beginner trade-readiness flow",
        "route": "/start",
        "required_for_segments": ["beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"],
    },
    {
        "task_id": "pdf_upload_quick_check",
        "label": "Run the PDF upload quick check",
        "route": "/trade-check",
        "required_for_segments": ["document_holding_import_or_export_user", "operator_or_consultant_style_user"],
        "allowed_not_applicable_segments": ["beginner_user_no_documents"],
    },
    {
        "task_id": "confirm_extracted_fields",
        "label": "Confirm extracted fields or explain why no document was available",
        "route": "/trade-check",
        "required_for_segments": ["beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"],
    },
    {
        "task_id": "download_reports",
        "label": "Download starter and missing-evidence reports",
        "route": "/reports",
        "required_for_segments": ["beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"],
    },
    {
        "task_id": "save_packet_or_workspace",
        "label": "Save a packet or open a workspace",
        "route": "/workspace",
        "required_for_segments": ["beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"],
    },
    {
        "task_id": "delete_files_request",
        "label": "Use deletion or retention controls",
        "route": "/privacy",
        "required_for_segments": ["document_holding_import_or_export_user", "operator_or_consultant_style_user"],
        "allowed_not_applicable_segments": ["beginner_user_no_documents"],
    },
    {
        "task_id": "chatgpt_safe_summary",
        "label": "Open the ChatGPT-safe summary or no-AI alternative",
        "route": "/summary",
        "required_for_segments": ["beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"],
    },
    {
        "task_id": "buyer_broker_packet",
        "label": "Open the buyer or broker packet",
        "route": "/packets",
        "required_for_segments": ["beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"],
    },
    {
        "task_id": "blocked_claims_next_move",
        "label": "Read blocked claims and the next valid move",
        "route": "/blocked-claims",
        "required_for_segments": ["beginner_user_no_documents", "document_holding_import_or_export_user", "operator_or_consultant_style_user"],
    },
)

CLAIM_COMPREHENSION_CHECKS: tuple[dict[str, str], ...] = (
    {
        "field": "participant_understood_no_customs_approval",
        "question": "Did the user understand the product is not customs approval?",
    },
    {
        "field": "participant_understood_no_buyer_validation",
        "question": "Did the user understand a lead or report is not buyer validation?",
    },
    {
        "field": "participant_understood_no_supplier_verification",
        "question": "Did the user understand collected supplier documents are not supplier verification?",
    },
    {
        "field": "participant_understood_next_valid_move",
        "question": "Could the user explain the next valid move in plain language?",
    },
)

REQUIRED_EVIDENCE_CATEGORIES: tuple[str, ...] = (
    "participant_profile",
    "consent_or_permission",
    "session_date_and_environment",
    "task_results",
    "claim_comprehension",
    "privacy_or_deletion_result",
    "issues_and_changes",
    "artifact_or_recording_references",
    "outcome_decision",
)

SOURCE_ANCHORS: tuple[dict[str, str], ...] = (
    {
        "source_id": "nng-usability-five-users",
        "name": "Why You Only Need to Test with 5 Users",
        "publisher": "Nielsen Norman Group",
        "url": "https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/",
        "checked_at": "2026-06-29",
        "product_use": "Supports a small qualitative first beta wave, not statistical validation.",
    },
    {
        "source_id": "opc-pipeda-principles",
        "name": "PIPEDA fair information principles",
        "publisher": "Office of the Privacy Commissioner of Canada",
        "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/",
        "checked_at": "2026-06-29",
        "product_use": "Requires beta evidence to record purpose, consent, limiting use/retention, safeguards, and deletion handling.",
    },
    {
        "source_id": "owasp-file-upload",
        "name": "File Upload Cheat Sheet",
        "publisher": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
        "checked_at": "2026-06-29",
        "product_use": "Keeps real user uploads blocked until hosted upload controls are proven.",
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


def _task_by_id() -> dict[str, dict[str, Any]]:
    return {task["task_id"]: dict(task) for task in TASKS}


def _task_result_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    raw_tasks = record.get("tasks") or record.get("task_results") or []
    if isinstance(raw_tasks, dict):
        for task_id, value in raw_tasks.items():
            if isinstance(value, dict):
                mapped[str(task_id)] = {"task_id": str(task_id), **value}
            else:
                mapped[str(task_id)] = {"task_id": str(task_id), "status": str(value)}
        return mapped
    for item in _as_list(raw_tasks):
        if not isinstance(item, dict):
            continue
        task_id = _text(item.get("task_id") or item.get("id"))
        if task_id:
            mapped[task_id] = item
    return mapped


def _issue_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _as_list(record.get("issues")):
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _artifact_refs(record: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("artifact_references", "artifacts", "recording_references", "evidence_links_or_files"):
        value = record.get(key)
        if isinstance(value, dict):
            for item in value.values():
                refs.extend(_text(ref) for ref in _as_list(item) if _text(ref))
        else:
            refs.extend(_text(ref) for ref in _as_list(value) if _text(ref))
    return refs


def build_private_beta_session_schema(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": SCHEMA_STATUS,
        "generated_at": generated_at,
        "required_session_count": sum(row["required_count"] for row in REQUIRED_SEGMENTS),
        "required_segments": list(REQUIRED_SEGMENTS),
        "optional_segments": list(OPTIONAL_SEGMENTS),
        "required_evidence_categories": list(REQUIRED_EVIDENCE_CATEGORIES),
        "task_count": len(TASKS),
        "tasks": list(TASKS),
        "claim_comprehension_checks": list(CLAIM_COMPREHENSION_CHECKS),
        "accepted_task_statuses": ["completed_without_help"],
        "non_passing_task_statuses": ["completed_with_help", "failed", "skipped", "not_observed"],
        "allowed_not_applicable_status": "not_applicable_with_reason",
        "required_record_fields": [
            "session_id",
            "participant_segment",
            "participant_role",
            "participant_is_real_target_user",
            "participant_is_internal_team",
            "session_date",
            "consent_record_ref",
            "environment_url_or_ref",
            "build_or_commit_ref",
            "task_results",
            "claim_comprehension",
            "privacy_or_deletion_result",
            "issues",
            "artifact_references",
            "outcome_decision",
        ],
        "blocked_until": [
            "Wave 1 external review decisions are received and P0/P1 findings are resolved or explicitly blocking.",
            "Hosted staging proof exists for the exact beta scope.",
            "Privacy/security/legal owner accepts scoped beta data handling.",
            "Five required real target-user sessions pass the required tasks without unsafe claim misunderstanding.",
        ],
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "This schema defines accepted private-beta evidence. It is not itself user validation or launch approval.",
    }


def validate_private_beta_session_record(
    record: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    segment = _text(record.get("participant_segment"))
    task_map = _task_result_map(record)
    task_catalog = _task_by_id()
    supported_segments = {row["segment"] for row in REQUIRED_SEGMENTS + OPTIONAL_SEGMENTS}
    missing_fields: list[str] = []
    for field in (
        "session_id",
        "participant_segment",
        "participant_role",
        "session_date",
        "consent_record_ref",
        "environment_url_or_ref",
        "build_or_commit_ref",
        "outcome_decision",
    ):
        if not _text(record.get(field)):
            missing_fields.append(field)

    if segment not in supported_segments:
        missing_fields.append("supported participant_segment")
    if record.get("participant_is_real_target_user") is not True:
        missing_fields.append("participant_is_real_target_user=true")
    if record.get("participant_is_internal_team") is not False:
        missing_fields.append("participant_is_internal_team=false")

    task_rows: list[dict[str, Any]] = []
    failed_required_tasks: list[str] = []
    missing_required_tasks: list[str] = []
    for task_id, task in task_catalog.items():
        required = segment in task.get("required_for_segments", [])
        allowed_na = segment in task.get("allowed_not_applicable_segments", [])
        task_result = task_map.get(task_id, {})
        status = _text(task_result.get("status"))
        if required and not status:
            missing_required_tasks.append(task_id)
        elif required and status != "completed_without_help":
            failed_required_tasks.append(task_id)
        elif allowed_na and status not in {"completed_without_help", "not_applicable_with_reason"}:
            failed_required_tasks.append(task_id)
        task_rows.append(
            {
                "task_id": task_id,
                "label": task["label"],
                "required_for_session": required,
                "allowed_not_applicable": allowed_na,
                "status": status or "not_observed",
                "evidence_ref": task_result.get("evidence_ref") or "",
                "passes": (
                    (required and status == "completed_without_help")
                    or (allowed_na and status in {"completed_without_help", "not_applicable_with_reason"})
                    or (not required and not allowed_na)
                ),
            }
        )

    comprehension = record.get("claim_comprehension") if isinstance(record.get("claim_comprehension"), dict) else {}
    missing_comprehension = [
        check["field"] for check in CLAIM_COMPREHENSION_CHECKS if comprehension.get(check["field"]) is not True
    ]
    unsafe_misunderstanding = comprehension.get("unsafe_approval_misunderstanding") is True
    privacy = record.get("privacy_or_deletion_result") if isinstance(record.get("privacy_or_deletion_result"), dict) else {}
    privacy_failures: list[str] = []
    if privacy.get("deletion_or_retention_choice_recorded") is not True:
        privacy_failures.append("deletion_or_retention_choice_recorded")
    if privacy.get("critical_upload_or_privacy_incident") is True:
        privacy_failures.append("critical_upload_or_privacy_incident")
    if privacy.get("real_upload_used") is True and privacy.get("upload_was_synthetic_or_permitted") is not True:
        privacy_failures.append("upload_permission_or_synthetic_fixture")

    issue_rows = _issue_rows(record)
    unresolved_p0_p1 = [
        row for row in issue_rows if str(row.get("severity") or "").upper() in {"P0", "P1"} and row.get("status") != "resolved"
    ]
    artifact_refs = _artifact_refs(record)
    evidence_category_failures: list[str] = []
    if not artifact_refs:
        evidence_category_failures.append("artifact_or_recording_references")
    if not task_map:
        evidence_category_failures.append("task_results")
    if not comprehension:
        evidence_category_failures.append("claim_comprehension")
    if not privacy:
        evidence_category_failures.append("privacy_or_deletion_result")

    simulated_or_internal = record.get("simulated") is True or record.get("participant_is_internal_team") is True
    passing = not any(
        (
            missing_fields,
            missing_required_tasks,
            failed_required_tasks,
            missing_comprehension,
            unsafe_misunderstanding,
            privacy_failures,
            unresolved_p0_p1,
            evidence_category_failures,
            simulated_or_internal,
        )
    )
    if passing:
        status = "accepted_real_user_session"
    elif simulated_or_internal:
        status = "blocked_simulated_or_internal_session"
    elif missing_fields:
        status = "received_missing_identity_scope_or_consent"
    elif missing_required_tasks or failed_required_tasks:
        status = "received_task_flow_not_passed"
    elif missing_comprehension or unsafe_misunderstanding:
        status = "received_claim_boundary_not_understood"
    elif privacy_failures:
        status = "received_privacy_or_upload_issue"
    elif unresolved_p0_p1:
        status = "received_unresolved_p0_p1_issue"
    else:
        status = "received_missing_supporting_evidence"

    return {
        "generated_at": generated_at,
        "session_id": record.get("session_id") or "",
        "participant_segment": segment or "missing",
        "status": status,
        "accepted_for_private_beta_evidence": passing,
        "simulated_or_internal": simulated_or_internal,
        "missing_fields": missing_fields,
        "missing_required_tasks": missing_required_tasks,
        "failed_required_tasks": failed_required_tasks,
        "task_rows": task_rows,
        "claim_comprehension_passed": not missing_comprehension and not unsafe_misunderstanding,
        "missing_claim_comprehension": missing_comprehension,
        "unsafe_approval_misunderstanding": unsafe_misunderstanding,
        "privacy_result_passed": not privacy_failures,
        "privacy_failures": privacy_failures,
        "unresolved_p0_p1_issue_count": len(unresolved_p0_p1),
        "unresolved_p0_p1_issues": unresolved_p0_p1,
        "artifact_reference_count": len(artifact_refs),
        "missing_evidence_categories": evidence_category_failures,
        "outcome_decision": record.get("outcome_decision") or "",
        "claims_opened_by_session_validation": False,
        "external_effects_created": False,
        "next_valid_move": _session_next_valid_move(status),
    }


def _session_next_valid_move(status: str) -> str:
    if status == "accepted_real_user_session":
        return "Keep the dated session evidence and continue until every required segment reaches its minimum count."
    if status == "blocked_simulated_or_internal_session":
        return "Keep this as internal QA only. It cannot count as real private-beta user evidence."
    if status == "received_missing_identity_scope_or_consent":
        return "Add participant segment, role, real-user status, session date, consent, environment, build, and decision."
    if status == "received_task_flow_not_passed":
        return "Fix the failed workflow or rerun the task with the user after the product change is shipped."
    if status == "received_claim_boundary_not_understood":
        return "Improve the UI/report language and rerun claim-comprehension checks."
    if status == "received_privacy_or_upload_issue":
        return "Resolve the privacy, upload permission, deletion, or retention issue before counting the session."
    if status == "received_unresolved_p0_p1_issue":
        return "Fix or explicitly block on unresolved P0/P1 findings before private beta can advance."
    return "Attach missing session evidence and rerun validation."


def _load_session_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    input_dir = repo_root / "external_inputs" / "private_beta_sessions"
    if input_dir.exists():
        for path in sorted(input_dir.glob("*.json")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                payload["source_file"] = str(path.relative_to(repo_root))
                records.append(payload)
    aggregate = _load_json(repo_root / "external_inputs" / "real_users_private_beta_outcomes.json", {})
    if isinstance(aggregate, dict):
        for item in _as_list(aggregate.get("session_records")):
            if isinstance(item, dict):
                item.setdefault("source_file", "external_inputs/real_users_private_beta_outcomes.json")
                records.append(item)
    return records


def _segment_summary(validations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for requirement in REQUIRED_SEGMENTS:
        segment = str(requirement["segment"])
        segment_rows = [row for row in validations if row["participant_segment"] == segment]
        accepted = [row for row in segment_rows if row["accepted_for_private_beta_evidence"] is True]
        rows.append(
            {
                "segment": segment,
                "required_count": requirement["required_count"],
                "received_session_count": len(segment_rows),
                "accepted_session_count": len(accepted),
                "missing_session_count": max(0, int(requirement["required_count"]) - len(accepted)),
                "requirement_met": len(accepted) >= int(requirement["required_count"]),
                "next_valid_move": (
                    "Keep accepted sessions attached."
                    if len(accepted) >= int(requirement["required_count"])
                    else f"Collect {max(0, int(requirement['required_count']) - len(accepted))} more passing real-user session(s)."
                ),
            }
        )
    return rows


def _gate_matrix(
    contract: dict[str, Any],
    smoke_plan: dict[str, Any],
    returned_input: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    real_users_input = next(
        (
            row for row in returned_input.get("validation_rows", [])
            if row.get("review_area") == "real_users_private_beta_outcomes"
        ),
        {},
    )
    rows = [
        {
            "gate": "wave_1_external_review_before_beta",
            "status": "blocked",
            "required_evidence": "Real Wave 1 reviewer decisions and resolved P0/P1 findings.",
            "current_evidence": "not_verified_by_this_contract",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
        },
        {
            "gate": "hosted_staging_before_real_users",
            "status": "blocked",
            "required_evidence": "Dated staging URL, build, TLS/secrets/storage/logging/rollback proof.",
            "current_evidence": "not_verified_by_this_contract",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
        },
        {
            "gate": "privacy_security_legal_scope_before_real_data",
            "status": "blocked",
            "required_evidence": "Scoped privacy/security/legal acceptance for beta data handling.",
            "current_evidence": "not_verified_by_this_contract",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
        },
        {
            "gate": "real_user_session_minimum",
            "status": "accepted" if contract["required_segments_met"] else "not_received",
            "required_evidence": "Five passing real target-user sessions across required segments.",
            "current_evidence": f"{contract['accepted_required_session_count']} of {contract['required_session_count']} accepted",
            "blocks_private_beta": contract["required_segments_met"] is not True,
            "blocks_public_launch": contract["required_segments_met"] is not True,
        },
        {
            "gate": "unsafe_approval_misunderstanding_zero",
            "status": "accepted" if contract["unsafe_approval_misunderstanding_count"] == 0 and contract["current_real_session_count"] > 0 else "not_received",
            "required_evidence": "Zero users leave believing the product approved customs, CFIA, buyer, supplier, or shipment readiness.",
            "current_evidence": str(contract["unsafe_approval_misunderstanding_count"]),
            "blocks_private_beta": contract["unsafe_approval_misunderstanding_count"] > 0 or contract["current_real_session_count"] == 0,
            "blocks_public_launch": contract["unsafe_approval_misunderstanding_count"] > 0 or contract["current_real_session_count"] == 0,
        },
        {
            "gate": "critical_privacy_upload_incidents_zero",
            "status": "accepted" if contract["privacy_or_upload_failure_count"] == 0 and contract["current_real_session_count"] > 0 else "not_received",
            "required_evidence": "Zero critical upload, consent, retention, or deletion incidents.",
            "current_evidence": str(contract["privacy_or_upload_failure_count"]),
            "blocks_private_beta": contract["privacy_or_upload_failure_count"] > 0 or contract["current_real_session_count"] == 0,
            "blocks_public_launch": contract["privacy_or_upload_failure_count"] > 0 or contract["current_real_session_count"] == 0,
        },
        {
            "gate": "returned_input_record_for_go_live_area",
            "status": real_users_input.get("status") or "not_received",
            "required_evidence": "A scoped returned-input record for real_users_private_beta_outcomes with attached participant/session evidence.",
            "current_evidence": real_users_input.get("source_file") or "external_inputs/real_users_private_beta_outcomes.json",
            "blocks_private_beta": True,
            "blocks_public_launch": real_users_input.get("accepted_for_area") is not True,
        },
    ]
    return {
        "status": GATE_MATRIX_STATUS,
        "generated_at": generated_at,
        "smoke_plan_status": smoke_plan.get("status", "missing"),
        "gate_count": len(rows),
        "blocked_gate_count": sum(1 for row in rows if row["status"] != "accepted"),
        "rows": rows,
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "The matrix shows beta evidence gates. It does not approve hosted beta or public launch.",
    }


def build_private_beta_outcome_contract(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    smoke_plan = _load_json(root / "system_review_graph" / "private_beta_smoke_test_plan.json", {})
    returned_input = _load_json(root / "system_review_graph" / "go_live_returned_input_evidence_manifest.json", {})
    records = _load_session_records(root)
    validations = [validate_private_beta_session_record(record, generated_at) for record in records]
    segment_rows = _segment_summary(validations)
    current_real_session_count = sum(
        1 for row in validations if row["simulated_or_internal"] is not True and row["participant_segment"] != "missing"
    )
    accepted_required_session_count = sum(
        row["accepted_session_count"] for row in segment_rows
    )
    contract = {
        "status": STATUS,
        "generated_at": generated_at,
        "research_mode": "source_backed_beta_evidence_contract",
        "source_anchors": list(SOURCE_ANCHORS),
        "required_session_count": sum(row["required_count"] for row in REQUIRED_SEGMENTS),
        "optional_reviewer_session_count": sum(row["required_count"] for row in OPTIONAL_SEGMENTS),
        "task_count": len(TASKS),
        "required_evidence_categories": list(REQUIRED_EVIDENCE_CATEGORIES),
        "current_real_session_count": current_real_session_count,
        "current_session_record_count": len(records),
        "current_accepted_session_count": sum(1 for row in validations if row["accepted_for_private_beta_evidence"] is True),
        "accepted_required_session_count": accepted_required_session_count,
        "simulated_or_internal_session_count": sum(1 for row in validations if row["simulated_or_internal"] is True),
        "unsafe_approval_misunderstanding_count": sum(1 for row in validations if row["unsafe_approval_misunderstanding"] is True),
        "privacy_or_upload_failure_count": sum(1 for row in validations if row["privacy_failures"]),
        "unresolved_p0_p1_issue_count": sum(row["unresolved_p0_p1_issue_count"] for row in validations),
        "required_segments_met": all(row["requirement_met"] for row in segment_rows),
        "segment_rows": segment_rows,
        "session_validations": validations,
        "real_user_evidence_ready": False,
        "hosted_private_beta_ready": False,
        "public_launch_ready": False,
        "claims_opened": False,
        "external_effects_created": False,
        "blocked_claims": [
            "private_beta_approved",
            "public_launch_approved",
            "buyer_validated",
            "supplier_verified",
            "customs_or_tariff_ready",
            "cfia_approved",
            "safe_for_real_uploads",
        ],
        "next_valid_move": (
            "Collect Wave 1/staging/privacy approvals first, then run five real target-user sessions and save each session record."
            if not records
            else "Fix incomplete or failing sessions, rerun beta evidence validation, and attach the accepted go-live returned input."
        ),
        "proof_boundary": (
            "This contract evaluates real private-beta session evidence. It does not create users, send outreach, "
            "approve hosted beta, approve public launch, or open customs, buyer, supplier, payment, privacy, security, or legal claims."
        ),
    }
    contract["real_user_evidence_ready"] = (
        contract["required_segments_met"]
        and contract["unsafe_approval_misunderstanding_count"] == 0
        and contract["privacy_or_upload_failure_count"] == 0
        and contract["unresolved_p0_p1_issue_count"] == 0
        and contract["current_real_session_count"] >= contract["required_session_count"]
    )
    contract["gate_matrix"] = _gate_matrix(contract, smoke_plan, returned_input, generated_at)
    return contract


def render_private_beta_outcome_contract(payload: dict[str, Any]) -> str:
    lines = [
        "# Private Beta Outcome Contract",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Current Result",
        "",
        f"- Required real sessions accepted: {payload['accepted_required_session_count']} of {payload['required_session_count']}",
        f"- Current real session records: {payload['current_real_session_count']}",
        f"- Simulated or internal sessions counted for launch: {payload['simulated_or_internal_session_count']}",
        f"- Unsafe approval misunderstandings: {payload['unsafe_approval_misunderstanding_count']}",
        f"- Privacy or upload failures: {payload['privacy_or_upload_failure_count']}",
        f"- Real user evidence ready: {str(payload['real_user_evidence_ready']).lower()}",
        f"- Public launch ready: {str(payload['public_launch_ready']).lower()}",
        "",
        "## Required Segments",
        "",
        "| Segment | Accepted | Required | Next valid move |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in payload["segment_rows"]:
        lines.append(
            f"| `{row['segment']}` | {row['accepted_session_count']} | {row['required_count']} | {row['next_valid_move']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Rule",
            "",
            "Internal demos, AI/simulated reviews, local smoke tests, and founder-only runs may support QA, but they do not count as real private-beta outcomes.",
            "",
            "## Source Anchors",
            "",
        ]
    )
    for source in payload["source_anchors"]:
        lines.append(f"- {source['publisher']}: {source['name']} ({source['url']})")
    lines.append("")
    return "\n".join(lines)


def write_private_beta_outcome_artifacts(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    graph = root / "system_review_graph"
    docs = root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    schema = build_private_beta_session_schema(generated_at)
    contract = build_private_beta_outcome_contract(root, generated_at)
    matrix = contract["gate_matrix"]
    (graph / "private_beta_session_evidence_schema.json").write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (graph / "private_beta_outcome_contract.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (graph / "private_beta_outcome_gate_matrix.json").write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (docs / "PRIVATE_BETA_OUTCOME_CONTRACT.md").write_text(
        render_private_beta_outcome_contract(contract),
        encoding="utf-8",
    )
    return {
        "status": contract["status"],
        "schema_status": schema["status"],
        "gate_matrix_status": matrix["status"],
        "required_session_count": contract["required_session_count"],
        "current_real_session_count": contract["current_real_session_count"],
        "real_user_evidence_ready": contract["real_user_evidence_ready"],
        "public_launch_ready": contract["public_launch_ready"],
        "claims_opened": contract["claims_opened"],
        "generated_at": generated_at,
    }
