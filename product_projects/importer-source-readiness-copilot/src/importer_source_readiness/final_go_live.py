"""Final go-live decision artifacts.

These helpers intentionally separate local development completion from real
public-launch approval. They generate a concise surface for solo-developer
handoff, external reviewers, and private-beta planning without opening any
legal, customs, security, privacy, payment, buyer, supplier, or launch gate.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .external_review import REVIEW_ROLES, review_role_dict


LOCAL_DEVELOPMENT_LABEL = "development_complete_local_go_live_contract"
CURRENT_PRODUCT_LABEL = "external_validation_pending"
FINAL_DECISION_STATUS = "local_go_live_contract_complete_public_launch_blocked"


SOURCE_ANCHORS: list[dict[str, Any]] = [
    {
        "gate": "canada_commercial_import_boundary",
        "source_name": "CBSA - Import commercial goods into Canada",
        "source_url": "https://www.cbsa-asfc.gc.ca/import/menu-eng.html",
        "publisher": "Canada Border Services Agency",
        "checked_at": "2026-06-26",
        "why_it_matters": "Public reports must not imply goods are ready to import or that CBSA accounting/release requirements are satisfied.",
        "product_rule": "Keep import-readiness claims blocked until current official-source review and qualified customs/trade review exist.",
    },
    {
        "gate": "canada_food_import_boundary",
        "source_name": "CFIA - Importing food, plants or animals",
        "source_url": "https://inspection.canada.ca/en/importing-food-plants-animals",
        "publisher": "Canadian Food Inspection Agency",
        "checked_at": "2026-06-26",
        "why_it_matters": "Food, plant, animal, and related products can require permits, licences, rules, forms, and current commodity-specific review.",
        "product_rule": "Keep CFIA/food-safety claims blocked until AIRS/current-source and qualified review evidence exists.",
    },
    {
        "gate": "canada_food_airs_boundary",
        "source_name": "CFIA - Automated Import Reference System",
        "source_url": "https://inspection.canada.ca/en/importing-food-plants-animals/airs",
        "publisher": "Canadian Food Inspection Agency",
        "checked_at": "2026-06-26",
        "why_it_matters": "AIRS is the current reference route for CFIA-regulated commodity import requirements.",
        "product_rule": "Treat AIRS/source refresh as a blocker surface, not as automated approval.",
    },
    {
        "gate": "privacy_pipeda_boundary",
        "source_name": "OPC - PIPEDA fair information principles",
        "source_url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/",
        "publisher": "Office of the Privacy Commissioner of Canada",
        "checked_at": "2026-06-26",
        "why_it_matters": "Hosted use with customer trade documents needs accountability, purpose, consent, limiting collection, safeguards, access, and retention/deletion controls.",
        "product_rule": "Keep hosted beta blocked until privacy notice, retention/deletion plan, processor inventory, and qualified privacy/legal review exist.",
    },
    {
        "gate": "public_upload_security_boundary",
        "source_name": "OWASP File Upload Cheat Sheet",
        "source_url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
        "publisher": "OWASP",
        "checked_at": "2026-06-26",
        "why_it_matters": "Public uploads need allowlists, safe storage, handler-mediated access, malware/sandbox controls, and resource limits.",
        "product_rule": "Keep public uploads local/private-beta only until hosted malware scanning, storage isolation, rate limits, and qualified security review exist.",
    },
    {
        "gate": "canada_security_ops_boundary",
        "source_name": "Canadian Centre for Cyber Security - Baseline Cyber Security Controls for Small and Medium Organizations",
        "source_url": "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations",
        "publisher": "Canadian Centre for Cyber Security",
        "checked_at": "2026-06-26",
        "why_it_matters": "Hosted private beta needs baseline operational controls, monitoring, backup/restore, access control, and incident response ownership.",
        "product_rule": "Keep production/private-beta deployment blocked until dated staging and operations evidence exists.",
    },
    {
        "gate": "ai_safety_prompt_injection_boundary",
        "source_name": "OWASP LLM01:2025 Prompt Injection",
        "source_url": "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
        "publisher": "OWASP Gen AI Security Project",
        "checked_at": "2026-06-26",
        "why_it_matters": "Uploaded PDFs and retrieved text can contain direct or indirect prompt injection that attempts to alter model behavior.",
        "product_rule": "Keep AI output fail-closed; AI can create blockers only and cannot open claim gates.",
    },
    {
        "gate": "ai_risk_management_boundary",
        "source_name": "NIST AI Risk Management Framework",
        "source_url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "publisher": "NIST",
        "checked_at": "2026-06-26",
        "why_it_matters": "AI-enabled document and review workflows need governance, mapping, measurement, and management before real customer use.",
        "product_rule": "Keep AI provider use blocked until policy, monitoring, redaction, incident response, and qualified review are complete.",
    },
    {
        "gate": "payment_activation_boundary",
        "source_name": "Stripe go-live checklist",
        "source_url": "https://docs.stripe.com/get-started/checklist/go-live",
        "publisher": "Stripe",
        "checked_at": "2026-06-26",
        "why_it_matters": "Live payments need live-mode configuration, webhooks, tax/refund/support decisions, and payment-flow validation.",
        "product_rule": "Keep live checkout disabled until pricing validation, payment review, live webhook proof, tax/refund policy, and support ownership exist.",
    },
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _status(path: Path, default: str = "missing") -> str:
    payload = _load_json(path, {})
    return str(payload.get("status") or default) if isinstance(payload, dict) else default


def build_current_external_gate_research(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": "current_external_gate_research_ready",
        "generated_at": generated_at,
        "research_mode": "official_or_primary_source_anchor_snapshot",
        "source_count": len(SOURCE_ANCHORS),
        "source_anchors": SOURCE_ANCHORS,
        "blocked_claims": [
            "customs_or_tariff_ready",
            "cfia_or_food_import_ready",
            "privacy_legal_ready",
            "security_ready",
            "ai_safety_ready",
            "payment_ready",
            "public_launch_ready",
        ],
        "next_valid_move": "Use these dated anchors in scoped external review; do not treat them as qualified approval.",
        "proof_boundary": (
            "This artifact records dated official/primary source anchors for reviewer work. It does not prove legal, "
            "customs, tariff, CFIA, privacy, security, AI, payment, or public-launch readiness."
        ),
    }


def build_reviewer_wave_execution_plan(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    roles = [review_role_dict(role) for role in REVIEW_ROLES]
    waves: dict[str, list[dict[str, Any]]] = {}
    for role in roles:
        waves.setdefault(str(role["wave"]), []).append(role)
    return {
        "status": "reviewer_wave_execution_plan_ready",
        "generated_at": generated_at,
        "wave_count": len(waves),
        "waves": waves,
        "wave_1_gate": "blocks_hosted_private_beta_until_real_findings_resolved",
        "wave_2_gate": "blocks_stronger_trade_freight_report_claims_until_real_findings_resolved",
        "wave_3_gate": "blocks_monetization_or_public_scale_until_real_findings_resolved",
        "decision_values_allowed": [
            "approve_within_scope",
            "block",
            "needs_more_evidence",
            "out_of_scope",
            "wrong_reviewer_type",
        ],
        "next_valid_move": "Send Wave 1 packets first; convert every finding into a blocker or scoped approval condition.",
        "proof_boundary": "This is an execution plan. It is not evidence that any reviewer has approved the product.",
    }


def build_private_beta_smoke_test_plan(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    return {
        "status": "private_beta_smoke_test_plan_ready_blocked_until_wave_1_and_staging",
        "generated_at": generated_at,
        "minimum_users": [
            {"segment": "beginner_user_no_documents", "count": 2},
            {"segment": "document_holding_import_or_export_user", "count": 2},
            {"segment": "operator_or_consultant_style_user", "count": 1},
            {"segment": "reviewer_broker_or_freight_forwarder_style_user", "count": 1, "optional_before_private_beta": True},
        ],
        "tasks": [
            "/start beginner starter flow",
            "/trade-check PDF upload quick check",
            "confirm extracted fields",
            "download starter and missing-evidence reports",
            "save packet or open workspace",
            "delete files or request deletion",
            "open ChatGPT-safe summary",
            "open buyer/broker packet",
            "read blocked claims and next valid move",
        ],
        "success_metrics": {
            "complete_core_flow_without_help": "5 of 5 required users",
            "unsafe_approval_misunderstanding": 0,
            "critical_upload_or_privacy_incidents": 0,
            "unresolved_p0_p1_findings": 0,
        },
        "blocked_until": [
            "real Wave 1 review decisions received",
            "P0/P1 Wave 1 findings fixed or explicitly blocking",
            "staging deployment proof exists",
            "privacy/security/legal owner accepts scoped beta data handling",
        ],
        "next_valid_move": "Run only after Wave 1 review and staging proof; record dated outcomes as evidence rows.",
        "proof_boundary": "This plan does not prove user validation. Real user outcomes must be collected before public launch.",
    }


def build_final_go_live_decision(root: Path, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    srg = root / "system_review_graph"
    all_stage = _load_json(srg / "all_stage_readiness_report.json", {})
    continuation = _load_json(srg / "continuation_plan.json", {})
    external_review = _load_json(srg / "external_review_findings_report.json", {})
    ai_review = _load_json(srg / "ai_assisted_external_review_findings_report.json", {})
    blockers = _load_jsonl(srg / "external_review_blocker_ledger.jsonl")
    local_contract_complete = (
        all_stage.get("status") == "all_local_stages_implemented_with_external_gates"
        and all_stage.get("stage_count") == 19
        and all_stage.get("implemented_stage_count") == 19
        and all_stage.get("go_live_state_count") == 18
    )
    public_launch_blockers = [
        "real Wave 1 external review findings and signoff",
        "five-user usability smoke evidence",
        "staging deployment with TLS/secrets/storage/logging/rollback proof",
        "qualified privacy/legal/security approval",
        "qualified trade/customs/CFIA/report-language approval before stronger claims",
        "payment review and live webhook/tax/refund/support proof before checkout",
        "private-beta outcomes and named public go/no-go owner approval",
    ]
    return {
        "status": FINAL_DECISION_STATUS,
        "generated_at": generated_at,
        "current_label": f"{LOCAL_DEVELOPMENT_LABEL}; {CURRENT_PRODUCT_LABEL}",
        "local_contract_complete": local_contract_complete,
        "public_launch_ready": False,
        "hosted_private_beta_ready": False,
        "safe_to_run_locally_today": True,
        "safe_to_send_external_review_package_today": True,
        "safe_public_launch_scope_today": [],
        "safe_review_or_demo_scope_today": [
            "local app demo on localhost",
            "external review package delivery",
            "AI-assisted simulated review and remediation",
            "staging preparation without real customer data",
        ],
        "must_not_claim": [
            "public_launch_approved",
            "production_deployment_approved",
            "legal_or_customs_advice_ready",
            "tariff_confirmed",
            "cfia_cleared",
            "supplier_verified",
            "buyer_validated",
            "payment_activation_approved",
            "private_beta_approved",
        ],
        "source_statuses": {
            "readiness": _status(srg / "readiness_report.json"),
            "external_gate": _status(srg / "external_gate_report.json"),
            "all_stages": _status(srg / "all_stage_readiness_report.json"),
            "customer_workflow": _status(srg / "customer_readiness_report.json"),
            "runtime": _status(srg / "product_runtime_state.json"),
            "deployment": _status(srg / "deployment_readiness_report.json"),
            "external_review": str(external_review.get("status") or "missing"),
            "ai_assisted_review": str(ai_review.get("status") or "missing"),
        },
        "external_review_counts": {
            "required": external_review.get("required_review_count", 0),
            "completed": external_review.get("completed_review_count", 0),
            "pending": external_review.get("pending_review_count", 0),
            "ai_assisted_simulated_findings": ai_review.get("simulated_finding_count", 0),
            "ai_assisted_private_beta_blocking_findings": ai_review.get("private_beta_blocking_findings", 0),
            "pending_blocker_rows": len(blockers),
        },
        "public_launch_blockers": public_launch_blockers,
        "next_valid_moves": [
            "Freeze and distribute executive and technical review packages.",
            "Run Wave 1 external review or solo simulated review remediation while keeping real approval gates closed.",
            "Fix every local P0/P1 that can be fixed today and rerun proof.",
            "Provision staging and collect deployment/security/privacy evidence before real users.",
            "Run private-beta smoke only after Wave 1/staging gates are satisfied.",
            "Hold public go/no-go only after private-beta, expert-review, hosting, privacy/security, support, and rollback evidence exists.",
        ],
        "continuation_must_continue": bool(continuation.get("must_continue", True)),
        "unsafe_gates_closed": True,
        "proof_boundary": (
            "This report completes the local go-live decision surface. It does not approve public launch, hosted private beta, "
            "legal/privacy/security readiness, customs/tariff/CFIA readiness, buyer/supplier validation, freight readiness, or payment activation."
        ),
    }


def render_final_handoff(decision: dict[str, Any], research: dict[str, Any]) -> str:
    blockers = "\n".join(f"- {item}" for item in decision["public_launch_blockers"])
    next_moves = "\n".join(f"- {item}" for item in decision["next_valid_moves"])
    sources = "\n".join(
        f"- {row['gate']}: {row['source_name']} ({row['source_url']})"
        for row in research["source_anchors"]
    )
    return f"""# Final Go-Live Handoff

Status: `{decision["status"]}`

Current label:

```text
{decision["current_label"]}
```

## What Is Complete

- Local Stage 0-18 go-live contract is represented.
- Local product proof gates pass when `scripts/check_product.py` passes.
- External review workflow, reviewer packets, AI-assisted simulated review, blocker ledgers, and source anchors are generated.
- Unsafe claims remain closed.
- The app can be run locally for demos and external review.

## What Is Not Approved

- public production launch
- hosted private beta with real customer data
- legal, customs, tariff, CFIA, privacy, security, payment, buyer, supplier, freight, or shipment-readiness claims
- live checkout or unrestricted OCR/AI

## Blocking Public Launch

{blockers}

## Next Valid Moves

{next_moves}

## Current Source Anchors

{sources}

## Proof Boundary

{decision["proof_boundary"]}
"""


def write_final_go_live_artifacts(root: Path, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    srg = root / "system_review_graph"
    srg.mkdir(parents=True, exist_ok=True)
    research = build_current_external_gate_research(generated_at)
    reviewer_plan = build_reviewer_wave_execution_plan(generated_at)
    smoke_plan = build_private_beta_smoke_test_plan(generated_at)
    decision = build_final_go_live_decision(root, generated_at)
    artifacts = {
        "current_external_gate_research": research,
        "reviewer_wave_execution_plan": reviewer_plan,
        "private_beta_smoke_test_plan": smoke_plan,
        "final_go_live_decision_report": decision,
    }
    for name, payload in artifacts.items():
        (srg / f"{name}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "FINAL_GO_LIVE_HANDOFF.md").write_text(render_final_handoff(decision, research), encoding="utf-8")
    return {
        "status": decision["status"],
        "local_contract_complete": decision["local_contract_complete"],
        "public_launch_ready": decision["public_launch_ready"],
        "hosted_private_beta_ready": decision["hosted_private_beta_ready"],
        "source_count": research["source_count"],
        "reviewer_role_count": sum(len(rows) for rows in reviewer_plan["waves"].values()),
        "generated_at": generated_at,
    }
