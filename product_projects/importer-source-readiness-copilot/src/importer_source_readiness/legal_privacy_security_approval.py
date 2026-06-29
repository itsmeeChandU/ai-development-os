"""Legal, privacy, and security approval proof intake.

The production trust engine maps local controls, but those controls are not
qualified legal/privacy/security approval. This module validates returned
approval evidence for the exact scope under review and keeps real uploads,
hosted private beta, public launch, and external claims closed until the wider
launch control plane has all required proof.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATUS = "legal_privacy_security_approval_intake_ready_real_approval_evidence_required_claims_closed"
CONTRACT_STATUS = "legal_privacy_security_approval_contract_ready_claims_closed"
GATE_MATRIX_STATUS = "legal_privacy_security_approval_gate_matrix_ready_claims_closed"
BLOCKER_EXPORT_STATUS = "legal_privacy_security_approval_blocker_export_ready_claims_closed"

ALLOWED_DECISIONS = (
    "approve_for_private_beta_scope",
    "approve_demo_no_real_data_only",
    "not_applicable_for_this_launch",
    "keep_blocked",
    "needs_more_evidence",
)

REQUIRED_REVIEWER_ROLES = (
    "privacy_legal_reviewer",
    "application_security_reviewer",
)

ROLE_ALIASES = {
    "qualified_privacy_security_reviewer": REQUIRED_REVIEWER_ROLES,
    "privacy_security_reviewer": REQUIRED_REVIEWER_ROLES,
    "legal_privacy_security_reviewer": REQUIRED_REVIEWER_ROLES,
}

APPROVAL_SCOPE_TYPES = (
    "private_beta_real_data",
    "hosted_private_beta_candidate",
)

DEMO_SCOPE_TYPES = (
    "demo_no_real_data",
    "internal_review_no_real_data",
)

REQUIRED_PROOF_CATEGORIES: tuple[dict[str, str], ...] = (
    {
        "category": "approval_scope_and_data_flow_map",
        "label": "Approval scope and data-flow map",
        "why": "The reviewer must know the exact product scope, routes, vendors, data categories, and real-data boundary.",
    },
    {
        "category": "reviewer_identity_qualification_scope",
        "label": "Reviewer identity, qualification, and scope",
        "why": "Legal/privacy/security approval requires named qualified reviewers and the exact scope they reviewed.",
    },
    {
        "category": "privacy_notice_consent_purpose_review",
        "label": "Privacy notice, consent, and purpose review",
        "why": "Customer-facing data collection needs clear purpose, consent, and notice language before real users or files.",
    },
    {
        "category": "collection_minimization_retention_review",
        "label": "Collection minimization and retention review",
        "why": "The product must limit collection, use, disclosure, and retention for trade documents and account data.",
    },
    {
        "category": "access_deletion_challenge_process",
        "label": "Access, deletion, and challenge process",
        "why": "Users need a reviewed process for access, correction, deletion, and challenging compliance.",
    },
    {
        "category": "breach_response_recordkeeping_notification",
        "label": "Breach response, recordkeeping, and notification",
        "why": "A privacy/security incident process must exist before sensitive trade documents are accepted.",
    },
    {
        "category": "vendor_processor_data_residency_review",
        "label": "Vendor, processor, and data-residency review",
        "why": "Hosting, storage, AI, payment, email, monitoring, and support vendors need privacy/security review and location decisions.",
    },
    {
        "category": "managed_auth_session_rbac_review",
        "label": "Managed auth, sessions, and RBAC review",
        "why": "Real users need reviewed authentication, admin MFA, tenant authorization, session, and access-control proof.",
    },
    {
        "category": "upload_malware_quarantine_controls",
        "label": "Upload, malware, and quarantine controls",
        "why": "Real file uploads must have allowlists, type checks, size limits, quarantine, scanning/CDR decision, and storage isolation.",
    },
    {
        "category": "ai_redaction_prompt_injection_review",
        "label": "AI redaction and prompt-injection review",
        "why": "Uploaded documents and source text can carry sensitive data or prompt-injection content; AI use needs consent, redaction, and review.",
    },
    {
        "category": "secrets_logging_monitoring_review",
        "label": "Secrets, logging, and monitoring review",
        "why": "Production secrets, logs, alerts, and monitoring must avoid leaking trade documents, credentials, or personal information.",
    },
    {
        "category": "backup_restore_incident_runbook_review",
        "label": "Backup, restore, and incident-runbook review",
        "why": "Operations must be able to recover, contain incidents, and notify owners before a real beta.",
    },
    {
        "category": "unresolved_findings_risk_acceptance",
        "label": "Unresolved findings and risk acceptance",
        "why": "Open findings need severity, owner, due date, and explicit risk acceptance before any scoped approval can count.",
    },
    {
        "category": "launch_owner_scope_decision",
        "label": "Launch owner scope decision",
        "why": "A named owner must decide whether the reviewed scope is approved, blocked, demo-only, or needs more evidence.",
    },
)

DEMO_SCOPE_CATEGORIES = (
    "review_scope_excludes_real_user_data",
    "reviewer_scope_acknowledgement",
    "no_real_uploads_or_ai_processing",
    "future_approval_condition",
)

SOURCE_ANCHORS: tuple[dict[str, str], ...] = (
    {
        "source_id": "opc-pipeda-principles",
        "name": "PIPEDA fair information principles",
        "publisher": "Office of the Privacy Commissioner of Canada",
        "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/",
        "checked_at": "2026-06-29",
        "product_use": "Accountability, purpose, consent, limiting collection/use/retention, safeguards, openness, access, and challenge evidence anchor.",
    },
    {
        "source_id": "opc-privacy-breach-reporting",
        "name": "Privacy breaches at your business",
        "publisher": "Office of the Privacy Commissioner of Canada",
        "url": "https://www.priv.gc.ca/en/privacy-topics/business-privacy/breaches-and-safeguards/privacy-breaches-at-your-business/gd_pb_201810/",
        "checked_at": "2026-06-29",
        "product_use": "Breach response, recordkeeping, notification, and incident owner evidence anchor.",
    },
    {
        "source_id": "canadian-centre-baseline-controls",
        "name": "Baseline cyber security controls for small and medium organizations",
        "publisher": "Canadian Centre for Cyber Security",
        "url": "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations",
        "checked_at": "2026-06-29",
        "product_use": "Account, backup, patching, malware, monitoring, and incident-readiness control anchor.",
    },
    {
        "source_id": "owasp-asvs",
        "name": "Application Security Verification Standard",
        "publisher": "OWASP",
        "url": "https://owasp.org/www-project-application-security-verification-standard/",
        "checked_at": "2026-06-29",
        "product_use": "Application security review depth, authentication, authorization, validation, API, and deployment evidence anchor.",
    },
    {
        "source_id": "owasp-file-upload",
        "name": "File Upload Cheat Sheet",
        "publisher": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
        "checked_at": "2026-06-29",
        "product_use": "Upload allowlisting, signature/type validation, generated filenames, size limits, authorization, isolated storage, malware checks, and CSRF anchor.",
    },
    {
        "source_id": "owasp-llm01-prompt-injection",
        "name": "LLM01 Prompt Injection",
        "publisher": "OWASP GenAI Security Project",
        "url": "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
        "checked_at": "2026-06-29",
        "product_use": "AI prompt-injection risk anchor for uploaded files, web/source summaries, and reviewer-work-order drafting.",
    },
    {
        "source_id": "nist-ai-rmf",
        "name": "AI Risk Management Framework",
        "publisher": "NIST",
        "url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "checked_at": "2026-06-29",
        "product_use": "AI trustworthiness, governance, evaluation, and human-review boundary anchor.",
    },
    {
        "source_id": "nist-csf-2",
        "name": "Cybersecurity Framework",
        "publisher": "NIST",
        "url": "https://www.nist.gov/cyberframework",
        "checked_at": "2026-06-29",
        "product_use": "Govern, identify, protect, detect, respond, and recover control grouping anchor.",
    },
    {
        "source_id": "cisa-secure-by-design",
        "name": "Secure by Design",
        "publisher": "Cybersecurity and Infrastructure Security Agency",
        "url": "https://www.cisa.gov/securebydesign",
        "checked_at": "2026-06-29",
        "product_use": "Secure-by-design/default posture and product-owner accountability anchor.",
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
        (("approval_scope_id", "approval_scope_name"), "approval scope id or name"),
        (("review_scope_type",), "review scope type"),
        (("jurisdiction",), "jurisdiction"),
        (("reviewer_name",), "reviewer name"),
        (("reviewer_qualification", "qualification_summary"), "reviewer qualification"),
        (("reviewed_at", "approved_at", "checked_at"), "reviewed or approved date"),
        (("build_or_commit_ref", "commit_ref", "build_ref"), "build or commit reference"),
        (("decision",), "decision"),
    )
    missing = []
    for names, label in checks:
        if not any(_text(record.get(name)) for name in names):
            missing.append(label)
    return missing


def _required_categories_for_decision(decision: str) -> tuple[str, ...]:
    if decision in {"approve_demo_no_real_data_only", "not_applicable_for_this_launch"}:
        return DEMO_SCOPE_CATEGORIES
    return tuple(item["category"] for item in REQUIRED_PROOF_CATEGORIES)


def validate_legal_privacy_security_approval_record(
    record: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    missing_fields = _missing_identity_fields(record)
    decision = _text(record.get("decision"))
    review_scope_type = _text(record.get("review_scope_type"))
    roles = _reviewer_roles(record)
    missing_roles = [role for role in REQUIRED_REVIEWER_ROLES if role not in roles]
    required_categories = _required_categories_for_decision(decision)
    attached_categories = _evidence_categories(record)
    missing_categories = [category for category in required_categories if category not in attached_categories]
    private_beta_scope = review_scope_type in APPROVAL_SCOPE_TYPES
    demo_scope = review_scope_type in DEMO_SCOPE_TYPES

    if missing_fields:
        status = "received_missing_approval_identity"
    elif decision not in ALLOWED_DECISIONS:
        status = "received_unknown_approval_decision"
    elif decision == "approve_for_private_beta_scope" and not private_beta_scope:
        status = "received_private_beta_approval_without_private_beta_scope"
    elif decision in {"approve_demo_no_real_data_only", "not_applicable_for_this_launch"} and not demo_scope:
        status = "received_demo_or_not_applicable_without_demo_scope"
    elif decision == "approve_for_private_beta_scope" and missing_roles:
        status = "received_missing_required_reviewer_roles"
    elif not (private_beta_scope or demo_scope):
        status = "received_unsupported_review_scope"
    elif missing_categories:
        status = "received_missing_required_approval_evidence"
    elif decision == "approve_for_private_beta_scope":
        status = "accepted_private_beta_legal_privacy_security_scope_evidence"
    elif decision in {"approve_demo_no_real_data_only", "not_applicable_for_this_launch"}:
        status = "accepted_demo_no_real_data_approval_scope_evidence"
    else:
        status = "received_approval_not_ready"

    accepted = status in {
        "accepted_private_beta_legal_privacy_security_scope_evidence",
        "accepted_demo_no_real_data_approval_scope_evidence",
    }
    approved_by_evidence = status == "accepted_private_beta_legal_privacy_security_scope_evidence"
    return {
        "generated_at": generated_at,
        "status": status,
        "approval_scope_id": record.get("approval_scope_id") or record.get("approval_scope_name") or "",
        "review_scope_type": review_scope_type,
        "jurisdiction": record.get("jurisdiction") or "",
        "reviewer_name": record.get("reviewer_name") or "",
        "reviewer_roles": sorted(roles),
        "missing_reviewer_roles": missing_roles,
        "reviewer_qualification": record.get("reviewer_qualification") or record.get("qualification_summary") or "",
        "reviewed_at": record.get("reviewed_at") or record.get("approved_at") or record.get("checked_at") or "",
        "build_or_commit_ref": record.get("build_or_commit_ref") or record.get("commit_ref") or record.get("build_ref") or "",
        "decision": decision,
        "source_file": record.get("source_file") or "",
        "missing_input_fields": missing_fields,
        "required_evidence_categories": list(required_categories),
        "missing_evidence_categories": missing_categories,
        "accepted_for_legal_privacy_security_evidence": accepted,
        "legal_privacy_security_approved_by_evidence": approved_by_evidence,
        "real_file_uploads_allowed_by_intake": False,
        "hosted_private_beta_ready_by_approval_evidence": False,
        "public_launch_ready_by_approval_evidence": False,
        "claims_opened_by_validation": False,
        "external_effects_created": False,
        "next_valid_move": _next_valid_move(status),
    }


def _next_valid_move(status: str) -> str:
    if status == "accepted_private_beta_legal_privacy_security_scope_evidence":
        return "Keep scoped approval attached, then require hosted proof, real beta outcomes, payment/launch gates, and owner go/no-go before opening any external effect."
    if status == "accepted_demo_no_real_data_approval_scope_evidence":
        return "Keep real uploads and real user data blocked; use this approval only for the reviewed demo/no-real-data scope."
    if status == "received_missing_approval_identity":
        return "Add scope, jurisdiction, reviewer, qualification, date, build reference, and decision."
    if status == "received_unknown_approval_decision":
        return "Use one of the allowed approval decisions and rerun validation."
    if status == "received_private_beta_approval_without_private_beta_scope":
        return "Set review_scope_type to private_beta_real_data or hosted_private_beta_candidate for private-beta approval evidence."
    if status == "received_demo_or_not_applicable_without_demo_scope":
        return "Set review_scope_type to demo_no_real_data or internal_review_no_real_data for demo/no-real-data evidence."
    if status == "received_missing_required_reviewer_roles":
        return "Attach privacy/legal and application-security reviewer coverage for the reviewed scope."
    if status == "received_unsupported_review_scope":
        return "Use a supported private-beta or demo/no-real-data review scope."
    if status == "received_missing_required_approval_evidence":
        return "Attach every required legal/privacy/security evidence category before counting approval proof."
    return "Resolve legal/privacy/security evidence issues and keep uploads, hosted beta, and public launch closed."


def build_legal_privacy_security_approval_contract(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": CONTRACT_STATUS,
        "generated_at": generated_at,
        "allowed_decisions": list(ALLOWED_DECISIONS),
        "required_reviewer_roles": list(REQUIRED_REVIEWER_ROLES),
        "approval_scope_types": list(APPROVAL_SCOPE_TYPES),
        "demo_scope_types": list(DEMO_SCOPE_TYPES),
        "required_evidence_categories": list(REQUIRED_PROOF_CATEGORIES),
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "demo_scope_evidence_categories": list(DEMO_SCOPE_CATEGORIES),
        "source_anchors": list(SOURCE_ANCHORS),
        "source_anchor_count": len(SOURCE_ANCHORS),
        "drop_paths": [
            "external_inputs/legal_privacy_security_approval.json",
            "external_inputs/legal_privacy_security_approvals/*.json",
        ],
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "This contract defines scoped legal/privacy/security approval evidence. It does not enable real uploads, create hosted users, approve AI/vendor processing, or approve public launch.",
    }


def _load_approval_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    single = _load_json(repo_root / "external_inputs" / "legal_privacy_security_approval.json", {})
    if isinstance(single, dict) and single:
        single["source_file"] = "external_inputs/legal_privacy_security_approval.json"
        records.append(single)
    proof_dir = repo_root / "external_inputs" / "legal_privacy_security_approvals"
    if proof_dir.exists():
        for path in sorted(proof_dir.glob("*.json")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                payload["source_file"] = str(path.relative_to(repo_root))
                records.append(payload)
    return records


def _selected_validation(validations: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in validations if row.get("accepted_for_legal_privacy_security_evidence") is True]
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
                "gate_id": f"legal_privacy_security:{category}",
                "category": category,
                "label": item["label"],
                "status": "missing_real_approval_evidence" if missing else "evidence_attached_for_review",
                "blocks_legal_privacy_security_approval": missing,
                "blocks_real_file_uploads": True,
                "blocks_private_beta": True,
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
        if row["blocks_legal_privacy_security_approval"] is not True:
            continue
        rows.append(
            {
                "id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "finding_id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "module": "legal_privacy_security_approval",
                "reviewer_role": "Legal/Privacy/Security Review",
                "severity": "P0",
                "affected_stage": "legal_privacy_security_approval",
                "affected_file_or_artifact": "system_review_graph/legal_privacy_security_approval_manifest.json",
                "issue": f"Legal/privacy/security approval proof missing: {row['label']}.",
                "owner": "privacy/legal/security reviewer",
                "required_fix": row["why"],
                "retest_command": "python3 scripts/check_product.py",
                "blocks_private_beta": True,
                "blocks_public_launch": True,
                "evidence": "legal_privacy_security_approval_manifest.json records missing scoped approval evidence.",
                "gate": "closed",
                "next_valid_move": "Attach real scoped legal/privacy/security approval proof or a demo/no-real-data decision and rerun approval intake.",
                "unsafe_to_bypass": True,
                "created_at": generated_at,
                "source_report": "system_review_graph/legal_privacy_security_approval_manifest.json",
            }
        )
    return rows


def build_legal_privacy_security_approval_intake(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    records = _load_approval_records(root)
    validations = [validate_legal_privacy_security_approval_record(record, generated_at) for record in records]
    selected = _selected_validation(validations)
    gate_rows = _gate_rows(selected, generated_at)
    blocker_rows = _blocker_rows(gate_rows, generated_at)
    accepted_count = sum(1 for row in validations if row["accepted_for_legal_privacy_security_evidence"] is True)
    approved_by_evidence = selected is not None and selected.get("legal_privacy_security_approved_by_evidence") is True
    return {
        "status": STATUS,
        "generated_at": generated_at,
        "approval_record_count": len(records),
        "accepted_approval_record_count": accepted_count,
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "attached_evidence_category_count": 0
        if selected is None
        else len(selected.get("required_evidence_categories", [])) - len(selected.get("missing_evidence_categories", [])),
        "missing_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES)
        if selected is None
        else len(selected.get("missing_evidence_categories", [])),
        "gate_count": len(gate_rows),
        "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_legal_privacy_security_approval"] is True),
        "blocker_export_count": len(blocker_rows),
        "selected_validation": selected or {},
        "validations": validations,
        "legal_privacy_security_approved_by_evidence": approved_by_evidence,
        "real_file_uploads_allowed_by_intake": False,
        "hosted_private_beta_ready_by_approval_evidence": False,
        "public_launch_ready_by_approval_evidence": False,
        "claims_opened_by_intake": False,
        "external_effects_created": False,
        "contract": build_legal_privacy_security_approval_contract(generated_at),
        "gate_matrix": {
            "status": GATE_MATRIX_STATUS,
            "generated_at": generated_at,
            "gate_count": len(gate_rows),
            "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_legal_privacy_security_approval"] is True),
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
        "next_valid_move": "Attach scoped legal/privacy/security approval proof or a demo/no-real-data approval decision, then rerun approval intake.",
        "proof_boundary": (
            "This validates scoped legal/privacy/security approval evidence only. It does not enable real uploads, "
            "hosted private beta, AI/vendor processing, payment activation, or public launch."
        ),
    }


def render_legal_privacy_security_approval_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Legal Privacy Security Approval Proof",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Current Result",
        "",
        f"- Approval records received: {payload['approval_record_count']}",
        f"- Accepted approval records: {payload['accepted_approval_record_count']}",
        f"- Missing evidence categories: {payload['missing_evidence_category_count']}",
        f"- Legal/privacy/security approved by evidence: {str(payload['legal_privacy_security_approved_by_evidence']).lower()}",
        f"- Real file uploads allowed by intake: {str(payload['real_file_uploads_allowed_by_intake']).lower()}",
        f"- Hosted private beta ready by approval evidence: {str(payload['hosted_private_beta_ready_by_approval_evidence']).lower()}",
        f"- Public launch ready by approval evidence: {str(payload['public_launch_ready_by_approval_evidence']).lower()}",
        f"- Claims opened by intake: {str(payload['claims_opened_by_intake']).lower()}",
        "",
        "## Drop Paths",
        "",
        "- `external_inputs/legal_privacy_security_approval.json`",
        "- `external_inputs/legal_privacy_security_approvals/*.json`",
        "",
        "## Gate Matrix",
        "",
        "| Evidence | Status | Blocks Approval |",
        "| --- | --- | --- |",
    ]
    for row in payload["gate_matrix"]["rows"]:
        lines.append(
            f"| {row['label']} | `{row['status']}` | `{str(row['blocks_legal_privacy_security_approval']).lower()}` |"
        )
    lines.extend(["", "## Source Anchors", ""])
    for source in payload["contract"]["source_anchors"]:
        lines.append(f"- {source['publisher']}: {source['name']} ({source['url']})")
    lines.append("")
    return "\n".join(lines)


def _render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def write_legal_privacy_security_approval_artifacts(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    graph = root / "system_review_graph"
    docs = root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    payload = build_legal_privacy_security_approval_intake(root, generated_at)
    (graph / "legal_privacy_security_approval_contract.json").write_text(_render_json(payload["contract"]), encoding="utf-8")
    manifest_payload = {key: value for key, value in payload.items() if key not in {"contract", "gate_matrix", "blocker_export"}}
    (graph / "legal_privacy_security_approval_manifest.json").write_text(_render_json(manifest_payload), encoding="utf-8")
    (graph / "legal_privacy_security_approval_gate_matrix.json").write_text(_render_json(payload["gate_matrix"]), encoding="utf-8")
    (graph / "legal_privacy_security_approval_blocker_export.jsonl").write_text(
        _render_jsonl(payload["blocker_export"]["rows"]),
        encoding="utf-8",
    )
    (docs / "LEGAL_PRIVACY_SECURITY_APPROVAL_PROOF.md").write_text(
        render_legal_privacy_security_approval_markdown(payload),
        encoding="utf-8",
    )
    return {
        "status": payload["status"],
        "approval_record_count": payload["approval_record_count"],
        "accepted_approval_record_count": payload["accepted_approval_record_count"],
        "blocked_gate_count": payload["blocked_gate_count"],
        "blocker_export_count": payload["blocker_export_count"],
        "legal_privacy_security_approved_by_evidence": payload["legal_privacy_security_approved_by_evidence"],
        "real_file_uploads_allowed_by_intake": payload["real_file_uploads_allowed_by_intake"],
        "claims_opened_by_intake": payload["claims_opened_by_intake"],
        "generated_at": generated_at,
    }
