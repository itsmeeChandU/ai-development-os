"""Repository-backed local production API service proof.

The enterprise API platform defines contracts. This module proves the safe read
paths can be dispatched through auth, tenant checks, and the production
repository while effectful/live routes fail closed.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .production_enterprise_api_platform import API_ENDPOINTS
from .production_repository import DEFAULT_PACKET_ID, ProductionRepository


STATUS = "production_api_service_ready_repository_backed_safe_reads_effects_closed"


EFFECT_CLOSED_ROUTES = {
    ("POST", "/api/packets"),
    ("POST", "/api/packets/:id/evidence"),
    ("POST", "/api/documents/upload"),
    ("POST", "/api/sources/refresh"),
    ("POST", "/api/reviews"),
    ("POST", "/api/api-keys"),
    ("POST", "/api/webhooks"),
}

SERVICE_HANDLED_ROUTES = EFFECT_CLOSED_ROUTES | {
    ("GET", "/api/packets/:id"),
    ("GET", "/api/packets/:id/scores"),
    ("GET", "/api/packets/:id/blocked-claims"),
    ("GET", "/api/api-keys"),
    ("GET", "/api/webhooks"),
    ("POST", "/api/reports"),
    ("POST", "/api/ai/safe-summary"),
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _actor(auth: dict[str, Any], session_token: str | None) -> dict[str, Any] | None:
    if not session_token:
        return None
    for row in auth.get("users", []):
        if row.get("session_token") == session_token:
            return row
    return None


def _contract(method: str, path: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
    method = method.upper()
    for row in API_ENDPOINTS:
        if row["method"] != method:
            continue
        pattern = "^" + re.escape(row["path"]).replace(re.escape(":id"), r"(?P<id>[^/]+)") + "$"
        match = re.match(pattern, path)
        if match:
            return dict(row), match.groupdict()
    return None, {}


def is_production_api_service_route(method: str, path: str) -> bool:
    """Return true when the local app should delegate a route to this service."""

    contract, _params = _contract(method, path)
    return contract is not None and (method.upper(), contract["path"]) in SERVICE_HANDLED_ROUTES


def _permission_row(enterprise: dict[str, Any], method: str, pattern_path: str) -> dict[str, Any]:
    for row in enterprise.get("permission_matrix", []):
        if row.get("method") == method and row.get("path") == pattern_path:
            return row
    return {"allowed_roles": [], "deny_by_default": True, "permission": "missing_permission_contract"}


def _closed_response(
    *,
    status_code: int,
    status: str,
    method: str,
    path: str,
    actor: dict[str, Any] | None,
    reason: str,
    next_valid_move: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status_code": status_code,
        "status": status,
        "method": method,
        "path": path,
        "actor_id": actor.get("id") if actor else None,
        "organization_id": actor.get("organization_id") if actor else None,
        "reason": reason,
        "next_valid_move": next_valid_move,
        "data": data or {},
        "external_effects_created": False,
        "claims_opened": False,
        "live_mode_enabled": False,
    }


def dispatch_production_api_request(
    repo_root: Path | None,
    method: str,
    path: str,
    *,
    session_token: str | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    auth = _load_json(graph / "auth_rbac_matrix.json", {})
    enterprise = _load_json(graph / "production_enterprise_api_manifest.json", {})
    repository = ProductionRepository(graph / "production_domain.sqlite")
    method = method.upper()
    body = body or {}
    actor = _actor(auth, session_token)
    contract, params = _contract(method, path)

    if not contract:
        return _closed_response(
            status_code=404,
            status="route_not_registered",
            method=method,
            path=path,
            actor=actor,
            reason="No production API contract exists for this route.",
            next_valid_move="Add a reviewed API contract before dispatching this route.",
        )
    if not actor:
        return _closed_response(
            status_code=401,
            status="authentication_required",
            method=method,
            path=path,
            actor=None,
            reason="A local session token is required for production API proof routes.",
            next_valid_move="Authenticate with a scoped user session.",
        )

    permission = _permission_row(enterprise, method, contract["path"])
    allowed_roles = set(permission.get("allowed_roles", []))
    if actor.get("role") not in allowed_roles:
        return _closed_response(
            status_code=403,
            status="permission_denied",
            method=method,
            path=path,
            actor=actor,
            reason=f"Role {actor.get('role')} is not allowed for {contract['path']}.",
            next_valid_move="Use a role explicitly allowed by the enterprise API permission matrix.",
            data={"required_permission": permission.get("permission"), "allowed_roles": sorted(allowed_roles)},
        )

    if (method, contract["path"]) in EFFECT_CLOSED_ROUTES:
        return _closed_response(
            status_code=423,
            status="effect_gate_closed",
            method=method,
            path=path,
            actor=actor,
            reason="This route would create, mutate, upload, refresh, issue credentials, or deliver an external effect.",
            next_valid_move="Keep this route closed until hosted auth, storage, review, monitoring, and approval gates pass.",
            data={"contract_gate": contract.get("gate", "production_effect_gate_closed")},
        )

    packet_id = params.get("id") or str(body.get("packet_id") or DEFAULT_PACKET_ID)
    organization_filter = actor.get("organization_id")

    if contract["path"] == "/api/packets/:id":
        context = repository.packet_context(packet_id, organization_id=organization_filter)
        if context.get("status") != "packet_context_ready_from_production_repository":
            return _closed_response(
                status_code=403,
                status=context.get("status", "packet_unavailable"),
                method=method,
                path=path,
                actor=actor,
                reason="Packet context is unavailable for this organization.",
                next_valid_move=context.get("next_valid_move", "Request access to an organization-scoped packet."),
            )
        return {
            "status_code": 200,
            "status": "ok_repository_packet_context",
            "method": method,
            "path": path,
            "actor_id": actor["id"],
            "organization_id": actor["organization_id"],
            "permission": permission.get("permission"),
            "data": context,
            "external_effects_created": False,
            "claims_opened": False,
            "live_mode_enabled": False,
        }

    if contract["path"] == "/api/packets/:id/scores":
        context = repository.report_context(packet_id, organization_id=organization_filter)
        if context.get("status") != "database_backed_report_context_ready":
            return _closed_response(
                status_code=403,
                status=context.get("status", "packet_unavailable"),
                method=method,
                path=path,
                actor=actor,
                reason="Score context is unavailable for this organization.",
                next_valid_move=context.get("next_valid_move", "Request access to an organization-scoped packet."),
            )
        return {
            "status_code": 200,
            "status": "ok_repository_scores",
            "method": method,
            "path": path,
            "actor_id": actor["id"],
            "organization_id": actor["organization_id"],
            "permission": permission.get("permission"),
            "data": {"packet_id": packet_id, "scores": context["score_summary"], "single_global_score": False},
            "external_effects_created": False,
            "claims_opened": False,
            "live_mode_enabled": False,
        }

    if contract["path"] == "/api/packets/:id/blocked-claims":
        context = repository.report_context(packet_id, organization_id=organization_filter)
        if context.get("status") != "database_backed_report_context_ready":
            return _closed_response(
                status_code=403,
                status=context.get("status", "packet_unavailable"),
                method=method,
                path=path,
                actor=actor,
                reason="Blocked claims are unavailable for this organization.",
                next_valid_move=context.get("next_valid_move", "Request access to an organization-scoped packet."),
            )
        return {
            "status_code": 200,
            "status": "ok_repository_blocked_claims",
            "method": method,
            "path": path,
            "actor_id": actor["id"],
            "organization_id": actor["organization_id"],
            "permission": permission.get("permission"),
            "data": {"packet_id": packet_id, "blocked_claims": context["blocked_claims"]},
            "external_effects_created": False,
            "claims_opened": False,
            "live_mode_enabled": False,
        }

    if contract["path"] == "/api/reports":
        context = repository.report_context(packet_id, organization_id=organization_filter)
        if context.get("status") != "database_backed_report_context_ready":
            return _closed_response(
                status_code=403,
                status=context.get("status", "packet_unavailable"),
                method=method,
                path=path,
                actor=actor,
                reason="Report context is unavailable for this organization.",
                next_valid_move=context.get("next_valid_move", "Request access to an organization-scoped packet."),
            )
        return {
            "status_code": 200,
            "status": "ok_repository_report_context_no_write",
            "method": method,
            "path": path,
            "actor_id": actor["id"],
            "organization_id": actor["organization_id"],
            "permission": permission.get("permission"),
            "data": context,
            "external_effects_created": False,
            "claims_opened": False,
            "live_mode_enabled": False,
            "report_written": False,
        }

    if contract["path"] == "/api/ai/safe-summary":
        context = repository.report_context(packet_id, organization_id=organization_filter)
        if context.get("status") != "database_backed_report_context_ready":
            return _closed_response(
                status_code=403,
                status=context.get("status", "packet_unavailable"),
                method=method,
                path=path,
                actor=actor,
                reason="AI safe summary context is unavailable for this organization.",
                next_valid_move=context.get("next_valid_move", "Request access to an organization-scoped packet."),
            )
        return {
            "status_code": 200,
            "status": "ok_safe_summary_no_live_model_call",
            "method": method,
            "path": path,
            "actor_id": actor["id"],
            "organization_id": actor["organization_id"],
            "permission": permission.get("permission"),
            "data": {
                "packet_id": packet_id,
                "product_name": context["product_name"],
                "visible_claim_count": len(context["visible_claims"]),
                "blocked_claim_count": len(context["blocked_claims"]),
                "watermark": context["watermark"],
                "live_model_call_made": False,
                "summary_boundary": "Safe summary is assembled from repository context; AI cannot open gates.",
            },
            "external_effects_created": False,
            "claims_opened": False,
            "live_mode_enabled": False,
        }

    if contract["path"] == "/api/api-keys":
        return {
            "status_code": 200,
            "status": "ok_api_key_contracts_no_live_secret",
            "method": method,
            "path": path,
            "actor_id": actor["id"],
            "organization_id": actor["organization_id"],
            "permission": permission.get("permission"),
            "data": {
                "api_key_records": enterprise.get("api_key_records", []),
                "raw_secret_returned": False,
                "live_key_issued": False,
            },
            "external_effects_created": False,
            "claims_opened": False,
            "live_mode_enabled": False,
        }

    if contract["path"] == "/api/webhooks":
        return {
            "status_code": 200,
            "status": "ok_webhook_contracts_delivery_closed",
            "method": method,
            "path": path,
            "actor_id": actor["id"],
            "organization_id": actor["organization_id"],
            "permission": permission.get("permission"),
            "data": {
                "webhook_records": enterprise.get("webhook_records", []),
                "delivery_enabled": False,
            },
            "external_effects_created": False,
            "claims_opened": False,
            "live_mode_enabled": False,
        }

    return _closed_response(
        status_code=501,
        status="contract_present_handler_not_enabled",
        method=method,
        path=path,
        actor=actor,
        reason="The route has a contract but no local repository-backed handler in this slice.",
        next_valid_move="Add a repository-backed handler and tests before enabling this route.",
    )


def build_production_api_service(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    packet_path = f"/api/packets/{DEFAULT_PACKET_ID}"
    samples = [
        {
            "name": "customer_packet_read",
            "request": {"method": "GET", "path": packet_path, "session_token": "customer-session"},
        },
        {
            "name": "customer_scores_read",
            "request": {"method": "GET", "path": f"{packet_path}/scores", "session_token": "customer-session"},
        },
        {
            "name": "customer_blocked_claims_read",
            "request": {"method": "GET", "path": f"{packet_path}/blocked-claims", "session_token": "customer-session"},
        },
        {
            "name": "customer_report_context",
            "request": {
                "method": "POST",
                "path": "/api/reports",
                "session_token": "customer-session",
                "body": {"packet_id": DEFAULT_PACKET_ID},
            },
        },
        {
            "name": "customer_safe_summary",
            "request": {
                "method": "POST",
                "path": "/api/ai/safe-summary",
                "session_token": "customer-session",
                "body": {"packet_id": DEFAULT_PACKET_ID},
            },
        },
        {
            "name": "other_customer_packet_denied",
            "request": {"method": "GET", "path": packet_path, "session_token": "other-customer-session"},
        },
        {
            "name": "anonymous_packet_denied",
            "request": {"method": "GET", "path": packet_path},
        },
        {
            "name": "upload_effect_closed",
            "request": {"method": "POST", "path": "/api/documents/upload", "session_token": "customer-session"},
        },
        {
            "name": "source_refresh_effect_closed",
            "request": {"method": "POST", "path": "/api/sources/refresh", "session_token": "customer-session"},
        },
        {
            "name": "api_key_issue_closed",
            "request": {"method": "POST", "path": "/api/api-keys", "session_token": "customer-session"},
        },
        {
            "name": "api_key_contract_read",
            "request": {"method": "GET", "path": "/api/api-keys", "session_token": "customer-session"},
        },
    ]
    responses = []
    for sample in samples:
        request = sample["request"]
        response = dispatch_production_api_request(
            root,
            request["method"],
            request["path"],
            session_token=request.get("session_token"),
            body=request.get("body"),
        )
        responses.append({"name": sample["name"], "request": request, "response": response})

    return {
        "generated_at": _now(),
        "status": STATUS,
        "repository_dependency_status": _load_json(
            root / "system_review_graph" / "production_repository_service_manifest.json", {}
        ).get("status"),
        "enterprise_dependency_status": _load_json(
            root / "system_review_graph" / "production_enterprise_api_manifest.json", {}
        ).get("status"),
        "simulated_request_count": len(responses),
        "sample_responses": responses,
        "safe_read_success_count": sum(1 for row in responses if row["response"]["status_code"] == 200),
        "tenant_denial_count": sum(1 for row in responses if row["response"]["status"] == "access_denied"),
        "unauthenticated_denial_count": sum(
            1 for row in responses if row["response"]["status"] == "authentication_required"
        ),
        "effect_gate_closed_count": sum(1 for row in responses if row["response"]["status"] == "effect_gate_closed"),
        "permission_denial_count": sum(1 for row in responses if row["response"]["status"] == "permission_denied"),
        "hosted_api_ready": False,
        "live_api_keys_issued": False,
        "webhook_delivery_enabled": False,
        "real_uploads_enabled": False,
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "proof_boundary": "Local API service proof only. It proves repository-backed safe reads and closed effects, not hosted production API readiness.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_production_api_service_markdown(payload: dict[str, Any]) -> str:
    response_lines = "\n".join(
        f"- `{row['name']}`: {row['response']['status_code']} `{row['response']['status']}`"
        for row in payload["sample_responses"]
    )
    return f"""# Production API Service

Status: `{payload['status']}`

The local production API service dispatches reviewed API contracts through the
database-backed production repository. It proves auth checks, organization
scope, safe packet/report reads, blocked-claim visibility, and fail-closed
effectful routes.

## Sample Responses

{response_lines}

## Gate Boundary

- Hosted API ready: {str(payload['hosted_api_ready']).lower()}
- Live API keys issued: {str(payload['live_api_keys_issued']).lower()}
- Webhook delivery enabled: {str(payload['webhook_delivery_enabled']).lower()}
- Real uploads enabled: {str(payload['real_uploads_enabled']).lower()}
- External effects created: {str(payload['external_effects_created']).lower()}
- Claims opened: {str(payload['claims_opened']).lower()}
- Public launch ready: {str(payload['public_launch_ready']).lower()}
"""


def write_production_api_service_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    paths = {
        "manifest": graph / "production_api_service_manifest.json",
        "sample_responses": graph / "production_api_service_sample_responses.json",
        "doc": docs / "PRODUCTION_API_SERVICE.md",
    }
    _write_json(paths["manifest"], payload)
    _write_json(
        paths["sample_responses"],
        {"status": "production_api_service_sample_responses_ready", "sample_responses": payload["sample_responses"]},
    )
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(render_production_api_service_markdown(payload), encoding="utf-8")
    return paths
