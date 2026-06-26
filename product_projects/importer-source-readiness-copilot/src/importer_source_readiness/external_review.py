"""External review workflow artifacts.

This module records the post-package review workflow without pretending that
reviews have happened. It creates reviewer packets, blank finding templates,
and machine-checkable blocker rows for the still-pending external decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


EXECUTIVE_REVIEW_PACKAGE_V1 = {
    "label": "external-review-ready audit package",
    "sha256": "717788683f557ab398a83e32b362608f85f4bbbf11c1b84f1810dab556936665",
    "package_name": "importer-source-readiness-go-live-external-review-20260626T133719Z.zip",
    "proof_boundary": (
        "This package proves local go-live artifacts are review-ready. It does "
        "not prove external reviewer approval, hosted private beta readiness, "
        "public launch readiness, legal readiness, customs readiness, buyer "
        "validation, freight validation, or payment readiness."
    ),
}

FINDING_FIELDS = [
    "finding_id",
    "reviewer_role",
    "severity",
    "affected_stage",
    "affected_file_or_artifact",
    "issue",
    "owner",
    "required_fix",
    "retest_command",
    "blocks_private_beta",
    "blocks_public_launch",
]

SEVERITY_GUIDE = {
    "P0": "Unsafe or blocks private beta.",
    "P1": "Blocks public launch or stronger trade/payment claims.",
    "P2": "Fix before broader beta.",
    "P3": "Improvement.",
}

AI_ASSISTED_REVIEW_SOURCES = {
    "security-public-upload": [
        {
            "label": "OWASP File Upload Cheat Sheet",
            "url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
            "use": "Public upload, validation, storage, malware, and access-control review anchor.",
        }
    ],
    "ai-safety": [
        {
            "label": "OWASP LLM01 Prompt Injection",
            "url": "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
            "use": "Prompt-injection and model-input/output risk review anchor.",
        },
        {
            "label": "NIST AI Risk Management Framework",
            "url": "https://www.nist.gov/itl/ai-risk-management-framework",
            "use": "AI risk framing, governance, measurement, and monitoring review anchor.",
        },
    ],
    "privacy-legal": [
        {
            "label": "Office of the Privacy Commissioner of Canada PIPEDA guidance",
            "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/",
            "use": "Canadian privacy-law self-check anchor for notices, consent, access, retention, and safeguards.",
        }
    ],
    "devops-production-readiness": [
        {
            "label": "Canadian Centre for Cyber Security baseline controls",
            "url": "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations",
            "use": "Hosted private-beta operations, access control, backup, monitoring, and incident-response review anchor.",
        }
    ],
    "trade-boundary-customs-language": [
        {
            "label": "CBSA importing commercial goods",
            "url": "https://www.cbsa-asfc.gc.ca/import/menu-eng.html",
            "use": "Canadian import/customs boundary and official-source language anchor.",
        },
        {
            "label": "CFIA importing food, plants, or animals",
            "url": "https://inspection.canada.ca/en/importing-food-plants-animals",
            "use": "Food/agriculture import-control boundary anchor for report wording.",
        },
    ],
    "billing-payment": [
        {
            "label": "Stripe go-live checklist",
            "url": "https://docs.stripe.com/get-started/checklist/go-live",
            "use": "Live checkout, webhook, support, refund, and payment activation review anchor.",
        }
    ],
}

AI_ASSISTED_MODEL_OR_AGENT = "Codex GPT-5 simulated reviewer"

AI_ASSISTED_WAVE_1_FINDINGS: dict[str, list[dict[str, Any]]] = {
    "ux-product": [
        {
            "finding_id": "UX_PRODUCT-AI-001",
            "severity": "P0",
            "affected_stage": "hosted_private_beta",
            "affected_file_or_artifact": "docs/GO_LIVE_READINESS.md",
            "issue": (
                "The product clearly labels private beta as externally gated, "
                "but the repo still has no dated target-user usability smoke "
                "evidence. The stage table explicitly says real beginner "
                "usability still needs beta users, so a solo AI pass cannot "
                "prove that importers/exporters understand blockers, reports, "
                "or next valid moves."
            ),
            "owner": "product/UX reviewer",
            "required_fix": (
                "Run a five-user private-beta usability smoke with beginner, "
                "importer, exporter, document-holding, and operator/reviewer "
                "tasks; record confusion, unsafe interpretations, task success, "
                "and P0/P1 fixes in a dated usability artifact."
            ),
            "retest_command": "python3 scripts/check_product.py",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
            "confidence": "high",
        }
    ],
    "security-public-upload": [
        {
            "finding_id": "SECURITY_PUBLIC_UPLOAD-AI-001",
            "severity": "P0",
            "affected_stage": "hosted_private_beta",
            "affected_file_or_artifact": "system_review_graph/public_upload_policy.json",
            "issue": (
                "Public PDF uploads are locally quarantined and direct serving "
                "is disabled, but hosted enforcement remains unproven. The "
                "policy says rate limiting is only local-policy ready and the "
                "deployment docs still require malware scanning before public "
                "hosting."
            ),
            "owner": "security reviewer",
            "required_fix": (
                "Add staged hosted upload enforcement with malware scanning, "
                "content-type and extension validation, storage isolation, rate "
                "limits, denial tests for unsafe files, and a qualified security "
                "review record before any external user upload."
            ),
            "retest_command": "python3 -m unittest tests/test_operator_app.py tests/test_document_processing.py",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
            "confidence": "high",
        }
    ],
    "privacy-legal": [
        {
            "finding_id": "PRIVACY_LEGAL-AI-001",
            "severity": "P0",
            "affected_stage": "hosted_private_beta",
            "affected_file_or_artifact": "REVIEW_USE_TERMS.md",
            "issue": (
                "The repo has review-use terms, AI policy controls, and deletion "
                "request tracking, but it does not yet contain a hosted-user "
                "privacy notice, retention schedule, processor/subprocessor "
                "inventory, or qualified privacy/legal signoff for customer "
                "trade documents."
            ),
            "owner": "privacy/legal reviewer",
            "required_fix": (
                "Create jurisdiction-scoped privacy terms for hosted beta, map "
                "data categories and retention/deletion handling, record "
                "processor/subprocessor obligations, and obtain qualified "
                "privacy/legal review before collecting real customer data."
            ),
            "retest_command": "python3 scripts/check_product.py",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
            "confidence": "high",
        }
    ],
    "ai-safety": [
        {
            "finding_id": "AI_SAFETY-AI-001",
            "severity": "P0",
            "affected_stage": "hosted_private_beta",
            "affected_file_or_artifact": "tests/test_operator_app.py",
            "issue": (
                "AI controls now include an adversarial uploaded-document "
                "prompt-injection regression, and AI output is fail-closed at "
                "the claim-gate level. Hosted beta still needs qualified AI "
                "safety review of model routing, redaction quality, prompt "
                "handling, logging, and incident response before real customer "
                "documents or provider calls are used."
            ),
            "owner": "AI safety reviewer",
            "required_fix": (
                "Have a qualified AI safety reviewer evaluate the prompt "
                "injection regression, AI/data policy, model route contracts, "
                "redaction previews, manual/no-AI fallback, and hosted provider "
                "controls; record any P0/P1 findings before private beta."
            ),
            "retest_command": "python3 -m unittest tests/test_operator_app.py tests/test_product_runtime.py",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
            "confidence": "high",
        }
    ],
    "devops-production-readiness": [
        {
            "finding_id": "DEVOPS_PRODUCTION_READINESS-AI-001",
            "severity": "P0",
            "affected_stage": "hosted_private_beta",
            "affected_file_or_artifact": "system_review_graph/deployment_readiness_report.json",
            "issue": (
                "The Docker/Compose stack and health routes make the product "
                "hostable locally, but no staging deployment proof exists for "
                "TLS, secure cookies, secret management, managed storage, backup "
                "restore, monitoring, rollback, support ownership, or incident "
                "response."
            ),
            "owner": "DevOps/production reviewer",
            "required_fix": (
                "Provision a staging private-beta environment, wire production "
                "identity/secrets/storage/observability controls, run backup and "
                "rollback drills, and attach dated runbook evidence before "
                "external users are invited."
            ),
            "retest_command": "python3 scripts/check_product.py",
            "blocks_private_beta": True,
            "blocks_public_launch": True,
            "confidence": "high",
        }
    ],
}


@dataclass(frozen=True)
class ReviewRole:
    role_id: str
    reviewer_role: str
    template_file: str
    packet_file: str
    wave: int
    severity_floor: str
    affected_stage: str
    owner: str
    required_decision: str
    scope: str
    primary_artifacts: tuple[str, ...]
    retest_command: str
    blocks_private_beta: bool
    blocks_public_launch: bool
    next_valid_move: str

    @property
    def blocker_id(self) -> str:
        return f"EXT-REVIEW-{self.role_id.upper().replace('-', '_')}-PENDING"


REVIEW_ROLES: tuple[ReviewRole, ...] = (
    ReviewRole(
        role_id="ux-product",
        reviewer_role="UX/Product Usability Review",
        template_file="UX_PRODUCT_REVIEW.md",
        packet_file="WAVE_1_UX_PRODUCT_REVIEW.md",
        wave=1,
        severity_floor="P0",
        affected_stage="hosted_private_beta",
        owner="product/UX reviewer",
        required_decision="Private-beta usability decision with P0/P1 findings listed.",
        scope="Can a target importer/exporter understand the flow, blockers, generated reports, and next valid move without unsafe advice?",
        primary_artifacts=(
            "README.md",
            "docs/GO_LIVE_READINESS.md",
            "system_review_graph/operator_dashboard.html",
            "system_review_graph/customer_readiness_report.md",
            "system_review_graph/public_trade_readiness_manifest.json",
        ),
        retest_command="python3 scripts/check_product.py",
        blocks_private_beta=True,
        blocks_public_launch=True,
        next_valid_move="Send Wave 1 UX/product packet, collect structured findings, fix every P0 before private beta.",
    ),
    ReviewRole(
        role_id="security-public-upload",
        reviewer_role="Security/Public Upload Review",
        template_file="SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        packet_file="WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.md",
        wave=1,
        severity_floor="P0",
        affected_stage="hosted_private_beta",
        owner="security reviewer",
        required_decision="Public upload, file handling, auth/RBAC, and deployment security decision.",
        scope="Review file upload, quarantine, auth/RBAC, scoped expert links, deletion controls, and public route exposure.",
        primary_artifacts=(
            "docs/SECURITY_PRIVACY.md",
            "docs/DEPLOYMENT.md",
            "system_review_graph/public_upload_policy.json",
            "system_review_graph/auth_rbac_matrix.json",
            "src/importer_source_readiness/operator_app.py",
        ),
        retest_command="python3 -m unittest tests/test_operator_app.py tests/test_document_processing.py",
        blocks_private_beta=True,
        blocks_public_launch=True,
        next_valid_move="Send Wave 1 security packet, collect structured findings, fix every P0 before hosted private beta.",
    ),
    ReviewRole(
        role_id="privacy-legal",
        reviewer_role="Privacy/Legal Review",
        template_file="PRIVACY_LEGAL_REVIEW.md",
        packet_file="WAVE_1_PRIVACY_LEGAL_REVIEW.md",
        wave=1,
        severity_floor="P0",
        affected_stage="hosted_private_beta",
        owner="privacy/legal reviewer",
        required_decision="Privacy, terms, data handling, and legal-claim boundary decision.",
        scope="Review upload notices, AI/data policy, retention/deletion controls, terms, and claim-boundary language.",
        primary_artifacts=(
            "REVIEW_USE_TERMS.md",
            "docs/AI_DATA_POLICY.md",
            "docs/SECURITY_PRIVACY.md",
            "system_review_graph/ai_data_policy.json",
            "system_review_graph/deletion_requests.json",
        ),
        retest_command="python3 scripts/check_product.py",
        blocks_private_beta=True,
        blocks_public_launch=True,
        next_valid_move="Send Wave 1 privacy/legal packet, collect structured findings, fix every P0 before private beta.",
    ),
    ReviewRole(
        role_id="ai-safety",
        reviewer_role="AI Safety/Prompt Injection Review",
        template_file="AI_SAFETY_REVIEW.md",
        packet_file="WAVE_1_AI_SAFETY_REVIEW.md",
        wave=1,
        severity_floor="P0",
        affected_stage="hosted_private_beta",
        owner="AI safety reviewer",
        required_decision="AI data, prompt-injection, no-AI fallback, and redaction safety decision.",
        scope="Review model routing, AI permission controls, redaction previews, manual fallback, and prompt-injection boundaries.",
        primary_artifacts=(
            "docs/AI_DATA_POLICY.md",
            "system_review_graph/ai_model_router.json",
            "system_review_graph/redaction_pipeline.json",
            "system_review_graph/manual_no_ai_workflow.json",
            "tests/test_operator_app.py",
        ),
        retest_command="python3 -m unittest tests/test_operator_app.py tests/test_product_runtime.py",
        blocks_private_beta=True,
        blocks_public_launch=True,
        next_valid_move="Send Wave 1 AI safety packet, collect structured findings, fix every P0 before private beta.",
    ),
    ReviewRole(
        role_id="devops-production-readiness",
        reviewer_role="DevOps/Production Readiness Review",
        template_file="DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        packet_file="WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.md",
        wave=1,
        severity_floor="P0",
        affected_stage="hosted_private_beta",
        owner="DevOps/production reviewer",
        required_decision="Hosted private-beta readiness decision for infrastructure, config, secrets, logging, and rollback.",
        scope="Review Docker/Compose, env contract, deployment readiness, health routes, logging, and external hosting gaps.",
        primary_artifacts=(
            "Dockerfile",
            "compose.yaml",
            ".env.example",
            "docs/DEPLOYMENT.md",
            "system_review_graph/deployment_readiness_report.json",
        ),
        retest_command="python3 scripts/check_product.py",
        blocks_private_beta=True,
        blocks_public_launch=True,
        next_valid_move="Send Wave 1 DevOps packet, collect structured findings, fix every P0 before hosted private beta.",
    ),
    ReviewRole(
        role_id="trade-boundary-customs-language",
        reviewer_role="Trade-Boundary/Customs-Language Review",
        template_file="TRADE_BOUNDARY_REVIEW.md",
        packet_file="WAVE_2_TRADE_BOUNDARY_REVIEW.md",
        wave=2,
        severity_floor="P1",
        affected_stage="stronger_trade_claims",
        owner="trade compliance reviewer",
        required_decision="Customs, tariff, CFIA, import/export wording and claim-boundary decision.",
        scope="Review public report and UI language for unsupported customs, tariff, legal, CFIA, and import/export readiness claims.",
        primary_artifacts=(
            "docs/PUBLIC_TRADE_READINESS.md",
            "system_review_graph/claims_gate_matrix.json",
            "system_review_graph/public_report_types.json",
            "system_review_graph/generated_reports/starter_checklist_packet-frozen-tuna-canada-001.json",
        ),
        retest_command="python3 scripts/check_product.py",
        blocks_private_beta=False,
        blocks_public_launch=True,
        next_valid_move="Send Wave 2 trade-boundary packet before any stronger trade/customs wording is used publicly.",
    ),
    ReviewRole(
        role_id="freight-logistics",
        reviewer_role="Freight/Logistics Review",
        template_file="FREIGHT_LOGISTICS_REVIEW.md",
        packet_file="WAVE_2_FREIGHT_LOGISTICS_REVIEW.md",
        wave=2,
        severity_floor="P1",
        affected_stage="stronger_trade_claims",
        owner="freight/logistics reviewer",
        required_decision="Forwarder packet, transport questions, and shipment-readiness boundary decision.",
        scope="Review transport readiness rows, broker/forwarder packets, Incoterms-style questions, and shipment-readiness boundaries.",
        primary_artifacts=(
            "system_review_graph/transport_readiness_report.json",
            "system_review_graph/generated_reports/broker_packet_packet-frozen-tuna-canada-001.json",
            "system_review_graph/public_report_types.json",
        ),
        retest_command="python3 scripts/check_product.py",
        blocks_private_beta=False,
        blocks_public_launch=True,
        next_valid_move="Send Wave 2 freight/logistics packet before shipment or forwarder-readiness claims are strengthened.",
    ),
    ReviewRole(
        role_id="report-language",
        reviewer_role="Report-Language Review",
        template_file="REPORT_LANGUAGE_REVIEW.md",
        packet_file="WAVE_2_REPORT_LANGUAGE_REVIEW.md",
        wave=2,
        severity_floor="P1",
        affected_stage="stronger_trade_claims",
        owner="report-language reviewer",
        required_decision="Generated PDF/report wording decision for customer-safe language.",
        scope="Review generated report types, missing-evidence language, buyer/broker packet wording, and customer-safe next moves.",
        primary_artifacts=(
            "system_review_graph/public_report_types.json",
            "system_review_graph/generated_reports/missing_evidence_packet-frozen-tuna-canada-001.json",
            "system_review_graph/generated_reports/chatgpt_safe_summary_packet-frozen-tuna-canada-001.json",
            "system_review_graph/customer_readiness_report.md",
        ),
        retest_command="python3 scripts/check_product.py",
        blocks_private_beta=False,
        blocks_public_launch=True,
        next_valid_move="Send Wave 2 report-language packet before public report language is treated as approved.",
    ),
    ReviewRole(
        role_id="billing-payment",
        reviewer_role="Billing/Payment Review",
        template_file="BILLING_PAYMENT_REVIEW.md",
        packet_file="WAVE_3_BILLING_PAYMENT_REVIEW.md",
        wave=3,
        severity_floor="P1",
        affected_stage="monetization_or_public_scale",
        owner="billing/payment reviewer",
        required_decision="Billing, tax/invoice/refund/payment-flow decision before live checkout.",
        scope="Review billing controls, usage ledger, pricing page, live-checkout disabled state, refund/tax/invoice gaps, and payment-flow blockers.",
        primary_artifacts=(
            "system_review_graph/billing_credit_controls.json",
            "system_review_graph/billing_usage_ledger.json",
            "system_review_graph/product_operations_report.json",
            "README.md",
        ),
        retest_command="python3 -m unittest tests/test_product_runtime.py tests/test_completion_platform.py",
        blocks_private_beta=False,
        blocks_public_launch=True,
        next_valid_move="Send Wave 3 billing/payment packet before enabling live checkout or monetized public scale.",
    ),
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def review_role_dict(role: ReviewRole) -> dict[str, Any]:
    return {
        "role_id": role.role_id,
        "reviewer_role": role.reviewer_role,
        "wave": role.wave,
        "severity_floor": role.severity_floor,
        "template_path": f"external_review_findings/{role.template_file}",
        "reviewer_packet_path": f"reviewer_packets/{role.packet_file}",
        "affected_stage": role.affected_stage,
        "owner": role.owner,
        "required_decision": role.required_decision,
        "scope": role.scope,
        "primary_artifacts": list(role.primary_artifacts),
        "retest_command": role.retest_command,
        "blocks_private_beta": role.blocks_private_beta,
        "blocks_public_launch": role.blocks_public_launch,
        "next_valid_move": role.next_valid_move,
        "ai_assisted_prompt_path": f"ai_assisted_review/role_prompts/{role.packet_file}",
        "research_anchors": AI_ASSISTED_REVIEW_SOURCES.get(role.role_id, []),
    }


def build_ai_assisted_review_plan(report: dict[str, Any]) -> dict[str, Any]:
    simulated = build_ai_assisted_findings_report(report["generated_at"])
    return {
        "status": "ai_assisted_external_review_ready",
        "generated_at": report["generated_at"],
        "solo_developer_mode": True,
        "uses_chatgpt_modes_agents_and_web_research": True,
        "wave_1_simulated_review_status": simulated["status"],
        "simulated_review_count": simulated["simulated_review_count"],
        "simulated_finding_count": simulated["simulated_finding_count"],
        "simulated_findings_report": "system_review_graph/ai_assisted_external_review_findings_report.json",
        "simulated_finding_files": simulated["finding_files"],
        "required_role_count": len(REVIEW_ROLES),
        "human_equivalent_approval": False,
        "can_open_private_beta_gate": False,
        "can_open_public_launch_gate": False,
        "can_reduce_findings_before_real_review": True,
        "required_output_label": "ai_assisted_simulated_review",
        "reviewer_roles": [review_role_dict(role) for role in REVIEW_ROLES],
        "research_anchors": AI_ASSISTED_REVIEW_SOURCES,
        "capture_paths": {
            "prompts": "ai_assisted_review/role_prompts/",
            "source_log": "ai_assisted_review/WEB_RESEARCH_SOURCE_LOG.md",
            "simulated_findings": "ai_assisted_review/simulated_findings/",
            "real_external_findings": "external_review_findings/",
        },
        "required_finding_fields": FINDING_FIELDS
        + [
            "review_origin",
            "model_or_agent_used",
            "web_sources_checked",
            "confidence",
            "human_followup_required",
        ],
        "blocked_claims": [
            "external_review_completed",
            "qualified_security_approval",
            "qualified_privacy_legal_approval",
            "qualified_trade_compliance_approval",
            "qualified_freight_approval",
            "qualified_payment_approval",
            "hosted_private_beta_ready",
            "public_launch_ready",
        ],
        "next_valid_move": (
            "Run each role prompt through separate ChatGPT modes/agents, attach "
            "web source notes where needed, record simulated findings, fix P0/P1 "
            "items, rerun proof, and keep qualified approval gates closed unless "
            "real reviewer evidence is later added."
        ),
        "proof_boundary": (
            "AI-assisted reviews are useful solo-developer risk discovery. They "
            "are not qualified external approvals and cannot open launch, legal, "
            "customs, security, privacy, freight, or payment gates by themselves."
        ),
    }


def simulated_review_filename(role: ReviewRole) -> str:
    return role.packet_file.replace(".md", ".json")


def _source_urls(role: ReviewRole) -> list[str]:
    return [source["url"] for source in AI_ASSISTED_REVIEW_SOURCES.get(role.role_id, [])]


def build_ai_assisted_simulated_reviews(generated_at: str | None = None) -> list[dict[str, Any]]:
    generated_at = generated_at or utc_now()
    reviews: list[dict[str, Any]] = []
    for role in REVIEW_ROLES:
        if role.wave != 1:
            continue
        source_urls = _source_urls(role)
        findings = []
        for finding in AI_ASSISTED_WAVE_1_FINDINGS[role.role_id]:
            findings.append(
                {
                    **finding,
                    "reviewer_role": role.reviewer_role,
                    "review_origin": "ai_assisted_simulated_review",
                    "model_or_agent_used": AI_ASSISTED_MODEL_OR_AGENT,
                    "web_sources_checked": source_urls,
                    "human_followup_required": True,
                }
            )
        verdict = (
            "blocked"
            if any(
                finding["severity"] == "P0" and finding["blocks_private_beta"]
                for finding in findings
            )
            else "needs_fixes"
        )
        reviews.append(
            {
                "review_origin": "ai_assisted_simulated_review",
                "reviewer_role": role.reviewer_role,
                "role_id": role.role_id,
                "wave": role.wave,
                "affected_stage": role.affected_stage,
                "model_or_agent_used": AI_ASSISTED_MODEL_OR_AGENT,
                "reviewed_at": generated_at,
                "web_sources_checked": source_urls,
                "source_artifacts_reviewed": list(role.primary_artifacts),
                "verdict": verdict,
                "human_followup_required": True,
                "finding_count": len(findings),
                "findings": findings,
                "proof_boundary": (
                    "This is an AI-assisted simulated review. It can create "
                    "fixes or blockers, but it cannot open qualified approval "
                    "or launch gates."
                ),
            }
        )
    return reviews


def build_ai_assisted_findings_report(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    reviews = build_ai_assisted_simulated_reviews(generated_at)
    findings = [finding for review in reviews for finding in review["findings"]]
    severity_counts: dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("severity") or "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return {
        "status": "ai_assisted_wave_1_reviewed_with_blockers",
        "review_origin": "ai_assisted_simulated_review",
        "generated_at": generated_at,
        "model_or_agent_used": AI_ASSISTED_MODEL_OR_AGENT,
        "wave": 1,
        "simulated_review_count": len(reviews),
        "simulated_finding_count": len(findings),
        "finding_counts_by_severity": severity_counts,
        "private_beta_blocking_findings": sum(
            1 for finding in findings if finding["blocks_private_beta"]
        ),
        "public_launch_blocking_findings": sum(
            1 for finding in findings if finding["blocks_public_launch"]
        ),
        "real_external_review_count": 0,
        "human_equivalent_approval": False,
        "can_open_private_beta_gate": False,
        "can_open_public_launch_gate": False,
        "human_followup_required": True,
        "finding_files": [
            f"ai_assisted_review/simulated_findings/{simulated_review_filename(role)}"
            for role in REVIEW_ROLES
            if role.wave == 1
        ],
        "simulated_reviews": reviews,
        "blocked_claims": [
            "hosted_private_beta_ready",
            "public_launch_ready",
            "qualified_security_approval",
            "qualified_privacy_legal_approval",
            "qualified_ai_safety_approval",
            "qualified_devops_approval",
            "real_user_usability_approval",
        ],
        "next_valid_move": (
            "Treat these Wave 1 simulated P0 rows as owner-specific blocker "
            "work, fix what can be fixed locally, and collect real qualified "
            "review evidence before hosted private beta or public launch gates "
            "can open."
        ),
        "proof_boundary": (
            "This report documents solo AI-assisted risk discovery only. It is "
            "not real external approval and does not change the external review "
            "completed count."
        ),
    }


def build_external_review_findings_report(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    roles = [review_role_dict(role) for role in REVIEW_ROLES]
    wave_counts: dict[str, int] = {}
    for role in REVIEW_ROLES:
        wave_counts[str(role.wave)] = wave_counts.get(str(role.wave), 0) + 1

    return {
        "status": "external_review_ready_findings_pending",
        "generated_at": generated_at,
        "actual_external_review_completed": False,
        "required_review_count": len(REVIEW_ROLES),
        "completed_review_count": 0,
        "pending_review_count": len(REVIEW_ROLES),
        "wave_counts": wave_counts,
        "wave_1_status": "pending_before_private_beta",
        "wave_2_status": "pending_before_stronger_trade_claims",
        "wave_3_status": "pending_before_monetization_or_public_scale",
        "private_beta_blocked_until_wave_1_complete": True,
        "stronger_trade_claims_blocked_until_wave_2_complete": True,
        "monetization_blocked_until_wave_3_complete": True,
        "public_launch_ready": False,
        "hosted_private_beta_ready": False,
        "unsafe_gates_closed": True,
        "executive_review_package_v1": EXECUTIVE_REVIEW_PACKAGE_V1,
        "reviewer_roles": roles,
        "finding_schema": FINDING_FIELDS,
        "severity_guide": SEVERITY_GUIDE,
        "package_variants_required": [
            "executive_expert_audit_package",
            "technical_source_review_package",
        ],
        "solo_ai_assisted_review_supported": True,
        "solo_ai_assisted_review_plan": "system_review_graph/ai_assisted_external_review_plan.json",
        "current_external_findings": [],
        "blocked_claims": [
            "external_review_completed",
            "hosted_private_beta_ready",
            "public_launch_ready",
            "legal_ready",
            "privacy_ready",
            "security_ready",
            "customs_or_tariff_ready",
            "freight_ready",
            "payment_ready",
            "buyer_validated",
        ],
        "next_valid_move": (
            "Send Wave 1 reviewer packets, collect structured findings, fix "
            "P0/P1 rows, rerun proof, build v2 packages, then run five-user "
            "private-beta usability smoke only after real Wave 1 signoff exists."
        ),
        "proof_boundary": (
            "Repo artifacts prove the external-review workflow is ready and "
            "gated. They do not substitute for actual reviewer decisions."
        ),
    }


def build_external_review_blocker_rows(
    report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    report = report or build_external_review_findings_report()
    generated_at = report["generated_at"]
    rows: list[dict[str, Any]] = []
    for role in REVIEW_ROLES:
        issue = f"Structured {role.reviewer_role} findings have not been received."
        rows.append(
            {
                "id": role.blocker_id,
                "finding_id": role.blocker_id,
                "module": "external_review",
                "reviewer_role": role.reviewer_role,
                "severity": role.severity_floor,
                "affected_stage": role.affected_stage,
                "affected_file_or_artifact": f"external_review_findings/{role.template_file}",
                "issue": issue,
                "owner": role.owner,
                "required_fix": role.required_decision,
                "retest_command": role.retest_command,
                "blocks_private_beta": role.blocks_private_beta,
                "blocks_public_launch": role.blocks_public_launch,
                "evidence": (
                    "external_review_findings/EXTERNAL_REVIEW_SUMMARY.json "
                    "records completed_review_count=0 and pending reviewer roles."
                ),
                "gate": "closed",
                "next_valid_move": role.next_valid_move,
                "unsafe_to_bypass": True,
                "created_at": generated_at,
                "source_report": "system_review_graph/external_review_findings_report.json",
            }
        )
    return rows


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def render_findings_template(role: ReviewRole) -> str:
    artifacts = "\n".join(f"- `{artifact}`" for artifact in role.primary_artifacts)
    fields = "\n".join(f"- `{field}`" for field in FINDING_FIELDS)
    return f"""# {role.reviewer_role}

Status: `pending_external_review`
Wave: `{role.wave}`
Severity floor: `{role.severity_floor}`
Affected stage: `{role.affected_stage}`

## Scope

{role.scope}

## Primary Artifacts

{artifacts}

## Required Decision

{role.required_decision}

## Finding Row Schema

Every finding must include:

{fields}

Severity guide:

- `P0`: {SEVERITY_GUIDE["P0"]}
- `P1`: {SEVERITY_GUIDE["P1"]}
- `P2`: {SEVERITY_GUIDE["P2"]}
- `P3`: {SEVERITY_GUIDE["P3"]}

## Findings

No external findings have been submitted yet.

Use this exact row shape when findings are received:

```json
{{
  "finding_id": "{role.role_id.upper().replace('-', '_')}-001",
  "reviewer_role": "{role.reviewer_role}",
  "severity": "{role.severity_floor}",
  "affected_stage": "{role.affected_stage}",
  "affected_file_or_artifact": "",
  "issue": "",
  "owner": "{role.owner}",
  "required_fix": "",
  "retest_command": "{role.retest_command}",
  "blocks_private_beta": {str(role.blocks_private_beta).lower()},
  "blocks_public_launch": {str(role.blocks_public_launch).lower()}
}}
```

## Gate

- blocks private beta: `{str(role.blocks_private_beta).lower()}`
- blocks public launch: `{str(role.blocks_public_launch).lower()}`
- gate state until actual review is recorded: `closed`
- next valid move: {role.next_valid_move}
"""


def render_reviewer_packet(role: ReviewRole) -> str:
    artifacts = "\n".join(f"- `{artifact}`" for artifact in role.primary_artifacts)
    return f"""# {role.reviewer_role} Packet

Status: `ready_to_send_to_external_reviewer`
Wave: `{role.wave}`

## Review Boundary

The attached product is locally implemented with external gates. Your decision
must not be treated as legal, customs, tariff, freight, security, privacy,
payment, buyer, production, or public-launch approval unless your role
explicitly covers that claim and your findings say so.

## Ask

{role.scope}

Required decision: {role.required_decision}

## Review These Artifacts

{artifacts}

## Finding Format

Return every issue with:

`finding_id`, `reviewer_role`, `severity`, `affected_stage`,
`affected_file_or_artifact`, `issue`, `owner`, `required_fix`,
`retest_command`, `blocks_private_beta`, `blocks_public_launch`.

Severity: `P0` unsafe or blocks private beta, `P1` blocks public launch,
`P2` fix before broader beta, `P3` improvement.

## Retest Command

```bash
{role.retest_command}
```

## Gate

- blocks private beta: `{str(role.blocks_private_beta).lower()}`
- blocks public launch: `{str(role.blocks_public_launch).lower()}`
- next valid move: {role.next_valid_move}
"""


def render_ai_assisted_readme(plan: dict[str, Any]) -> str:
    return f"""# AI-Assisted External Review

Status: `{plan["status"]}`
Wave 1 simulated review status: `{plan["wave_1_simulated_review_status"]}`

This folder is for a solo developer using ChatGPT modes, separate agents, and
web research to approximate external review pressure before real qualified
review is available.

AI-assisted review can find P0/P1 issues and improve the product. It cannot
open private beta, public launch, legal/privacy/security, customs, freight, or
payment gates by itself.

## Workflow

1. Run each prompt in `role_prompts/` in a separate model mode or agent.
2. For source-sensitive roles, record web sources in `WEB_RESEARCH_SOURCE_LOG.md`.
3. Save outputs in `simulated_findings/` with `review_origin:
   ai_assisted_simulated_review`.
4. Convert actionable rows into fixes or blocker rows.
5. Rerun `python3 scripts/check_product.py`.

## Current Simulated Review Evidence

- simulated review count: `{plan["simulated_review_count"]}`
- simulated finding count: `{plan["simulated_finding_count"]}`
- simulated findings report: `{plan["simulated_findings_report"]}`

## Gate Boundary

- human-equivalent approval: `{str(plan["human_equivalent_approval"]).lower()}`
- can open private beta gate: `{str(plan["can_open_private_beta_gate"]).lower()}`
- can open public launch gate: `{str(plan["can_open_public_launch_gate"]).lower()}`
- can reduce findings before real review: `{str(plan["can_reduce_findings_before_real_review"]).lower()}`
"""


def render_ai_source_log(plan: dict[str, Any], findings_report: dict[str, Any]) -> str:
    lines = [
        "# Web Research Source Log",
        "",
        "Status: `wave_1_ai_assisted_sources_recorded`",
        "",
        "Record the exact sources checked by each AI-assisted reviewer. Keep this",
        "separate from `external_review_findings/` unless a real qualified reviewer",
        "has provided the decision.",
        "",
        "## Seed Sources",
        "",
    ]
    for role_id, sources in sorted(AI_ASSISTED_REVIEW_SOURCES.items()):
        role = next((item for item in REVIEW_ROLES if item.role_id == role_id), None)
        label = role.reviewer_role if role else role_id
        lines.append(f"### {label}")
        lines.append("")
        for source in sources:
            lines.append(f"- {source['label']}: {source['url']}")
            lines.append(f"  - use: {source['use']}")
        lines.append("")
    lines.extend(
        [
            "## Wave 1 Run Records",
            "",
            "These records are AI-assisted simulated reviews. They are not real",
            "qualified external approval.",
            "",
        ]
    )
    for review in findings_report["simulated_reviews"]:
        lines.extend(
            [
                f"### {review['reviewer_role']}",
                "",
                "```json",
                render_json(
                    {
                        "reviewer_role": review["reviewer_role"],
                        "model_or_agent_used": review["model_or_agent_used"],
                        "searched_at": review["reviewed_at"],
                        "queries_or_sources_checked": review["source_artifacts_reviewed"],
                        "source_urls": review["web_sources_checked"],
                        "notes": review["verdict"],
                        "finding_file": (
                            "ai_assisted_review/simulated_findings/"
                            f"{simulated_review_filename(next(role for role in REVIEW_ROLES if role.role_id == review['role_id']))}"
                        ),
                    }
                ).rstrip(),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Run Log Template",
            "",
            "```json",
            "{",
            '  "reviewer_role": "",',
            '  "model_or_agent_used": "",',
            '  "searched_at": "",',
            '  "queries_or_sources_checked": [],',
            '  "source_urls": [],',
            '  "notes": "",',
            '  "finding_file": "ai_assisted_review/simulated_findings/ROLE.json"',
            "}",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def render_ai_assisted_summary_md(findings_report: dict[str, Any]) -> str:
    review_rows = "\n".join(
        (
            f"- `{review['reviewer_role']}` -> `{review['verdict']}`, "
            f"findings: `{review['finding_count']}`"
        )
        for review in findings_report["simulated_reviews"]
    )
    return f"""# AI-Assisted Review Summary

Status: `{findings_report["status"]}`

This is the solo-developer Wave 1 simulated external review pass. It is useful
for risk discovery, but it is not qualified external approval.

## Current Truth

- simulated review count: `{findings_report["simulated_review_count"]}`
- simulated finding count: `{findings_report["simulated_finding_count"]}`
- private-beta blocking simulated findings: `{findings_report["private_beta_blocking_findings"]}`
- public-launch blocking simulated findings: `{findings_report["public_launch_blocking_findings"]}`
- real external review count: `{findings_report["real_external_review_count"]}`
- human-equivalent approval: `{str(findings_report["human_equivalent_approval"]).lower()}`
- can open private beta gate: `{str(findings_report["can_open_private_beta_gate"]).lower()}`
- can open public launch gate: `{str(findings_report["can_open_public_launch_gate"]).lower()}`

## Wave 1 Results

{review_rows}

## Next Valid Move

{findings_report["next_valid_move"]}

## Proof Boundary

{findings_report["proof_boundary"]}
"""


def render_ai_role_prompt(role: ReviewRole) -> str:
    artifacts = "\n".join(f"- `{artifact}`" for artifact in role.primary_artifacts)
    sources = AI_ASSISTED_REVIEW_SOURCES.get(role.role_id, [])
    if sources:
        source_lines = "\n".join(f"- {source['label']}: {source['url']}" for source in sources)
    else:
        source_lines = "- Add current sources if you search the web for this role."
    return f"""# AI-Assisted {role.reviewer_role} Prompt

Status: `ready_for_solo_ai_review`

Use this in a separate ChatGPT mode, agent, or model context. Treat yourself as
an independent reviewer, not as the product builder. Be skeptical, concrete, and
file-specific.

## Boundary

This is an AI-assisted simulated review. Your output can create fixes or
blockers. It cannot approve hosted private beta, public launch, legal/privacy
readiness, security readiness, customs/tariff readiness, freight readiness, or
payment readiness.

## Product Context

The product is a blocked-safe import/export readiness checker. The expected
state is local readiness with external gates closed.

## Review Role

- reviewer_role: `{role.reviewer_role}`
- wave: `{role.wave}`
- severity floor: `{role.severity_floor}`
- affected stage: `{role.affected_stage}`
- scope: {role.scope}

## Review These Artifacts

{artifacts}

## Suggested Source Anchors

{source_lines}

## Task

1. Inspect the artifacts for this role.
2. If web research is useful, use current sources and list exact URLs.
3. Find unsafe claims, missing controls, confusing UX, missing blocker rows, or
   untested behavior.
4. Return only structured findings plus a short verdict.

## Required Output

```json
{{
  "review_origin": "ai_assisted_simulated_review",
  "reviewer_role": "{role.reviewer_role}",
  "model_or_agent_used": "",
  "web_sources_checked": [],
  "verdict": "blocked|needs_fixes|no_p0_p1_found",
  "human_followup_required": true,
  "findings": [
    {{
      "finding_id": "{role.role_id.upper().replace('-', '_')}-AI-001",
      "reviewer_role": "{role.reviewer_role}",
      "severity": "{role.severity_floor}",
      "affected_stage": "{role.affected_stage}",
      "affected_file_or_artifact": "",
      "issue": "",
      "owner": "{role.owner}",
      "required_fix": "",
      "retest_command": "{role.retest_command}",
      "blocks_private_beta": {str(role.blocks_private_beta).lower()},
      "blocks_public_launch": {str(role.blocks_public_launch).lower()},
      "confidence": "low|medium|high",
      "human_followup_required": true
    }}
  ]
}}
```
"""


def render_process_doc(report: dict[str, Any]) -> str:
    wave_1 = ", ".join(role.reviewer_role for role in REVIEW_ROLES if role.wave == 1)
    wave_2 = ", ".join(role.reviewer_role for role in REVIEW_ROLES if role.wave == 2)
    wave_3 = ", ".join(role.reviewer_role for role in REVIEW_ROLES if role.wave == 3)
    return f"""# External Review Process

Status: `{report["status"]}`

The product has an external-review-ready package and a technical source-review
workflow. This is not external review completion. Real reviewer decisions must
be collected in `external_review_findings/` before any gate opens.

Solo-developer AI-assisted review is supported in `ai_assisted_review/`. Those
reviews can discover and fix issues, but they remain simulated and cannot open
qualified approval gates by themselves.

## Package Variants

- Executive/expert audit package: high-level artifacts for product, trade, legal,
  privacy, security, operations, and launch reviewers.
- Technical source review package: source code, tests, scripts, Docker/Compose,
  environment example, migrations, docs, and generated review artifacts.

## Review Waves

- Wave 1 before hosted private beta: {wave_1}.
- Wave 2 before stronger trade/customs/freight/report claims: {wave_2}.
- Wave 3 before monetization or public scale: {wave_3}.

## Required Finding Fields

Every external finding row must include:

{chr(10).join(f"- `{field}`" for field in FINDING_FIELDS)}

## Current Gate

- completed external reviews: `{report["completed_review_count"]}`
- required external reviews: `{report["required_review_count"]}`
- hosted private beta ready: `{str(report["hosted_private_beta_ready"]).lower()}`
- public launch ready: `{str(report["public_launch_ready"]).lower()}`
- unsafe gates closed: `{str(report["unsafe_gates_closed"]).lower()}`
- solo AI-assisted review supported: `{str(report["solo_ai_assisted_review_supported"]).lower()}`

## Next Valid Move

{report["next_valid_move"]}
"""


def render_summary_md(report: dict[str, Any], blockers: list[dict[str, Any]]) -> str:
    role_rows = "\n".join(
        f"- Wave {role.wave}: `{role.reviewer_role}` -> pending, gate closed"
        for role in REVIEW_ROLES
    )
    return f"""# External Review Summary

Status: `{report["status"]}`

The current package is correctly labeled as an
`{EXECUTIVE_REVIEW_PACKAGE_V1["label"]}`. It is not evidence that external
review is complete.

## Current Truth

- completed external reviews: `{report["completed_review_count"]}`
- required external reviews: `{report["required_review_count"]}`
- pending external blockers: `{len(blockers)}`
- hosted private beta ready: `{str(report["hosted_private_beta_ready"]).lower()}`
- public launch ready: `{str(report["public_launch_ready"]).lower()}`
- unsafe gates closed: `{str(report["unsafe_gates_closed"]).lower()}`
- solo AI-assisted review supported: `{str(report["solo_ai_assisted_review_supported"]).lower()}`
- v1 package sha256: `{EXECUTIVE_REVIEW_PACKAGE_V1["sha256"]}`

## Pending Reviews

{role_rows}

## Next Valid Move

{report["next_valid_move"]}

## Proof Boundary

{report["proof_boundary"]}

AI-assisted solo reviews in `ai_assisted_review/` are useful for risk discovery
and remediation. They are not qualified external approval.
"""


def build_external_review_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": report["status"],
        "actual_external_review_completed": False,
        "required_review_count": report["required_review_count"],
        "completed_review_count": report["completed_review_count"],
        "pending_review_count": report["pending_review_count"],
        "private_beta_blocked_until_wave_1_complete": True,
        "public_launch_ready": False,
        "unsafe_gates_closed": True,
        "solo_ai_assisted_review_supported": True,
        "ai_assisted_review_plan": "system_review_graph/ai_assisted_external_review_plan.json",
        "reviewer_roles": report["reviewer_roles"],
        "next_valid_move": report["next_valid_move"],
        "proof_boundary": report["proof_boundary"],
    }


def existing_generated_at(root: Path) -> str | None:
    path = root / "system_review_graph" / "external_review_findings_report.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    generated_at = data.get("generated_at")
    return generated_at if isinstance(generated_at, str) else None


def write_external_review_artifacts(root: Path) -> dict[str, Any]:
    report = build_external_review_findings_report(existing_generated_at(root))
    blockers = build_external_review_blocker_rows(report)
    ai_plan = build_ai_assisted_review_plan(report)
    ai_findings_report = build_ai_assisted_findings_report(report["generated_at"])

    paths = {
        "docs": root / "docs",
        "findings": root / "external_review_findings",
        "packets": root / "reviewer_packets",
        "ai_review": root / "ai_assisted_review",
        "ai_prompts": root / "ai_assisted_review" / "role_prompts",
        "ai_findings": root / "ai_assisted_review" / "simulated_findings",
        "srg": root / "system_review_graph",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    (paths["docs"] / "EXTERNAL_REVIEW_PROCESS.md").write_text(
        render_process_doc(report),
        encoding="utf-8",
    )
    (root / "EXTERNAL_REVIEW_SUMMARY.md").write_text(
        render_summary_md(report, blockers),
        encoding="utf-8",
    )
    (paths["srg"] / "external_review_findings_report.json").write_text(
        render_json(report),
        encoding="utf-8",
    )
    (paths["srg"] / "external_review_blocker_ledger.jsonl").write_text(
        render_jsonl(blockers),
        encoding="utf-8",
    )
    (paths["srg"] / "ai_assisted_external_review_plan.json").write_text(
        render_json(ai_plan),
        encoding="utf-8",
    )
    (paths["srg"] / "ai_assisted_external_review_findings_report.json").write_text(
        render_json(ai_findings_report),
        encoding="utf-8",
    )
    (paths["findings"] / "EXTERNAL_REVIEW_SUMMARY.json").write_text(
        render_json(build_external_review_summary(report)),
        encoding="utf-8",
    )
    (paths["findings"] / "README.md").write_text(
        "# External Review Findings\n\n"
        "Status: `pending_external_review`\n\n"
        "Store real external reviewer decisions here. Do not mark any gate open "
        "until a reviewer-specific file contains actual structured findings and "
        "the summary JSON is updated from repo evidence.\n",
        encoding="utf-8",
    )
    (paths["packets"] / "README.md").write_text(
        "# Reviewer Packets\n\n"
        "Status: `ready_to_send_to_external_reviewer`\n\n"
        "Each packet scopes one external reviewer role and points to the "
        "finding schema expected in `external_review_findings/`.\n",
        encoding="utf-8",
    )
    (paths["ai_review"] / "README.md").write_text(
        render_ai_assisted_readme(ai_plan),
        encoding="utf-8",
    )
    (paths["ai_review"] / "AI_ASSISTED_REVIEW_SUMMARY.md").write_text(
        render_ai_assisted_summary_md(ai_findings_report),
        encoding="utf-8",
    )
    (paths["ai_review"] / "WEB_RESEARCH_SOURCE_LOG.md").write_text(
        render_ai_source_log(ai_plan, ai_findings_report),
        encoding="utf-8",
    )
    (paths["ai_findings"] / ".gitkeep").write_text("", encoding="utf-8")

    for role in REVIEW_ROLES:
        (paths["findings"] / role.template_file).write_text(
            render_findings_template(role),
            encoding="utf-8",
        )
        (paths["packets"] / role.packet_file).write_text(
            render_reviewer_packet(role),
            encoding="utf-8",
        )
        (paths["ai_prompts"] / role.packet_file).write_text(
            render_ai_role_prompt(role),
            encoding="utf-8",
        )
    for simulated_review in ai_findings_report["simulated_reviews"]:
        role = next(role for role in REVIEW_ROLES if role.role_id == simulated_review["role_id"])
        (paths["ai_findings"] / simulated_review_filename(role)).write_text(
            render_json(simulated_review),
            encoding="utf-8",
        )

    return {
        "status": report["status"],
        "required_review_count": report["required_review_count"],
        "completed_review_count": report["completed_review_count"],
        "blocker_count": len(blockers),
        "ai_assisted_review_status": ai_plan["status"],
        "ai_assisted_wave_1_status": ai_findings_report["status"],
        "simulated_review_count": ai_findings_report["simulated_review_count"],
        "simulated_finding_count": ai_findings_report["simulated_finding_count"],
        "generated_at": report["generated_at"],
    }
