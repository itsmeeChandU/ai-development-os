"""Production security, privacy, reliability, and trust engine.

Phase 19 turns the existing local controls into one reviewable production-trust
surface. It performs a real local backup/restore hash drill over critical
artifacts, maps controls to evidence, registers vendor/data-processing review
requirements, and keeps hosted/private-beta/real-file gates closed until the
required external proof exists.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_security_privacy_reliability_engine_ready_local_controls_external_trust_gates_closed"
LEGAL_PRIVACY_SECURITY_APPROVAL_FALLBACK_GATE_COUNT = 14

TRUST_RESEARCH_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "source_id": "opc-pipeda-principles",
        "source_name": "Office of the Privacy Commissioner of Canada PIPEDA principles",
        "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/",
        "product_use": "Privacy control mapping for accountability, consent, limiting collection/use/retention, safeguards, openness, access, and challenge rights.",
    },
    {
        "source_id": "opc-privacy-breach-response",
        "source_name": "Office of the Privacy Commissioner of Canada breach response guidance",
        "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-breaches/respond-to-a-privacy-breach-at-your-business/",
        "product_use": "Breach-process, notification, and incident runbook requirements before real user data is accepted.",
    },
    {
        "source_id": "owasp-file-upload",
        "source_name": "OWASP File Upload Cheat Sheet",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
        "product_use": "Upload allowlisting, signature/type validation, generated filenames, size limits, authorization, isolated storage, malware checks, and CSRF.",
    },
    {
        "source_id": "owasp-llm01-prompt-injection",
        "source_name": "OWASP LLM01 Prompt Injection",
        "url": "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
        "product_use": "AI prompt-injection review for uploaded files, source summaries, and reviewer work-order drafts.",
    },
    {
        "source_id": "nist-ai-rmf",
        "source_name": "NIST AI Risk Management Framework",
        "url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "product_use": "AI governance framing for trustworthy design, evaluation, and human-review boundaries.",
    },
    {
        "source_id": "canadian-centre-baseline-controls",
        "source_name": "Canadian Centre for Cyber Security baseline cyber security controls",
        "url": "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations",
        "product_use": "SMB-focused baseline controls for account security, backups, patching, monitoring, and incident readiness.",
    },
    {
        "source_id": "nist-csf-2",
        "source_name": "NIST Cybersecurity Framework 2.0",
        "url": "https://www.nist.gov/cyberframework",
        "product_use": "Govern, identify, protect, detect, respond, and recover control grouping.",
    },
    {
        "source_id": "nist-sp-800-61r2",
        "source_name": "NIST SP 800-61 Rev. 2 Computer Security Incident Handling Guide",
        "url": "https://csrc.nist.gov/pubs/sp/800/61/r2/final",
        "product_use": "Incident preparation, detection, analysis, containment, eradication, recovery, and lessons-learned runbook structure.",
    },
    {
        "source_id": "openai-api-data-controls",
        "source_name": "OpenAI platform data controls",
        "url": "https://platform.openai.com/docs/guides/your-data",
        "product_use": "AI vendor data-use, retention, and endpoint-review input if OpenAI API processing is enabled later.",
    },
)

CONTROL_REQUIREMENTS: tuple[dict[str, Any], ...] = (
    {
        "control_id": "managed_auth",
        "label": "Managed authentication",
        "local_basis": ["auth_rbac_matrix.json"],
        "local_status": "local_session_auth_contract_ready",
        "production_required_evidence": "Managed identity provider, account lifecycle, password/MFA policy, session settings, and hosted smoke proof.",
        "gate_id": "hosted_managed_auth_gate",
        "source_ids": ["canadian-centre-baseline-controls", "nist-csf-2"],
    },
    {
        "control_id": "admin_mfa",
        "label": "Admin MFA",
        "local_basis": ["auth_rbac_matrix.json"],
        "local_status": "role_identified_mfa_not_configured",
        "production_required_evidence": "Admin MFA enforced in hosted identity provider with recovery and break-glass policy.",
        "gate_id": "admin_mfa_gate",
        "source_ids": ["canadian-centre-baseline-controls"],
    },
    {
        "control_id": "organization_rbac",
        "label": "Organization RBAC and tenant isolation",
        "local_basis": ["auth_rbac_matrix.json", "production_enterprise_rbac_policy.json"],
        "local_status": "local_rbac_and_org_scope_ready",
        "production_required_evidence": "Hosted object-level authorization tests for every customer, operator, expert, and admin route.",
        "gate_id": "tenant_authorization_gate",
        "source_ids": ["nist-csf-2"],
    },
    {
        "control_id": "secure_sessions_csrf",
        "label": "Secure sessions and CSRF",
        "local_basis": ["auth_rbac_matrix.json", "product_runtime_state.json"],
        "local_status": "local_cookie_and_csrf_contract_ready",
        "production_required_evidence": "TLS, secure cookies, same-site policy, CSRF tests, logout/session-expiry tests, and cookie flag proof.",
        "gate_id": "hosted_session_security_gate",
        "source_ids": ["owasp-file-upload", "canadian-centre-baseline-controls"],
    },
    {
        "control_id": "rate_limits",
        "label": "Rate limits",
        "local_basis": ["public_upload_policy.json", "production_enterprise_api_manifest.json"],
        "local_status": "local_policy_ready_hosted_enforcement_required",
        "production_required_evidence": "Hosted per-user/per-IP/per-organization limits with alerting and abuse-case tests.",
        "gate_id": "hosted_rate_limit_gate",
        "source_ids": ["owasp-file-upload", "nist-csf-2"],
    },
    {
        "control_id": "private_object_storage",
        "label": "Private object storage",
        "local_basis": ["public_upload_policy.json", "production_document_intelligence_manifest.json"],
        "local_status": "local_quarantine_metadata_ready_private_storage_missing",
        "production_required_evidence": "Private object bucket, no public listing, signed-access policy, retention tags, and storage-region decision.",
        "gate_id": "private_storage_gate",
        "source_ids": ["opc-pipeda-principles", "owasp-file-upload"],
    },
    {
        "control_id": "malware_scanning",
        "label": "Malware scanning and file safety",
        "local_basis": ["public_upload_policy.json", "production_document_intelligence_manifest.json"],
        "local_status": "local_parser_limits_ready_malware_scanner_missing",
        "production_required_evidence": "Malware scanner or CDR provider, quarantine workflow, positive/negative sample tests, and reviewer signoff.",
        "gate_id": "malware_scan_gate",
        "source_ids": ["owasp-file-upload"],
    },
    {
        "control_id": "audit_logs",
        "label": "Audit logs",
        "local_basis": ["audit_events.json", "production_enterprise_audit_export_policy.json"],
        "local_status": "local_audit_records_ready",
        "production_required_evidence": "Immutable audit storage, retention period, export controls, alerting, and access-review proof.",
        "gate_id": "production_audit_log_gate",
        "source_ids": ["opc-pipeda-principles", "nist-csf-2"],
    },
    {
        "control_id": "deletion_retention",
        "label": "Deletion and retention",
        "local_basis": ["deletion_requests.json", "public_upload_manifest.json", "public_upload_policy.json"],
        "local_status": "local_deletion_request_and_expiry_contract_ready",
        "production_required_evidence": "Approved retention schedule, deletion SLA, export/delete workflow test, and privacy/legal review.",
        "gate_id": "retention_deletion_gate",
        "source_ids": ["opc-pipeda-principles"],
    },
    {
        "control_id": "vendor_register",
        "label": "Vendor register",
        "local_basis": ["ai_data_policy.json", "production_payment_monetization_manifest.json"],
        "local_status": "vendor_register_generated_approvals_missing",
        "production_required_evidence": "Vendor DPA/security/privacy review, data-residency decision, subprocessors, support contact, and exit plan.",
        "gate_id": "vendor_approval_gate",
        "source_ids": ["opc-pipeda-principles", "openai-api-data-controls"],
    },
    {
        "control_id": "backup_restore",
        "label": "Backup and restore",
        "local_basis": ["customer_workflow.sqlite", "product_runtime_state.json", "production_redevelopment_plan.json"],
        "local_status": "local_backup_restore_hash_drill_ready",
        "production_required_evidence": "Managed database/object-store backup schedule, restore drill, RPO/RTO decision, and recovery owner.",
        "gate_id": "production_backup_restore_gate",
        "source_ids": ["canadian-centre-baseline-controls", "nist-csf-2"],
    },
    {
        "control_id": "monitoring",
        "label": "Monitoring and alerting",
        "local_basis": ["product_runtime_state.json", "launch_operations_report.json"],
        "local_status": "local_health_and_operations_reports_ready",
        "production_required_evidence": "Hosted uptime, error, queue, upload, AI, payment, and source-refresh alerts with owner escalation.",
        "gate_id": "production_monitoring_gate",
        "source_ids": ["nist-csf-2", "canadian-centre-baseline-controls"],
    },
    {
        "control_id": "incident_runbooks",
        "label": "Incident response runbooks",
        "local_basis": ["launch_operations_report.json"],
        "local_status": "incident_runbook_contract_generated_rehearsal_missing",
        "production_required_evidence": "Runbook rehearsal for security, privacy, data deletion, upload abuse, AI prompt injection, payment, and rollback incidents.",
        "gate_id": "incident_response_gate",
        "source_ids": ["nist-sp-800-61r2", "opc-privacy-breach-response"],
    },
    {
        "control_id": "secrets_management",
        "label": "Secrets management",
        "local_basis": ["production_enterprise_api_manifest.json", "production_payment_monetization_manifest.json", "ai_data_policy.json"],
        "local_status": "no_live_secrets_issued_secret_manager_missing",
        "production_required_evidence": "Hosted secret manager, key rotation, restricted live keys, no secrets in logs, and reviewer proof.",
        "gate_id": "secret_management_gate",
        "source_ids": ["canadian-centre-baseline-controls", "openai-api-data-controls"],
    },
    {
        "control_id": "data_residency",
        "label": "Data residency and processing location",
        "local_basis": ["ai_data_policy.json", "public_upload_policy.json"],
        "local_status": "processing_location_decision_required",
        "production_required_evidence": "Chosen hosting/storage/AI/payment/support regions and privacy/legal approval for customer data flows.",
        "gate_id": "data_residency_gate",
        "source_ids": ["opc-pipeda-principles", "openai-api-data-controls"],
    },
)

VENDOR_RECORDS: tuple[dict[str, Any], ...] = (
    {
        "vendor_id": "hosting_storage_provider_tbd",
        "vendor_name": "Cloud hosting and private object storage provider",
        "purpose": "Hosted app, database, object storage, backups, and logs.",
        "data_categories": ["account", "packet", "trade_document", "audit", "report"],
        "provider_selected": False,
    },
    {
        "vendor_id": "openai_api_candidate",
        "vendor_name": "OpenAI API candidate",
        "purpose": "Optional AI extraction, summarization, redaction, and reviewer-work-order drafting.",
        "data_categories": ["redacted_document_text", "packet_metadata", "structured_ai_output"],
        "provider_selected": False,
    },
    {
        "vendor_id": "stripe_candidate",
        "vendor_name": "Stripe payment processor candidate",
        "purpose": "Future live checkout and billing if payment gates pass.",
        "data_categories": ["billing_contact", "subscription", "payment_event"],
        "provider_selected": False,
    },
    {
        "vendor_id": "malware_cdr_provider_tbd",
        "vendor_name": "Malware scanning or CDR provider",
        "purpose": "Production upload quarantine scanning and file-safety decisioning.",
        "data_categories": ["uploaded_file", "file_hash", "scan_result"],
        "provider_selected": False,
    },
    {
        "vendor_id": "monitoring_error_provider_tbd",
        "vendor_name": "Monitoring and error reporting provider",
        "purpose": "Operational monitoring, errors, alerting, and incident response.",
        "data_categories": ["logs", "metrics", "trace_ids", "error_context"],
        "provider_selected": False,
    },
    {
        "vendor_id": "support_email_provider_tbd",
        "vendor_name": "Support/email provider",
        "purpose": "Support contact, incident notices, and account communications.",
        "data_categories": ["email", "support_message", "incident_notice"],
        "provider_selected": False,
    },
)

TRUST_GATES: tuple[dict[str, Any], ...] = (
    {"gate_id": "hosted_managed_auth_gate", "owner": "security_owner", "state": "blocked"},
    {"gate_id": "admin_mfa_gate", "owner": "security_owner", "state": "blocked"},
    {"gate_id": "tenant_authorization_gate", "owner": "engineering_owner", "state": "blocked"},
    {"gate_id": "hosted_session_security_gate", "owner": "security_owner", "state": "blocked"},
    {"gate_id": "hosted_rate_limit_gate", "owner": "engineering_owner", "state": "blocked"},
    {"gate_id": "private_storage_gate", "owner": "security_owner", "state": "blocked"},
    {"gate_id": "malware_scan_gate", "owner": "security_owner", "state": "blocked"},
    {"gate_id": "production_audit_log_gate", "owner": "security_owner", "state": "blocked"},
    {"gate_id": "retention_deletion_gate", "owner": "privacy_owner", "state": "blocked"},
    {"gate_id": "vendor_approval_gate", "owner": "privacy_owner", "state": "blocked"},
    {"gate_id": "production_backup_restore_gate", "owner": "operations_owner", "state": "blocked"},
    {"gate_id": "production_monitoring_gate", "owner": "operations_owner", "state": "blocked"},
    {"gate_id": "incident_response_gate", "owner": "operations_owner", "state": "blocked"},
    {"gate_id": "secret_management_gate", "owner": "security_owner", "state": "blocked"},
    {"gate_id": "data_residency_gate", "owner": "privacy_owner", "state": "blocked"},
    {"gate_id": "real_file_upload_gate", "owner": "security_privacy_reviewer", "state": "blocked"},
)

CRITICAL_BACKUP_ARTIFACTS: tuple[str, ...] = (
    "system_review_graph/customer_workflow.sqlite",
    "system_review_graph/product_runtime_state.json",
    "system_review_graph/production_redevelopment_plan.json",
    "system_review_graph/production_payment_monetization_manifest.json",
    "system_review_graph/auth_rbac_matrix.json",
    "system_review_graph/public_upload_policy.json",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _local_backup_restore_drill(root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="trc-backup-restore-") as tmp:
        restore_root = Path(tmp)
        for relative in CRITICAL_BACKUP_ARTIFACTS:
            source = root / relative
            record: dict[str, Any] = {
                "relative_path": relative,
                "source_exists": source.exists(),
                "restored": False,
                "hash_matches": False,
            }
            if source.exists():
                destination = restore_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                source_hash = _sha256(source)
                restored_hash = _sha256(destination)
                record.update(
                    {
                        "source_bytes": source.stat().st_size,
                        "source_sha256": source_hash,
                        "restored_sha256": restored_hash,
                        "restored": destination.exists(),
                        "hash_matches": source_hash == restored_hash,
                    }
                )
            records.append(record)
    existing = [row for row in records if row["source_exists"]]
    return {
        "status": "local_backup_restore_hash_drill_passed" if existing and all(row["hash_matches"] for row in existing) else "local_backup_restore_hash_drill_failed",
        "generated_at": _now(),
        "scope": "local_artifact_roundtrip_only",
        "production_backup_restore_test_passed": False,
        "artifact_count": len(records),
        "existing_artifact_count": len(existing),
        "restored_artifact_count": len([row for row in existing if row["restored"]]),
        "hash_match_count": len([row for row in existing if row["hash_matches"]]),
        "records": records,
        "proof_boundary": "This proves local artifact backup/restore hashing only; hosted database, private object storage, and managed backup restore proof remain external gates.",
    }


def _artifact_status(root: Path, relative: str) -> dict[str, Any]:
    path = root / "system_review_graph" / relative
    return {"artifact": relative, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def _trust_control_records(root: Path, backup_drill: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for control in CONTROL_REQUIREMENTS:
        basis = [_artifact_status(root, artifact) for artifact in control["local_basis"]]
        local_evidence_present = all(row["exists"] for row in basis)
        if control["control_id"] == "backup_restore":
            local_evidence_present = backup_drill["status"] == "local_backup_restore_hash_drill_passed"
        records.append(
            {
                **control,
                "local_evidence_present": local_evidence_present,
                "production_gate_state": "blocked",
                "production_approved": False,
                "real_user_data_allowed": False,
                "basis_artifacts": basis,
            }
        )
    return records


def _vendor_records() -> list[dict[str, Any]]:
    return [
        {
            **vendor,
            "privacy_review_status": "not_approved",
            "security_review_status": "not_approved",
            "data_residency_decision": "not_decided",
            "contract_or_dpa_status": "not_attached",
            "production_approved": False,
            "customer_data_allowed": False,
            "exit_plan_required": True,
        }
        for vendor in VENDOR_RECORDS
    ]


def _event_count(payload: Any) -> int:
    if isinstance(payload, dict):
        events = payload.get("events", [])
        return len(events) if isinstance(events, list) else 0
    if isinstance(payload, list):
        return len(payload)
    return 0


def _incident_runbooks() -> list[dict[str, Any]]:
    scenarios = [
        "privacy_breach_or_wrong_recipient",
        "malicious_file_upload",
        "prompt_injection_from_uploaded_document",
        "tenant_access_violation",
        "lost_or_corrupt_data_restore_needed",
        "payment_webhook_or_live_checkout_incident",
        "source_monitor_material_change",
        "public_claim_or_report_language_issue",
    ]
    return [
        {
            "scenario": scenario,
            "owner": "operations_owner",
            "steps": [
                "triage severity and affected records",
                "contain external effects and disable risky workflow",
                "preserve audit evidence",
                "notify required owner/reviewer",
                "record corrective action and retest",
            ],
            "rehearsed": False,
            "production_ready": False,
        }
        for scenario in scenarios
    ]


def build_production_security_privacy_reliability_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    auth_rbac = _load_json(graph / "auth_rbac_matrix.json", {})
    upload_policy = _load_json(graph / "public_upload_policy.json", {})
    ai_policy = _load_json(graph / "ai_data_policy.json", {})
    audit_events = _load_json(graph / "audit_events.json", {})
    deletion_requests = _load_json(graph / "deletion_requests.json", {})
    approval_proof = _load_json(graph / "legal_privacy_security_approval_manifest.json", {})
    backup_drill = _local_backup_restore_drill(root)
    controls = _trust_control_records(root, backup_drill)
    vendors = _vendor_records()
    runbooks = _incident_runbooks()
    gates = [
        {
            **gate,
            "required_evidence": next(
                (
                    row["production_required_evidence"]
                    for row in CONTROL_REQUIREMENTS
                    if row["gate_id"] == gate["gate_id"]
                ),
                "Production security/privacy/reliability reviewer approval.",
            ),
            "opened_by_local_artifact": False,
        }
        for gate in TRUST_GATES
    ]
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "research_reference_count": len(TRUST_RESEARCH_REFERENCES),
        "research_references": list(TRUST_RESEARCH_REFERENCES),
        "trust_control_count": len(controls),
        "trust_controls": controls,
        "local_control_evidence_count": len([row for row in controls if row["local_evidence_present"]]),
        "trust_gate_count": len(gates),
        "blocked_trust_gate_count": len([row for row in gates if row["state"] == "blocked"]),
        "trust_gates": gates,
        "vendor_record_count": len(vendors),
        "vendor_register": vendors,
        "unapproved_vendor_count": len([row for row in vendors if not row["production_approved"]]),
        "incident_runbook_count": len(runbooks),
        "incident_runbooks": runbooks,
        "backup_restore_drill": backup_drill,
        "auth_role_count": len(auth_rbac.get("roles", [])),
        "auth_membership_count": len(auth_rbac.get("memberships", [])),
        "upload_policy_status": upload_policy.get("status", "missing"),
        "ai_policy_status": ai_policy.get("status", "missing"),
        "audit_event_count": _event_count(audit_events),
        "deletion_request_count": len(deletion_requests.get("requests", [])),
        "legal_privacy_security_approval_evidence_status": approval_proof.get(
            "status",
            "legal_privacy_security_approval_manifest_missing",
        ),
        "legal_privacy_security_approval_record_count": approval_proof.get("approval_record_count", 0),
        "legal_privacy_security_accepted_approval_record_count": approval_proof.get("accepted_approval_record_count", 0),
        "legal_privacy_security_approval_blocked_gate_count": approval_proof.get(
            "blocked_gate_count",
            LEGAL_PRIVACY_SECURITY_APPROVAL_FALLBACK_GATE_COUNT,
        ),
        "legal_privacy_security_approved_by_evidence": approval_proof.get(
            "legal_privacy_security_approved_by_evidence",
            False,
        ),
        "legal_privacy_security_claims_opened_by_intake": approval_proof.get("claims_opened_by_intake", False),
        "managed_auth_ready": False,
        "admin_mfa_enforced": False,
        "hosted_secure_sessions_ready": False,
        "hosted_rate_limits_enforced": False,
        "private_object_storage_ready": False,
        "malware_scanning_ready": False,
        "production_audit_log_ready": False,
        "retention_policy_approved": False,
        "vendor_register_approved": False,
        "production_backup_restore_passed": False,
        "production_monitoring_ready": False,
        "incident_runbook_rehearsed": False,
        "secrets_manager_ready": False,
        "data_residency_approved": False,
        "real_file_uploads_allowed": False,
        "unrestricted_uploads_enabled": False,
        "hosted_private_beta_ready": False,
        "production_trust_approved": False,
        "public_launch_ready": False,
        "proof_boundary": "Local controls, evidence mapping, vendor register, incident runbooks, and local backup/restore hash drill are ready for review. Hosted production trust, real file uploads, private beta, and public launch stay blocked until managed auth, MFA, private storage, malware scanning, retention, vendor review, monitoring, incident rehearsal, backup restore, secrets, data-residency, and qualified privacy/security signoff are proven.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _doc(manifest: dict[str, Any]) -> str:
    controls = "\n".join(
        f"- {row['label']}: {row['local_status']} / production gate {row['production_gate_state']}"
        for row in manifest["trust_controls"]
    )
    gates = "\n".join(f"- {row['gate_id']}: {row['state']} ({row['owner']})" for row in manifest["trust_gates"])
    return f"""# Production Security, Privacy, Reliability, And Trust Engine

Status: `{manifest['status']}`

The production-trust engine turns local auth, RBAC, upload, AI, deletion,
audit, payment, and operations controls into one reviewable trust package. It
also performs a local backup/restore hash drill over critical artifacts.

## Controls

{controls}

## Gates

{gates}

## Local Backup/Restore Drill

- Status: `{manifest['backup_restore_drill']['status']}`
- Existing artifacts checked: `{manifest['backup_restore_drill']['existing_artifact_count']}`
- Hash matches: `{manifest['backup_restore_drill']['hash_match_count']}`

## Gate Boundary

- Real file uploads allowed: `{str(manifest['real_file_uploads_allowed']).lower()}`
- Hosted private beta ready: `{str(manifest['hosted_private_beta_ready']).lower()}`
- Production trust approved: `{str(manifest['production_trust_approved']).lower()}`
- Public launch ready: `{str(manifest['public_launch_ready']).lower()}`

## Returned Approval Evidence

- Approval evidence status: `{manifest['legal_privacy_security_approval_evidence_status']}`
- Approval records received: `{manifest['legal_privacy_security_approval_record_count']}`
- Accepted approval records: `{manifest['legal_privacy_security_accepted_approval_record_count']}`
- Approval gates blocked: `{manifest['legal_privacy_security_approval_blocked_gate_count']}`
- Legal/privacy/security approved by evidence: `{str(manifest['legal_privacy_security_approved_by_evidence']).lower()}`

No local artifact proves hosted authentication, admin MFA, private object
storage, malware scanning, production monitoring, managed backups, privacy/legal
approval, security approval, AI vendor approval, or public launch approval.
"""


def write_production_security_privacy_reliability_engine_artifacts(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Path]:
    root = repo_root or Path(__file__).resolve().parents[2]
    srg = root / "system_review_graph"
    docs = root / "docs"
    paths = {
        "manifest": srg / "production_security_privacy_reliability_manifest.json",
        "controls": srg / "production_trust_control_matrix.json",
        "vendors": srg / "production_vendor_register.json",
        "backup_restore": srg / "production_backup_restore_drill.json",
        "incidents": srg / "production_incident_runbooks.json",
        "research": srg / "production_trust_research_references.json",
        "doc": docs / "PRODUCTION_SECURITY_PRIVACY_RELIABILITY_ENGINE.md",
    }
    _write_json(paths["manifest"], manifest)
    _write_json(paths["controls"], {"status": "production_trust_control_matrix_ready_external_gates_closed", "trust_controls": manifest["trust_controls"], "trust_gates": manifest["trust_gates"]})
    _write_json(paths["vendors"], {"status": "production_vendor_register_ready_approvals_required", "vendor_register": manifest["vendor_register"]})
    _write_json(paths["backup_restore"], manifest["backup_restore_drill"])
    _write_json(paths["incidents"], {"status": "production_incident_runbooks_ready_rehearsal_required", "incident_runbooks": manifest["incident_runbooks"]})
    _write_json(paths["research"], {"status": "production_trust_research_references_ready", "research_references": manifest["research_references"]})
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(_doc(manifest), encoding="utf-8")
    return paths
