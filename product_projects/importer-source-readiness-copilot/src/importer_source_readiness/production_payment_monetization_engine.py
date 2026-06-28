"""Production payments and monetization engine.

Phase 18 defines what the product may charge for and what it must never sell.
It converts local billing controls, usage rows, Stripe/payment research, and
claim-language boundaries into a live-checkout gate package. No live charges,
checkout URLs, customer payment objects, or webhook deliveries are created.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .business_logic import build_payment_pricing_contract


STATUS = "production_payment_monetization_engine_ready_live_checkout_closed"

PAYMENT_RESEARCH_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "source_id": "stripe-go-live",
        "source_name": "Stripe Go-live checklist",
        "url": "https://docs.stripe.com/get-started/checklist/go-live",
        "product_use": "Live-mode readiness, API versions, logging, live objects, and production webhooks.",
    },
    {
        "source_id": "stripe-webhooks",
        "source_name": "Stripe Webhooks",
        "url": "https://docs.stripe.com/webhooks",
        "product_use": "Webhook endpoint, event handling, retries, and signature verification requirements.",
    },
    {
        "source_id": "stripe-idempotent-requests",
        "source_name": "Stripe Idempotent requests",
        "url": "https://docs.stripe.com/api/idempotent_requests",
        "product_use": "Duplicate and retry-safe payment request handling.",
    },
    {
        "source_id": "stripe-api-keys",
        "source_name": "Stripe API keys",
        "url": "https://docs.stripe.com/keys",
        "product_use": "Secret-key, restricted-key, and live-mode key handling boundary.",
    },
    {
        "source_id": "stripe-testing",
        "source_name": "Stripe Testing",
        "url": "https://docs.stripe.com/testing",
        "product_use": "Test-mode payment behavior is not live activation proof.",
    },
)

PRICING_TIERS: tuple[dict[str, Any], ...] = (
    {"tier_id": "free_quick_check", "label": "Free quick check", "price_state": "free", "paid": False, "meter": "quick_check"},
    {"tier_id": "starter_packet", "label": "Starter packet", "price_state": "requires_founder_pricing_decision", "paid": True, "meter": "packet"},
    {"tier_id": "pro_packet_workspace", "label": "Pro packet workspace", "price_state": "requires_founder_pricing_decision", "paid": True, "meter": "workspace"},
    {"tier_id": "expert_review_add_on", "label": "Expert review add-on", "price_state": "requires_reviewer_and_payment_scope_review", "paid": True, "meter": "review_request"},
    {"tier_id": "broker_advisor_workspace", "label": "Broker/advisor workspace", "price_state": "requires_founder_pricing_decision", "paid": True, "meter": "seat_or_workspace"},
    {"tier_id": "enterprise", "label": "Enterprise", "price_state": "private_contract_required", "paid": True, "meter": "contract"},
    {"tier_id": "api_data_access", "label": "API/data access", "price_state": "requires_security_and_usage_review", "paid": True, "meter": "api_usage"},
)

ALLOWED_PAID_SCOPE = (
    "prepared trade readiness packet",
    "market research brief",
    "document organization",
    "source monitoring",
    "buyer-ready report",
    "broker-review packet",
    "expert review workflow",
    "broker/advisor workspace",
    "API usage contract",
)

FORBIDDEN_PAID_SCOPE = (
    "customs approval",
    "tariff confirmation",
    "legal advice",
    "CFIA approval",
    "buyer validation",
    "supplier verification",
    "shipment approval",
    "public launch approval",
)

PAYMENT_GATES: tuple[dict[str, Any], ...] = (
    {"gate_id": "pricing_decision", "owner": "founder", "status": "blocked", "required_evidence": "approved price sheet"},
    {"gate_id": "refund_support_policy", "owner": "billing_owner", "status": "blocked", "required_evidence": "refund policy and support contact"},
    {"gate_id": "tax_accounting_review", "owner": "accounting_reviewer", "status": "blocked", "required_evidence": "tax and accounting decision"},
    {"gate_id": "stripe_live_mode_objects", "owner": "billing_owner", "status": "blocked", "required_evidence": "live products, prices, checkout, customer portal settings"},
    {"gate_id": "production_webhook_endpoint", "owner": "billing_owner", "status": "blocked", "required_evidence": "production webhook endpoint with signature verification"},
    {"gate_id": "webhook_idempotency_and_ordering", "owner": "engineering_owner", "status": "blocked", "required_evidence": "duplicate, delayed, and out-of-order webhook tests"},
    {"gate_id": "secure_api_keys", "owner": "security_reviewer", "status": "blocked", "required_evidence": "secret storage and restricted key review"},
    {"gate_id": "payment_security_review", "owner": "security_reviewer", "status": "blocked", "required_evidence": "payment security signoff"},
    {"gate_id": "claim_language_review", "owner": "report_language_reviewer", "status": "blocked", "required_evidence": "paid-scope wording approval"},
    {"gate_id": "activation_decision", "owner": "founder", "status": "blocked", "required_evidence": "dated live checkout approval"},
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _tier_records() -> list[dict[str, Any]]:
    return [
        {
            **tier,
            "allowed_scope": list(ALLOWED_PAID_SCOPE) if tier["paid"] else ["safe quick check", "sample report", "source-routing preview"],
            "forbidden_scope": list(FORBIDDEN_PAID_SCOPE),
            "can_charge_for_approval": False,
            "claim_language_review_required": tier["paid"],
            "live_checkout_enabled": False,
        }
        for tier in PRICING_TIERS
    ]


def _checkout_controls() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "checkout_live_mode",
            "status": "blocked",
            "live_mode_enabled": False,
            "checkout_url_created": False,
            "external_charge_created": False,
        },
        {
            "control_id": "checkout_copy_boundary",
            "status": "ready_local_review_required",
            "must_say": "Users pay for preparation and evidence organization.",
            "must_not_say": "Users pay for customs approval, legal advice, buyer validation, supplier verification, tariff confirmation, or shipment approval.",
        },
        {
            "control_id": "checkout_refund_support",
            "status": "blocked",
            "refund_policy_approved": False,
            "support_contact_approved": False,
        },
        {
            "control_id": "checkout_tax_accounting",
            "status": "blocked",
            "tax_review_completed": False,
            "invoice_policy_approved": False,
        },
    ]


def _webhook_controls() -> list[dict[str, Any]]:
    events = [
        "checkout.session.completed",
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "invoice.paid",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ]
    return [
        {
            "event_type": event,
            "delivery_enabled": False,
            "signature_verification_required": True,
            "idempotency_required": True,
            "duplicate_event_handling_required": True,
            "delayed_event_handling_required": True,
            "out_of_order_event_handling_required": True,
            "external_effects_created": False,
        }
        for event in events
    ]


def build_production_payment_monetization_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    graph = root / "system_review_graph"
    billing_controls = _load_json(graph / "billing_credit_controls.json", {})
    billing_usage = _load_json(graph / "billing_usage_ledger.json", {})
    payment_contract = build_payment_pricing_contract()
    tier_records = _tier_records()
    webhook_controls = _webhook_controls()
    checkout_controls = _checkout_controls()
    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "payment_contract_status": payment_contract["status"],
        "research_reference_count": len(PAYMENT_RESEARCH_REFERENCES),
        "research_references": list(PAYMENT_RESEARCH_REFERENCES),
        "pricing_tier_count": len(tier_records),
        "pricing_tiers": tier_records,
        "allowed_paid_scope": list(ALLOWED_PAID_SCOPE),
        "forbidden_paid_scope": list(FORBIDDEN_PAID_SCOPE),
        "payment_gate_count": len(PAYMENT_GATES),
        "payment_gates": [dict(row) for row in PAYMENT_GATES],
        "blocked_payment_gate_count": len([row for row in PAYMENT_GATES if row["status"] == "blocked"]),
        "checkout_control_count": len(checkout_controls),
        "checkout_controls": checkout_controls,
        "webhook_control_count": len(webhook_controls),
        "webhook_controls": webhook_controls,
        "billing_action_count": len(billing_controls.get("billable_actions", [])),
        "usage_row_count": len(billing_usage.get("usage_rows", [])),
        "external_charge_created": False,
        "live_checkout_enabled": False,
        "live_payment_ready": False,
        "live_mode_objects_created": False,
        "checkout_url_created": False,
        "webhook_delivery_enabled": False,
        "stripe_secret_key_configured": False,
        "pricing_approved": False,
        "refund_support_policy_approved": False,
        "tax_accounting_review_completed": False,
        "payment_security_review_completed": False,
        "claim_language_review_completed": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "proof_boundary": "Payments are preparation-scope monetization contracts only. This does not prove Stripe live mode, tax/accounting approval, refund/support approval, payment security review, claim-language approval, live checkout, or public launch.",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _doc(manifest: dict[str, Any]) -> str:
    tiers = "\n".join(f"- {row['label']}: {row['price_state']}" for row in manifest["pricing_tiers"])
    gates = "\n".join(f"- {row['gate_id']}: {row['status']} ({row['required_evidence']})" for row in manifest["payment_gates"])
    return f"""# Production Payment Monetization Engine

Status: `{manifest['status']}`

The payment engine defines what the product may charge for: preparation,
evidence organization, reports, source monitoring, review workflow, workspaces,
and API usage. It keeps approval, advice, validation, verification, shipment,
and launch claims out of paid scope.

## Pricing Tiers

{tiers}

## Payment Gates

{gates}

## Gate Boundary

- Live checkout enabled: {str(manifest['live_checkout_enabled']).lower()}
- Live payment ready: {str(manifest['live_payment_ready']).lower()}
- External charge created: {str(manifest['external_charge_created']).lower()}
- Webhook delivery enabled: {str(manifest['webhook_delivery_enabled']).lower()}
- Claims opened: {str(manifest['claims_opened']).lower()}

No local artifact creates live Stripe objects, live checkout URLs, external
charges, webhook delivery, payment approval, legal/tax approval, or public
launch approval.
"""


def write_production_payment_monetization_engine_artifacts(
    manifest: dict[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Path]:
    root = repo_root or Path(__file__).resolve().parents[2]
    srg = root / "system_review_graph"
    docs = root / "docs"
    paths = {
        "manifest": srg / "production_payment_monetization_manifest.json",
        "pricing": srg / "production_pricing_tiers.json",
        "paid_scope": srg / "production_paid_scope_policy.json",
        "checkout": srg / "production_checkout_gate_controls.json",
        "webhooks": srg / "production_payment_webhook_controls.json",
        "research": srg / "production_payment_research_references.json",
        "doc": docs / "PRODUCTION_PAYMENT_MONETIZATION_ENGINE.md",
    }
    _write_json(paths["manifest"], manifest)
    _write_json(paths["pricing"], {"status": "production_pricing_tiers_ready_review_required", "pricing_tiers": manifest["pricing_tiers"]})
    _write_json(paths["paid_scope"], {"status": "production_paid_scope_policy_ready", "allowed_paid_scope": manifest["allowed_paid_scope"], "forbidden_paid_scope": manifest["forbidden_paid_scope"]})
    _write_json(paths["checkout"], {"status": "production_checkout_gate_controls_ready_live_checkout_closed", "checkout_controls": manifest["checkout_controls"], "payment_gates": manifest["payment_gates"]})
    _write_json(paths["webhooks"], {"status": "production_payment_webhook_controls_ready_delivery_closed", "webhook_controls": manifest["webhook_controls"]})
    _write_json(paths["research"], {"status": "production_payment_research_references_ready", "research_references": manifest["research_references"]})
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(_doc(manifest), encoding="utf-8")
    return paths
