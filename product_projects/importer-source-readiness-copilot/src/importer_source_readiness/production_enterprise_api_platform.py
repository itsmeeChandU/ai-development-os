"""Production enterprise SaaS and API platform engine.

Phase 17 converts the local organization, workspace, RBAC, packet, report,
audit, and route artifacts into enterprise/API contracts. The contracts are
reviewable and testable locally, while live API keys, webhook delivery,
unrestricted uploads, hosted production, payments, and claim-opening behavior
remain closed gates.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_enterprise_api_platform_ready_local_contracts_external_gates_closed"

ENTERPRISE_RESEARCH_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "source_id": "owasp-api-security-2023",
        "source_name": "OWASP API Security Top 10 2023",
        "url": "https://owasp.org/API-Security/editions/2023/en/0x11-t10/",
        "product_use": "API authorization, object access, resource-use, and inventory controls for enterprise endpoints.",
    },
    {
        "source_id": "ietf-rfc-6749-oauth2",
        "source_name": "IETF RFC 6749 OAuth 2.0 Authorization Framework",
        "url": "https://www.rfc-editor.org/rfc/rfc6749",
        "product_use": "Future hosted API authorization model and client credential review.",
    },
    {
        "source_id": "ietf-rfc-6750-bearer",
        "source_name": "IETF RFC 6750 OAuth 2.0 Bearer Token Usage",
        "url": "https://www.rfc-editor.org/rfc/rfc6750",
        "product_use": "Bearer-token handling boundary for API-key and access-token contracts.",
    },
    {
        "source_id": "nist-sp-800-53-rev5",
        "source_name": "NIST SP 800-53 Rev. 5",
        "url": "https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final",
        "product_use": "Access control, audit/accountability, system integrity, and privacy control framing.",
    },
    {
        "source_id": "ietf-rfc-7644-scim",
        "source_name": "IETF RFC 7644 SCIM Protocol",
        "url": "https://www.rfc-editor.org/rfc/rfc7644",
        "product_use": "Future enterprise identity provisioning boundary; not active locally.",
    },
)

API_ENDPOINTS: tuple[dict[str, Any], ...] = (
    {
        "method": "POST",
        "path": "/api/packets",
        "purpose": "Create a Trade Readiness Packet.",
        "permission": "packet:create",
        "tenant_scope": "organization",
    },
    {
        "method": "GET",
        "path": "/api/packets/:id",
        "purpose": "Read a packet visible to the caller.",
        "permission": "packet:read:own_org",
        "tenant_scope": "packet.organization_id",
    },
    {
        "method": "POST",
        "path": "/api/packets/:id/evidence",
        "purpose": "Attach evidence metadata to a packet.",
        "permission": "evidence:create:own_org",
        "tenant_scope": "packet.organization_id",
    },
    {
        "method": "POST",
        "path": "/api/documents/upload",
        "purpose": "Enterprise document-upload contract; real files remain blocked until production upload gates pass.",
        "permission": "evidence:create:own_org",
        "tenant_scope": "packet.organization_id",
        "gate": "real_file_upload_security_gate_closed",
    },
    {
        "method": "POST",
        "path": "/api/sources/refresh",
        "purpose": "Refresh packet source routes without proving current law.",
        "permission": "source:refresh:own_org",
        "tenant_scope": "packet.organization_id",
    },
    {
        "method": "GET",
        "path": "/api/packets/:id/scores",
        "purpose": "Return separate capped decision scores.",
        "permission": "packet:read:own_org",
        "tenant_scope": "packet.organization_id",
    },
    {
        "method": "GET",
        "path": "/api/packets/:id/blocked-claims",
        "purpose": "Return blocked claims from the evidence claim-gate engine.",
        "permission": "packet:read:own_org",
        "tenant_scope": "packet.organization_id",
    },
    {
        "method": "POST",
        "path": "/api/reviews",
        "purpose": "Draft a scoped review request without contacting a reviewer.",
        "permission": "review:request:own_org",
        "tenant_scope": "packet.organization_id",
    },
    {
        "method": "POST",
        "path": "/api/reports",
        "purpose": "Generate or list safe packet reports with blocked claims visible.",
        "permission": "report:export:own_org",
        "tenant_scope": "packet.organization_id",
    },
    {
        "method": "POST",
        "path": "/api/ai/safe-summary",
        "purpose": "Return a safe local packet summary without a live model call.",
        "permission": "report:draft",
        "tenant_scope": "packet.organization_id",
        "gate": "ai_live_model_gate_closed",
    },
    {
        "method": "GET",
        "path": "/api/team-workspace",
        "purpose": "Read team workspace and approval-board state.",
        "permission": "packet:read:own_org",
        "tenant_scope": "organization",
    },
    {
        "method": "GET",
        "path": "/api/billing/usage",
        "purpose": "Read local usage ledger with no live charges.",
        "permission": "billing:read:own_org",
        "tenant_scope": "organization",
    },
    {
        "method": "GET",
        "path": "/api/audit",
        "purpose": "Read scoped audit records.",
        "permission": "audit:read:own_org",
        "tenant_scope": "organization_or_admin",
    },
    {
        "method": "POST",
        "path": "/api/api-keys",
        "purpose": "Record API-key request contract without issuing a live secret.",
        "permission": "api_key:manage:own_org",
        "tenant_scope": "organization",
        "gate": "hosted_auth_and_secret_storage_gate_closed",
    },
    {
        "method": "GET",
        "path": "/api/api-keys",
        "purpose": "List local API-key contract fingerprints only.",
        "permission": "api_key:read:own_org",
        "tenant_scope": "organization",
        "gate": "hosted_auth_and_secret_storage_gate_closed",
    },
    {
        "method": "POST",
        "path": "/api/webhooks",
        "purpose": "Record webhook subscription contract with delivery disabled.",
        "permission": "webhook:manage:own_org",
        "tenant_scope": "organization",
        "gate": "webhook_delivery_gate_closed",
    },
    {
        "method": "GET",
        "path": "/api/webhooks",
        "purpose": "List local webhook event contracts.",
        "permission": "webhook:read:own_org",
        "tenant_scope": "organization",
        "gate": "webhook_delivery_gate_closed",
    },
)

ENTERPRISE_CAPABILITIES: tuple[dict[str, str], ...] = (
    {"capability": "organizations", "source": "auth_rbac_matrix.json", "status": "implemented_local"},
    {"capability": "workspaces", "source": "team_workspace_report.json", "status": "implemented_local"},
    {"capability": "roles_rbac", "source": "auth_rbac_matrix.json", "status": "implemented_local"},
    {"capability": "client_accounts", "source": "organizations", "status": "implemented_local"},
    {"capability": "multi_packet_dashboard", "source": "customer_readiness_report.json", "status": "implemented_local"},
    {"capability": "team_activity", "source": "team_workspace_activity.json", "status": "implemented_local"},
    {"capability": "review_assignment", "source": "production_review_requests.json", "status": "implemented_local"},
    {"capability": "audit_export", "source": "audit_events.json plus report_exports.json", "status": "implemented_local"},
    {"capability": "api_keys", "source": "production_enterprise_api_manifest.json", "status": "local_contract_live_keys_closed"},
    {"capability": "webhooks", "source": "production_enterprise_webhook_policy.json", "status": "local_contract_delivery_closed"},
    {"capability": "usage_limits", "source": "billing_usage_ledger.json", "status": "implemented_local_no_charges"},
    {"capability": "white_label_reports", "source": "production_reports_engine_manifest.json", "status": "local_policy_language_review_required"},
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _route_contracts(api_routes: set[str]) -> list[dict[str, Any]]:
    contracts = []
    for row in API_ENDPOINTS:
        route_present = row["path"] in api_routes
        contracts.append(
            {
                **row,
                "route_present": route_present,
                "status": "route_present_gate_checked" if route_present else "route_missing",
                "auth_required": True,
                "tenant_filter_required": True,
                "object_level_authorization_required": True,
                "claim_gate_required": True,
                "rate_limit_required_before_hosting": True,
                "external_effects_created": False,
                "claims_opened": False,
                "live_mode_enabled": False,
                "proof_boundary": "Enterprise API output must reuse packet, evidence, report, and claim-gate rules.",
            }
        )
    return contracts


def _permission_matrix(auth: dict[str, Any]) -> list[dict[str, Any]]:
    roles = {row.get("role"): set(row.get("permissions", [])) for row in auth.get("roles", [])}
    rows = []
    for contract in API_ENDPOINTS:
        permission = str(contract["permission"])
        allowed_roles = sorted(role for role, permissions in roles.items() if permission in permissions or role in {"admin", "operator"} and contract["tenant_scope"] == "organization_or_admin")
        if permission.startswith(("api_key", "webhook", "billing")):
            allowed_roles = sorted(set(allowed_roles) | {"admin", "customer_admin"})
        if permission == "source:refresh:own_org":
            allowed_roles = sorted(set(allowed_roles) | {"operator", "customer_admin"})
        if permission == "report:draft":
            allowed_roles = sorted(set(allowed_roles) | {"customer", "customer_admin", "operator"})
        rows.append(
            {
                "path": contract["path"],
                "method": contract["method"],
                "permission": permission,
                "allowed_roles": allowed_roles,
                "deny_by_default": True,
                "cross_org_access_allowed": False,
            }
        )
    return rows


def _workspace_controls(auth: dict[str, Any], team: dict[str, Any], customer: dict[str, Any], data_model: dict[str, Any]) -> list[dict[str, Any]]:
    packet_count = len(customer.get("packets", []))
    rls_tables = set(data_model.get("row_level_security_tables", []))
    controls = []
    for org in auth.get("organizations", []):
        org_id = str(org.get("id"))
        memberships = [row for row in auth.get("memberships", []) if row.get("organization_id") == org_id]
        workspace_rows = [
            {
                "workspace_id": row.get("workspace_id"),
                "packet_id": row.get("packet_id"),
                "approval_board": row.get("approval_board", []),
            }
            for row in team.get("workspaces", [])
            if org_id == "org-importer-demo" or org.get("type") == "internal"
        ]
        controls.append(
            {
                "organization_id": org_id,
                "organization_name": org.get("name"),
                "organization_type": org.get("type"),
                "membership_count": len(memberships),
                "roles": sorted({row.get("role") for row in memberships}),
                "workspace_count": len(workspace_rows),
                "packet_count_visible_locally": packet_count if org_id in {"org-importer-demo", "org-internal-ops"} else 0,
                "workspaces": workspace_rows,
                "tenant_isolation_required": True,
                "row_level_security_tables_present": bool(rls_tables),
                "row_level_security_table_count": len(rls_tables),
                "cross_org_packet_access_allowed": org.get("type") == "internal",
                "external_claims_opened": False,
            }
        )
    return controls


def _api_key_records(auth: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for org in auth.get("organizations", []):
        if org.get("type") == "internal":
            continue
        fingerprint = hashlib.sha256(f"{org.get('id')}:local-contract-only".encode("utf-8")).hexdigest()[:16]
        records.append(
            {
                "api_key_id": f"api-key-contract:{org.get('id')}",
                "organization_id": org.get("id"),
                "fingerprint": fingerprint,
                "scopes": ["packets:read", "packets:write", "reports:read", "reviews:write"],
                "raw_secret_returned": False,
                "live_key_issued": False,
                "rotation_days": 90,
                "secret_storage_required": True,
                "hosted_auth_required": True,
                "rate_limit_policy": "100 requests per minute local contract; production limits need hosted proof",
            }
        )
    return records


def _webhook_records(auth: dict[str, Any]) -> list[dict[str, Any]]:
    event_types = ["packet.created", "packet.updated", "report.generated", "review.finding_submitted", "source.stale"]
    return [
        {
            "webhook_id": f"webhook-contract:{org.get('id')}",
            "organization_id": org.get("id"),
            "event_types": event_types,
            "delivery_enabled": False,
            "signing_secret_stored": False,
            "signature_required": True,
            "retry_policy_required": True,
            "external_effects_created": False,
            "next_valid_move": "Approve customer endpoint, signing-secret storage, retry policy, and monitoring before delivery.",
        }
        for org in auth.get("organizations", [])
        if org.get("type") != "internal"
    ]


def _audit_export_policy(runtime: dict[str, Any], reports: dict[str, Any], claim_gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "enterprise_audit_export_policy_ready_local",
        "included_records": [
            "packets",
            "evidence",
            "reports",
            "claim_gate_decisions",
            "score_records",
            "review_requests",
            "audit_events",
            "source_refresh_records",
        ],
        "audit_event_count": len(runtime.get("audit_events", [])),
        "report_export_count": reports.get("export_record_count", 0),
        "claim_gate_decision_count": claim_gate.get("claim_gate_decision_count", 0),
        "tamper_evident_hash_required_before_hosting": True,
        "retention_approval_required": True,
        "external_effects_created": False,
    }


def _usage_limits() -> list[dict[str, Any]]:
    return [
        {"metric": "api_requests_per_minute", "local_limit": 100, "hosted_enforcement_required": True},
        {"metric": "packets_per_workspace", "local_limit": 250, "hosted_enforcement_required": True},
        {"metric": "pdf_exports_per_day", "local_limit": 100, "hosted_enforcement_required": True},
        {"metric": "ai_safe_summaries_per_day", "local_limit": 25, "hosted_enforcement_required": True},
        {"metric": "webhook_deliveries", "local_limit": 0, "hosted_enforcement_required": True},
        {"metric": "real_file_upload_bytes", "local_limit": 0, "hosted_enforcement_required": True},
    ]


def _white_label_policy() -> dict[str, Any]:
    return {
        "status": "white_label_report_policy_ready_language_review_required",
        "allowed_customization": ["logo", "organization_name", "contact_email", "report_cover_note"],
        "forbidden_customization": [
            "remove blocked claims",
            "remove draft watermark before review",
            "remove source citations",
            "change claim-gate language",
            "imply customs, tariff, CFIA, buyer, supplier, payment, or launch approval",
        ],
        "report_language_review_required": True,
        "claims_opened": False,
    }


def build_production_enterprise_api_platform(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    runtime = _load_json(graph / "product_runtime_state.json", {})
    auth = _load_json(graph / "auth_rbac_matrix.json", {})
    data_model = _load_json(graph / "production_data_model_manifest.json", {})
    reports = _load_json(graph / "production_reports_engine_manifest.json", {})
    claim_gate = _load_json(graph / "production_evidence_claim_gate_manifest.json", {})
    team = _load_json(graph / "team_workspace_report.json", {})
    customer = _load_json(graph / "customer_readiness_report.json", {})
    portals = _load_json(graph / "production_portal_workflow_manifest.json", {})

    api_routes = {str(route) for route in runtime.get("api_routes", [])}
    api_contracts = _route_contracts(api_routes)
    permission_matrix = _permission_matrix(auth)
    workspace_controls = _workspace_controls(auth, team, customer, data_model)
    api_key_records = _api_key_records(auth)
    webhook_records = _webhook_records(auth)
    usage_limits = _usage_limits()
    audit_export_policy = _audit_export_policy(runtime, reports, claim_gate)
    white_label_policy = _white_label_policy()

    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "research_reference_count": len(ENTERPRISE_RESEARCH_REFERENCES),
        "research_references": list(ENTERPRISE_RESEARCH_REFERENCES),
        "capability_count": len(ENTERPRISE_CAPABILITIES),
        "capabilities": list(ENTERPRISE_CAPABILITIES),
        "api_contract_count": len(api_contracts),
        "api_contracts": api_contracts,
        "all_required_api_routes_present": all(row["route_present"] for row in api_contracts),
        "permission_matrix_count": len(permission_matrix),
        "permission_matrix": permission_matrix,
        "workspace_control_count": len(workspace_controls),
        "workspace_controls": workspace_controls,
        "api_key_record_count": len(api_key_records),
        "api_key_records": api_key_records,
        "webhook_record_count": len(webhook_records),
        "webhook_records": webhook_records,
        "usage_limit_count": len(usage_limits),
        "usage_limits": usage_limits,
        "audit_export_policy": audit_export_policy,
        "white_label_policy": white_label_policy,
        "portal_dependency_status": portals.get("status"),
        "report_dependency_status": reports.get("status"),
        "claim_gate_dependency_status": claim_gate.get("status"),
        "hosted_enterprise_ready": False,
        "live_api_keys_issued": False,
        "webhook_delivery_enabled": False,
        "unrestricted_uploads_enabled": False,
        "white_label_claims_approved": False,
        "external_effects_created": False,
        "claims_opened": False,
        "live_payment_ready": False,
        "public_launch_ready": False,
        "proof_boundary": "Enterprise SaaS/API contracts are local and gate-closed; they do not prove hosted auth, live API credentials, webhook delivery, customer terms, production security, or public launch readiness.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _doc(manifest: dict[str, Any]) -> str:
    endpoint_lines = "\n".join(
        f"- {row['method']} `{row['path']}`: {row['purpose']} ({row['status']})"
        for row in manifest["api_contracts"]
    )
    capability_lines = "\n".join(
        f"- {row['capability']}: {row['status']}"
        for row in manifest["capabilities"]
    )
    return f"""# Production Enterprise API Platform

Status: `{manifest['status']}`

The enterprise API platform turns the existing organization, workspace, packet,
report, claim-gate, audit, and portal artifacts into scoped API contracts for
brokers, advisors, and enterprise teams.

## Capabilities

{capability_lines}

## API Contracts

{endpoint_lines}

## Gate Boundary

- Hosted enterprise ready: {str(manifest['hosted_enterprise_ready']).lower()}
- Live API keys issued: {str(manifest['live_api_keys_issued']).lower()}
- Webhook delivery enabled: {str(manifest['webhook_delivery_enabled']).lower()}
- Unrestricted uploads enabled: {str(manifest['unrestricted_uploads_enabled']).lower()}
- White-label claims approved: {str(manifest['white_label_claims_approved']).lower()}
- Claims opened: {str(manifest['claims_opened']).lower()}

The product can expose reviewable local API contracts, API-key fingerprints,
webhook event shapes, audit export rules, usage limits, and white-label report
rules. It still needs hosted auth, live credential storage, webhook delivery
approval, enterprise terms, security review, and customer validation before
enterprise production gates can open.
"""


def write_production_enterprise_api_platform_artifacts(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Path]:
    root = repo_root or Path(__file__).resolve().parents[2]
    srg = root / "system_review_graph"
    docs = root / "docs"
    paths = {
        "manifest": srg / "production_enterprise_api_manifest.json",
        "api_contracts": srg / "production_enterprise_api_contracts.json",
        "rbac_policy": srg / "production_enterprise_rbac_policy.json",
        "workspace_controls": srg / "production_enterprise_workspace_controls.json",
        "webhook_policy": srg / "production_enterprise_webhook_policy.json",
        "audit_export_policy": srg / "production_enterprise_audit_export_policy.json",
        "research_references": srg / "production_enterprise_research_references.json",
        "doc": docs / "PRODUCTION_ENTERPRISE_API_PLATFORM.md",
    }
    _write_json(paths["manifest"], manifest)
    _write_json(paths["api_contracts"], {"status": "production_enterprise_api_contracts_ready", "api_contracts": manifest["api_contracts"]})
    _write_json(paths["rbac_policy"], {"status": "production_enterprise_rbac_policy_ready", "permission_matrix": manifest["permission_matrix"]})
    _write_json(paths["workspace_controls"], {"status": "production_enterprise_workspace_controls_ready", "workspace_controls": manifest["workspace_controls"], "usage_limits": manifest["usage_limits"], "white_label_policy": manifest["white_label_policy"]})
    _write_json(paths["webhook_policy"], {"status": "production_enterprise_webhook_policy_ready_delivery_closed", "webhook_records": manifest["webhook_records"], "api_key_records": manifest["api_key_records"]})
    _write_json(paths["audit_export_policy"], manifest["audit_export_policy"])
    _write_json(paths["research_references"], {"status": "production_enterprise_research_references_ready", "research_references": manifest["research_references"]})
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(_doc(manifest), encoding="utf-8")
    return paths
