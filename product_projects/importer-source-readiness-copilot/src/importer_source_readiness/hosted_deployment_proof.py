"""Hosted staging/production proof intake.

Local Docker health and deployment reports are useful, but they are not hosted
private-beta proof. This module defines the exact evidence needed before a
hosted environment can count as real staging evidence, while keeping hosted
private beta and public launch closed until the launch control plane and human
review gates agree.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATUS = "hosted_deployment_proof_intake_ready_real_hosted_evidence_required_claims_closed"
CONTRACT_STATUS = "hosted_deployment_proof_contract_ready_claims_closed"
GATE_MATRIX_STATUS = "hosted_deployment_gate_matrix_ready_claims_closed"
BLOCKER_EXPORT_STATUS = "hosted_deployment_blocker_export_ready_claims_closed"

ALLOWED_DECISIONS = (
    "ready_for_private_beta_scope",
    "demo_hosted_no_real_data_only",
    "not_ready",
    "needs_more_evidence",
)

REQUIRED_PROOF_CATEGORIES: tuple[dict[str, str], ...] = (
    {
        "category": "live_url_or_environment",
        "label": "Hosted URL or named environment",
        "why": "A localhost or local Docker run is not hosted private-beta proof.",
    },
    {
        "category": "build_or_commit",
        "label": "Build or commit reference",
        "why": "Reviewers need to know exactly what code and artifact were deployed.",
    },
    {
        "category": "tls_https_cookie_flags",
        "label": "TLS, HTTPS, and secure cookie proof",
        "why": "Hosted sessions must be protected in transit and by session cookie settings.",
    },
    {
        "category": "managed_auth_and_session_config",
        "label": "Managed auth and session configuration",
        "why": "Real users need account/session controls beyond local seeded sessions.",
    },
    {
        "category": "secrets_manager_and_key_rotation",
        "label": "Secrets manager and key rotation",
        "why": "Hosted API, AI, storage, and payment keys must not live in local files or logs.",
    },
    {
        "category": "private_database_and_object_storage",
        "label": "Private database and object storage",
        "why": "Real trade files and packet data need private managed persistence, not local filesystem proof.",
    },
    {
        "category": "upload_file_safety_controls",
        "label": "Upload scanning, quarantine, and file-safety controls",
        "why": "Real uploads stay closed until hosted malware scanning, type checks, and quarantine are proven.",
    },
    {
        "category": "rate_limit_and_abuse_controls",
        "label": "Rate-limit and abuse controls",
        "why": "Public routes and upload/API paths need hosted abuse controls and evidence.",
    },
    {
        "category": "smoke_test_result",
        "label": "Hosted smoke-test result",
        "why": "The exact environment must pass core app flows, not just local tests.",
    },
    {
        "category": "monitoring_or_logs",
        "label": "Monitoring, logs, and alert ownership",
        "why": "Private beta needs visibility into errors, uploads, auth, AI, jobs, and incidents.",
    },
    {
        "category": "backup_restore_or_rollback",
        "label": "Backup, restore, or rollback proof",
        "why": "Operators must prove recovery from bad deploys or data loss before real users.",
    },
    {
        "category": "incident_support_owner",
        "label": "Incident and support owner",
        "why": "A real beta needs named support and incident-response ownership.",
    },
    {
        "category": "privacy_data_handling_scope",
        "label": "Privacy and data-handling scope",
        "why": "Hosted beta must document whether real files, AI, retention, deletion, and vendors are in scope.",
    },
)

SOURCE_ANCHORS: tuple[dict[str, str], ...] = (
    {
        "source_id": "canadian-centre-baseline-controls",
        "name": "Baseline cyber security controls for small and medium organizations",
        "publisher": "Canadian Centre for Cyber Security",
        "url": "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations",
        "checked_at": "2026-06-29",
        "product_use": "Baseline hosted operations, backups, patching, monitoring, and incident-readiness reference.",
    },
    {
        "source_id": "owasp-tls-cheat-sheet",
        "name": "Transport Layer Security Cheat Sheet",
        "publisher": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html",
        "checked_at": "2026-06-29",
        "product_use": "TLS/HTTPS and transport protection evidence anchor.",
    },
    {
        "source_id": "owasp-secrets-management",
        "name": "Secrets Management Cheat Sheet",
        "publisher": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html",
        "checked_at": "2026-06-29",
        "product_use": "Hosted secrets, tokens, and key-control evidence anchor.",
    },
    {
        "source_id": "owasp-logging-cheat-sheet",
        "name": "Logging Cheat Sheet",
        "publisher": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html",
        "checked_at": "2026-06-29",
        "product_use": "Security logging and operational monitoring evidence anchor.",
    },
    {
        "source_id": "cisa-secure-by-design",
        "name": "Secure by Design",
        "publisher": "Cybersecurity and Infrastructure Security Agency",
        "url": "https://www.cisa.gov/securebydesign",
        "checked_at": "2026-06-29",
        "product_use": "Secure-by-design/default launch posture and product owner accountability anchor.",
    },
)

LOCAL_ONLY_RE = re.compile(r"^(https?://)?(localhost|127\.0\.0\.1|0\.0\.0\.0|::1)(:|/|$)", re.IGNORECASE)


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


def _missing_identity_fields(record: dict[str, Any]) -> list[str]:
    checks = (
        (("environment_id", "environment_name"), "environment id or name"),
        (("environment_url", "live_url", "url"), "hosted environment URL"),
        (("environment_type",), "environment type"),
        (("operator_name", "owner_name"), "operator or owner name"),
        (("deployed_at", "checked_at"), "deployed or checked date"),
        (("build_or_commit_ref", "commit_ref", "build_ref"), "build or commit reference"),
        (("decision",), "decision"),
    )
    missing = []
    for names, label in checks:
        if not any(_text(record.get(name)) for name in names):
            missing.append(label)
    return missing


def _environment_url(record: dict[str, Any]) -> str:
    return _text(record.get("environment_url") or record.get("live_url") or record.get("url"))


def validate_hosted_deployment_record(
    record: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    missing_fields = _missing_identity_fields(record)
    decision = _text(record.get("decision"))
    environment_type = _text(record.get("environment_type"))
    environment_url = _environment_url(record)
    missing_categories = [
        item["category"] for item in REQUIRED_PROOF_CATEGORIES if item["category"] not in _evidence_categories(record)
    ]
    local_url_used = bool(environment_url and LOCAL_ONLY_RE.search(environment_url))
    https_ready = environment_url.startswith("https://")
    allowed_environment = environment_type in {"staging_private_beta", "production_candidate", "demo_hosted_no_real_data"}
    if missing_fields:
        status = "received_missing_environment_identity"
    elif decision not in ALLOWED_DECISIONS:
        status = "received_unknown_decision"
    elif not allowed_environment:
        status = "received_unsupported_environment_type"
    elif local_url_used:
        status = "received_localhost_not_hosted_proof"
    elif not https_ready:
        status = "received_without_https_proof"
    elif missing_categories:
        status = "received_missing_required_hosted_evidence"
    elif decision == "ready_for_private_beta_scope":
        status = "accepted_hosted_private_beta_scope_evidence"
    elif decision == "demo_hosted_no_real_data_only":
        status = "accepted_demo_hosted_no_real_data_only"
    else:
        status = "received_not_ready"

    accepted = status in {"accepted_hosted_private_beta_scope_evidence", "accepted_demo_hosted_no_real_data_only"}
    private_beta_ready = status == "accepted_hosted_private_beta_scope_evidence"
    return {
        "generated_at": generated_at,
        "status": status,
        "environment_id": record.get("environment_id") or record.get("environment_name") or "",
        "environment_type": environment_type,
        "environment_url": environment_url,
        "operator_name": record.get("operator_name") or record.get("owner_name") or "",
        "deployed_at": record.get("deployed_at") or record.get("checked_at") or "",
        "build_or_commit_ref": record.get("build_or_commit_ref") or record.get("commit_ref") or record.get("build_ref") or "",
        "decision": decision,
        "source_file": record.get("source_file") or "",
        "missing_input_fields": missing_fields,
        "required_evidence_categories": [item["category"] for item in REQUIRED_PROOF_CATEGORIES],
        "missing_evidence_categories": missing_categories,
        "local_url_used": local_url_used,
        "https_ready": https_ready,
        "accepted_for_hosted_deployment_evidence": accepted,
        "hosted_private_beta_ready_by_environment_evidence": private_beta_ready,
        "public_launch_ready_by_environment_evidence": False,
        "real_file_uploads_allowed_by_environment_evidence": False,
        "claims_opened_by_validation": False,
        "external_effects_created": False,
        "next_valid_move": _next_valid_move(status),
    }


def _next_valid_move(status: str) -> str:
    if status == "accepted_hosted_private_beta_scope_evidence":
        return "Keep hosted proof attached, then require Wave 1 review, privacy/security approval, beta outcomes, and launch-control approval."
    if status == "accepted_demo_hosted_no_real_data_only":
        return "Use this only for demo/no-real-data scope; collect private-beta hosted controls before real users or files."
    if status == "received_missing_environment_identity":
        return "Add environment identity, URL, type, operator, deployment date, build reference, and decision."
    if status == "received_unknown_decision":
        return "Use one of the allowed hosted deployment decisions and rerun validation."
    if status == "received_unsupported_environment_type":
        return "Classify the environment as staging_private_beta, production_candidate, or demo_hosted_no_real_data."
    if status == "received_localhost_not_hosted_proof":
        return "Provide a real hosted URL or named hosted environment; localhost cannot count."
    if status == "received_without_https_proof":
        return "Attach HTTPS/TLS evidence for the hosted URL."
    if status == "received_missing_required_hosted_evidence":
        return "Attach every required hosted evidence category before counting the environment."
    return "Resolve hosted deployment issues and keep private beta/public launch closed."


def build_hosted_deployment_contract(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": CONTRACT_STATUS,
        "generated_at": generated_at,
        "allowed_decisions": list(ALLOWED_DECISIONS),
        "required_evidence_categories": list(REQUIRED_PROOF_CATEGORIES),
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "source_anchors": list(SOURCE_ANCHORS),
        "source_anchor_count": len(SOURCE_ANCHORS),
        "drop_paths": [
            "external_inputs/hosted_staging_production_proof.json",
            "external_inputs/hosted_deployment_proofs/*.json",
        ],
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "This contract defines hosted deployment proof. It is not proof that a hosted environment exists.",
    }


def _load_hosted_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    single = _load_json(repo_root / "external_inputs" / "hosted_staging_production_proof.json", {})
    if isinstance(single, dict) and single:
        single["source_file"] = "external_inputs/hosted_staging_production_proof.json"
        records.append(single)
    proof_dir = repo_root / "external_inputs" / "hosted_deployment_proofs"
    if proof_dir.exists():
        for path in sorted(proof_dir.glob("*.json")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                payload["source_file"] = str(path.relative_to(repo_root))
                records.append(payload)
    return records


def _selected_validation(validations: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in validations if row.get("accepted_for_hosted_deployment_evidence") is True]
    candidates = accepted or validations
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: str(row.get("deployed_at") or row.get("generated_at") or row.get("source_file") or ""))[-1]


def _gate_rows(selected: dict[str, Any] | None, generated_at: str) -> list[dict[str, Any]]:
    rows = []
    for item in REQUIRED_PROOF_CATEGORIES:
        category = item["category"]
        missing = selected is None or category in selected.get("missing_evidence_categories", [])
        rows.append(
            {
                "generated_at": generated_at,
                "gate_id": f"hosted:{category}",
                "category": category,
                "label": item["label"],
                "status": "missing_real_hosted_evidence" if missing else "evidence_attached_for_review",
                "blocks_private_beta": missing,
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
        if row["blocks_private_beta"] is not True:
            continue
        rows.append(
            {
                "id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "finding_id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "module": "hosted_deployment_proof",
                "reviewer_role": "DevOps/Production Readiness Review",
                "severity": "P0",
                "affected_stage": "hosted_private_beta",
                "affected_file_or_artifact": "system_review_graph/hosted_deployment_proof_manifest.json",
                "issue": f"Hosted deployment proof missing: {row['label']}.",
                "owner": "DevOps/production reviewer",
                "required_fix": row["why"],
                "retest_command": "python3 scripts/check_product.py",
                "blocks_private_beta": True,
                "blocks_public_launch": True,
                "evidence": "hosted_deployment_proof_manifest.json records missing hosted evidence.",
                "gate": "closed",
                "next_valid_move": "Attach real hosted deployment proof and rerun hosted deployment intake.",
                "unsafe_to_bypass": True,
                "created_at": generated_at,
                "source_report": "system_review_graph/hosted_deployment_proof_manifest.json",
            }
        )
    return rows


def build_hosted_deployment_proof_intake(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    records = _load_hosted_records(root)
    validations = [validate_hosted_deployment_record(record, generated_at) for record in records]
    selected = _selected_validation(validations)
    gate_rows = _gate_rows(selected, generated_at)
    blocker_rows = _blocker_rows(gate_rows, generated_at)
    accepted_count = sum(1 for row in validations if row["accepted_for_hosted_deployment_evidence"] is True)
    private_beta_ready = selected is not None and selected.get("hosted_private_beta_ready_by_environment_evidence") is True
    return {
        "status": STATUS,
        "generated_at": generated_at,
        "hosted_record_count": len(records),
        "accepted_hosted_record_count": accepted_count,
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "attached_evidence_category_count": 0
        if selected is None
        else len(REQUIRED_PROOF_CATEGORIES) - len(selected.get("missing_evidence_categories", [])),
        "missing_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES)
        if selected is None
        else len(selected.get("missing_evidence_categories", [])),
        "gate_count": len(gate_rows),
        "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_private_beta"] is True),
        "blocker_export_count": len(blocker_rows),
        "selected_validation": selected or {},
        "validations": validations,
        "hosted_private_beta_ready_by_environment_evidence": private_beta_ready,
        "public_launch_ready_by_environment_evidence": False,
        "real_file_uploads_allowed_by_environment_evidence": False,
        "claims_opened_by_intake": False,
        "external_effects_created": False,
        "contract": build_hosted_deployment_contract(generated_at),
        "gate_matrix": {
            "status": GATE_MATRIX_STATUS,
            "generated_at": generated_at,
            "gate_count": len(gate_rows),
            "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_private_beta"] is True),
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
        "next_valid_move": "Provision or document hosted staging, attach every required proof category, and rerun hosted deployment intake.",
        "proof_boundary": (
            "This validates hosted deployment evidence only. It does not approve real uploads, hosted private beta, "
            "public launch, legal/privacy/security readiness, payments, customs, buyer validation, or supplier verification."
        ),
    }


def render_hosted_deployment_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Hosted Deployment Proof",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Current Result",
        "",
        f"- Hosted records received: {payload['hosted_record_count']}",
        f"- Accepted hosted records: {payload['accepted_hosted_record_count']}",
        f"- Missing evidence categories: {payload['missing_evidence_category_count']}",
        f"- Hosted private beta ready by environment evidence: {str(payload['hosted_private_beta_ready_by_environment_evidence']).lower()}",
        f"- Public launch ready by environment evidence: {str(payload['public_launch_ready_by_environment_evidence']).lower()}",
        f"- Claims opened by intake: {str(payload['claims_opened_by_intake']).lower()}",
        "",
        "## Drop Paths",
        "",
        "- `external_inputs/hosted_staging_production_proof.json`",
        "- `external_inputs/hosted_deployment_proofs/*.json`",
        "",
        "## Gate Matrix",
        "",
        "| Evidence | Status | Blocks Private Beta |",
        "| --- | --- | --- |",
    ]
    for row in payload["gate_matrix"]["rows"]:
        lines.append(f"| {row['label']} | `{row['status']}` | `{str(row['blocks_private_beta']).lower()}` |")
    lines.extend(["", "## Source Anchors", ""])
    for source in payload["contract"]["source_anchors"]:
        lines.append(f"- {source['publisher']}: {source['name']} ({source['url']})")
    lines.append("")
    return "\n".join(lines)


def _render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def write_hosted_deployment_proof_artifacts(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    graph = root / "system_review_graph"
    docs = root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    payload = build_hosted_deployment_proof_intake(root, generated_at)
    (graph / "hosted_deployment_proof_contract.json").write_text(_render_json(payload["contract"]), encoding="utf-8")
    manifest_payload = {key: value for key, value in payload.items() if key not in {"contract", "gate_matrix", "blocker_export"}}
    (graph / "hosted_deployment_proof_manifest.json").write_text(_render_json(manifest_payload), encoding="utf-8")
    (graph / "hosted_deployment_gate_matrix.json").write_text(_render_json(payload["gate_matrix"]), encoding="utf-8")
    (graph / "hosted_deployment_blocker_export.jsonl").write_text(
        _render_jsonl(payload["blocker_export"]["rows"]),
        encoding="utf-8",
    )
    (docs / "HOSTED_DEPLOYMENT_PROOF.md").write_text(render_hosted_deployment_markdown(payload), encoding="utf-8")
    return {
        "status": payload["status"],
        "hosted_record_count": payload["hosted_record_count"],
        "accepted_hosted_record_count": payload["accepted_hosted_record_count"],
        "blocked_gate_count": payload["blocked_gate_count"],
        "blocker_export_count": payload["blocker_export_count"],
        "hosted_private_beta_ready_by_environment_evidence": payload["hosted_private_beta_ready_by_environment_evidence"],
        "claims_opened_by_intake": payload["claims_opened_by_intake"],
        "generated_at": generated_at,
    }
