"""Runtime product contract for customer, operator, and expert workflows."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CSRF_TOKEN = "local-dev-csrf-token"
MAX_EVIDENCE_UPLOAD_BYTES = 5 * 1024 * 1024

PRODUCT_BOUNDARY = (
    "Importer Source Readiness Copilot organizes evidence and blockers. It does not provide "
    "legal, customs, tariff, tax, CFIA, supplier, buyer, compliance, or launch advice."
)

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "customer": [
        "packet:create",
        "packet:read:own_org",
        "packet:update:own_org",
        "evidence:create:own_org",
        "report:export:own_org",
        "review:request:own_org",
        "deletion:request:own_org",
    ],
    "customer_admin": [
        "packet:create",
        "packet:read:own_org",
        "packet:update:own_org",
        "evidence:create:own_org",
        "report:export:own_org",
        "review:request:own_org",
        "deletion:request:own_org",
        "member:manage:own_org",
    ],
    "operator": [
        "packet:read:any_org",
        "blocker:triage",
        "evidence:inspect",
        "ai_review:run",
        "review:request",
        "report:export",
        "audit:read",
    ],
    "expert": [
        "review:read:scoped",
        "review:finding:create:scoped",
    ],
    "admin": [
        "user:manage",
        "organization:manage",
        "source:manage",
        "claim_rule:manage",
        "audit:read",
        "system:configure",
    ],
    "ai_system": [
        "extract:fields",
        "summarize:evidence",
        "review:simulate",
        "blocker:suggest",
        "report:draft",
    ],
}

USERS = [
    {
        "id": "user-customer-001",
        "email": "customer@example.local",
        "name": "Local Customer",
        "role": "customer_admin",
        "organization_id": "org-importer-demo",
        "session_token": "customer-session",
    },
    {
        "id": "user-operator-001",
        "email": "operator@example.local",
        "name": "Internal Operator",
        "role": "operator",
        "organization_id": "org-internal-ops",
        "session_token": "operator-session",
    },
    {
        "id": "user-admin-001",
        "email": "admin@example.local",
        "name": "Product Admin",
        "role": "admin",
        "organization_id": "org-internal-ops",
        "session_token": "admin-session",
    },
    {
        "id": "user-other-customer-001",
        "email": "other@example.local",
        "name": "Other Customer",
        "role": "customer",
        "organization_id": "org-other-demo",
        "session_token": "other-customer-session",
    },
]

ORGANIZATIONS = [
    {
        "id": "org-importer-demo",
        "name": "Importer Demo Co.",
        "type": "customer",
        "default": True,
    },
    {
        "id": "org-other-demo",
        "name": "Other Customer Org",
        "type": "customer",
        "default": False,
    },
    {
        "id": "org-internal-ops",
        "name": "Importer Source Readiness Ops",
        "type": "internal",
        "default": False,
    },
]

CLAIM_RULES = [
    {
        "claim_type": "source_freshness_claim",
        "display_name": "Source freshness",
        "default_status": "blocked_stale_source",
        "required_evidence_types": ["source_refresh_record"],
        "requires_human_review": False,
        "customer_copy": "Official/reference sources need a dated refresh record before they support even internal reference use.",
    },
    {
        "claim_type": "tariff_classification_claim",
        "display_name": "Tariff / HS classification",
        "default_status": "blocked_requires_human_review",
        "required_evidence_types": ["official_source_reference", "expert_review_finding"],
        "requires_human_review": True,
        "customer_copy": "Tariff/HS classification requires qualified review before external use.",
    },
    {
        "claim_type": "food_safety_claim",
        "display_name": "Food safety / CFIA",
        "default_status": "blocked_requires_human_review",
        "required_evidence_types": ["official_source_reference", "expert_review_finding"],
        "requires_human_review": True,
        "customer_copy": "CFIA/food-import claims stay blocked until a scoped qualified finding exists.",
    },
    {
        "claim_type": "source_rights_claim",
        "display_name": "Source rights / commercial contract",
        "default_status": "blocked_source_rights_unknown",
        "required_evidence_types": ["commercial_contract"],
        "requires_human_review": True,
        "customer_copy": "Source or commercial rights need a contract, terms, or review record.",
    },
    {
        "claim_type": "buyer_validation_claim",
        "display_name": "Buyer validation",
        "default_status": "blocked_missing_evidence",
        "required_evidence_types": ["buyer_feedback"],
        "requires_human_review": False,
        "customer_copy": "Buyer validation needs dated buyer/operator evidence.",
    },
    {
        "claim_type": "launch_readiness_claim",
        "display_name": "Launch readiness",
        "default_status": "blocked_missing_evidence",
        "required_evidence_types": ["private_beta_gate_report"],
        "requires_human_review": True,
        "customer_copy": "Launch readiness remains closed until all product, security, privacy, and human gates are complete.",
    },
]

REVIEW_TEMPLATES = [
    {
        "id": "canada-food-import-review",
        "name": "Canada food import/source readiness",
        "reviewer_role": "Qualified Canada trade/food reviewer",
        "scope": "Review evidence and claim language for Canada import, food, and tariff readiness.",
        "questions": [
            "Does the current evidence support any scoped statement about Canada import/food requirements?",
            "Which claims remain blocked and why?",
            "What evidence or source refresh is required next?",
        ],
        "out_of_scope": [
            "General legal advice",
            "Customs brokerage services",
            "Supplier recommendation",
            "Buyer validation",
            "Commercial launch approval",
        ],
    },
    {
        "id": "privacy-security-review",
        "name": "Privacy and private-beta security review",
        "reviewer_role": "Privacy/security reviewer",
        "scope": "Review private-beta controls, privacy notice, deletion workflow, upload controls, audit, and access boundaries.",
        "questions": [
            "Are org isolation and scoped expert links operating as expected?",
            "Are data deletion and audit records sufficient for private beta?",
            "What controls remain before hosted external use?",
        ],
        "out_of_scope": ["Legal sign-off", "Production penetration test", "Insurance or regulatory certification"],
    },
]

ALLOWED_EVIDENCE_TYPES = {
    "customer_uploaded_document",
    "official_source_reference",
    "third_party_reference",
    "supplier_document",
    "commercial_contract",
    "buyer_feedback",
    "operator_note",
    "expert_review_finding",
    "restricted_party_screening_record",
    "source_refresh_record",
    "customer_uploaded_reference",
    "source_url",
}

FORBIDDEN_REPORT_PHRASES = [
    "approval certificate",
    "compliance certificate",
    "import-ready certificate",
    "safe to import",
    "tariff confirmed",
    "CFIA cleared",
    "supplier verified",
    "buyer validated",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def packet_org_id(packet: dict[str, Any]) -> str:
    return str(packet.get("organization_id") or "org-importer-demo")


def hash_snapshot(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def actor_by_session(session_token: str | None) -> dict[str, Any] | None:
    if not session_token:
        return None
    for user in USERS:
        if user["session_token"] == session_token:
            return {**user, "permissions": ROLE_PERMISSIONS[user["role"]]}
    return None


def default_actor() -> dict[str, Any]:
    return actor_by_session("customer-session") or {}


def can_access_packet(actor: dict[str, Any], packet: dict[str, Any]) -> bool:
    role = actor.get("role")
    if role in {"admin", "operator"}:
        return True
    if role in {"customer", "customer_admin"}:
        return actor.get("organization_id") == packet_org_id(packet)
    if role == "expert":
        return str(packet.get("packet_id")) in set(actor.get("packet_ids", []))
    return False


def claim_matrix_for_packet(packet: dict[str, Any]) -> list[dict[str, Any]]:
    blocker_groups = packet.get("blocker_groups", [])
    group_titles = {str(row.get("title")) for row in blocker_groups}
    evidence_ids = [str(row.get("evidence_id")) for row in packet.get("evidence_items", [])]
    matrix: list[dict[str, Any]] = []
    for rule in CLAIM_RULES:
        status = rule["default_status"]
        if rule["claim_type"] == "source_freshness_claim" and "Source Freshness" not in group_titles:
            status = "allowed_internal_reference"
        elif rule["claim_type"] in {"buyer_validation_claim", "source_rights_claim"} and not packet.get("blockers"):
            status = "allowed_internal_reference"
        matrix.append(
            {
                "id": f"{packet.get('packet_id')}:{rule['claim_type']}",
                "packet_id": packet.get("packet_id"),
                "claim_type": rule["claim_type"],
                "claim_text": rule["display_name"],
                "status": status,
                "evidence_required": rule["required_evidence_types"],
                "evidence_attached": evidence_ids,
                "source_ids": [],
                "blocker_ids": [str(row.get("id")) for row in packet.get("blockers", [])],
                "human_review_required": rule["requires_human_review"],
                "human_review_finding_id": "",
                "allowed_display_text": "Internal reference only" if status == "allowed_internal_reference" else "",
                "blocked_display_text": rule["customer_copy"],
                "last_evaluated_at": now_iso(),
            }
        )
    return matrix


def review_requests_for_workflow(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    due_at = (datetime.now(timezone.utc) + timedelta(days=14)).replace(microsecond=0).isoformat()
    rows: list[dict[str, Any]] = []
    for packet in workflow.get("packets", []):
        template = REVIEW_TEMPLATES[0]
        rows.append(
            {
                "id": f"review-request-{packet['packet_id']}",
                "packet_id": packet["packet_id"],
                "review_type": template["id"],
                "reviewer_email": "reviewer@example.local",
                "reviewer_name": "Scoped Expert Reviewer",
                "reviewer_role": template["reviewer_role"],
                "scope": template["scope"],
                "questions": template["questions"],
                "out_of_scope": template["out_of_scope"],
                "status": "draft",
                "token": f"review-token-{packet['packet_id']}",
                "created_by": "user-operator-001",
                "created_at": workflow.get("generated_at") or now_iso(),
                "due_at": due_at,
                "completed_at": "",
                "packet_ids": [packet["packet_id"]],
            }
        )
    return rows


def report_exports_for_workflow(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    exports: list[dict[str, Any]] = []
    for packet in workflow.get("packets", []):
        packet_id = packet["packet_id"]
        for report_type, fmt in (
            ("customer_readiness_report", "markdown"),
            ("customer_readiness_report", "json"),
            ("expert_review_packet", "markdown"),
            ("operator_blocker_report", "html"),
            ("private_beta_gate_report", "json"),
            ("customer_readiness_report", "pdf"),
        ):
            exports.append(
                {
                    "id": f"{report_type}:{packet_id}:{fmt}",
                    "packet_id": packet_id,
                    "report_type": report_type,
                    "format": fmt,
                    "status": "draft_internal_export_ready" if fmt != "pdf" else "pdf_renderer_ready_basic",
                    "file_id": "",
                    "generated_by": "system",
                    "generated_at": workflow.get("generated_at") or now_iso(),
                    "source_snapshot_hash": hash_snapshot(packet),
                    "included_evidence_ids": [str(row.get("evidence_id")) for row in packet.get("evidence_items", [])],
                    "included_claim_ids": [f"{packet_id}:{rule['claim_type']}" for rule in CLAIM_RULES],
                    "included_blocker_ids": [str(row.get("id")) for row in packet.get("blockers", [])],
                }
            )
    return exports


def audit_events_for_workflow(workflow: dict[str, Any], extra_events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    generated_at = workflow.get("generated_at") or now_iso()
    for packet in workflow.get("packets", []):
        packet_id = packet["packet_id"]
        org_id = packet_org_id(packet)
        events.extend(
            [
                {
                    "id": f"audit:{packet_id}:packet-created",
                    "organization_id": org_id,
                    "actor_type": "customer",
                    "actor_user_id": "user-customer-001",
                    "actor_system_name": "",
                    "event_type": "packet_created",
                    "entity_type": "SourcePacket",
                    "entity_id": packet_id,
                    "before_json": {},
                    "after_json": {"status": packet.get("customer_visible_status")},
                    "ip_address": "local-dev",
                    "user_agent": "local-app",
                    "created_at": generated_at,
                },
                {
                    "id": f"audit:{packet_id}:ai-review-run",
                    "organization_id": org_id,
                    "actor_type": "ai_system",
                    "actor_user_id": "",
                    "actor_system_name": "simulated_ai_review",
                    "event_type": "ai_review_run",
                    "entity_type": "AIReviewRun",
                    "entity_id": f"ai-review-{packet_id}",
                    "before_json": {},
                    "after_json": {"can_open_gate": False},
                    "ip_address": "local-dev",
                    "user_agent": "system",
                    "created_at": generated_at,
                },
                {
                    "id": f"audit:{packet_id}:report-exported",
                    "organization_id": org_id,
                    "actor_type": "operator",
                    "actor_user_id": "user-operator-001",
                    "actor_system_name": "",
                    "event_type": "report_exported",
                    "entity_type": "ReportExport",
                    "entity_id": f"customer_readiness_report:{packet_id}:json",
                    "before_json": {},
                    "after_json": {"status": "draft_internal_export_ready"},
                    "ip_address": "local-dev",
                    "user_agent": "local-app",
                    "created_at": generated_at,
                },
            ]
        )
    for row in extra_events or []:
        event_id = row.get("id") or row.get("event_id") or f"audit:extra:{len(events) + 1}"
        events.append(
            {
                "id": event_id,
                "organization_id": row.get("organization_id") or "org-importer-demo",
                "actor_type": row.get("actor_type") or "operator",
                "actor_user_id": row.get("actor_user_id") or "user-operator-001",
                "actor_system_name": row.get("actor_system_name") or "",
                "event_type": row.get("event_type") or "operator_action",
                "entity_type": row.get("entity_type") or "SourcePacket",
                "entity_id": row.get("packet_id") or row.get("entity_id") or "",
                "before_json": row.get("before_json") or {},
                "after_json": row.get("after_json") or row,
                "ip_address": row.get("ip_address") or "local-dev",
                "user_agent": row.get("user_agent") or "local-app",
                "created_at": row.get("created_at") or now_iso(),
            }
        )
    return events


def private_beta_checklist() -> list[dict[str, Any]]:
    return [
        {"item": "Auth exists", "status": "implemented_local_session"},
        {"item": "Organizations exist", "status": "implemented"},
        {"item": "RBAC tests pass", "status": "implemented"},
        {"item": "Cross-org access blocked", "status": "implemented"},
        {"item": "Expert links scoped", "status": "implemented"},
        {"item": "File upload restrictions exist", "status": "implemented_metadata_and_size_limits"},
        {"item": "Audit logs exist", "status": "implemented"},
        {"item": "Privacy notice exists", "status": "implemented"},
        {"item": "Terms exist", "status": "implemented"},
        {"item": "Data deletion workflow exists", "status": "implemented_request_tracking"},
        {"item": "Route traversal fixed", "status": "implemented"},
        {"item": "AI simulated review cannot open gates", "status": "implemented"},
        {"item": "Reports avoid unsafe approval language", "status": "implemented"},
        {"item": "Source refresh works", "status": "implemented"},
        {"item": "Stale source creates blocker", "status": "implemented"},
        {"item": "Backup process exists", "status": "documented"},
        {"item": "Incident response draft exists", "status": "documented"},
        {"item": "Support contact/process exists", "status": "implemented_local_support"},
    ]


def deployment_readiness() -> dict[str, Any]:
    return {
        "status": "deployable_local_stack_ready_with_external_hosting_gates",
        "health_endpoints": ["/healthz", "/readyz", "/api/system-health"],
        "local_runtime": ["python3 scripts/serve_operator_app.py --host 127.0.0.1 --port 8765"],
        "containers": ["Dockerfile", "compose.yaml"],
        "environment_files": [".env.example"],
        "logs": "structured application/audit events are written to generated JSON and SQLite artifacts",
        "backups": "SQLite and system_review_graph artifacts can be backed up from the mounted /app/system_review_graph volume",
        "monitoring": "health endpoints expose app, store, route, and generated-artifact readiness",
        "external_gates": [
            "Provision real managed database/object storage before production",
            "Configure real secret manager and TLS termination before public hosting",
            "Run qualified security/privacy review before external customers",
            "Test backup restore in staging before production",
        ],
        "proof_boundary": "Deployment artifacts make the product hostable; they do not prove a live production environment exists.",
    }


def build_runtime_state(workflow: dict[str, Any], *, extra_audit_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    claims = [claim for packet in workflow.get("packets", []) for claim in claim_matrix_for_packet(packet)]
    review_requests = review_requests_for_workflow(workflow)
    report_exports = report_exports_for_workflow(workflow)
    audit_events = audit_events_for_workflow(workflow, extra_events=extra_audit_events)
    return {
        "generated_at": workflow.get("generated_at") or now_iso(),
        "product": "Importer Source Readiness Copilot",
        "category": "Source Readiness Management",
        "status": "private_beta_candidate_with_external_human_gates",
        "customer_promise": (
            "Turn a messy product/source/import idea into an evidence-backed readiness packet that shows "
            "what is known, what is missing, which claims are blocked, and what review is required before moving forward."
        ),
        "boundary": PRODUCT_BOUNDARY,
        "users": USERS,
        "organizations": ORGANIZATIONS,
        "memberships": [
            {
                "user_id": user["id"],
                "organization_id": user["organization_id"],
                "role": user["role"],
                "permissions": ROLE_PERMISSIONS[user["role"]],
            }
            for user in USERS
        ],
        "roles": [{"role": role, "permissions": permissions} for role, permissions in ROLE_PERMISSIONS.items()],
        "claim_rules": CLAIM_RULES,
        "claims": claims,
        "review_templates": REVIEW_TEMPLATES,
        "review_requests": review_requests,
        "reviewer_access_grants": [
            {
                "token": row["token"],
                "review_request_id": row["id"],
                "packet_ids": row["packet_ids"],
                "status": "active",
                "expires_at": row["due_at"],
            }
            for row in review_requests
        ],
        "human_review_findings": [],
        "report_exports": report_exports,
        "audit_events": audit_events,
        "data_deletion_requests": [],
        "security_controls": {
            "authentication": "local session auth implemented for private beta dry-run",
            "organization_isolation": "packet queries filter by organization unless operator/admin",
            "rbac": "role permission matrix enforced by route handlers",
            "scoped_expert_links": "review tokens grant packet-scoped access only",
            "csrf": "local form token available for browser unsafe actions",
            "upload_validation": {
                "allowed_evidence_types": sorted(ALLOWED_EVIDENCE_TYPES),
                "max_bytes": MAX_EVIDENCE_UPLOAD_BYTES,
                "malicious_html_policy": "reject script-bearing metadata and always HTML-escape display",
            },
            "route_traversal": "route-specific artifact base directories with resolved-path checks",
            "audit": "packet, AI, review, export, deletion, and permission events are recorded",
        },
        "private_beta_checklist": private_beta_checklist(),
        "deployment": deployment_readiness(),
        "ui_routes": {
            "customer": [
                "/",
                "/login",
                "/signup",
                "/onboarding",
                "/dashboard",
                "/packets",
                "/packets/new",
                "/packets/:packetId",
                "/packets/:packetId/evidence",
                "/packets/:packetId/blockers",
                "/packets/:packetId/readiness",
                "/packets/:packetId/reviews",
                "/packets/:packetId/reports",
                "/packets/:packetId/settings",
                "/account",
                "/support",
            ],
            "operator": [
                "/operator",
                "/operator/queue",
                "/operator/packets",
                "/operator/packets/:packetId",
                "/operator/blockers",
                "/operator/reviews",
                "/operator/reports",
                "/operator/sources",
                "/operator/gates",
            ],
            "expert": [
                "/review/:reviewToken",
                "/review/:reviewToken/evidence",
                "/review/:reviewToken/questions",
                "/review/:reviewToken/submit",
            ],
            "admin": [
                "/admin",
                "/admin/users",
                "/admin/organizations",
                "/admin/sources",
                "/admin/claim-rules",
                "/admin/review-templates",
                "/admin/audit",
                "/admin/system-health",
            ],
        },
        "api_routes": [
            "/api/auth/signup",
            "/api/auth/login",
            "/api/auth/logout",
            "/api/auth/me",
            "/api/orgs/current",
            "/api/orgs/current/members",
            "/api/packets",
            "/api/packets/:id",
            "/api/packets/:id/evidence",
            "/api/packets/:id/blockers",
            "/api/packets/:id/claims",
            "/api/packets/:id/gates",
            "/api/packets/:id/ai-reviews",
            "/api/packets/:id/review-requests",
            "/api/packets/:id/reports",
            "/api/packets/:id/audit",
            "/api/sources",
            "/api/blockers/:id",
            "/api/review-requests/:id",
            "/api/external-review/:token",
            "/api/external-review/:token/findings",
            "/api/reports/:id",
            "/api/reports/:id/download",
            "/api/audit",
            "/api/system-health",
        ],
    }


def write_runtime_artifacts(repo_root: Path, workflow: dict[str, Any], *, extra_audit_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    state = build_runtime_state(workflow, extra_audit_events=extra_audit_events)
    graph = repo_root / "system_review_graph"
    graph.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "product_runtime_state.json": state,
        "auth_rbac_matrix.json": {
            "users": state["users"],
            "organizations": state["organizations"],
            "memberships": state["memberships"],
            "roles": state["roles"],
            "security_controls": state["security_controls"],
        },
        "claims_gate_matrix.json": {
            "claim_rules": state["claim_rules"],
            "claims": state["claims"],
            "blocked_by_default": True,
        },
        "review_requests.json": state["review_requests"],
        "human_review_findings.json": state["human_review_findings"],
        "report_exports.json": state["report_exports"],
        "audit_events.json": {"events": state["audit_events"]},
        "deletion_requests.json": {"requests": state["data_deletion_requests"]},
        "deployment_readiness_report.json": state["deployment"],
        "private_beta_readiness_checklist.json": {"items": state["private_beta_checklist"]},
    }
    for name, payload in artifacts.items():
        (graph / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state
