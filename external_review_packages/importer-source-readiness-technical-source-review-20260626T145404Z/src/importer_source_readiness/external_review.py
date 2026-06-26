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
    return {
        "status": "ai_assisted_external_review_ready",
        "generated_at": report["generated_at"],
        "solo_developer_mode": True,
        "uses_chatgpt_modes_agents_and_web_research": True,
        "simulated_review_count": 0,
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

## Gate Boundary

- human-equivalent approval: `{str(plan["human_equivalent_approval"]).lower()}`
- can open private beta gate: `{str(plan["can_open_private_beta_gate"]).lower()}`
- can open public launch gate: `{str(plan["can_open_public_launch_gate"]).lower()}`
- can reduce findings before real review: `{str(plan["can_reduce_findings_before_real_review"]).lower()}`
"""


def render_ai_source_log(plan: dict[str, Any]) -> str:
    lines = [
        "# Web Research Source Log",
        "",
        "Status: `ready_for_ai_assisted_review`",
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
    (paths["ai_review"] / "WEB_RESEARCH_SOURCE_LOG.md").write_text(
        render_ai_source_log(ai_plan),
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

    return {
        "status": report["status"],
        "required_review_count": report["required_review_count"],
        "completed_review_count": report["completed_review_count"],
        "blocker_count": len(blockers),
        "ai_assisted_review_status": ai_plan["status"],
        "generated_at": report["generated_at"],
    }
