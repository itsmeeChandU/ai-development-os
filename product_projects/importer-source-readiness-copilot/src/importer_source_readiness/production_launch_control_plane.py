"""Production launch control plane.

Phase 20 decides what exact scope may be considered for launch and which gates
still block it. It reads the existing local business, country/source, market,
security/privacy, AI, expert-review, payment, user-validation, deployment, and
final go-live artifacts, then produces a fail-closed launch decision. The
control plane can describe a candidate public scope, but it cannot approve
public launch without real evidence and owner approval.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS = "production_launch_control_plane_ready_exact_scope_public_launch_blocked"

LAUNCH_GATE_REQUIREMENTS: tuple[dict[str, Any], ...] = (
    {
        "gate_id": "business_logic_gate",
        "label": "Business logic gate",
        "evidence_artifacts": ["business_logic_phase_report.json", "business_phase_completion_report.json"],
        "required_external_evidence": "No external evidence required for local review scope; public launch still needs final owner approval.",
    },
    {
        "gate_id": "country_pack_gate",
        "label": "Country-pack gate",
        "evidence_artifacts": ["production_country_source_engine_manifest.json", "production_country_packs.json"],
        "required_external_evidence": "Country-pack reviewer approval for the exact supported country/product scope.",
    },
    {
        "gate_id": "source_freshness_gate",
        "label": "Source freshness gate",
        "evidence_artifacts": ["production_source_lifecycle.json", "source_refresh_runs.json"],
        "required_external_evidence": "Dated source refresh proof immediately before launch-scope approval.",
    },
    {
        "gate_id": "market_data_gate",
        "label": "Market-data gate",
        "evidence_artifacts": ["production_market_intelligence_manifest.json", "production_market_signals.json"],
        "required_external_evidence": "Dataset freshness, licensing/terms review, and no demand/profitability overclaim.",
    },
    {
        "gate_id": "security_gate",
        "label": "Security gate",
        "evidence_artifacts": ["production_security_privacy_reliability_manifest.json", "production_trust_control_matrix.json"],
        "required_external_evidence": "Hosted auth, MFA, storage, malware scanning, monitoring, incident, secrets, and security signoff.",
    },
    {
        "gate_id": "privacy_gate",
        "label": "Privacy gate",
        "evidence_artifacts": ["production_vendor_register.json", "go_live_input_readiness_report.json"],
        "required_external_evidence": "Privacy notice, retention/deletion, vendor/data-residency approval, and qualified privacy/legal review.",
    },
    {
        "gate_id": "ai_safety_gate",
        "label": "AI safety gate",
        "evidence_artifacts": ["production_ai_copilot_manifest.json", "production_ai_safety_checks.json"],
        "required_external_evidence": "Provider terms, redaction, prompt-injection, model-routing, incident, and human-review approval.",
    },
    {
        "gate_id": "trade_language_gate",
        "label": "Trade-language gate",
        "evidence_artifacts": ["production_evidence_claim_gate_manifest.json", "production_claim_gate_decisions.json"],
        "required_external_evidence": "Qualified customs/trade/report-language review for public copy and generated reports.",
    },
    {
        "gate_id": "expert_review_gate",
        "label": "Expert-review gate",
        "evidence_artifacts": ["production_expert_review_network_manifest.json", "external_review_findings_report.json"],
        "required_external_evidence": "Real scoped reviewer findings with no unresolved public-launch blocker.",
    },
    {
        "gate_id": "payment_gate",
        "label": "Payment gate",
        "evidence_artifacts": ["production_payment_monetization_manifest.json", "production_payment_webhook_controls.json"],
        "required_external_evidence": "Live-mode objects, webhook proof, refund/support, tax/accounting, payment security, and paid-copy approval.",
    },
    {
        "gate_id": "real_user_evidence_gate",
        "label": "Real-user evidence gate",
        "evidence_artifacts": ["private_beta_smoke_test_plan.json", "go_live_input_readiness_report.json"],
        "required_external_evidence": "Private-beta outcomes, five-user smoke evidence, confusion testing, and P0/P1 closure.",
    },
    {
        "gate_id": "production_infrastructure_gate",
        "label": "Production infrastructure gate",
        "evidence_artifacts": ["deployment_readiness_report.json", "launch_operations_report.json"],
        "required_external_evidence": "Hosted staging/production proof with TLS, storage, secrets, logs, backups, monitoring, rollback, and support owner.",
    },
    {
        "gate_id": "final_owner_gate",
        "label": "Final owner gate",
        "evidence_artifacts": ["final_go_live_decision_report.json", "board_go_live_readiness_report.json"],
        "required_external_evidence": "Dated public go/no-go approval for the exact approved scope and expiry.",
    },
)

PUBLIC_SCOPE_CANDIDATES: tuple[dict[str, Any], ...] = (
    {"scope_id": "landing_page", "label": "Landing page", "scope_type": "candidate_allowed_after_final_gate"},
    {"scope_id": "public_quick_check", "label": "Public quick check", "scope_type": "candidate_allowed_after_final_gate"},
    {"scope_id": "no_document_starter_packet", "label": "No-document starter packet", "scope_type": "candidate_allowed_after_final_gate"},
    {"scope_id": "source_routing", "label": "Source routing", "scope_type": "candidate_allowed_after_final_gate"},
    {"scope_id": "sample_reports", "label": "Sample reports", "scope_type": "candidate_allowed_after_final_gate"},
    {"scope_id": "waitlist_demo_booking", "label": "Waitlist/demo booking", "scope_type": "candidate_allowed_after_final_gate"},
)

PUBLIC_SCOPE_BLOCKED: tuple[dict[str, str], ...] = (
    {"scope_id": "unrestricted_real_uploads", "label": "Unrestricted real uploads"},
    {"scope_id": "live_payments", "label": "Live payments"},
    {"scope_id": "automated_outreach", "label": "Automated outreach"},
    {"scope_id": "tariff_cfia_customs_approval_language", "label": "Tariff/CFIA/customs approval language"},
    {"scope_id": "buyer_validated_language", "label": "Buyer validated language"},
    {"scope_id": "supplier_verified_language", "label": "Supplier verified language"},
    {"scope_id": "shipment_approval", "label": "Shipment approval"},
    {"scope_id": "public_compliance_or_legal_advice", "label": "Public compliance/legal advice"},
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_status(root: Path, relative: str) -> dict[str, Any]:
    path = root / "system_review_graph" / relative
    return {"artifact": relative, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def _gate_records(root: Path, source_statuses: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for requirement in LAUNCH_GATE_REQUIREMENTS:
        artifacts = [_artifact_status(root, artifact) for artifact in requirement["evidence_artifacts"]]
        local_evidence_present = all(row["exists"] for row in artifacts)
        local_scope_ready = requirement["gate_id"] in {
            "business_logic_gate",
            "country_pack_gate",
            "market_data_gate",
            "ai_safety_gate",
            "trade_language_gate",
        }
        state = "approved_for_scope" if local_scope_ready and local_evidence_present else "blocked"
        if requirement["gate_id"] in {
            "security_gate",
            "privacy_gate",
            "expert_review_gate",
            "payment_gate",
            "real_user_evidence_gate",
            "production_infrastructure_gate",
            "final_owner_gate",
            "source_freshness_gate",
        }:
            state = "blocked"
        records.append(
            {
                **requirement,
                "state": state,
                "approved_scope": "local_review_only" if state == "approved_for_scope" else "",
                "local_evidence_present": local_evidence_present,
                "public_launch_contribution": False,
                "source_status": source_statuses.get(requirement["gate_id"], "not_proven_for_public_launch"),
                "artifacts": artifacts,
            }
        )
    return records


def _source_statuses(root: Path) -> dict[str, Any]:
    graph = root / "system_review_graph"
    business = _load_json(graph / "business_logic_phase_report.json", {})
    country = _load_json(graph / "production_country_source_engine_manifest.json", {})
    market = _load_json(graph / "production_market_intelligence_manifest.json", {})
    trust = _load_json(graph / "production_security_privacy_reliability_manifest.json", {})
    ai = _load_json(graph / "production_ai_copilot_manifest.json", {})
    claim_gate = _load_json(graph / "production_evidence_claim_gate_manifest.json", {})
    expert = _load_json(graph / "production_expert_review_network_manifest.json", {})
    payment = _load_json(graph / "production_payment_monetization_manifest.json", {})
    go_live_input = _load_json(graph / "go_live_input_readiness_report.json", {})
    deployment = _load_json(graph / "deployment_readiness_report.json", {})
    final_go_live = _load_json(graph / "final_go_live_decision_report.json", {})
    return {
        "business_logic_gate": business.get("status", "missing"),
        "country_pack_gate": country.get("status", "missing"),
        "source_freshness_gate": "blocked_until_launch_refresh",
        "market_data_gate": market.get("status", "missing"),
        "security_gate": trust.get("status", "missing"),
        "privacy_gate": go_live_input.get("status", "missing"),
        "ai_safety_gate": ai.get("status", "missing"),
        "trade_language_gate": claim_gate.get("status", "missing"),
        "expert_review_gate": expert.get("status", "missing"),
        "payment_gate": payment.get("status", "missing"),
        "real_user_evidence_gate": go_live_input.get("status", "missing"),
        "production_infrastructure_gate": deployment.get("status", "missing"),
        "final_owner_gate": final_go_live.get("status", "missing"),
    }


def build_production_launch_control_plane(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    final_go_live = _load_json(graph / "final_go_live_decision_report.json", {})
    trust = _load_json(graph / "production_security_privacy_reliability_manifest.json", {})
    payment = _load_json(graph / "production_payment_monetization_manifest.json", {})
    external_review = _load_json(graph / "external_review_findings_report.json", {})
    go_live_input = _load_json(graph / "go_live_input_readiness_report.json", {})
    source_statuses = _source_statuses(root)
    gates = _gate_records(root, source_statuses)
    candidate_scope = [
        {
            **row,
            "activation_allowed": False,
            "blocked_until": ["final_owner_gate", "security_gate", "privacy_gate", "production_infrastructure_gate", "real_user_evidence_gate"],
        }
        for row in PUBLIC_SCOPE_CANDIDATES
    ]
    blocked_scope = [
        {
            **row,
            "activation_allowed": False,
            "reason": "Not in approved public launch scope; requires explicit future workflow and reviewer approval.",
        }
        for row in PUBLIC_SCOPE_BLOCKED
    ]
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "launch_gate_count": len(gates),
        "launch_gates": gates,
        "approved_for_local_scope_count": len([row for row in gates if row["state"] == "approved_for_scope"]),
        "blocked_launch_gate_count": len([row for row in gates if row["state"] == "blocked"]),
        "public_scope_candidate_count": len(candidate_scope),
        "public_scope_candidates": candidate_scope,
        "blocked_public_scope_count": len(blocked_scope),
        "blocked_public_scope": blocked_scope,
        "final_go_live_status": final_go_live.get("status", "missing"),
        "external_review_status": external_review.get("status", "missing"),
        "external_review_completed_count": external_review.get("completed_review_count", 0),
        "missing_go_live_input_count": go_live_input.get("missing_input_count", 0),
        "security_real_file_uploads_allowed": trust.get("real_file_uploads_allowed", False),
        "payment_live_checkout_enabled": payment.get("live_checkout_enabled", False),
        "exact_public_scope_approved": False,
        "public_launch_approved": False,
        "hosted_private_beta_ready": False,
        "production_infrastructure_ready": False,
        "real_user_evidence_ready": False,
        "payment_activation_ready": False,
        "external_claims_opened": False,
        "activation_allowed": False,
        "expires_at": None,
        "final_owner_approval_recorded": False,
        "next_valid_move": "Collect real external review, hosted proof, private-beta evidence, payment proof, and final owner approval before activating even the limited public scope.",
        "proof_boundary": "This launch control plane approves local review scope only. It does not approve public launch, hosted private beta, live payment, real file uploads, automated outreach, approval language, buyer validation, supplier verification, legal advice, customs/tariff/CFIA approval, or shipment approval.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _doc(manifest: dict[str, Any]) -> str:
    gates = "\n".join(f"- {row['gate_id']}: {row['state']}" for row in manifest["launch_gates"])
    allowed = "\n".join(f"- {row['label']}: activation allowed {str(row['activation_allowed']).lower()}" for row in manifest["public_scope_candidates"])
    blocked = "\n".join(f"- {row['label']}" for row in manifest["blocked_public_scope"])
    return f"""# Production Launch Control Plane

Status: `{manifest['status']}`

The launch control plane records the exact public scope that could be considered
later and the capabilities that remain blocked now.

## Launch Gates

{gates}

## Candidate Public Scope

{allowed}

## Blocked Public Scope

{blocked}

## Decision

- Public launch approved: `{str(manifest['public_launch_approved']).lower()}`
- Activation allowed: `{str(manifest['activation_allowed']).lower()}`
- Exact public scope approved: `{str(manifest['exact_public_scope_approved']).lower()}`
- External claims opened: `{str(manifest['external_claims_opened']).lower()}`

No local artifact approves public launch. The final owner gate remains blocked
until real review, hosted proof, real-user evidence, payment proof, and the
exact dated scope approval exist.
"""


def write_production_launch_control_plane_artifacts(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Path]:
    root = repo_root or Path(__file__).resolve().parents[2]
    srg = root / "system_review_graph"
    docs = root / "docs"
    paths = {
        "manifest": srg / "production_launch_control_plane_manifest.json",
        "gates": srg / "production_launch_gate_states.json",
        "scope": srg / "production_launch_scope_matrix.json",
        "decision": srg / "production_public_launch_decision.json",
        "doc": docs / "PRODUCTION_LAUNCH_CONTROL_PLANE.md",
    }
    _write_json(paths["manifest"], manifest)
    _write_json(paths["gates"], {"status": "production_launch_gate_states_ready_public_launch_blocked", "launch_gates": manifest["launch_gates"]})
    _write_json(
        paths["scope"],
        {
            "status": "production_launch_scope_matrix_ready_activation_blocked",
            "public_scope_candidates": manifest["public_scope_candidates"],
            "blocked_public_scope": manifest["blocked_public_scope"],
        },
    )
    _write_json(
        paths["decision"],
        {
            "status": "production_public_launch_decision_blocked",
            "public_launch_approved": manifest["public_launch_approved"],
            "activation_allowed": manifest["activation_allowed"],
            "exact_public_scope_approved": manifest["exact_public_scope_approved"],
            "next_valid_move": manifest["next_valid_move"],
        },
    )
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(_doc(manifest), encoding="utf-8")
    return paths
