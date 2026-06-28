"""Production portal workflow engine.

Phase 16 turns the existing UI/API route surface into explicit user-portal
workflow contracts. It checks that business-owner workflows have real routes,
plain next actions, accessibility review hooks, and closed public/payment/
approval gates.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_portal_workflow_engine_ready_routes_gated_business_owner_ux"

FIRST_SCREEN_OPTIONS: tuple[dict[str, str], ...] = (
    {"option_id": "explore_market", "label": "Explore a market", "route": "/opportunities"},
    {"option_id": "prepare_buyer_packet", "label": "Prepare a buyer packet", "route": "/tools/buyer-broker-packet"},
    {"option_id": "check_documents", "label": "Check my documents", "route": "/tools/document-check"},
    {"option_id": "prepare_expert_review", "label": "Prepare for broker/expert review", "route": "/expert-network"},
)

PORTALS: tuple[dict[str, Any], ...] = (
    {
        "portal_id": "public_portal",
        "label": "Public portal",
        "persona": "business owner exploring a trade lane",
        "required_ui_routes": ("/", "/start", "/tools", "/trade-check", "/tools/document-check", "/reports/sample", "/security"),
        "required_api_routes": ("/api/public/starter", "/api/public/quick-check"),
        "allowed_actions": ("start quick check", "view sample report", "read security and AI-use boundaries"),
        "blocked_actions": ("unrestricted real uploads", "live payment", "approval claims"),
    },
    {
        "portal_id": "exporter_portal",
        "label": "Exporter portal",
        "persona": "foreign exporter preparing a Canada-facing packet",
        "required_ui_routes": ("/workspace", "/packets/new", "/packets/:packetId/evidence", "/packets/:packetId/reports", "/tools/export-readiness"),
        "required_api_routes": ("/api/packets", "/api/packets/:id/evidence", "/api/reports/:id/download"),
        "allowed_actions": ("create packet", "attach evidence", "download cited reports", "prepare buyer or broker questions"),
        "blocked_actions": ("buyer validated", "supplier verified", "shipment approved"),
    },
    {
        "portal_id": "importer_portal",
        "label": "Importer portal",
        "persona": "Canadian importer checking source, supplier, and responsibility questions",
        "required_ui_routes": ("/tools/import-readiness", "/packets/:packetId/readiness", "/packets/:packetId/source-monitoring", "/country-coverage"),
        "required_api_routes": ("/api/public/packets/:id/refresh-official-sources", "/api/country-coverage"),
        "allowed_actions": ("review missing import evidence", "refresh source routes", "prepare broker review packet"),
        "blocked_actions": ("tariff confirmed", "CFIA approved", "customs ready"),
    },
    {
        "portal_id": "expert_reviewer_portal",
        "label": "Expert reviewer portal",
        "persona": "scoped external reviewer",
        "required_ui_routes": ("/review/:reviewToken", "/review/:reviewToken/evidence", "/review/:reviewToken/questions", "/review/:reviewToken/submit"),
        "required_api_routes": ("/api/external-review/:token/findings",),
        "allowed_actions": ("review scoped evidence", "answer scoped questions", "submit finding for exact scope"),
        "blocked_actions": ("blanket approval", "out-of-scope claim approval", "unscoped file access"),
    },
    {
        "portal_id": "operator_admin_portal",
        "label": "Operator and admin portal",
        "persona": "internal operator or admin",
        "required_ui_routes": ("/operator/queue", "/operator/packets/:packetId", "/operator/reviews", "/admin/sources", "/admin/audit", "/admin/system-health"),
        "required_api_routes": ("/api/audit", "/api/system-health", "/api/packets/:id/audit"),
        "allowed_actions": ("inspect blockers", "refresh artifacts", "route reviews", "check health and audit"),
        "blocked_actions": ("public launch approval", "live payment activation", "unsupported claim override"),
    },
    {
        "portal_id": "enterprise_portal",
        "label": "Enterprise portal",
        "persona": "broker, advisor, or team managing multiple packets",
        "required_ui_routes": ("/team-workspace", "/agent-api", "/billing/usage", "/research-plan", "/launch-operations"),
        "required_api_routes": ("/api/team-workspace", "/api/agent-api", "/api/billing/usage"),
        "allowed_actions": ("manage workspaces", "review usage", "use scoped local API contracts", "export audit-ready reports"),
        "blocked_actions": ("unreviewed white-label claims", "external webhooks", "live charges"),
    },
)

UX_RESEARCH_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "source_id": "w3c-wcag-22",
        "source_name": "W3C Web Content Accessibility Guidelines 2.2",
        "url": "https://www.w3.org/TR/WCAG22/",
        "use": "accessibility review criteria for perceivable, operable, understandable, and robust UI behavior",
    },
    {
        "source_id": "canada-design-system",
        "source_name": "Government of Canada Design System",
        "url": "https://design.canada.ca/",
        "use": "plain-language and service-design reference for public-facing Canada-oriented workflows",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _routes(repo_root: Path) -> tuple[dict[str, list[str]], set[str], set[str]]:
    runtime = _load_json(repo_root / "system_review_graph" / "product_runtime_state.json", {})
    ui_routes = runtime.get("ui_routes", {})
    if not isinstance(ui_routes, dict):
        ui_routes = {}
    api_routes = set(str(route) for route in runtime.get("api_routes", []))
    all_ui = {str(route) for routes in ui_routes.values() for route in routes}
    return {str(role): [str(route) for route in routes] for role, routes in ui_routes.items()}, all_ui, api_routes


def _route_status(required: tuple[str, ...], available: set[str]) -> list[dict[str, Any]]:
    return [
        {
            "route": route,
            "exists": route in available,
            "status": "route_present" if route in available else "route_missing",
        }
        for route in required
    ]


def _portal_records(repo_root: Path) -> list[dict[str, Any]]:
    _, all_ui, api_routes = _routes(repo_root)
    rows = []
    for portal in PORTALS:
        ui = _route_status(portal["required_ui_routes"], all_ui)
        api = _route_status(portal["required_api_routes"], api_routes)
        missing = [row["route"] for row in ui + api if not row["exists"]]
        rows.append(
            {
                "portal_id": portal["portal_id"],
                "label": portal["label"],
                "persona": portal["persona"],
                "ui_routes": ui,
                "api_routes": api,
                "route_coverage_status": "covered" if not missing else "missing_routes",
                "missing_routes": missing,
                "allowed_actions": list(portal["allowed_actions"]),
                "blocked_actions": list(portal["blocked_actions"]),
                "business_owner_language": True,
                "mobile_review_required": True,
                "accessibility_review_required": True,
                "confusion_testing_required": True,
                "can_open_approval_payment_or_launch_gate": False,
            }
        )
    return rows


def _first_screen_records(repo_root: Path) -> list[dict[str, Any]]:
    _, all_ui, _ = _routes(repo_root)
    return [
        {
            "option_id": row["option_id"],
            "label": row["label"],
            "route": row["route"],
            "route_exists": row["route"] in all_ui,
            "copy_style": "plain_business_owner_language",
            "next_action": "Open route and generate a packet or report without approval claims.",
            "can_open_external_gate": False,
        }
        for row in FIRST_SCREEN_OPTIONS
    ]


def _workflow_records(portal_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for portal in portal_records:
        rows.append(
            {
                "workflow_id": f"workflow:{portal['portal_id']}",
                "portal_id": portal["portal_id"],
                "steps": [
                    "choose goal",
                    "enter product and lane context",
                    "review missing evidence",
                    "generate cited packet/report",
                    "route to scoped review when needed",
                ],
                "success_state": "useful_preparation_output_ready",
                "blocked_state": "external_claims_or_real_world_actions_need_evidence",
                "plain_language_label": portal["label"],
                "buttons_expected": ["start", "review evidence", "download report", "request scoped review"],
                "unsafe_button_labels_blocked": ["approve", "ready to ship", "confirm tariff", "validate buyer", "verify supplier"],
                "route_coverage_status": portal["route_coverage_status"],
            }
        )
    return rows


def _ux_checks(portal_records: list[dict[str, Any]], first_screen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        ("first_screen_has_four_default_choices", len(first_screen) == 4),
        ("first_screen_routes_exist", all(row["route_exists"] for row in first_screen)),
        ("all_portal_routes_covered", all(row["route_coverage_status"] == "covered" for row in portal_records)),
        ("plain_business_language_required", all(row["business_owner_language"] for row in portal_records)),
        ("mobile_review_required", all(row["mobile_review_required"] for row in portal_records)),
        ("accessibility_review_required", all(row["accessibility_review_required"] for row in portal_records)),
        ("blocked_vs_approved_confusion_testing_required", all(row["confusion_testing_required"] for row in portal_records)),
    ]
    return [
        {
            "check_id": check_id,
            "passed": bool(passed),
            "status": "passed" if passed else "needs_changes",
            "external_review_required": check_id.endswith("required"),
        }
        for check_id, passed in checks
    ]


def _gate_controls(portal_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls = []
    for portal in portal_records:
        controls.append(
            {
                "gate_control_id": f"portal-gate:{portal['portal_id']}",
                "portal_id": portal["portal_id"],
                "blocked_actions": portal["blocked_actions"],
                "public_launch_ready": False,
                "unrestricted_uploads_enabled": False,
                "live_payment_enabled": False,
                "approval_claims_enabled": False,
                "external_effects_created": False,
                "claims_opened": False,
            }
        )
    return controls


def build_production_portal_workflow_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    ui_routes, all_ui, api_routes = _routes(root)
    portal_records = _portal_records(root)
    first_screen = _first_screen_records(root)
    workflows = _workflow_records(portal_records)
    ux_checks = _ux_checks(portal_records, first_screen)
    gate_controls = _gate_controls(portal_records)
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "portal_count": len(portal_records),
        "workflow_count": len(workflows),
        "first_screen_option_count": len(first_screen),
        "ui_route_count": len(all_ui),
        "api_route_count": len(api_routes),
        "ux_check_count": len(ux_checks),
        "gate_control_count": len(gate_controls),
        "ui_routes_by_role": ui_routes,
        "portal_records": portal_records,
        "first_screen_options": first_screen,
        "workflow_records": workflows,
        "ux_checks": ux_checks,
        "gate_controls": gate_controls,
        "ux_research_references": list(UX_RESEARCH_REFERENCES),
        "all_required_routes_present": all(row["route_coverage_status"] == "covered" for row in portal_records),
        "first_screen_routes_present": all(row["route_exists"] for row in first_screen),
        "plain_language_required": True,
        "accessibility_review_required": True,
        "mobile_review_required": True,
        "confusion_testing_required": True,
        "claims_opened": False,
        "external_effects_created": False,
        "public_launch_ready": False,
        "live_payment_ready": False,
        "unrestricted_uploads_enabled": False,
        "proof_boundary": "Portal workflow records prove local route and gate coverage; real UX test results, accessibility signoff, mobile review, and public launch approval remain external gates.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _doc(manifest: dict[str, Any]) -> str:
    portal_lines = "\n".join(
        f"- {row['label']}: {row['persona']} ({row['route_coverage_status']})"
        for row in manifest["portal_records"]
    )
    first_screen_lines = "\n".join(
        f"- {row['label']}: `{row['route']}` ({'route present' if row['route_exists'] else 'route missing'})"
        for row in manifest["first_screen_options"]
    )
    ux_lines = "\n".join(
        f"- {row['check_id'].replace('_', ' ')}: {row['status']}"
        for row in manifest["ux_checks"]
    )
    return f"""# Production Portal Workflow Engine

Status: `{manifest['status']}`

The portal workflow engine maps the existing UI/API routes to complete
business-owner, reviewer, operator, admin, and enterprise workflows.

## Portals

{portal_lines}

## Default First Screen

{first_screen_lines}

## Business-Owner UX Checks

{ux_lines}

## Gate Boundary

- Public launch ready: {str(manifest['public_launch_ready']).lower()}
- Live payment ready: {str(manifest['live_payment_ready']).lower()}
- Unrestricted uploads enabled: {str(manifest['unrestricted_uploads_enabled']).lower()}
- Claims opened: {str(manifest['claims_opened']).lower()}

The product can guide users through preparation workflows. It still needs real
business-owner UX feedback, accessibility signoff, mobile review, hosted proof,
live payment approval, unrestricted upload approval, and public launch approval
before those gates can open.
"""


def write_production_portal_workflow_engine_artifacts(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Path]:
    root = repo_root or Path(__file__).resolve().parents[2]
    srg = root / "system_review_graph"
    docs = root / "docs"
    route_matrix = {
        "status": "production_portal_route_matrix_ready",
        "portal_records": manifest["portal_records"],
        "first_screen_options": manifest["first_screen_options"],
    }
    ux_checks = {
        "status": "production_portal_ux_checks_ready_external_review_required",
        "ux_checks": manifest["ux_checks"],
        "ux_research_references": manifest["ux_research_references"],
    }
    gates = {
        "status": "production_portal_gate_controls_ready_closed",
        "gate_controls": manifest["gate_controls"],
    }
    paths = {
        "manifest": srg / "production_portal_workflow_manifest.json",
        "routes": srg / "production_portal_route_matrix.json",
        "ux_checks": srg / "production_portal_ux_checks.json",
        "gates": srg / "production_portal_gate_controls.json",
        "doc": docs / "PRODUCTION_PORTAL_WORKFLOWS.md",
    }
    _write_json(paths["manifest"], manifest)
    _write_json(paths["routes"], route_matrix)
    _write_json(paths["ux_checks"], ux_checks)
    _write_json(paths["gates"], gates)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(_doc(manifest), encoding="utf-8")
    return paths
