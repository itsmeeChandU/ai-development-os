"""Runtime product contract for customer, operator, and expert workflows."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CSRF_TOKEN = "local-dev-csrf-token"
MAX_EVIDENCE_UPLOAD_BYTES = 5 * 1024 * 1024
AI_PROCESSING_MODES = [
    "no_ai",
    "metadata_only",
    "redacted",
    "business_api",
    "private_hosted_llm",
    "customer_managed_llm",
    "on_prem_manual",
]

SENSITIVITY_LEVELS = ["public", "internal", "confidential", "restricted", "regulated"]
PRIVATE_AI_MODES = {"no_ai", "metadata_only", "private_hosted_llm", "customer_managed_llm", "on_prem_manual"}
REDACTION_CATEGORIES = [
    "person_names",
    "emails",
    "phone_numbers",
    "addresses",
    "supplier_names",
    "buyer_names",
    "prices",
    "bank_details",
    "contract_terms",
    "signatures",
    "ids",
    "sensitive_notes",
]

PRODUCT_BOUNDARY = (
    "Trade Readiness Copilot organizes import/export evidence and blockers. It does not provide "
    "legal, customs, tariff, tax, CFIA, supplier, buyer, compliance, shipment, or launch advice."
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

AI_DATA_POLICIES = [
    {
        "id": "ai-policy-org-importer-demo",
        "organization_id": "org-importer-demo",
        "default_mode": "redacted",
        "allowed_modes": AI_PROCESSING_MODES,
        "allowed_sensitivity": ["public", "internal", "confidential"],
        "restricted_sensitivity_modes": sorted(PRIVATE_AI_MODES),
        "redaction_required_for": ["confidential", "restricted", "regulated"],
        "prompt_retention": "hash_only",
        "output_retention": "store_structured_output",
        "audit_level": "full",
        "private_model_endpoint_id": "private-endpoint-canada-001",
        "customer_managed_endpoint_id": "customer-managed-demo",
        "no_ai_fallback": "manual_operator_review",
        "terms_accepted": True,
        "privacy_notice_accepted": True,
        "ai_use_disclosure_accepted": True,
    },
    {
        "id": "ai-policy-org-other-demo",
        "organization_id": "org-other-demo",
        "default_mode": "no_ai",
        "allowed_modes": ["no_ai", "metadata_only", "on_prem_manual"],
        "allowed_sensitivity": ["public", "internal"],
        "restricted_sensitivity_modes": ["no_ai", "metadata_only", "on_prem_manual"],
        "redaction_required_for": ["confidential", "restricted", "regulated"],
        "prompt_retention": "none",
        "output_retention": "none",
        "audit_level": "full",
        "private_model_endpoint_id": "",
        "customer_managed_endpoint_id": "",
        "no_ai_fallback": "manual_operator_review",
        "terms_accepted": True,
        "privacy_notice_accepted": True,
        "ai_use_disclosure_accepted": False,
    },
]

MODEL_ENDPOINTS = [
    {
        "id": "business-api-default",
        "mode": "business_api",
        "endpoint_url": "provider://business-api",
        "auth_method": "server_secret_reference",
        "api_key_reference": "IMPORTER_LLM_API_KEY",
        "model_name": "structured-review-model",
        "supports_json_schema": True,
        "max_context_tokens": 64000,
        "timeout_seconds": 60,
        "retention_policy": "business_api_default_no_training_by_product_policy",
        "health_check_status": "not_configured_for_public_hosting",
    },
    {
        "id": "private-endpoint-canada-001",
        "mode": "private_hosted_llm",
        "endpoint_url": "https://private-llm.example.local",
        "auth_method": "private_network_secret_reference",
        "api_key_reference": "PRIVATE_LLM_API_KEY",
        "model_name": "private-structured-review",
        "supports_json_schema": True,
        "max_context_tokens": 128000,
        "timeout_seconds": 90,
        "retention_policy": "private_tenant_no_provider_training",
        "health_check_status": "design_ready_not_live",
    },
    {
        "id": "customer-managed-demo",
        "mode": "customer_managed_llm",
        "endpoint_url": "https://customer-model.example.local",
        "auth_method": "customer_secret_reference",
        "api_key_reference": "CUSTOMER_MANAGED_LLM_KEY",
        "model_name": "customer-managed-review",
        "supports_json_schema": True,
        "max_context_tokens": 32000,
        "timeout_seconds": 90,
        "retention_policy": "customer_controlled",
        "health_check_status": "design_ready_not_live",
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
        "claim_type": "export_to_canada_readiness_claim",
        "display_name": "Export-to-Canada readiness",
        "default_status": "blocked_missing_evidence",
        "required_evidence_types": ["customer_uploaded_document", "expert_review_finding", "source_refresh_record"],
        "requires_human_review": True,
        "customer_copy": "Export-to-Canada readiness needs exporter-side documents, Canadian importer responsibility, and broker/expert review.",
    },
    {
        "claim_type": "importer_of_record_claim",
        "display_name": "Importer of record",
        "default_status": "blocked_missing_evidence",
        "required_evidence_types": ["commercial_contract", "expert_review_finding"],
        "requires_human_review": True,
        "customer_copy": "Importer-of-record and DDP/non-resident importer responsibility must be confirmed before shipment decisions.",
    },
    {
        "claim_type": "trade_document_completeness_claim",
        "display_name": "Trade document completeness",
        "default_status": "blocked_missing_evidence",
        "required_evidence_types": ["customer_uploaded_document", "expert_review_finding"],
        "requires_human_review": True,
        "customer_copy": "Product, commercial, certificate, proof-of-origin, and shipping documents remain incomplete until reviewed.",
    },
    {
        "claim_type": "trade_agreement_preference_claim",
        "display_name": "Trade agreement or preference claim",
        "default_status": "blocked_requires_human_review",
        "required_evidence_types": ["official_source_reference", "expert_review_finding"],
        "requires_human_review": True,
        "customer_copy": "Trade agreement, MoU, rules-of-origin, or preference claims need official evidence and qualified review.",
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

REQUIREMENTS_TRACEABILITY = [
    {
        "id": "REQ-01",
        "name": "Identity, organization, permissions",
        "status": "implemented_local_private_beta",
        "artifacts": ["product_runtime_state.json", "auth_rbac_matrix.json", "customer_workflow.sqlite"],
        "proof": ["tests/test_product_runtime.py", "tests/test_operator_app.py"],
        "boundary": "Local session auth and RBAC are implemented for private beta dry-runs; production identity review remains external.",
    },
    {
        "id": "REQ-02",
        "name": "Packet intake",
        "status": "implemented",
        "artifacts": ["customer_source_packets.json", "customer_readiness_report.json"],
        "proof": ["tests/test_operator_app.py", "tests/test_source_packet_workflow.py"],
        "boundary": "Packet intake creates review state, not import approval.",
    },
    {
        "id": "REQ-03",
        "name": "Evidence ledger",
        "status": "implemented",
        "artifacts": ["evidence_ledger.json"],
        "proof": ["tests/test_source_packet_workflow.py"],
        "boundary": "No evidence, no claim; stale/reference-only evidence blocks external claims.",
    },
    {
        "id": "REQ-04",
        "name": "Official source refresh",
        "status": "implemented_with_live_fetch_boundary",
        "artifacts": ["source_refresh_runs.json", "source_refresh_report_packet-frozen-tuna-canada-001.json"],
        "proof": ["tests/test_source_packet_workflow.py"],
        "boundary": "Refresh records are evidence inputs; they do not replace qualified review.",
    },
    {
        "id": "REQ-05",
        "name": "Claim and blocker engine",
        "status": "implemented_fail_closed",
        "artifacts": ["claims_gate_matrix.json", "customer_readiness_report.json", "blockers.jsonl"],
        "proof": ["scripts/check_product.py"],
        "boundary": "External-world claims stay blocked until evidence and human gates close.",
    },
    {
        "id": "REQ-06",
        "name": "AI processing and model routing",
        "status": "implemented_policy_router",
        "artifacts": ["ai_data_policy.json", "ai_model_router.json", "customer_ai_review_runs.json"],
        "proof": ["tests/test_product_runtime.py", "tests/test_operator_app.py"],
        "boundary": "Router controls local simulated review and endpoint contracts; no live provider call is made by default.",
    },
    {
        "id": "REQ-07",
        "name": "AI simulated reviewers",
        "status": "implemented_fail_closed",
        "artifacts": ["customer_ai_review_runs.json"],
        "proof": ["tests/test_product_runtime.py", "tests/test_source_packet_workflow.py"],
        "boundary": "AI reviewers create findings and next moves only; they cannot open gates.",
    },
    {
        "id": "REQ-08",
        "name": "Operator UX",
        "status": "implemented_local_app",
        "artifacts": ["operator_dashboard.html", "operator_workflow_report.json"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "Operator UX is local/private-beta oriented.",
    },
    {
        "id": "REQ-09",
        "name": "Expert review UX",
        "status": "implemented_scoped_tokens",
        "artifacts": ["review_requests.json", "expert_review_packet_packet-frozen-tuna-canada-001.md"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "Expert review packet is scoped; no advice or approval is implied by the app.",
    },
    {
        "id": "REQ-10",
        "name": "Reports and exports",
        "status": "implemented_safe_exports",
        "artifacts": ["report_exports.json", "customer_readiness_report.md"],
        "proof": ["tests/test_source_packet_workflow.py", "scripts/check_product.py"],
        "boundary": "Reports disclose blockers and AI involvement; they are not certificates.",
    },
    {
        "id": "REQ-11",
        "name": "Customer UX",
        "status": "implemented",
        "artifacts": ["product_runtime_state.json"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "Customer UX is private-beta candidate, not public launch proof.",
    },
    {
        "id": "REQ-12",
        "name": "Admin UX",
        "status": "implemented",
        "artifacts": ["product_runtime_state.json"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "Admin controls are local/private-beta implementation surfaces.",
    },
    {
        "id": "REQ-13",
        "name": "Privacy and data controls",
        "status": "implemented_with_external_review_gate",
        "artifacts": ["ai_data_policy.json", "redaction_pipeline.json", "deletion_requests.json"],
        "proof": ["tests/test_product_runtime.py", "tests/test_operator_app.py"],
        "boundary": "Policies and deletion workflow exist; qualified privacy/legal review remains required before hosted customer use.",
    },
    {
        "id": "REQ-14",
        "name": "Security",
        "status": "implemented_local_controls_with_hosting_gates",
        "artifacts": ["auth_rbac_matrix.json", "deployment_readiness_report.json"],
        "proof": ["tests/test_operator_app.py", "scripts/check_product.py"],
        "boundary": "Production identity, TLS, secret manager, malware scanning, and security review remain external gates.",
    },
    {
        "id": "REQ-15",
        "name": "Audit and observability",
        "status": "implemented",
        "artifacts": ["audit_events.json", "customer_action_log.json", "deployment_readiness_report.json"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "Local JSON/SQLite audit exists; production observability stack remains a deployment gate.",
    },
    {
        "id": "REQ-16",
        "name": "Deployment environments",
        "status": "implemented_hostable_local_stack",
        "artifacts": ["Dockerfile", "compose.yaml", ".env.example", "deployment_readiness_report.json"],
        "proof": ["scripts/check_product.py"],
        "boundary": "Hostable artifacts exist; no live production environment is claimed.",
    },
    {
        "id": "REQ-17",
        "name": "Testing and acceptance gates",
        "status": "implemented",
        "artifacts": ["RUN_RESULTS.md", "requirements_traceability_matrix.json"],
        "proof": ["python3 -m unittest discover -s tests -p test_*.py", "python3 scripts/check_product.py"],
        "boundary": "Acceptance proves local product behavior and generated artifacts, not external legal/compliance approval.",
    },
    {
        "id": "REQ-PUBLIC-01",
        "name": "Public trade readiness quick check",
        "status": "implemented_local_public_surface",
        "artifacts": ["public_trade_readiness_manifest.json", "public_upload_manifest.json", "report_exports.json"],
        "proof": ["tests/test_operator_app.py", "scripts/check_product.py"],
        "boundary": "Public quick check is no-login draft PDF generation with delete controls; it is not approval, advice, shipment readiness, or persistent account history.",
    },
    {
        "id": "REQ-EXPORT-01",
        "name": "Create Export-to-Canada packet",
        "status": "implemented",
        "artifacts": ["customer_readiness_report.json", "public_trade_readiness_manifest.json"],
        "proof": ["tests/test_source_packet_workflow.py", "tests/test_operator_app.py"],
        "boundary": "Exporter packet creates evidence gaps and review packets only.",
    },
    {
        "id": "REQ-EXPORT-02",
        "name": "Identify Canadian buyer/importer",
        "status": "implemented_fail_closed",
        "artifacts": ["customer_readiness_report.json"],
        "proof": ["tests/test_source_packet_workflow.py"],
        "boundary": "Missing buyer/importer creates a blocker; presence is not buyer validation.",
    },
    {
        "id": "REQ-EXPORT-03",
        "name": "Capture Incoterms or delivery responsibility",
        "status": "implemented_fail_closed",
        "artifacts": ["customer_readiness_report.json"],
        "proof": ["tests/test_source_packet_workflow.py"],
        "boundary": "Incoterms classify responsibility path only; they do not prove legal or customs readiness.",
    },
    {
        "id": "REQ-EXPORT-04",
        "name": "Mark Canadian import responsibility",
        "status": "implemented_fail_closed",
        "artifacts": ["customer_readiness_report.json"],
        "proof": ["tests/test_source_packet_workflow.py"],
        "boundary": "Exporter/DDP/non-resident importer responsibility triggers broker review gates.",
    },
    {
        "id": "REQ-EXPORT-05",
        "name": "Check Canadian-side readiness blockers",
        "status": "implemented_fail_closed",
        "artifacts": ["claims_gate_matrix.json", "customer_readiness_report.json"],
        "proof": ["scripts/check_product.py"],
        "boundary": "Canadian official/reference checks remain evidence only until qualified review.",
    },
    {
        "id": "REQ-EXPORT-06",
        "name": "Check exporter-side document readiness",
        "status": "implemented_fail_closed",
        "artifacts": ["customer_readiness_report.json"],
        "proof": ["tests/test_source_packet_workflow.py"],
        "boundary": "Exporter-side readiness is a document-gap lane, not country legal advice.",
    },
    {
        "id": "REQ-EXPORT-07",
        "name": "Generate buyer-ready packet",
        "status": "implemented_pdf_draft",
        "artifacts": ["report_exports.json"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "Buyer packet is a draft question/evidence packet and cannot claim buyer validation.",
    },
    {
        "id": "REQ-EXPORT-08",
        "name": "Generate Canadian broker-review packet",
        "status": "implemented_pdf_draft",
        "artifacts": ["report_exports.json", "review_requests.json"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "Broker packet asks for scoped review; it is not broker advice or clearance.",
    },
    {
        "id": "REQ-EXPORT-09",
        "name": "Block compliance, tariff, CFIA, buyer, and shipment claims",
        "status": "implemented_fail_closed",
        "artifacts": ["claims_gate_matrix.json", "customer_readiness_report.json"],
        "proof": ["tests/test_source_packet_workflow.py", "scripts/check_product.py"],
        "boundary": "All external-world claims remain blocked without qualified evidence and human gates.",
    },
    {
        "id": "REQ-STARTER-01",
        "name": "Beginner no-documents starter flow",
        "status": "implemented_local_public_surface",
        "artifacts": ["customer_readiness_report.json", "public_trade_readiness_manifest.json"],
        "proof": ["tests/test_operator_app.py", "tests/test_source_packet_workflow.py"],
        "boundary": "Starter mode creates a missing-evidence packet and checklist; it is not advice or approval.",
    },
    {
        "id": "REQ-PDF-01",
        "name": "PDF triage and native text extraction decision",
        "status": "implemented_local_parser_with_ocr_gate",
        "artifacts": ["public_upload_manifest.json", "public_upload_policy.json"],
        "proof": ["tests/test_document_processing.py", "tests/test_operator_app.py"],
        "boundary": "PDF triage detects local text/OCR needs and asks for confirmation; it does not verify document authenticity.",
    },
    {
        "id": "REQ-CONFIRM-01",
        "name": "User confirmation before extracted fields become packet context",
        "status": "implemented",
        "artifacts": ["customer_readiness_report.json", "audit_events.json"],
        "proof": ["tests/test_operator_app.py"],
        "boundary": "User confirmation records draft context only; human experts still own external claims.",
    },
    {
        "id": "REQ-IH-01",
        "name": "Intelligence Hub policy/source monitoring contract",
        "status": "implemented_database_style_contract",
        "artifacts": ["intelligence_hub_policy_monitor.json", "policy_source_snapshots.json", "policy_change_impact_report.json", "policy_intelligence.sqlite"],
        "proof": ["tests/test_policy_intelligence.py", "scripts/run_policy_intelligence.py"],
        "boundary": "The contract maps sources, snapshots, diffs, and packet impacts; live source truth and qualified review remain external gates.",
    },
    {
        "id": "REQ-OPPORTUNITY-01",
        "name": "Opportunity scanner with research gates",
        "status": "implemented_signal_contract",
        "artifacts": ["opportunity_scanner_report.json", "completion_platform_manifest.json"],
        "proof": ["tests/test_completion_platform.py", "scripts/run_completion_platform.py"],
        "boundary": "Opportunity rows are signals and research prompts, not recommendations, demand proof, margin proof, or buyer validation.",
    },
    {
        "id": "REQ-COVERAGE-01",
        "name": "Country coverage tiers",
        "status": "implemented_claim_gated_contract",
        "artifacts": ["country_coverage_report.json", "completion_platform_manifest.json"],
        "proof": ["tests/test_completion_platform.py", "scripts/run_completion_platform.py"],
        "boundary": "Coverage tiers describe product support level only; they are not country-specific legal, customs, tariff, or compliance correctness.",
    },
    {
        "id": "REQ-TRANSPORT-01",
        "name": "Transport readiness lane",
        "status": "implemented_forwarder_question_contract",
        "artifacts": ["transport_readiness_report.json", "completion_platform_manifest.json"],
        "proof": ["tests/test_completion_platform.py", "scripts/run_completion_platform.py"],
        "boundary": "Transport readiness prepares freight-forwarder questions; it does not guarantee routes, costs, carrier choice, or shipment readiness.",
    },
    {
        "id": "REQ-BILLING-01",
        "name": "Billing and credit controls",
        "status": "implemented_local_metering_contract",
        "artifacts": ["billing_credit_controls.json", "completion_platform_manifest.json"],
        "proof": ["tests/test_completion_platform.py", "scripts/run_completion_platform.py"],
        "boundary": "Billing controls define plan, credit, and heavy-job authorization only; live checkout and invoicing are disabled.",
    },
    {
        "id": "REQ-AGENT-01",
        "name": "Agent/API contract",
        "status": "implemented_scoped_api_contract",
        "artifacts": ["agent_api_manifest.json", "completion_platform_manifest.json"],
        "proof": ["tests/test_completion_platform.py", "scripts/run_completion_platform.py"],
        "boundary": "Agents can create packets and reports through product gates only; no live public API gateway or claim-opening tool is exposed.",
    },
    {
        "id": "REQ-TRAFFIC-01",
        "name": "Traffic-first public pages",
        "status": "implemented_manifest_and_routes",
        "artifacts": ["traffic_pages_manifest.json", "public_trade_readiness_manifest.json"],
        "proof": ["tests/test_operator_app.py", "tests/test_completion_platform.py"],
        "boundary": "Traffic/checklist pages educate and route to the tool; they are not legal, customs, tariff, supplier, buyer, or shipment advice.",
    },
    {
        "id": "REQ-STAGE-01",
        "name": "All local product stages",
        "status": "implemented_stage_runtime",
        "artifacts": ["all_stage_readiness_report.json", "completion_platform_manifest.json"],
        "proof": ["tests/test_completion_platform.py", "scripts/run_completion_platform.py"],
        "boundary": "All locally implementable stages have routes, APIs, and artifacts; real-world approvals remain external gates.",
    },
    {
        "id": "REQ-RESEARCH-01",
        "name": "Research and data execution routing",
        "status": "implemented_evidence_lane_router",
        "artifacts": ["research_execution_plan.json"],
        "proof": ["tests/test_completion_platform.py"],
        "boundary": "Research routing chooses model-prior, web, official-source, dataset, and expert/user lanes; it does not prove the external facts.",
    },
    {
        "id": "REQ-EXPERT-01",
        "name": "Expert network and review routing",
        "status": "implemented_local_review_network",
        "artifacts": ["expert_network_report.json", "review_requests.json"],
        "proof": ["tests/test_completion_platform.py", "tests/test_operator_app.py"],
        "boundary": "The product can prepare and route scoped expert packets; real qualified findings remain external evidence.",
    },
    {
        "id": "REQ-TEAM-01",
        "name": "Business/team workspace",
        "status": "implemented_local_workspace",
        "artifacts": ["team_workspace_report.json", "auth_rbac_matrix.json"],
        "proof": ["tests/test_completion_platform.py", "tests/test_operator_app.py"],
        "boundary": "Team workspace roles and approval boards are local coordination surfaces, not real owner approval.",
    },
    {
        "id": "REQ-API-GATEWAY-01",
        "name": "Agent API gateway executor",
        "status": "implemented_local_executor_no_external_effects",
        "artifacts": ["agent_api_gateway_contract.json", "agent_api_manifest.json", "product_operations_report.json"],
        "proof": ["tests/test_completion_platform.py", "tests/test_operator_app.py", "scripts/run_product_operations.py"],
        "boundary": "Gateway tools execute local product operations only; no public API, credentials, payments, or claim-opening authority are exposed.",
    },
    {
        "id": "REQ-LAUNCH-OPS-01",
        "name": "Launch operations and private beta controls",
        "status": "implemented_private_beta_ops_contract",
        "artifacts": ["launch_operations_report.json", "board_go_live_readiness_report.json"],
        "proof": ["tests/test_completion_platform.py", "scripts/check_product.py"],
        "boundary": "Launch operations are ready for private-beta review; production deployment and public launch require owner approval.",
    },
    {
        "id": "REQ-OPERATIONS-01",
        "name": "Executable local product operations",
        "status": "implemented_local_operations_engine",
        "artifacts": [
            "product_operations_report.json",
            "research_execution_runs.json",
            "expert_review_work_orders.json",
            "team_workspace_activity.json",
            "billing_usage_ledger.json",
            "launch_operations_events.json",
        ],
        "proof": ["tests/test_operator_app.py", "scripts/run_product_operations.py", "scripts/check_product.py"],
        "boundary": "Local operations mutate product state, reports, and ledgers; they still do not create external legal, customs, tariff, buyer, supplier, payment, or launch approvals.",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def packet_org_id(packet: dict[str, Any]) -> str:
    return str(packet.get("organization_id") or "org-importer-demo")


def hash_snapshot(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def ai_policy_for_org(organization_id: str) -> dict[str, Any]:
    for policy in AI_DATA_POLICIES:
        if policy["organization_id"] == organization_id:
            return policy
    return {
        "id": f"ai-policy-{organization_id}",
        "organization_id": organization_id,
        "default_mode": "no_ai",
        "allowed_modes": ["no_ai", "metadata_only", "on_prem_manual"],
        "allowed_sensitivity": ["public", "internal"],
        "restricted_sensitivity_modes": ["no_ai", "metadata_only", "on_prem_manual"],
        "redaction_required_for": ["confidential", "restricted", "regulated"],
        "prompt_retention": "none",
        "output_retention": "none",
        "audit_level": "full",
        "private_model_endpoint_id": "",
        "customer_managed_endpoint_id": "",
        "no_ai_fallback": "manual_operator_review",
        "terms_accepted": False,
        "privacy_notice_accepted": False,
        "ai_use_disclosure_accepted": False,
    }


def endpoint_for_mode(mode: str, policy: dict[str, Any]) -> dict[str, Any] | None:
    endpoint_id = ""
    if mode == "private_hosted_llm":
        endpoint_id = str(policy.get("private_model_endpoint_id") or "")
    elif mode == "customer_managed_llm":
        endpoint_id = str(policy.get("customer_managed_endpoint_id") or "")
    elif mode == "business_api":
        endpoint_id = "business-api-default"
    if not endpoint_id:
        return None
    return next((endpoint for endpoint in MODEL_ENDPOINTS if endpoint["id"] == endpoint_id), None)


def route_ai_task(
    *,
    organization_id: str,
    packet_id: str,
    evidence_id: str,
    task_type: str,
    document_sensitivity: str,
    requested_mode: str,
    evidence_permission: str,
) -> dict[str, Any]:
    policy = ai_policy_for_org(organization_id)
    mode = requested_mode if requested_mode in AI_PROCESSING_MODES else policy["default_mode"]
    if evidence_permission in {"no_ai", "metadata_only", "on_prem_manual"}:
        mode = evidence_permission
    denied_reason = ""
    if mode not in policy["allowed_modes"]:
        denied_reason = f"mode {mode} is not allowed by organization policy"
    if document_sensitivity not in policy["allowed_sensitivity"] and mode not in policy["restricted_sensitivity_modes"]:
        denied_reason = f"sensitivity {document_sensitivity} requires private/no-AI mode"
    if evidence_permission == "no_ai" and mode not in {"no_ai", "metadata_only", "on_prem_manual"}:
        denied_reason = "evidence item blocks AI processing"
    redaction_required = document_sensitivity in policy["redaction_required_for"] or mode == "redacted"
    endpoint = endpoint_for_mode(mode, policy)
    if mode in {"business_api", "private_hosted_llm", "customer_managed_llm"} and endpoint is None:
        denied_reason = f"no endpoint configured for {mode}"
    allowed = denied_reason == "" and mode not in {"no_ai", "on_prem_manual"}
    return {
        "organization_id": organization_id,
        "packet_id": packet_id,
        "evidence_id": evidence_id,
        "task_type": task_type,
        "document_sensitivity": document_sensitivity,
        "requested_mode": requested_mode,
        "evidence_permission": evidence_permission,
        "organization_policy_id": policy["id"],
        "allowed": allowed,
        "mode": mode,
        "redaction_required": redaction_required,
        "store_prompt": policy["prompt_retention"] != "none" and allowed,
        "store_output": policy["output_retention"] != "none" and allowed,
        "audit_level": policy["audit_level"],
        "model_endpoint_id": endpoint["id"] if endpoint else "",
        "reason_if_denied": denied_reason,
        "next_valid_move_if_denied": "Use metadata-only/manual review or change organization and document-level AI permission.",
        "no_ai_fallback": policy["no_ai_fallback"],
    }


def redaction_preview_for_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    sensitivity = str(evidence.get("sensitivity_level") or "internal")
    mode = str(evidence.get("ai_processing_mode") or evidence.get("ai_processing_allowed") or "metadata_only")
    redaction_required = bool(evidence.get("redaction_required")) or sensitivity in {"confidential", "restricted", "regulated"} or mode == "redacted"
    redacted_fields = REDACTION_CATEGORIES if redaction_required else []
    return {
        "evidence_id": evidence.get("evidence_id"),
        "packet_id": evidence.get("packet_id"),
        "redaction_required": redaction_required,
        "redaction_status": "redaction_required" if redaction_required else "not_required",
        "redaction_categories": redacted_fields,
        "redacted_artifact_id": f"redacted-{evidence.get('evidence_id')}" if redaction_required else "",
        "linked_original_evidence_id": evidence.get("evidence_id"),
        "audit_event_type": "redaction_preview_generated" if redaction_required else "redaction_not_required",
    }


def manual_workflow_state(workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "manual_no_ai_workflow_ready",
        "ai_disabled_supported": True,
        "features": [
            "manual packet creation",
            "manual evidence upload",
            "manual evidence classification",
            "manual blocker creation",
            "manual operator review",
            "manual expert-review packet generation",
            "manual report generation",
            "manual source refresh",
        ],
        "packet_count": workflow.get("packet_count", 0),
        "report_disclosure": "No AI processing is required. Reports disclose whether AI was used.",
        "next_valid_move": "Use operator review and scoped expert-review packet when AI is disabled.",
    }


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
            ("draft_trade_readiness_report", "pdf"),
            ("buyer_ready_packet", "pdf"),
            ("broker_review_packet", "pdf"),
            ("missing_evidence_checklist", "pdf"),
            ("operator_review_report", "pdf"),
            ("expert_review_packet", "pdf"),
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
                    "ai_involvement_disclosure": "AI simulated review may be included when present; AI never opens approval gates.",
                    "proof_boundary": PRODUCT_BOUNDARY,
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
        {"item": "AI data policy and model router exist", "status": "implemented"},
        {"item": "No-AI/manual workflow exists", "status": "implemented"},
        {"item": "Redaction pipeline contract exists", "status": "implemented"},
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
        "model_endpoints": {
            "default_behavior": "local deterministic simulator; no provider call by default",
            "endpoint_contracts": [endpoint["id"] for endpoint in MODEL_ENDPOINTS],
        },
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
    evidence_rows = [row for packet in workflow.get("packets", []) for row in packet.get("evidence_items", [])]
    packet_orgs = {str(packet.get("packet_id")): packet_org_id(packet) for packet in workflow.get("packets", [])}
    ai_route_decisions = [
        route_ai_task(
            organization_id=packet_orgs.get(str(row.get("packet_id")), str(row.get("organization_id") or "org-importer-demo")),
            packet_id=str(row.get("packet_id")),
            evidence_id=str(row.get("evidence_id")),
            task_type="evidence_readiness_review",
            document_sensitivity=str(row.get("sensitivity_level") or "internal"),
            requested_mode=str(row.get("ai_processing_mode") or "metadata_only"),
            evidence_permission=str(row.get("ai_processing_permission") or row.get("ai_processing_mode") or "metadata_only"),
        )
        for row in evidence_rows
    ]
    redaction_previews = [redaction_preview_for_evidence(row) for row in evidence_rows]
    return {
        "generated_at": workflow.get("generated_at") or now_iso(),
        "product": "Trade Readiness Copilot",
        "internal_engine": "Importer Source Readiness Copilot",
        "public_product": "Trade Readiness Copilot",
        "category": "Source Readiness Management",
        "status": "private_beta_candidate_with_external_human_gates",
        "customer_promise": (
            "Before you import or export, know what is missing. Turn a messy trade idea into an evidence-backed readiness packet that shows "
            "what is known, what is missing, which claims are blocked, and what review is required before moving forward."
        ),
        "public_product_surface": {
            "status": "public_quick_check_ready_local_with_external_gates",
            "levels": [
                "Level 0 beginner starter - no documents, missing-evidence checklist, source/research routing",
                "Level 1 public free tool - no login, limited PDF upload, draft PDF, auto-delete/delete controls",
                "Level 2 free account - saved history and workspace",
                "Level 3 Pro - more packets and review workflows",
                "Level 4 Business - team/operator workbench",
                "Level 5 Enterprise/private AI - customer-managed or private hosted model routing",
                "Level 6 opportunity scanner - signal-only research prompts",
                "Level 7 country coverage - support tiers and claim gates",
                "Level 8 transport readiness - freight-forwarder question packets",
                "Level 9 billing/credits - local metering and heavy-job gates",
                "Level 10 agent/API layer - scoped tool manifest",
                "Level 11 traffic-first growth pages - checklists and sample reports",
                "Level 12 research execution - model, web, official, dataset, and expert lanes",
                "Level 13 expert network - scoped review routing",
                "Level 14 business/team workspace - approval board and roles",
                "Level 15 launch operations - private beta controls and outcome loop",
            ],
            "customer_flow": [
                "choose beginner start or document mode",
                "enter what is known",
                "upload PDF if available",
                "triage native text or OCR need",
                "confirm extracted fields",
                "preview gaps",
                "download starter/missing-evidence/draft PDF",
                "delete files or create account",
            ],
            "visible_modules": [
                "Beginner Start",
                "Import Readiness",
                "Export Readiness",
                "Source Packet Builder",
                "Evidence Ledger",
                "PDF Triage",
                "User Confirmation",
                "PDF Report Generator",
                "ChatGPT-Safe Summary",
                "Expert Review Packet",
                "Operator Workbench",
                "Policy Source Monitor",
                "Opportunity Scanner",
                "Country Coverage",
                "Transport Readiness",
                "Billing/Credits",
                "Agent API",
                "Traffic Checklist Pages",
                "Research Execution",
                "Expert Network",
                "Team Workspace",
                "Launch Operations",
            ],
            "hidden_internal_terms": ["system_review_graph", "proof logs", "operator screenshots", "fixture-backed language", "board gates"],
        },
        "trade_direction_values": ["import", "export", "both", "unknown"],
        "public_privacy_controls": {
            "upload_notice": "required",
            "ai_use_notice": "required",
            "retention_notice": "delete or expire after public quick check",
            "delete_after_processing_control": "implemented_local_route",
            "no_ai_mode": "supported by organization/evidence policy",
            "redacted_ai_mode": "supported",
            "private_ai_mode": "supported by endpoint contract",
            "review_boundary": "PIPEDA/OWASP/NIST references are control prompts, not legal or security certification claims.",
        },
        "boundary": PRODUCT_BOUNDARY,
        "users": USERS,
        "organizations": ORGANIZATIONS,
        "ai_data_policies": AI_DATA_POLICIES,
        "model_endpoints": MODEL_ENDPOINTS,
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
        "ai_model_router": {
            "status": "ai_model_router_ready",
            "modes": AI_PROCESSING_MODES,
            "policy_count": len(AI_DATA_POLICIES),
            "endpoint_count": len(MODEL_ENDPOINTS),
            "route_decisions": ai_route_decisions,
            "manual_fallback": "manual_operator_review",
            "proof_boundary": "Router decisions bound local simulated review and endpoint contracts; they do not prove live model provider availability.",
        },
        "redaction_pipeline": {
            "status": "redaction_pipeline_ready",
            "categories": REDACTION_CATEGORIES,
            "previews": redaction_previews,
            "proof_boundary": "Redaction preview names fields/categories to remove before AI; production redaction requires security/privacy review.",
        },
        "manual_no_ai_workflow": manual_workflow_state(workflow),
        "requirements_traceability": REQUIREMENTS_TRACEABILITY,
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
                "rate_limit": "local policy bucket: public_quick_check allows 6 uploads per 10 minutes per browser/IP before hosted deployment",
                "quarantine_storage": "public_uploads/:packetId/quarantine with generated filenames",
                "parser_sandbox": "local bounded parser only; no shell execution, no remote fetch, no direct file serving",
                "direct_file_serving": "disabled",
                "pdf_triage": "native text extraction attempted, OCR need flagged, user confirmation required",
                "ocr_cost_gate": "OCR pages are estimated and require explicit user approval before any external OCR/AI charge",
                "malicious_html_policy": "reject script-bearing metadata and always HTML-escape display",
                "audit_event_types": [
                    "public_upload_received",
                    "public_pdf_triaged",
                    "public_upload_quarantined",
                    "public_fields_confirmed",
                    "public_upload_deleted",
                ],
            },
            "route_traversal": "route-specific artifact base directories with resolved-path checks",
            "audit": "packet, AI, review, export, deletion, and permission events are recorded",
            "ai_data_policy": "organization policy controls allowed modes, sensitivity, endpoint routing, retention, and no-AI fallback",
            "model_router": "per-evidence model routing denies disallowed modes and records endpoint decisions",
            "redaction_pipeline": "sensitive evidence is marked for redaction before AI processing",
            "no_ai_mode": "manual workflow remains available when AI is disabled at org or evidence level",
        },
        "private_beta_checklist": private_beta_checklist(),
        "deployment": deployment_readiness(),
        "ui_routes": {
            "customer": [
                "/",
                "/start",
                "/tools",
                "/trade-check",
                "/tools/import-readiness",
                "/tools/export-readiness",
                "/tools/buyer-broker-packet",
                "/tools/document-check",
                "/tools/canadian-references",
                "/opportunities",
                "/country-coverage",
                "/transport-readiness",
                "/reports/sample",
                "/pricing",
                "/billing",
                "/billing/usage",
                "/agent-api",
                "/stages",
                "/research-plan",
                "/expert-network",
                "/team-workspace",
                "/launch-operations",
                "/ai-data-policy",
                "/security",
                "/public/packets/:packetId/result",
                "/public/packets/:packetId/confirm",
                "/workspace",
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
                "/packets/:packetId/source-monitoring",
                "/packets/:packetId/safe-summary",
                "/packets/:packetId/settings",
                "/settings/ai-data-policy",
                "/account",
                "/support",
                "/privacy",
                "/terms",
                "/ai-use",
                "/data-retention",
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
            "/api/public/starter",
            "/api/public/quick-check",
            "/api/public/packets/:id/refresh-official-sources",
            "/api/public/packets/:id/confirm",
            "/api/public/packets/:id/chatgpt-safe-summary",
            "/api/public/packets/:id/reports/starter.pdf",
            "/api/public/packets/:id/reports/draft.pdf",
            "/api/public/packets/:id/reports/missing.pdf",
            "/api/public/packets/:id/reports/buyer.pdf",
            "/api/public/packets/:id/reports/broker.pdf",
            "/api/public/packets/:id/delete-files",
            "/api/opportunities",
            "/api/country-coverage",
            "/api/billing/controls",
            "/api/billing/usage",
            "/api/agent-api",
            "/api/agent-api/gateway",
            "/api/traffic-pages",
            "/api/transport-readiness",
            "/api/stages",
            "/api/research-plan",
            "/api/expert-network",
            "/api/team-workspace",
            "/api/launch-operations",
            "/api/product-operations/report",
            "/api/product-operations/run",
            "/api/agent-tools/:tool",
            "/api/orgs/current",
            "/api/orgs/current/members",
            "/api/orgs/current/ai-policy",
            "/api/orgs/current/ai-policy/test-model-endpoint",
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
            "/api/evidence/:evidenceId/ai-permission",
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
        "ai_data_policy.json": {
            "status": "ai_data_policy_ready",
            "policies": state["ai_data_policies"],
            "model_endpoints": state["model_endpoints"],
            "proof_boundary": "Policies are product controls; qualified privacy/legal/security review is still required before hosted customer use.",
        },
        "model_endpoints.json": {"endpoints": state["model_endpoints"]},
        "ai_model_router.json": state["ai_model_router"],
        "redaction_pipeline.json": state["redaction_pipeline"],
        "manual_no_ai_workflow.json": state["manual_no_ai_workflow"],
        "requirements_traceability_matrix.json": {
            "status": "requirements_traceability_ready",
            "requirements": state["requirements_traceability"],
        },
        "public_trade_readiness_manifest.json": {
            "status": "public_trade_readiness_ready_local",
            "public_product": state["public_product"],
            "internal_engine": state["internal_engine"],
            "promise": state["customer_promise"],
            "trade_direction_values": state["trade_direction_values"],
            "public_product_surface": state["public_product_surface"],
            "public_privacy_controls": state["public_privacy_controls"],
            "routes": {
                "ui": [
                    "/",
                    "/start",
                    "/tools",
                    "/trade-check",
                    "/tools/import-readiness",
                    "/tools/export-readiness",
                    "/tools/buyer-broker-packet",
                    "/tools/document-check",
                    "/opportunities",
                    "/country-coverage",
                    "/transport-readiness",
                    "/reports/sample",
                    "/pricing",
                    "/billing",
                    "/billing/usage",
                    "/agent-api",
                    "/stages",
                    "/research-plan",
                    "/expert-network",
                    "/team-workspace",
                    "/launch-operations",
                    "/ai-data-policy",
                    "/security",
                    "/public/packets/:packetId/result",
                    "/public/packets/:packetId/confirm",
                    "/workspace",
                ],
                "api": [
                    "/api/public/starter",
                    "/api/public/quick-check",
                    "/api/public/packets/:id/confirm",
                    "/api/public/packets/:id/chatgpt-safe-summary",
                    "/api/public/packets/:id/reports/starter.pdf",
                    "/api/public/packets/:id/reports/draft.pdf",
                    "/api/public/packets/:id/reports/missing.pdf",
                    "/api/public/packets/:id/reports/buyer.pdf",
                    "/api/public/packets/:id/reports/broker.pdf",
                    "/api/public/packets/:id/delete-files",
                    "/api/opportunities",
                    "/api/country-coverage",
                    "/api/billing/controls",
                    "/api/billing/usage",
                    "/api/agent-api",
                    "/api/agent-api/gateway",
                    "/api/traffic-pages",
                    "/api/transport-readiness",
                    "/api/stages",
                    "/api/research-plan",
                    "/api/expert-network",
                    "/api/team-workspace",
                    "/api/launch-operations",
                ],
            },
            "modes": {
                "beginner_no_documents": "Creates a missing-evidence starter packet and checklist without requiring uploads.",
                "document_mode": "Quarantines uploaded PDFs, triages native text/OCR need, and requires user confirmation.",
                "saved_workspace": "Local SQLite/artifact workspace with account CTA and external hosting gates.",
                "opportunity_scanner": "Shows possible opportunity signals and research prompts only.",
                "transport_readiness": "Creates freight-forwarder questions and blocks route/cost/shipment claims.",
                "billing_controls": "Estimates plan/credit gates locally; live checkout remains disabled.",
                "all_stage_runtime": "Every locally implementable stage exposes a route, API, artifact, and proof check.",
            },
            "completion_stage_contracts": {
                "manifest": "system_review_graph/completion_platform_manifest.json",
                "all_stage_readiness": "system_review_graph/all_stage_readiness_report.json",
                "country_coverage": "system_review_graph/country_coverage_report.json",
                "opportunity_scanner": "system_review_graph/opportunity_scanner_report.json",
                "transport_readiness": "system_review_graph/transport_readiness_report.json",
                "billing_credit_controls": "system_review_graph/billing_credit_controls.json",
                "billing_usage_ledger": "system_review_graph/billing_usage_ledger.json",
                "agent_api_manifest": "system_review_graph/agent_api_manifest.json",
                "agent_api_gateway": "system_review_graph/agent_api_gateway_contract.json",
                "traffic_pages_manifest": "system_review_graph/traffic_pages_manifest.json",
                "research_execution_plan": "system_review_graph/research_execution_plan.json",
                "expert_network": "system_review_graph/expert_network_report.json",
                "team_workspace": "system_review_graph/team_workspace_report.json",
                "launch_operations": "system_review_graph/launch_operations_report.json",
                "proof_boundary": "Completion contracts are local/private-beta product surfaces; external market, legal, customs, payment, and expert-review gates remain closed.",
            },
            "intelligence_hub_policy_monitor": {
                "artifact": "system_review_graph/intelligence_hub_policy_monitor.json",
                "store": "system_review_graph/policy_intelligence.sqlite",
                "status": "database_style_contract_ready",
                "proof_boundary": "Source monitoring detects stale packet risk; it does not prove current compliance truth.",
            },
            "blocked_claims": [
                "approval",
                "tariff_confirmed",
                "CFIA_cleared",
                "buyer_validated",
                "shipment_ready",
                "legal_or_customs_advice",
            ],
            "proof_boundary": PRODUCT_BOUNDARY,
        },
        "exporter_mode_requirements.json": {
            "status": "exporter_mode_requirements_ready",
            "user_types": ["foreign_exporter", "canadian_importer", "broker_or_consultant", "operator"],
            "required_fields": [
                "trade_direction",
                "origin_country",
                "destination_country",
                "exporter_name",
                "buyer_name_or_importer_name",
                "importer_of_record",
                "incoterms_if_known",
                "hs_code_if_known",
                "product_documents",
                "commercial_documents",
                "certificates",
                "proof_of_origin",
            ],
            "readiness_lanes": ["exporter_side_readiness", "importer_side_readiness"],
            "acceptance": [
                "create Export-to-Canada packet",
                "generate buyer-ready packet PDF",
                "generate Canadian broker-review packet PDF",
                "block compliance/tariff/CFIA/buyer/shipment claims",
            ],
        },
        "public_report_types.json": {
            "status": "public_report_types_ready",
            "reports": [
                "Starter Checklist.pdf",
                "Draft Trade Readiness Report.pdf",
                "Buyer-Ready Packet.pdf",
                "Broker Review Packet.pdf",
                "Broker/Freight-Forwarder Packet.pdf",
                "Missing Evidence Checklist.pdf",
                "Opportunity Research Report.pdf",
                "Policy Change Impact Report.pdf",
                "Operator Review Report.pdf",
                "Expert Review Packet.pdf",
            ],
            "sections": [
                "Summary",
                "Product details",
                "Trade direction",
                "Countries",
                "Beginner starter unknowns",
                "Documents provided",
                "PDF triage",
                "User-confirmed fields",
                "Evidence quality",
                "Missing docs",
                "Blocked claims",
                "Official/reference sources",
                "Required reviews",
                "Next valid moves",
                "AI involvement disclosure",
                "Boundary/disclaimer",
            ],
        },
        "public_upload_policy.json": {
            "status": "public_upload_policy_ready",
            "max_bytes": MAX_EVIDENCE_UPLOAD_BYTES,
            "accepted_file_types": ["application/pdf"],
            "max_pages_per_pdf": 25,
            "rate_limit": {
                "bucket": "public_quick_check",
                "limit": 6,
                "window_minutes": 10,
                "implementation_status": "local_policy_ready_hosted_enforcement_required",
            },
            "notice_required": True,
            "quarantine": "enabled",
            "generated_storage_names": True,
            "parser_sandbox": {
                "mode": "local_bounded_metadata_parser",
                "no_shell_execution": True,
                "no_network_fetch": True,
                "direct_file_serving": False,
                "native_text_limit_chars": 4000,
            },
            "direct_file_serving": False,
            "user_confirmation_required": True,
            "ocr_decision": "flag OCR requirement when native text is not available",
            "ocr_cost_gate": {
                "estimated_credits_per_page": 2,
                "external_charge_created": False,
                "requires_user_approval": True,
            },
            "retention": "delete or expire after public quick check",
            "delete_route": "/api/public/packets/:id/delete-files",
            "audit_event_types": [
                "public_upload_received",
                "public_pdf_triaged",
                "public_upload_quarantined",
                "public_fields_confirmed",
                "public_upload_deleted",
            ],
            "ai_modes": ["no_ai", "metadata_only", "redacted", "private_hosted_llm", "customer_managed_llm"],
            "review_boundary": "Controls are implemented locally; qualified privacy/security/legal review remains required before hosted public use.",
        },
    }
    for name, payload in artifacts.items():
        (graph / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state
