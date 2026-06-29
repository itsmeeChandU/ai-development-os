"""Live payment activation proof intake.

The production payment engine defines paid scope, but that is not proof that
Stripe live checkout may be enabled. This module evaluates returned payment
activation evidence and keeps checkout, public launch, legal/tax, and payment
claims closed until real external proof exists.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATUS = "payment_activation_proof_intake_ready_real_payment_evidence_required_claims_closed"
CONTRACT_STATUS = "payment_activation_proof_contract_ready_claims_closed"
GATE_MATRIX_STATUS = "payment_activation_gate_matrix_ready_claims_closed"
BLOCKER_EXPORT_STATUS = "payment_activation_blocker_export_ready_claims_closed"

ALLOWED_DECISIONS = (
    "activate_live_checkout_for_scope",
    "not_applicable_for_this_launch",
    "keep_live_checkout_disabled",
    "needs_more_evidence",
)

REQUIRED_PROOF_CATEGORIES: tuple[dict[str, str], ...] = (
    {
        "category": "launch_scope_and_paid_scope_decision",
        "label": "Launch scope and paid-scope decision",
        "why": "The product must charge for preparation only, not approval, legal advice, buyer validation, supplier verification, or shipment decisions.",
    },
    {
        "category": "stripe_live_mode_account_review",
        "label": "Stripe live-mode account review",
        "why": "A test-mode account or local checkout contract is not live activation proof.",
    },
    {
        "category": "live_products_prices_checkout_portal",
        "label": "Live products, prices, checkout, and portal proof",
        "why": "Live-mode objects must match the approved paid scope before any customer can pay.",
    },
    {
        "category": "production_webhook_endpoint",
        "label": "Production webhook endpoint",
        "why": "Live checkout needs a production webhook endpoint tied to the deployed environment.",
    },
    {
        "category": "webhook_signature_verification",
        "label": "Webhook signature verification",
        "why": "Payment events must be authenticated before updating billing state.",
    },
    {
        "category": "webhook_idempotency_duplicate_ordering",
        "label": "Webhook idempotency, duplicate, delayed, and ordering tests",
        "why": "Billing state must tolerate retries, duplicates, delayed events, and out-of-order events.",
    },
    {
        "category": "api_version_error_logging",
        "label": "API version, error handling, and logging",
        "why": "Operators need stable API behavior, logged failures, and traceable payment errors before activation.",
    },
    {
        "category": "secure_api_keys_secrets_rotation",
        "label": "Secure API keys, secrets storage, and rotation",
        "why": "Live secret keys must be stored outside source code and local files with an owner and rotation process.",
    },
    {
        "category": "tax_accounting_invoice_review",
        "label": "Tax, accounting, and invoice review",
        "why": "Live payments need tax/accounting treatment and invoice policy reviewed for the launch scope.",
    },
    {
        "category": "refund_support_dispute_policy",
        "label": "Refund, support, and dispute policy",
        "why": "Customers need clear refund/support handling before money is accepted.",
    },
    {
        "category": "payment_security_pci_review",
        "label": "Payment security and PCI-scope review",
        "why": "The product must document that card data is handled by the payment provider and review remaining payment-security scope.",
    },
    {
        "category": "claim_language_receipt_copy_review",
        "label": "Claim language, checkout copy, and receipt wording review",
        "why": "Checkout and receipts must not imply customs approval, legal advice, buyer validation, supplier verification, or shipment approval.",
    },
    {
        "category": "activation_owner_go_no_go",
        "label": "Activation owner go/no-go",
        "why": "A named accountable owner must approve the exact live-payment scope and rollback path.",
    },
)

DISABLED_SCOPE_CATEGORIES = (
    "launch_scope_excludes_live_payments",
    "owner_decision",
    "future_activation_condition",
)

SOURCE_ANCHORS: tuple[dict[str, str], ...] = (
    {
        "source_id": "stripe-go-live-checklist",
        "name": "Go-live checklist",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/get-started/checklist/go-live",
        "checked_at": "2026-06-29",
        "product_use": "Live-mode objects, API versions, logging, webhook, event, and key readiness anchor.",
    },
    {
        "source_id": "stripe-webhooks",
        "name": "Webhooks",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/webhooks",
        "checked_at": "2026-06-29",
        "product_use": "Production webhook endpoint, delivery, retry, and event handling anchor.",
    },
    {
        "source_id": "stripe-webhook-signatures",
        "name": "Resolve webhook signature verification errors",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/webhooks/signature",
        "checked_at": "2026-06-29",
        "product_use": "Webhook signing secret and signature verification evidence anchor.",
    },
    {
        "source_id": "stripe-idempotent-requests",
        "name": "Idempotent requests",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/api/idempotent_requests",
        "checked_at": "2026-06-29",
        "product_use": "Duplicate and retry-safe request handling anchor.",
    },
    {
        "source_id": "stripe-api-keys",
        "name": "API keys",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/keys",
        "checked_at": "2026-06-29",
        "product_use": "Live/test key boundary and secret-key handling anchor.",
    },
    {
        "source_id": "stripe-testing",
        "name": "Testing",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/testing",
        "checked_at": "2026-06-29",
        "product_use": "Test-mode evidence boundary; test payment success is not live activation proof.",
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


def _missing_identity_fields(record: dict[str, Any]) -> list[str]:
    checks = (
        (("payment_scope_id", "payment_scope_name"), "payment scope id or name"),
        (("payment_provider",), "payment provider"),
        (("environment_mode", "payment_mode"), "payment environment mode"),
        (("owner_name", "approver_name"), "owner or approver name"),
        (("checked_at", "approved_at", "decided_at"), "checked or approved date"),
        (("build_or_commit_ref", "commit_ref", "build_ref"), "build or commit reference"),
        (("decision",), "decision"),
    )
    missing = []
    for names, label in checks:
        if not any(_text(record.get(name)) for name in names):
            missing.append(label)
    return missing


def _required_categories_for_decision(decision: str) -> tuple[str, ...]:
    if decision == "not_applicable_for_this_launch":
        return DISABLED_SCOPE_CATEGORIES
    return tuple(item["category"] for item in REQUIRED_PROOF_CATEGORIES)


def validate_payment_activation_record(
    record: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    missing_fields = _missing_identity_fields(record)
    decision = _text(record.get("decision"))
    provider = _text(record.get("payment_provider")).lower()
    environment_mode = _text(record.get("environment_mode") or record.get("payment_mode"))
    required_categories = _required_categories_for_decision(decision)
    attached_categories = _evidence_categories(record)
    missing_categories = [category for category in required_categories if category not in attached_categories]
    test_mode_only = environment_mode in {"test_mode_only", "stripe_test_mode"}
    live_mode = environment_mode == "stripe_live_mode"
    disabled_scope = environment_mode == "disabled_for_launch"

    if missing_fields:
        status = "received_missing_payment_identity"
    elif provider != "stripe":
        status = "received_unsupported_payment_provider"
    elif decision not in ALLOWED_DECISIONS:
        status = "received_unknown_payment_decision"
    elif decision == "activate_live_checkout_for_scope" and not live_mode:
        status = "received_activation_without_live_mode"
    elif decision == "not_applicable_for_this_launch" and not disabled_scope:
        status = "received_disabled_scope_without_disabled_mode"
    elif test_mode_only and decision == "activate_live_checkout_for_scope":
        status = "received_test_mode_not_live_activation_proof"
    elif missing_categories:
        status = "received_missing_required_payment_evidence"
    elif decision == "activate_live_checkout_for_scope":
        status = "accepted_live_payment_activation_scope_evidence"
    elif decision == "not_applicable_for_this_launch":
        status = "accepted_live_payment_disabled_scope_evidence"
    else:
        status = "received_payment_not_ready"

    accepted = status in {
        "accepted_live_payment_activation_scope_evidence",
        "accepted_live_payment_disabled_scope_evidence",
    }
    live_payment_ready = status == "accepted_live_payment_activation_scope_evidence"
    return {
        "generated_at": generated_at,
        "status": status,
        "payment_scope_id": record.get("payment_scope_id") or record.get("payment_scope_name") or "",
        "payment_provider": provider,
        "environment_mode": environment_mode,
        "owner_name": record.get("owner_name") or record.get("approver_name") or "",
        "checked_at": record.get("checked_at") or record.get("approved_at") or record.get("decided_at") or "",
        "build_or_commit_ref": record.get("build_or_commit_ref") or record.get("commit_ref") or record.get("build_ref") or "",
        "decision": decision,
        "source_file": record.get("source_file") or "",
        "missing_input_fields": missing_fields,
        "required_evidence_categories": list(required_categories),
        "missing_evidence_categories": missing_categories,
        "test_mode_only": test_mode_only,
        "accepted_for_payment_activation_evidence": accepted,
        "live_payment_ready_by_payment_evidence": live_payment_ready,
        "live_checkout_enabled_by_intake": False,
        "external_charge_created": False,
        "public_launch_ready_by_payment_evidence": False,
        "claims_opened_by_validation": False,
        "external_effects_created": False,
        "next_valid_move": _next_valid_move(status),
    }


def _next_valid_move(status: str) -> str:
    if status == "accepted_live_payment_activation_scope_evidence":
        return "Keep payment proof attached, then require launch-control, support, tax/accounting, security, and owner approval before enabling live checkout in config."
    if status == "accepted_live_payment_disabled_scope_evidence":
        return "Keep live checkout disabled for this launch and document the future activation condition."
    if status == "received_missing_payment_identity":
        return "Add payment scope, provider, environment mode, owner, date, build reference, and decision."
    if status == "received_unsupported_payment_provider":
        return "Use the supported Stripe proof contract or add a reviewed provider-specific contract first."
    if status == "received_unknown_payment_decision":
        return "Use one of the allowed payment decisions and rerun validation."
    if status == "received_activation_without_live_mode":
        return "Activation proof must identify Stripe live mode; test or disabled scope cannot activate checkout."
    if status == "received_disabled_scope_without_disabled_mode":
        return "For not-applicable payment scope, set environment_mode to disabled_for_launch."
    if status == "received_test_mode_not_live_activation_proof":
        return "Attach real live-mode proof; Stripe test mode is useful for QA but not live activation."
    if status == "received_missing_required_payment_evidence":
        return "Attach every required payment evidence category before counting payment activation proof."
    return "Resolve payment evidence issues and keep live checkout/public launch closed."


def build_payment_activation_contract(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": CONTRACT_STATUS,
        "generated_at": generated_at,
        "allowed_decisions": list(ALLOWED_DECISIONS),
        "required_evidence_categories": list(REQUIRED_PROOF_CATEGORIES),
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "disabled_scope_evidence_categories": list(DISABLED_SCOPE_CATEGORIES),
        "source_anchors": list(SOURCE_ANCHORS),
        "source_anchor_count": len(SOURCE_ANCHORS),
        "drop_paths": [
            "external_inputs/live_payment_activation_proof.json",
            "external_inputs/payment_activation_proofs/*.json",
        ],
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": "This contract defines live-payment activation evidence. It does not create Stripe objects, enable checkout, charge customers, or approve public launch.",
    }


def _load_payment_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    single = _load_json(repo_root / "external_inputs" / "live_payment_activation_proof.json", {})
    if isinstance(single, dict) and single:
        single["source_file"] = "external_inputs/live_payment_activation_proof.json"
        records.append(single)
    proof_dir = repo_root / "external_inputs" / "payment_activation_proofs"
    if proof_dir.exists():
        for path in sorted(proof_dir.glob("*.json")):
            payload = _load_json(path, {})
            if isinstance(payload, dict):
                payload["source_file"] = str(path.relative_to(repo_root))
                records.append(payload)
    return records


def _selected_validation(validations: list[dict[str, Any]]) -> dict[str, Any] | None:
    accepted = [row for row in validations if row.get("accepted_for_payment_activation_evidence") is True]
    candidates = accepted or validations
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: str(row.get("checked_at") or row.get("generated_at") or row.get("source_file") or ""))[-1]


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
                "gate_id": f"payment:{category}",
                "category": category,
                "label": item["label"],
                "status": "missing_real_payment_evidence" if missing else "evidence_attached_for_review",
                "blocks_live_payment": missing,
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
        if row["blocks_live_payment"] is not True:
            continue
        rows.append(
            {
                "id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "finding_id": row["gate_id"].upper().replace(":", "-").replace("_", "-"),
                "module": "payment_activation_proof",
                "reviewer_role": "Billing/Payment Review",
                "severity": "P0",
                "affected_stage": "live_payment_activation",
                "affected_file_or_artifact": "system_review_graph/payment_activation_proof_manifest.json",
                "issue": f"Live payment activation proof missing: {row['label']}.",
                "owner": "billing/payment reviewer",
                "required_fix": row["why"],
                "retest_command": "python3 scripts/check_product.py",
                "blocks_private_beta": False,
                "blocks_public_launch": True,
                "evidence": "payment_activation_proof_manifest.json records missing live-payment evidence.",
                "gate": "closed",
                "next_valid_move": "Attach real live-payment activation proof or disabled-payment launch decision and rerun payment activation intake.",
                "unsafe_to_bypass": True,
                "created_at": generated_at,
                "source_report": "system_review_graph/payment_activation_proof_manifest.json",
            }
        )
    return rows


def build_payment_activation_proof_intake(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    records = _load_payment_records(root)
    validations = [validate_payment_activation_record(record, generated_at) for record in records]
    selected = _selected_validation(validations)
    gate_rows = _gate_rows(selected, generated_at)
    blocker_rows = _blocker_rows(gate_rows, generated_at)
    accepted_count = sum(1 for row in validations if row["accepted_for_payment_activation_evidence"] is True)
    live_payment_ready = selected is not None and selected.get("live_payment_ready_by_payment_evidence") is True
    return {
        "status": STATUS,
        "generated_at": generated_at,
        "payment_record_count": len(records),
        "accepted_payment_record_count": accepted_count,
        "required_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES),
        "attached_evidence_category_count": 0
        if selected is None
        else len(selected.get("required_evidence_categories", [])) - len(selected.get("missing_evidence_categories", [])),
        "missing_evidence_category_count": len(REQUIRED_PROOF_CATEGORIES)
        if selected is None
        else len(selected.get("missing_evidence_categories", [])),
        "gate_count": len(gate_rows),
        "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_live_payment"] is True),
        "blocker_export_count": len(blocker_rows),
        "selected_validation": selected or {},
        "validations": validations,
        "live_payment_ready_by_payment_evidence": live_payment_ready,
        "live_checkout_enabled_by_intake": False,
        "external_charge_created": False,
        "public_launch_ready_by_payment_evidence": False,
        "claims_opened_by_intake": False,
        "external_effects_created": False,
        "contract": build_payment_activation_contract(generated_at),
        "gate_matrix": {
            "status": GATE_MATRIX_STATUS,
            "generated_at": generated_at,
            "gate_count": len(gate_rows),
            "blocked_gate_count": sum(1 for row in gate_rows if row["blocks_live_payment"] is True),
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
        "next_valid_move": "Attach Stripe live-payment activation proof or a disabled-payment launch decision, then rerun payment activation intake.",
        "proof_boundary": (
            "This validates payment activation evidence only. It does not create Stripe objects, enable checkout, "
            "charge customers, approve tax/accounting/security/legal readiness, or approve public launch."
        ),
    }


def render_payment_activation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Payment Activation Proof",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["proof_boundary"],
        "",
        "## Current Result",
        "",
        f"- Payment records received: {payload['payment_record_count']}",
        f"- Accepted payment records: {payload['accepted_payment_record_count']}",
        f"- Missing evidence categories: {payload['missing_evidence_category_count']}",
        f"- Live payment ready by payment evidence: {str(payload['live_payment_ready_by_payment_evidence']).lower()}",
        f"- Live checkout enabled by intake: {str(payload['live_checkout_enabled_by_intake']).lower()}",
        f"- External charge created: {str(payload['external_charge_created']).lower()}",
        f"- Public launch ready by payment evidence: {str(payload['public_launch_ready_by_payment_evidence']).lower()}",
        f"- Claims opened by intake: {str(payload['claims_opened_by_intake']).lower()}",
        "",
        "## Drop Paths",
        "",
        "- `external_inputs/live_payment_activation_proof.json`",
        "- `external_inputs/payment_activation_proofs/*.json`",
        "",
        "## Gate Matrix",
        "",
        "| Evidence | Status | Blocks Live Payment |",
        "| --- | --- | --- |",
    ]
    for row in payload["gate_matrix"]["rows"]:
        lines.append(f"| {row['label']} | `{row['status']}` | `{str(row['blocks_live_payment']).lower()}` |")
    lines.extend(["", "## Source Anchors", ""])
    for source in payload["contract"]["source_anchors"]:
        lines.append(f"- {source['publisher']}: {source['name']} ({source['url']})")
    lines.append("")
    return "\n".join(lines)


def _render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def write_payment_activation_proof_artifacts(
    repo_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    generated_at = generated_at or utc_now()
    graph = root / "system_review_graph"
    docs = root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    payload = build_payment_activation_proof_intake(root, generated_at)
    (graph / "payment_activation_proof_contract.json").write_text(_render_json(payload["contract"]), encoding="utf-8")
    manifest_payload = {key: value for key, value in payload.items() if key not in {"contract", "gate_matrix", "blocker_export"}}
    (graph / "payment_activation_proof_manifest.json").write_text(_render_json(manifest_payload), encoding="utf-8")
    (graph / "payment_activation_gate_matrix.json").write_text(_render_json(payload["gate_matrix"]), encoding="utf-8")
    (graph / "payment_activation_blocker_export.jsonl").write_text(
        _render_jsonl(payload["blocker_export"]["rows"]),
        encoding="utf-8",
    )
    (docs / "PAYMENT_ACTIVATION_PROOF.md").write_text(render_payment_activation_markdown(payload), encoding="utf-8")
    return {
        "status": payload["status"],
        "payment_record_count": payload["payment_record_count"],
        "accepted_payment_record_count": payload["accepted_payment_record_count"],
        "blocked_gate_count": payload["blocked_gate_count"],
        "blocker_export_count": payload["blocker_export_count"],
        "live_payment_ready_by_payment_evidence": payload["live_payment_ready_by_payment_evidence"],
        "live_checkout_enabled_by_intake": payload["live_checkout_enabled_by_intake"],
        "claims_opened_by_intake": payload["claims_opened_by_intake"],
        "generated_at": generated_at,
    }
