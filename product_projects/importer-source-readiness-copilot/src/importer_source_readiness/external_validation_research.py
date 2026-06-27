"""External validation requirements for real-world launch gates.

This module is intentionally data-heavy. It turns the remaining real-world
approval work into machine-checkable requirements instead of treating launch
blockers as prose.
"""

from __future__ import annotations

import json
import textwrap
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CHECKED_AT = "2026-06-27"
STATUS = "external_validation_requirements_ready_all_real_world_gates_blocked"

GATE_IDS = [
    "real_external_expert_reviews",
    "legal_privacy_security_approval",
    "qualified_customs_trade_review",
    "hosted_staging_production_proof",
    "live_payment_activation",
    "real_users_private_beta_outcomes",
    "buyer_supplier_validation",
    "public_go_no_go_approval",
]

SOURCE_ANCHORS: list[dict[str, Any]] = [
    {
        "source_id": "cbsa-commercial-import",
        "name": "Import commercial goods into Canada",
        "publisher": "Canada Border Services Agency",
        "url": "https://www.cbsa-asfc.gc.ca/import/menu-eng.html",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review"],
        "project_use": "Import readiness language, importer obligations, accounting/release boundaries, and broker handoff scope.",
    },
    {
        "source_id": "cbsa-customs-tariff",
        "name": "Customs Tariff",
        "publisher": "Canada Border Services Agency",
        "url": "https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/menu-eng.html",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review"],
        "project_use": "HS/tariff source refresh, classification evidence, and tariff-claim blocker boundaries.",
    },
    {
        "source_id": "cbsa-advance-rulings",
        "name": "Advance rulings for tariff classification",
        "publisher": "Canada Border Services Agency",
        "url": "https://www.cbsa-asfc.gc.ca/import/ar-da/menu-eng.html",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review"],
        "project_use": "Evidence boundary for products that need binding or qualified classification confirmation.",
    },
    {
        "source_id": "cfia-importing-food-plants-animals",
        "name": "Importing food, plants or animals",
        "publisher": "Canadian Food Inspection Agency",
        "url": "https://inspection.canada.ca/en/importing-food-plants-animals",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review"],
        "project_use": "Food, plant, animal, and commodity-specific import requirement boundaries.",
    },
    {
        "source_id": "cfia-airs",
        "name": "Automated Import Reference System",
        "publisher": "Canadian Food Inspection Agency",
        "url": "https://inspection.canada.ca/en/importing-food-plants-animals/airs",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review"],
        "project_use": "Current commodity requirement source for CFIA-regulated imports.",
    },
    {
        "source_id": "cfia-food-licences",
        "name": "Food licences",
        "publisher": "Canadian Food Inspection Agency",
        "url": "https://inspection.canada.ca/en/food-licences",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review"],
        "project_use": "Safe Food for Canadians licence and regulated-food readiness boundaries.",
    },
    {
        "source_id": "gac-sanctions",
        "name": "Canadian sanctions",
        "publisher": "Global Affairs Canada",
        "url": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/index.aspx?lang=eng",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review", "buyer_supplier_validation"],
        "project_use": "Sanctions/restricted-party screening blocker and export/import control boundary.",
    },
    {
        "source_id": "gac-consolidated-sanctions-list",
        "name": "Consolidated Canadian Autonomous Sanctions List",
        "publisher": "Global Affairs Canada",
        "url": "https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/consolidated-consolide.aspx?lang=eng",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review", "buyer_supplier_validation"],
        "project_use": "Named-party screening evidence and refresh rule source.",
    },
    {
        "source_id": "gac-trade-controls",
        "name": "Export and import controls",
        "publisher": "Global Affairs Canada",
        "url": "https://www.international.gc.ca/controls-controles/index.aspx?lang=eng",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["qualified_customs_trade_review"],
        "project_use": "Permit/control boundary for controlled goods or destination-specific claims.",
    },
    {
        "source_id": "opc-pipeda-principles",
        "name": "PIPEDA fair information principles",
        "publisher": "Office of the Privacy Commissioner of Canada",
        "url": "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval"],
        "project_use": "Privacy notice, consent, limiting collection/use/disclosure, safeguards, access, and accountability requirements.",
    },
    {
        "source_id": "opc-breach-reporting",
        "name": "Privacy breaches at your business",
        "publisher": "Office of the Privacy Commissioner of Canada",
        "url": "https://www.priv.gc.ca/en/privacy-topics/business-privacy/breaches-and-safeguards/privacy-breaches-at-your-business/gd_pb_201810/",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval", "hosted_staging_production_proof"],
        "project_use": "Breach response, notification, safeguard, and recordkeeping evidence requirements.",
    },
    {
        "source_id": "cccs-baseline-controls",
        "name": "Baseline cyber security controls for small and medium organizations",
        "publisher": "Canadian Centre for Cyber Security",
        "url": "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval", "hosted_staging_production_proof"],
        "project_use": "Baseline security control, access, monitoring, backup, incident, and operations evidence requirements.",
    },
    {
        "source_id": "nist-csf-2",
        "name": "Cybersecurity Framework",
        "publisher": "National Institute of Standards and Technology",
        "url": "https://www.nist.gov/cyberframework",
        "source_type": "official_standard_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval", "hosted_staging_production_proof", "public_go_no_go_approval"],
        "project_use": "Govern, identify, protect, detect, respond, and recover evidence structure.",
    },
    {
        "source_id": "cisa-secure-by-design",
        "name": "Secure by Design",
        "publisher": "Cybersecurity and Infrastructure Security Agency",
        "url": "https://www.cisa.gov/securebydesign",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval", "hosted_staging_production_proof"],
        "project_use": "Secure-by-default product and manufacturer accountability evidence.",
    },
    {
        "source_id": "owasp-file-upload",
        "name": "File Upload Cheat Sheet",
        "publisher": "OWASP",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
        "source_type": "security_primary_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval", "hosted_staging_production_proof"],
        "project_use": "Public upload allowlists, storage isolation, malware scanning, handler-mediated access, and size/rate-limit proof.",
    },
    {
        "source_id": "owasp-asvs",
        "name": "Application Security Verification Standard",
        "publisher": "OWASP",
        "url": "https://owasp.org/www-project-application-security-verification-standard/",
        "source_type": "security_primary_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval", "hosted_staging_production_proof"],
        "project_use": "Application security review depth, authentication, authorization, validation, API, and deployment checks.",
    },
    {
        "source_id": "owasp-llm01-prompt-injection",
        "name": "LLM01: Prompt Injection",
        "publisher": "OWASP GenAI Security Project",
        "url": "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
        "source_type": "security_primary_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval", "real_external_expert_reviews"],
        "project_use": "Prompt-injection threat model, AI red-team evidence, and fail-closed AI output constraints.",
    },
    {
        "source_id": "stripe-go-live",
        "name": "Go-live checklist",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/get-started/checklist/go-live",
        "source_type": "vendor_primary_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["live_payment_activation"],
        "project_use": "Live mode, account, domain, webhook, payment method, tax, support, and operational payment evidence.",
    },
    {
        "source_id": "stripe-webhooks",
        "name": "Webhooks",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/webhooks",
        "source_type": "vendor_primary_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["live_payment_activation", "hosted_staging_production_proof"],
        "project_use": "Webhook endpoint, signing secret, retry, idempotency, and event log proof.",
    },
    {
        "source_id": "stripe-testing",
        "name": "Testing",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/testing",
        "source_type": "vendor_primary_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["live_payment_activation"],
        "project_use": "Pre-live card, webhook, refund, dispute, and failure-path payment proof.",
    },
    {
        "source_id": "stripe-security",
        "name": "Security at Stripe",
        "publisher": "Stripe",
        "url": "https://docs.stripe.com/security",
        "source_type": "vendor_primary_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["live_payment_activation", "legal_privacy_security_approval"],
        "project_use": "Payment security, PCI boundary, account access, and credential handling evidence.",
    },
    {
        "source_id": "govuk-user-research",
        "name": "User research",
        "publisher": "GOV.UK Service Manual",
        "url": "https://www.gov.uk/service-manual/user-research",
        "source_type": "official_service_delivery_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["real_users_private_beta_outcomes"],
        "project_use": "Structured participant research, task evidence, and learning capture for private beta.",
    },
    {
        "source_id": "govuk-service-standard",
        "name": "Service Standard",
        "publisher": "GOV.UK Service Manual",
        "url": "https://www.gov.uk/service-manual/service-standard",
        "source_type": "official_service_delivery_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["real_users_private_beta_outcomes", "public_go_no_go_approval"],
        "project_use": "User need, accessibility, security, operation, and improvement criteria for service readiness.",
    },
    {
        "source_id": "govuk-service-assessments",
        "name": "Service assessments",
        "publisher": "GOV.UK Service Manual",
        "url": "https://www.gov.uk/service-manual/service-assessments",
        "source_type": "official_service_delivery_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["public_go_no_go_approval"],
        "project_use": "Assessment-style go/no-go record, evidence pack, decision owner, and launch caveat structure.",
    },
    {
        "source_id": "nng-five-users",
        "name": "Why You Only Need to Test with 5 Users",
        "publisher": "Nielsen Norman Group",
        "url": "https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/",
        "source_type": "industry_product_research_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["real_users_private_beta_outcomes"],
        "project_use": "Minimum small-sample usability smoke threshold before a broader beta.",
    },
    {
        "source_id": "yc-talk-to-users",
        "name": "How to Talk to Users",
        "publisher": "Y Combinator",
        "url": "https://www.ycombinator.com/library/gx-how-to-talk-to-users",
        "source_type": "startup_product_validation_guidance",
        "checked_at": CHECKED_AT,
        "applies_to": ["buyer_supplier_validation", "real_users_private_beta_outcomes"],
        "project_use": "Customer-discovery interview discipline and evidence capture for demand validation.",
    },
    {
        "source_id": "w3c-wcag-22",
        "name": "Web Content Accessibility Guidelines 2.2",
        "publisher": "W3C",
        "url": "https://www.w3.org/TR/WCAG22/",
        "source_type": "accessibility_standard_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["real_users_private_beta_outcomes", "public_go_no_go_approval"],
        "project_use": "Accessibility review, keyboard/screen-reader checks, contrast, form errors, and report readability evidence.",
    },
    {
        "source_id": "california-ccpa",
        "name": "California Consumer Privacy Act",
        "publisher": "California Department of Justice",
        "url": "https://oag.ca.gov/privacy/ccpa",
        "source_type": "official_government_source",
        "checked_at": CHECKED_AT,
        "applies_to": ["legal_privacy_security_approval"],
        "project_use": "Future US/California user privacy expansion checklist; not a current approval substitute.",
    },
]


GATES: list[dict[str, Any]] = [
    {
        "gate_id": "real_external_expert_reviews",
        "name": "Real External Expert Reviews",
        "status": "blocked_waiting_for_real_named_reviewers",
        "owner": "founder",
        "why_project_needs_it": "AI-assisted reviews can reduce defects, but only real named reviewers can provide scoped approval evidence.",
        "required_reviewers_or_owners": [
            "UX/product usability reviewer",
            "application security reviewer",
            "privacy/legal reviewer",
            "AI safety/prompt-injection reviewer",
            "DevOps/production readiness reviewer",
            "trade/customs language reviewer",
            "freight/logistics reviewer when logistics claims are shown",
            "billing/payment reviewer before monetization",
        ],
        "required_evidence": [
            "reviewer identity, role, qualifications, and contact/channel record",
            "review scope tied to exact commit, package hash, URL, environment, and artifacts reviewed",
            "structured findings with severity, owner, required fix, retest command, and launch impact",
            "explicit decision value: approve_within_scope, block, needs_more_evidence, out_of_scope, or wrong_reviewer_type",
            "dated signoff or blocker record for each wave and role",
            "resolution evidence for every P0/P1 or explicit decision to keep the gate blocked",
        ],
        "required_data_fields": [
            "reviewer_name",
            "reviewer_role",
            "qualification_basis",
            "review_scope",
            "commit_sha",
            "package_sha256",
            "environment_url_or_local_path",
            "findings",
            "decision",
            "signed_at",
            "expires_or_refresh_rule",
        ],
        "approval_artifacts": [
            "external_review_findings/EXTERNAL_REVIEW_SUMMARY.json",
            "system_review_graph/external_review_findings_report.json",
            "system_review_graph/external_review_blocker_ledger.jsonl",
        ],
        "minimum_acceptance": "All required roles have dated scoped decisions; all P0/P1 findings are fixed, retested, or explicitly blocking.",
        "blocking_conditions": [
            "AI-only review is the only evidence",
            "reviewer identity or scope is missing",
            "reviewed commit/package differs from production candidate",
            "P0/P1 findings remain unresolved",
        ],
        "source_ids": ["owasp-llm01-prompt-injection", "owasp-asvs", "govuk-service-assessments"],
        "blocks_private_beta": True,
        "blocks_public_launch": True,
        "blocks_live_payment": True,
        "blocks_trade_claims": True,
        "refresh_rule": "Refresh after material code, policy, data-flow, hosting, payment, or claim-language changes.",
        "cannot_claim_until": "External review complete, scoped approvals attached, and blocker ledger has no unresolved launch-blocking rows.",
        "next_valid_move": "Send executive and technical packages to Wave 1 reviewers, record decisions, and convert every finding into a blocker row.",
    },
    {
        "gate_id": "legal_privacy_security_approval",
        "name": "Legal, Privacy, And Security Approval",
        "status": "blocked_waiting_for_qualified_approval",
        "owner": "privacy_security_owner",
        "why_project_needs_it": "The product processes customer trade documents and optional AI outputs, so data handling, claims, security, and incident duties need qualified review before hosted use.",
        "required_reviewers_or_owners": [
            "privacy/legal reviewer familiar with Canada and target customer jurisdictions",
            "application security reviewer",
            "security operations owner",
            "AI/data-processing owner",
        ],
        "required_evidence": [
            "privacy notice, terms/review-use terms, data retention/deletion policy, and AI data policy reviewed against actual flows",
            "data inventory with personal, commercial, customs, supplier, buyer, file-upload, AI, log, and payment metadata fields",
            "processor/subprocessor and vendor inventory with contracts or acceptance notes",
            "threat model covering PDF upload, prompt injection, data leakage, auth/RBAC, API routes, file storage, logs, and payment boundaries",
            "security scan results for dependencies, secrets, SAST/DAST/API checks, file upload controls, and auth/RBAC",
            "incident response, breach triage, notification, backup/restore, and deletion request evidence",
            "accessibility and safe-claims review for public pages and generated reports",
        ],
        "required_data_fields": [
            "reviewer_name",
            "law_or_standard_scope",
            "data_inventory_version",
            "privacy_notice_version",
            "terms_version",
            "processor_inventory",
            "security_test_results",
            "incident_response_owner",
            "approval_decision",
            "approval_limits",
            "signed_at",
        ],
        "approval_artifacts": [
            "docs/SECURITY_PRIVACY.md",
            "docs/AI_DATA_POLICY.md",
            "REDACTION_REPORT.md",
            "system_review_graph/ai_data_policy.json",
            "system_review_graph/public_upload_policy.json",
            "system_review_graph/auth_rbac_matrix.json",
        ],
        "minimum_acceptance": "Qualified reviewers approve scoped hosted beta data handling and security controls, with unresolved findings either fixed or blocking.",
        "blocking_conditions": [
            "privacy notice does not match actual data flows",
            "public upload malware/isolation/rate-limit proof missing",
            "AI provider or retention behavior is unreviewed",
            "incident/breach/deletion process has no owner",
            "secrets, auth, or storage proof is missing",
        ],
        "source_ids": [
            "opc-pipeda-principles",
            "opc-breach-reporting",
            "cccs-baseline-controls",
            "nist-csf-2",
            "cisa-secure-by-design",
            "owasp-file-upload",
            "owasp-asvs",
            "owasp-llm01-prompt-injection",
            "w3c-wcag-22",
            "california-ccpa",
        ],
        "blocks_private_beta": True,
        "blocks_public_launch": True,
        "blocks_live_payment": True,
        "blocks_trade_claims": False,
        "refresh_rule": "Refresh before hosted real-user data, public launch, payment activation, jurisdiction expansion, or any data-flow change.",
        "cannot_claim_until": "Qualified privacy/legal/security approvals are attached with exact scope and effective dates.",
        "next_valid_move": "Assemble the data map, threat model, upload controls proof, incident process, privacy notice, and AI processor inventory for qualified review.",
    },
    {
        "gate_id": "qualified_customs_trade_review",
        "name": "Qualified Customs And Trade Review",
        "status": "blocked_waiting_for_broker_or_trade_specialist",
        "owner": "trade_compliance_owner",
        "why_project_needs_it": "The product can route evidence, but it must not imply tariff, CFIA, sanctions, permit, or import/export readiness without qualified review.",
        "required_reviewers_or_owners": [
            "licensed customs broker or qualified customs/trade compliance specialist",
            "CFIA/commodity specialist for regulated food, plant, animal, or similar categories",
            "sanctions/export-controls reviewer for restricted destinations or parties",
            "freight/logistics reviewer for shipment or carrier claims",
        ],
        "required_evidence": [
            "product identity, composition, use, origin, seller/supplier, buyer, Incoterms, value, and documents reviewed",
            "HS/tariff classification basis with source links, assumptions, and confidence limits",
            "CBSA, CFIA AIRS, food licence, permit, quota, inspection, labelling, and country requirement checks where applicable",
            "restricted-party/sanctions screening source, timestamp, exact party names, jurisdictions, and result",
            "broker or qualified specialist decision on what the app may and may not say",
            "claim-language approval for generated reports, buyer packets, broker packets, and public pages",
        ],
        "required_data_fields": [
            "reviewer_name",
            "credential_or_company",
            "product_category",
            "hs_code_candidate",
            "origin_country",
            "destination_country",
            "official_sources_checked",
            "party_screening_record",
            "assumptions",
            "approved_claim_language",
            "blocked_claim_language",
            "signed_at",
        ],
        "approval_artifacts": [
            "system_review_graph/current_external_gate_research.json",
            "system_review_graph/country_coverage_report.json",
            "system_review_graph/transport_readiness_report.json",
            "system_review_graph/generated_reports/broker_packet_packet-frozen-tuna-canada-001.json",
        ],
        "minimum_acceptance": "Qualified reviewer approves only scoped source-routing language; no tariff/import/export advice claims open without explicit dated signoff.",
        "blocking_conditions": [
            "HS or tariff confidence is inferred by the app only",
            "AIRS/CFIA/source refresh is stale or absent",
            "restricted-party screening is missing",
            "reviewer is not qualified for commodity or jurisdiction",
            "report language implies customs advice or clearance",
        ],
        "source_ids": [
            "cbsa-commercial-import",
            "cbsa-customs-tariff",
            "cbsa-advance-rulings",
            "cfia-importing-food-plants-animals",
            "cfia-airs",
            "cfia-food-licences",
            "gac-sanctions",
            "gac-consolidated-sanctions-list",
            "gac-trade-controls",
        ],
        "blocks_private_beta": False,
        "blocks_public_launch": True,
        "blocks_live_payment": False,
        "blocks_trade_claims": True,
        "refresh_rule": "Refresh for every new commodity, origin/destination, source policy change, or claim-language change.",
        "cannot_claim_until": "Broker/trade specialist approval exists for the exact product category, jurisdiction, and claim text.",
        "next_valid_move": "Prepare one dated broker packet per sample packet and request scoped language approval from a qualified customs/trade reviewer.",
    },
    {
        "gate_id": "hosted_staging_production_proof",
        "name": "Hosted Staging And Production Proof",
        "status": "blocked_waiting_for_real_hosted_environment",
        "owner": "devops_owner",
        "why_project_needs_it": "Localhost proves local logic only. Real users require deployed environment proof for TLS, secrets, storage, logs, monitoring, rollback, backups, access, and abuse controls.",
        "required_reviewers_or_owners": [
            "DevOps/SRE reviewer",
            "application security reviewer",
            "privacy/security owner",
            "support/incident owner",
        ],
        "required_evidence": [
            "staging URL, commit SHA, image/build digest, deploy timestamp, environment variables inventory, and secret-source proof",
            "TLS/domain proof, security headers, CORS/CSRF/session cookie settings, and route exposure map",
            "database/storage isolation, upload quarantine, malware scanning, retention/deletion jobs, backup and restore drill",
            "health checks, structured logs, audit logs, monitoring alerts, error tracking, and uptime/rollback runbook",
            "load/rate-limit and abuse-path smoke tests for upload, public APIs, auth, reports, and deletion",
            "production promotion checklist with human approver and rollback owner",
        ],
        "required_data_fields": [
            "environment_name",
            "public_url",
            "commit_sha",
            "build_digest",
            "deployed_at",
            "secrets_store",
            "tls_evidence",
            "storage_evidence",
            "monitoring_links",
            "backup_restore_result",
            "rollback_result",
            "approver",
        ],
        "approval_artifacts": [
            "docs/DEPLOYMENT.md",
            "system_review_graph/deployment_readiness_report.json",
            "system_review_graph/product_runtime_state.json",
            "system_review_graph/private_beta_smoke_test_plan.json",
        ],
        "minimum_acceptance": "A reachable staging environment passes smoke, security, privacy, backup/restore, observability, and rollback proof without real customer data leakage.",
        "blocking_conditions": [
            "only localhost proof exists",
            "production secrets or storage isolation are unverified",
            "uploads are publicly reachable or not quarantined",
            "logs contain sensitive document content",
            "backup/restore or rollback is untested",
        ],
        "source_ids": ["cccs-baseline-controls", "nist-csf-2", "cisa-secure-by-design", "owasp-file-upload", "owasp-asvs", "stripe-webhooks"],
        "blocks_private_beta": True,
        "blocks_public_launch": True,
        "blocks_live_payment": True,
        "blocks_trade_claims": False,
        "refresh_rule": "Refresh for every deployment platform, infrastructure, secret, storage, auth, logging, upload, or payment integration change.",
        "cannot_claim_until": "Staging and production-candidate proof exists with named human promotion and rollback approval.",
        "next_valid_move": "Provision staging, deploy exact commit, run smoke/security/upload/privacy/backup/rollback checks, and attach evidence.",
    },
    {
        "gate_id": "live_payment_activation",
        "name": "Live Payment Activation",
        "status": "blocked_waiting_for_payment_account_and_policy_proof",
        "owner": "billing_owner",
        "why_project_needs_it": "Pricing pages and billing ledgers are local-only; live charges need payment account configuration, tax/refund/support decisions, security, and webhook proof.",
        "required_reviewers_or_owners": [
            "billing/payment owner",
            "privacy/security owner",
            "tax/accounting reviewer where applicable",
            "support/refund owner",
        ],
        "required_evidence": [
            "Stripe live-mode account, business profile, domain, payment methods, product/price IDs, and checkout links reviewed",
            "webhook endpoint, signing secret, event delivery, idempotency, retry, failure, refund, dispute, and cancellation tests",
            "tax/VAT/GST/sales-tax decision record and invoice/receipt language",
            "terms, refund policy, support contact, complaint handling, chargeback, and account access controls",
            "test-mode proof followed by live penny/low-risk transaction or Stripe-approved live proof if appropriate",
            "explicit monetization go/no-go decision that does not imply trade/customs/legal advice",
        ],
        "required_data_fields": [
            "stripe_account_mode",
            "product_ids",
            "price_ids",
            "checkout_urls",
            "webhook_endpoint",
            "webhook_event_log",
            "tax_decision_record",
            "refund_policy_version",
            "support_contact",
            "test_results",
            "live_activation_approver",
            "activated_at",
        ],
        "approval_artifacts": [
            "system_review_graph/billing_credit_controls.json",
            "system_review_graph/billing_usage_ledger.json",
            "system_review_graph/claims_gate_matrix.json",
        ],
        "minimum_acceptance": "Live payment remains disabled until checkout, webhook, tax, refund, support, security, and account controls are approved in scope.",
        "blocking_conditions": [
            "test-mode only proof exists",
            "webhook signing/retry/idempotency proof is missing",
            "tax/refund/support terms are undecided",
            "pricing implies legal/customs/trade outcome guarantees",
            "payment account access controls are unreviewed",
        ],
        "source_ids": ["stripe-go-live", "stripe-webhooks", "stripe-testing", "stripe-security"],
        "blocks_private_beta": False,
        "blocks_public_launch": True,
        "blocks_live_payment": True,
        "blocks_trade_claims": False,
        "refresh_rule": "Refresh for pricing, plan, tax, support, refund, Stripe account, webhook, or claim-language changes.",
        "cannot_claim_until": "Live checkout, billing policy, tax/refund/support, and webhook proof are attached with a named activation approver.",
        "next_valid_move": "Keep live checkout disabled; complete Stripe live-mode configuration and payment policy proof after staged security/privacy approval.",
    },
    {
        "gate_id": "real_users_private_beta_outcomes",
        "name": "Real Users And Private Beta Outcomes",
        "status": "blocked_waiting_for_real_user_sessions",
        "owner": "product_research_owner",
        "why_project_needs_it": "The product needs evidence that target users can complete the flow and understand blocked claims before public launch.",
        "required_reviewers_or_owners": [
            "product/UX research owner",
            "support owner",
            "privacy/security owner for beta data handling",
            "founder or beta program owner",
        ],
        "required_evidence": [
            "recruiting criteria, consent, participant segment, date, session notes, and task recordings/observations where permitted",
            "at least five target-user task attempts covering no-document starter flow, PDF quick check, report download, blocked-claims comprehension, and deletion",
            "critical issue list with severity, owner, fix, retest result, and launch impact",
            "support/contact outcomes, misunderstood claims, privacy concerns, and trust objections",
            "measured outcomes: task completion, time to first result, unsafe misunderstanding count, deletion success, report usefulness, and willingness-to-continue",
            "private beta summary with go/no-go recommendation and unresolved blockers",
        ],
        "required_data_fields": [
            "participant_id",
            "segment",
            "consent_record",
            "tasks_attempted",
            "task_completion",
            "misunderstood_claims",
            "issues_found",
            "support_events",
            "privacy_or_security_concerns",
            "willingness_signal",
            "retest_result",
            "beta_decision",
        ],
        "approval_artifacts": [
            "system_review_graph/private_beta_smoke_test_plan.json",
            "system_review_graph/customer_readiness_report.json",
            "system_review_graph/audit_events.json",
        ],
        "minimum_acceptance": "Five or more representative users complete core tasks without unsafe claim misunderstanding, unresolved P0/P1 issues, or privacy/security incidents.",
        "blocking_conditions": [
            "no real users have used hosted staging/private beta",
            "participants are not target users",
            "user confusion causes customs/legal/payment overclaiming",
            "P0/P1 product or trust issues remain unresolved",
            "privacy/security consent and deletion proof is missing",
        ],
        "source_ids": ["govuk-user-research", "govuk-service-standard", "nng-five-users", "yc-talk-to-users", "w3c-wcag-22"],
        "blocks_private_beta": True,
        "blocks_public_launch": True,
        "blocks_live_payment": False,
        "blocks_trade_claims": False,
        "refresh_rule": "Refresh after major UX, flow, claim-language, pricing, data-handling, or target-segment changes.",
        "cannot_claim_until": "Real user session evidence proves target users can complete the flow and understand its blocked-safe boundaries.",
        "next_valid_move": "After Wave 1 and staging proof, run five structured private-beta sessions and convert every issue into a blocker or fixed proof row.",
    },
    {
        "gate_id": "buyer_supplier_validation",
        "name": "Buyer And Supplier Validation",
        "status": "blocked_waiting_for_real_market_counterparties",
        "owner": "commercial_validation_owner",
        "why_project_needs_it": "A readiness checker is not commercially validated until real buyers, suppliers, importers/exporters, or advisors show the workflow solves a real decision problem.",
        "required_reviewers_or_owners": [
            "founder or commercial validation owner",
            "target importer/exporter buyer persona",
            "supplier or broker/forwarder persona",
            "trade compliance reviewer for claims made during validation",
        ],
        "required_evidence": [
            "customer/buyer/supplier interview notes tied to a segment, use case, urgency, current workaround, and willingness signal",
            "named design partners or beta candidates with permission to store contact and validation outcome",
            "source packet or document sample supplied by a real counterparty or explicitly anonymized with permission",
            "buyer/supplier pain ranking, requested workflow, price/value signal, and objections",
            "counterparty legitimacy and sanctions/restricted-party screening where any transaction/recommendation could be implied",
            "clear separation between validation, recommendation, referral, and commercial matchmaking claims",
        ],
        "required_data_fields": [
            "counterparty_id",
            "role",
            "company_or_context",
            "permission_scope",
            "problem_statement",
            "current_workaround",
            "documents_shared",
            "willingness_signal",
            "price_signal",
            "objections",
            "screening_result",
            "followup_commitment",
        ],
        "approval_artifacts": [
            "system_review_graph/opportunity_scanner_report.json",
            "system_review_graph/research_execution_plan.json",
            "system_review_graph/team_workspace_report.json",
        ],
        "minimum_acceptance": "Multiple target counterparties validate a real workflow and no generated content implies supplier recommendation, buyer validation, or transaction readiness.",
        "blocking_conditions": [
            "validation is hypothetical or AI-generated",
            "no named target segment or counterparty exists",
            "documents were used without permission",
            "supplier or buyer is implied as verified without screening/review",
            "no willingness, urgency, or follow-up signal is recorded",
        ],
        "source_ids": ["yc-talk-to-users", "gac-sanctions", "gac-consolidated-sanctions-list", "govuk-user-research"],
        "blocks_private_beta": False,
        "blocks_public_launch": True,
        "blocks_live_payment": False,
        "blocks_trade_claims": True,
        "refresh_rule": "Refresh for new segments, countries, commodities, pricing, buyer/supplier features, or matchmaking/referral claims.",
        "cannot_claim_until": "Real counterparties and design partners provide dated validation, with screening and claim boundaries attached.",
        "next_valid_move": "Run structured interviews with target importers/exporters/brokers and record the evidence without opening recommendation claims.",
    },
    {
        "gate_id": "public_go_no_go_approval",
        "name": "Public Go/No-Go Approval",
        "status": "blocked_waiting_for_named_decision_owner",
        "owner": "launch_decision_owner",
        "why_project_needs_it": "Public launch should be a controlled decision using actual evidence, rollback/support plans, and explicit unresolved-risk acceptance.",
        "required_reviewers_or_owners": [
            "founder or accountable launch owner",
            "privacy/legal approver",
            "security/operations approver",
            "product/beta approver",
            "trade-claims approver",
            "billing/support approver when monetization is enabled",
        ],
        "required_evidence": [
            "release candidate commit, deployment URL, package hashes, environment proof, and smoke results",
            "all gate statuses with evidence links, unresolved blockers, accepted risks, and explicit no-go conditions",
            "support runbook, incident response, refund/payment support, abuse handling, deletion request process, and owner rota",
            "claims matrix proving public pages, reports, AI summaries, pricing, and packets do not overclaim",
            "rollback plan, communications plan, monitoring dashboard, analytics/privacy setting, and launch freeze window",
            "signed public go/no-go record with date, scope, owner, decision, caveats, and next review date",
        ],
        "required_data_fields": [
            "release_candidate_commit",
            "production_url",
            "package_hashes",
            "gate_statuses",
            "unresolved_blockers",
            "accepted_risks",
            "rollback_owner",
            "support_owner",
            "launch_scope",
            "decision",
            "approver",
            "decided_at",
        ],
        "approval_artifacts": [
            "system_review_graph/final_go_live_decision_report.json",
            "system_review_graph/launch_operations_report.json",
            "system_review_graph/claims_gate_matrix.json",
            "board/launch_control_checklist.md",
        ],
        "minimum_acceptance": "Named owner approves a specific public scope after all required external gates are approved or explicitly no-go.",
        "blocking_conditions": [
            "any required gate has missing or simulated-only evidence",
            "launch owner is unnamed",
            "support, rollback, incident, or deletion process is unstaffed",
            "public pages or reports still imply blocked claims",
            "payment, trade, privacy, or security approval scope is unclear",
        ],
        "source_ids": ["govuk-service-standard", "govuk-service-assessments", "nist-csf-2", "w3c-wcag-22"],
        "blocks_private_beta": False,
        "blocks_public_launch": True,
        "blocks_live_payment": True,
        "blocks_trade_claims": True,
        "refresh_rule": "Required for every public launch, major product change, new market/jurisdiction, pricing activation, or claim expansion.",
        "cannot_claim_until": "A named launch owner signs a dated go decision after reviewing all evidence and unresolved risks.",
        "next_valid_move": "Do not hold public go/no-go until the other seven gates have real evidence; keep launch state blocked-safe.",
    },
]


PROJECT_REQUIRED_DATA_CATALOG: list[dict[str, Any]] = [
    {
        "category_id": "business_identity_and_contacts",
        "owner": "founder",
        "minimum_fields": ["legal_entity_or_solo_operator_label", "domain", "support_contact", "privacy_contact", "security_contact", "billing_contact"],
        "storage_artifact": "system_review_graph/external_validation_requirements_report.json",
        "refresh_rule": "Refresh before public launch, payment activation, or support-policy change.",
        "blocks": ["public_go_no_go_approval", "live_payment_activation", "legal_privacy_security_approval"],
    },
    {
        "category_id": "product_scope_and_claim_boundaries",
        "owner": "product_owner",
        "minimum_fields": ["public_product_name", "internal_engine_name", "allowed_claims", "blocked_claims", "target_users", "target_jurisdictions"],
        "storage_artifact": "system_review_graph/claims_gate_matrix.json",
        "refresh_rule": "Refresh for any feature, report, page, or claim-language change.",
        "blocks": ["qualified_customs_trade_review", "public_go_no_go_approval"],
    },
    {
        "category_id": "official_source_registry",
        "owner": "research_owner",
        "minimum_fields": ["source_id", "publisher", "url", "checked_at", "jurisdiction", "claim_boundary", "refresh_due_at"],
        "storage_artifact": "data/official_source_registry.json",
        "refresh_rule": "Refresh before external review, before launch, and after detected source changes.",
        "blocks": ["qualified_customs_trade_review", "buyer_supplier_validation", "public_go_no_go_approval"],
    },
    {
        "category_id": "customer_document_and_upload_data",
        "owner": "privacy_security_owner",
        "minimum_fields": ["file_id", "filename", "mime_type", "size", "storage_path", "quarantine_state", "malware_scan_state", "retention_until", "delete_status"],
        "storage_artifact": "system_review_graph/public_upload_manifest.json",
        "refresh_rule": "Refresh whenever upload, storage, scanning, or deletion flow changes.",
        "blocks": ["legal_privacy_security_approval", "hosted_staging_production_proof"],
    },
    {
        "category_id": "ai_data_processing_and_redaction",
        "owner": "ai_data_owner",
        "minimum_fields": ["model_route", "input_categories", "redaction_result", "user_permission", "retention_mode", "provider", "manual_fallback"],
        "storage_artifact": "system_review_graph/ai_data_policy.json",
        "refresh_rule": "Refresh when model provider, prompt, redaction, data permission, or retention mode changes.",
        "blocks": ["legal_privacy_security_approval", "real_external_expert_reviews"],
    },
    {
        "category_id": "privacy_legal_records",
        "owner": "privacy_legal_owner",
        "minimum_fields": ["privacy_notice_version", "terms_version", "consent_record", "retention_policy", "deletion_request", "processor_inventory", "breach_process"],
        "storage_artifact": "docs/SECURITY_PRIVACY.md",
        "refresh_rule": "Refresh before real user data collection, jurisdiction expansion, and public launch.",
        "blocks": ["legal_privacy_security_approval", "public_go_no_go_approval"],
    },
    {
        "category_id": "security_operational_records",
        "owner": "security_owner",
        "minimum_fields": ["threat_model", "scan_results", "auth_rbac", "secrets_inventory", "audit_logs", "backup_restore", "incident_response", "vulnerability_process"],
        "storage_artifact": "system_review_graph/deployment_readiness_report.json",
        "refresh_rule": "Refresh for every hosted deploy, security-impacting change, and incident.",
        "blocks": ["legal_privacy_security_approval", "hosted_staging_production_proof", "public_go_no_go_approval"],
    },
    {
        "category_id": "hosted_environment_records",
        "owner": "devops_owner",
        "minimum_fields": ["environment", "url", "commit_sha", "build_digest", "tls", "secrets_store", "database", "storage", "logs", "monitoring", "rollback"],
        "storage_artifact": "system_review_graph/deployment_readiness_report.json",
        "refresh_rule": "Refresh for every staging/production deploy and infrastructure change.",
        "blocks": ["hosted_staging_production_proof", "real_users_private_beta_outcomes", "public_go_no_go_approval"],
    },
    {
        "category_id": "trade_customs_records",
        "owner": "trade_compliance_owner",
        "minimum_fields": ["product_category", "hs_code_candidate", "origin", "destination", "official_sources", "broker_review", "cfia_airs_result", "permit_result", "claim_language"],
        "storage_artifact": "system_review_graph/country_coverage_report.json",
        "refresh_rule": "Refresh per commodity, country pair, policy/source update, and report-language change.",
        "blocks": ["qualified_customs_trade_review", "buyer_supplier_validation", "public_go_no_go_approval"],
    },
    {
        "category_id": "sanctions_and_party_screening",
        "owner": "trade_compliance_owner",
        "minimum_fields": ["party_name", "party_role", "jurisdiction", "screening_source", "screened_at", "result", "reviewer", "followup_required"],
        "storage_artifact": "system_review_graph/external_validation_evidence_requirements.json",
        "refresh_rule": "Refresh before any buyer/supplier validation that could imply transaction readiness.",
        "blocks": ["qualified_customs_trade_review", "buyer_supplier_validation"],
    },
    {
        "category_id": "payment_billing_records",
        "owner": "billing_owner",
        "minimum_fields": ["account_mode", "product_ids", "price_ids", "checkout_url", "webhook_events", "tax_decision", "refund_policy", "support_contact", "activation_decision"],
        "storage_artifact": "system_review_graph/billing_credit_controls.json",
        "refresh_rule": "Refresh for every pricing, plan, tax, refund, support, or Stripe configuration change.",
        "blocks": ["live_payment_activation", "public_go_no_go_approval"],
    },
    {
        "category_id": "private_beta_user_outcomes",
        "owner": "product_research_owner",
        "minimum_fields": ["participant_segment", "consent", "tasks", "completion", "issues", "trust_objections", "misunderstood_claims", "support_events", "decision"],
        "storage_artifact": "system_review_graph/private_beta_smoke_test_plan.json",
        "refresh_rule": "Refresh after major UX, claims, data-flow, or pricing changes.",
        "blocks": ["real_users_private_beta_outcomes", "public_go_no_go_approval"],
    },
    {
        "category_id": "buyer_supplier_validation_records",
        "owner": "commercial_validation_owner",
        "minimum_fields": ["counterparty_role", "permission_scope", "problem", "current_workaround", "documents_shared", "willingness_signal", "objections", "screening_result"],
        "storage_artifact": "system_review_graph/team_workspace_report.json",
        "refresh_rule": "Refresh for every new segment, commodity, market, pricing tier, or recommendation-like feature.",
        "blocks": ["buyer_supplier_validation", "qualified_customs_trade_review", "public_go_no_go_approval"],
    },
    {
        "category_id": "support_incident_and_deletion_records",
        "owner": "support_owner",
        "minimum_fields": ["support_contact", "triage_sla", "incident_owner", "breach_process", "deletion_request", "refund_process", "abuse_process", "escalation_path"],
        "storage_artifact": "system_review_graph/launch_operations_report.json",
        "refresh_rule": "Refresh before hosted beta, payment activation, and public launch.",
        "blocks": ["hosted_staging_production_proof", "legal_privacy_security_approval", "public_go_no_go_approval"],
    },
    {
        "category_id": "accessibility_and_content_quality",
        "owner": "product_owner",
        "minimum_fields": ["keyboard_check", "screen_reader_check", "contrast_check", "form_error_check", "plain_language_review", "blocked_claims_comprehension"],
        "storage_artifact": "system_review_graph/external_validation_requirements_report.json",
        "refresh_rule": "Refresh before public launch and after UI/report changes.",
        "blocks": ["real_users_private_beta_outcomes", "public_go_no_go_approval"],
    },
    {
        "category_id": "public_launch_decision_records",
        "owner": "launch_decision_owner",
        "minimum_fields": ["release_commit", "production_url", "gate_statuses", "unresolved_blockers", "accepted_risks", "rollback_plan", "support_plan", "decision", "approver"],
        "storage_artifact": "system_review_graph/final_go_live_decision_report.json",
        "refresh_rule": "Required for every public release, material feature change, market expansion, or claim expansion.",
        "blocks": ["public_go_no_go_approval"],
    },
]


REVIEWER_QUALIFICATION_MATRIX: list[dict[str, Any]] = [
    {
        "role": "customs_trade_reviewer",
        "acceptable_qualification": "Licensed customs broker, trade compliance specialist, or commodity/jurisdiction expert for the reviewed scope.",
        "must_review": ["broker packets", "official source registry", "HS/tariff assumptions", "CFIA/AIRS/permit checks", "claim language"],
        "not_acceptable_alone": ["AI review", "generic web search", "founder opinion", "unqualified buyer feedback"],
    },
    {
        "role": "privacy_legal_reviewer",
        "acceptable_qualification": "Privacy/legal professional or qualified compliance advisor for the target jurisdiction and data flows.",
        "must_review": ["privacy notice", "terms", "data map", "processor inventory", "retention/deletion", "breach process", "AI data policy"],
        "not_acceptable_alone": ["template policy", "AI-generated legal text", "privacy page without data-flow proof"],
    },
    {
        "role": "application_security_reviewer",
        "acceptable_qualification": "Application security practitioner able to review upload, auth, API, AI, and deployment threats.",
        "must_review": ["threat model", "file upload controls", "auth/RBAC", "dependency/secret scans", "LLM prompt injection controls", "logs/storage"],
        "not_acceptable_alone": ["unit tests only", "localhost smoke only", "no-scan manual clickthrough"],
    },
    {
        "role": "devops_sre_reviewer",
        "acceptable_qualification": "Operator able to validate hosted deploy, observability, backup, rollback, incident, and access controls.",
        "must_review": ["staging URL", "commit/build digest", "TLS/secrets", "monitoring", "backup/restore", "rollback", "support handoff"],
        "not_acceptable_alone": ["Dockerfile exists", "app runs locally", "deploy docs without live environment"],
    },
    {
        "role": "payment_billing_reviewer",
        "acceptable_qualification": "Payment/billing owner or advisor who can validate Stripe live-mode, tax/refund/support, and access controls.",
        "must_review": ["live account configuration", "products/prices", "webhooks", "tax/refund/support", "receipt language", "billing claims"],
        "not_acceptable_alone": ["pricing page exists", "test-mode checkout only", "manual ledger only"],
    },
    {
        "role": "product_ux_researcher",
        "acceptable_qualification": "Researcher or product owner able to run structured target-user sessions and report outcomes.",
        "must_review": ["task scripts", "participant criteria", "consent", "task completion", "claim comprehension", "issue severity"],
        "not_acceptable_alone": ["founder self-test", "AI persona test", "screenshots without users"],
    },
    {
        "role": "launch_decision_owner",
        "acceptable_qualification": "Named accountable owner who can accept residual risk and stop launch if evidence is incomplete.",
        "must_review": ["all gate evidence", "unresolved blockers", "support and rollback", "public claims", "decision scope"],
        "not_acceptable_alone": ["implicit approval", "passing tests", "pushed commit", "simulated board review"],
    },
]


COLLECTION_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_id": "external_review_decision_record",
        "required_fields": ["reviewer_name", "role", "qualification_basis", "scope", "commit_sha", "package_sha256", "findings", "decision", "signed_at"],
        "valid_decisions": ["approve_within_scope", "block", "needs_more_evidence", "out_of_scope", "wrong_reviewer_type"],
    },
    {
        "template_id": "legal_privacy_security_approval_record",
        "required_fields": ["approver", "scope", "privacy_notice_version", "data_map_version", "security_tests", "approved_controls", "unresolved_findings", "decision", "signed_at"],
        "valid_decisions": ["approve_hosted_beta", "approve_public_launch", "block", "needs_more_evidence"],
    },
    {
        "template_id": "customs_trade_review_record",
        "required_fields": ["reviewer", "credential", "product_category", "hs_code_candidate", "origin", "destination", "official_sources", "assumptions", "approved_claims", "blocked_claims", "decision"],
        "valid_decisions": ["approve_language_only", "approve_specific_packet", "block", "needs_more_evidence"],
    },
    {
        "template_id": "hosted_environment_proof_record",
        "required_fields": ["environment", "url", "commit_sha", "build_digest", "tls", "secrets", "storage", "logs", "monitoring", "backup_restore", "rollback", "smoke_result", "approver"],
        "valid_decisions": ["approve_staging_beta", "approve_production_candidate", "block", "needs_more_evidence"],
    },
    {
        "template_id": "payment_activation_record",
        "required_fields": ["stripe_mode", "product_ids", "price_ids", "checkout_url", "webhook_events", "tax_decision", "refund_policy", "support_contact", "test_result", "activation_decision"],
        "valid_decisions": ["activate_live_checkout", "keep_disabled", "block", "needs_more_evidence"],
    },
    {
        "template_id": "private_beta_outcome_record",
        "required_fields": ["participant_id", "segment", "consent", "tasks", "completion", "issues", "misunderstood_claims", "support_events", "privacy_concerns", "decision"],
        "valid_decisions": ["continue_beta", "expand_beta", "block_public_launch", "needs_more_evidence"],
    },
    {
        "template_id": "buyer_supplier_validation_record",
        "required_fields": ["counterparty_id", "role", "permission_scope", "problem", "current_workaround", "documents_shared", "willingness_signal", "price_signal", "objections", "screening_result"],
        "valid_decisions": ["validated_problem", "validated_design_partner", "not_validated", "needs_more_evidence"],
    },
    {
        "template_id": "public_go_no_go_record",
        "required_fields": ["release_commit", "production_url", "gate_statuses", "unresolved_blockers", "accepted_risks", "support_owner", "rollback_owner", "decision", "approver", "decided_at"],
        "valid_decisions": ["go_with_scope", "no_go", "go_after_blockers", "needs_more_evidence"],
    },
]


LAUNCH_READINESS_SEQUENCE: list[dict[str, Any]] = [
    {"order": 1, "phase": "local_contract", "required_state": "local app, reports, proof scripts, and blocker ledgers pass"},
    {"order": 2, "phase": "external_validation_requirements", "required_state": "this requirements pack generated and checked"},
    {"order": 3, "phase": "wave_1_external_review", "required_state": "UX, security, privacy/legal, AI safety, and DevOps reviewers decide"},
    {"order": 4, "phase": "staging_environment", "required_state": "real hosted staging with security, privacy, backup, rollback, and upload proof"},
    {"order": 5, "phase": "private_beta", "required_state": "five-plus target users complete core tasks without unsafe misunderstandings"},
    {"order": 6, "phase": "trade_and_commercial_validation", "required_state": "qualified trade review and real buyer/supplier validation attach scoped evidence"},
    {"order": 7, "phase": "payment_activation", "required_state": "Stripe live-mode, webhook, tax/refund/support, and billing claim approval attach"},
    {"order": 8, "phase": "production_candidate_review", "required_state": "production candidate deploy, monitoring, support, incident, deletion, and rollback proof attach"},
    {"order": 9, "phase": "public_go_no_go", "required_state": "named owner signs go/no-go with unresolved risks and scope"},
]

GO_LIVE_INPUT_REQUESTS: list[dict[str, Any]] = [
    {
        "review_area": "real_external_expert_reviews",
        "plain_title": "Outside Expert Review",
        "who_to_ask": "Product, security, privacy/legal, AI safety, operations, trade, and payment reviewers as relevant.",
        "simple_question": "Have the right outside reviewers checked the right scope?",
        "ready_answer": "Ready for my area",
        "minimum_input": ["reviewer name", "reviewed scope", "decision", "top issues", "missing evidence", "signed date"],
    },
    {
        "review_area": "legal_privacy_security_approval",
        "plain_title": "Legal, Privacy, And Security",
        "who_to_ask": "Privacy/legal reviewer plus application security reviewer.",
        "simple_question": "Is customer data handling, security, AI use, retention, deletion, and incident handling acceptable for the launch scope?",
        "ready_answer": "Ready for my area",
        "minimum_input": ["reviewer name", "data/privacy scope", "security scope", "decision", "missing evidence", "signed date"],
    },
    {
        "review_area": "qualified_customs_trade_review",
        "plain_title": "Customs And Trade Language",
        "who_to_ask": "Licensed customs broker or qualified trade/compliance reviewer.",
        "simple_question": "Does the product avoid unsupported customs, tariff, CFIA, sanctions, and trade-readiness claims?",
        "ready_answer": "Ready for my area or not applicable for this launch",
        "minimum_input": ["reviewer name", "country/product scope", "approved wording", "wording to avoid", "decision", "signed date"],
    },
    {
        "review_area": "hosted_staging_production_proof",
        "plain_title": "Hosted Staging Or Production",
        "who_to_ask": "DevOps, SRE, or operations owner.",
        "simple_question": "Is there real hosted evidence for the launch scope, not only localhost?",
        "ready_answer": "Ready for my area",
        "minimum_input": ["environment URL", "commit/build", "smoke result", "monitoring", "rollback owner", "decision", "signed date"],
    },
    {
        "review_area": "live_payment_activation",
        "plain_title": "Payments",
        "who_to_ask": "Billing/payment owner, tax/accounting advisor if needed, and support owner.",
        "simple_question": "Are live checkout, webhook, tax/refund/support, and billing wording ready, or is payment intentionally off for launch?",
        "ready_answer": "Ready for my area or not applicable for this launch",
        "minimum_input": ["payment scope", "Stripe mode", "webhook evidence", "refund/support owner", "decision", "signed date"],
    },
    {
        "review_area": "real_users_private_beta_outcomes",
        "plain_title": "Real User Feedback",
        "who_to_ask": "Product/UX owner or user research owner.",
        "simple_question": "Have real target users used the product and understood what is and is not approved?",
        "ready_answer": "Ready for my area",
        "minimum_input": ["participant count", "segments", "task results", "top issues", "what changed", "decision", "signed date"],
    },
    {
        "review_area": "buyer_supplier_validation",
        "plain_title": "Buyer Or Supplier Validation",
        "who_to_ask": "Founder or commercial validation owner.",
        "simple_question": "Have real buyers, suppliers, importers, exporters, or advisors validated the problem and workflow?",
        "ready_answer": "Ready for my area or not applicable for this launch",
        "minimum_input": ["counterparty type", "problem validated", "evidence summary", "permission scope", "decision", "signed date"],
    },
    {
        "review_area": "public_go_no_go_approval",
        "plain_title": "Final Go Live Decision",
        "who_to_ask": "Named launch owner.",
        "simple_question": "After all other inputs are in, is this launch approved for the exact stated scope?",
        "ready_answer": "Go for public launch",
        "minimum_input": ["launch scope", "production URL", "remaining risks", "support owner", "rollback owner", "decision", "signed date"],
    },
]

READY_INPUT_DECISIONS = {"ready_for_my_area", "not_applicable_for_this_launch", "go_for_public_launch"}
HUMAN_READY_INPUT_DECISIONS = [
    "ready_for_my_area",
    "not_ready_yet",
    "need_more_evidence",
    "not_my_area",
    "send_to_different_reviewer",
    "not_applicable_for_this_launch",
    "go_for_public_launch",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_ids() -> set[str]:
    return {row["source_id"] for row in SOURCE_ANCHORS}


def build_evidence_requirements() -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for gate in GATES:
        for index, artifact in enumerate(gate["required_evidence"], start=1):
            requirements.append(
                {
                    "evidence_id": f"{gate['gate_id']}:E{index:02d}",
                    "gate_id": gate["gate_id"],
                    "artifact_or_record": artifact,
                    "owner": gate["owner"],
                    "reviewer_or_source": gate["required_reviewers_or_owners"],
                    "required_fields": gate["required_data_fields"],
                    "acceptance_test": gate["minimum_acceptance"],
                    "expires_or_refresh_rule": gate["refresh_rule"],
                    "blocks_private_beta": gate["blocks_private_beta"],
                    "blocks_public_launch": gate["blocks_public_launch"],
                    "blocks_live_payment": gate["blocks_live_payment"],
                    "blocks_trade_claims": gate["blocks_trade_claims"],
                    "next_valid_move": gate["next_valid_move"],
                }
            )
    return requirements


def validate_external_validation_requirements(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("status") != STATUS:
        errors.append(f"unexpected status: {payload.get('status')!r}")
    if payload.get("gate_count") != len(GATE_IDS):
        errors.append("unexpected gate count")
    if payload.get("public_launch_ready") is not False:
        errors.append("public launch must remain false")
    if payload.get("hosted_private_beta_ready") is not False:
        errors.append("hosted private beta must remain false")
    if payload.get("live_payment_ready") is not False:
        errors.append("live payment must remain false")
    if payload.get("real_world_external_evidence_received") is not False:
        errors.append("real-world evidence must remain false until attached")
    source_ids = {row.get("source_id") for row in payload.get("source_anchors", [])}
    for required in ("cbsa-commercial-import", "cfia-airs", "opc-pipeda-principles", "owasp-file-upload", "stripe-go-live", "govuk-user-research"):
        if required not in source_ids:
            errors.append(f"missing source anchor {required}")
    if len(source_ids) < 24:
        errors.append("source anchor count is too small for full project gates")
    gate_ids = [row.get("gate_id") for row in payload.get("gates", [])]
    if gate_ids != GATE_IDS:
        errors.append("gate IDs or ordering changed unexpectedly")
    for gate in payload.get("gates", []):
        if not str(gate.get("status", "")).startswith("blocked_"):
            errors.append(f"gate {gate.get('gate_id')} is not blocked")
        for key in ("required_reviewers_or_owners", "required_evidence", "required_data_fields", "minimum_acceptance", "cannot_claim_until", "next_valid_move"):
            if not gate.get(key):
                errors.append(f"gate {gate.get('gate_id')} missing {key}")
        for source_id in gate.get("source_ids", []):
            if source_id not in source_ids:
                errors.append(f"gate {gate.get('gate_id')} references unknown source {source_id}")
    if payload.get("required_data_category_count", 0) < 14:
        errors.append("required data catalog should cover the full project lifecycle")
    if payload.get("evidence_requirement_count", 0) < 44:
        errors.append("evidence requirement count is too small")
    unacceptable = {
        item
        for role in payload.get("reviewer_qualification_matrix", [])
        for item in role.get("not_acceptable_alone", [])
    }
    if "AI review" not in unacceptable and "AI-generated legal text" not in unacceptable:
        errors.append("reviewer matrix must reject AI-only approval")
    return errors


def build_external_validation_requirements(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    evidence_requirements = build_evidence_requirements()
    source_ids = _source_ids()
    unknown_sources = sorted(
        {
            source_id
            for gate in GATES
            for source_id in gate["source_ids"]
            if source_id not in source_ids
        }
    )
    payload = {
        "status": STATUS,
        "generated_at": generated_at,
        "checked_at": CHECKED_AT,
        "project": "Trade Readiness Copilot / Importer Source Readiness Copilot",
        "scope": "Complete real-world evidence requirements for private beta, public launch, payments, trade/customs claims, and commercial validation.",
        "gate_count": len(GATES),
        "gate_ids": GATE_IDS,
        "source_count": len(SOURCE_ANCHORS),
        "evidence_requirement_count": len(evidence_requirements),
        "required_data_category_count": len(PROJECT_REQUIRED_DATA_CATALOG),
        "reviewer_role_count": len(REVIEWER_QUALIFICATION_MATRIX),
        "collection_template_count": len(COLLECTION_TEMPLATES),
        "requirements_are_complete_for_current_product_scope": True,
        "real_world_external_evidence_received": False,
        "public_launch_ready": False,
        "hosted_private_beta_ready": False,
        "live_payment_ready": False,
        "qualified_trade_claims_ready": False,
        "buyer_supplier_validation_ready": False,
        "simulated_ai_review_can_open_gate": False,
        "unknown_source_ids": unknown_sources,
        "source_anchors": SOURCE_ANCHORS,
        "gates": GATES,
        "evidence_requirements": evidence_requirements,
        "required_data_catalog": PROJECT_REQUIRED_DATA_CATALOG,
        "reviewer_qualification_matrix": REVIEWER_QUALIFICATION_MATRIX,
        "collection_templates": COLLECTION_TEMPLATES,
        "launch_readiness_sequence": LAUNCH_READINESS_SEQUENCE,
        "requirements_need_refresh_when": [
            "new country, commodity, buyer/supplier segment, or regulated product category is added",
            "hosted infrastructure, data flow, upload handling, AI provider, payment setup, or claim language changes",
            "privacy/security/trade/payment source changes are detected",
            "public launch, live checkout, private beta expansion, or market expansion is considered",
        ],
        "unsafe_shortcuts_rejected": [
            "AI-assisted simulated review as approval",
            "localhost proof as hosted production proof",
            "Stripe test mode as live payment activation",
            "generic web search as legal/privacy/security/customs approval",
            "founder self-test as real user validation",
            "buyer interest as buyer validation without dated evidence and claim boundaries",
        ],
        "next_valid_move": "Use this pack as the master evidence intake checklist; attach real records one gate at a time and keep all gates closed until evidence exists.",
        "proof_boundary": (
            "This artifact gathers requirements and current source anchors. It does not prove any external approval, legal/privacy/security signoff, "
            "qualified customs/trade review, hosted production proof, live payment activation, private-beta outcome, buyer/supplier validation, or public go/no-go."
        ),
    }
    validation_errors = validate_external_validation_requirements(payload)
    if validation_errors:
        payload["status"] = "external_validation_requirements_invalid"
        payload["validation_errors"] = validation_errors
    return payload


def build_evidence_requirements_payload(report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = report or build_external_validation_requirements()
    rows = report["evidence_requirements"]
    return {
        "status": "external_validation_evidence_requirements_ready",
        "generated_at": report["generated_at"],
        "checked_at": report["checked_at"],
        "gate_count": report["gate_count"],
        "evidence_requirement_count": len(rows),
        "rows": rows,
        "proof_boundary": "These are required records to collect. They are not collected approvals.",
    }


def build_go_live_input_templates(report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = report or build_external_validation_requirements()
    templates = []
    for item in GO_LIVE_INPUT_REQUESTS:
        templates.append(
            {
                "review_area": item["review_area"],
                "plain_title": item["plain_title"],
                "who_to_ask": item["who_to_ask"],
                "simple_question": item["simple_question"],
                "ready_answer": item["ready_answer"],
                "allowed_decisions": HUMAN_READY_INPUT_DECISIONS,
                "minimum_input": item["minimum_input"],
                "record_template": {
                    "review_area": item["review_area"],
                    "reviewer_name": "",
                    "reviewer_role": "",
                    "scope_reviewed": "",
                    "decision": "need_more_evidence",
                    "top_issues": [],
                    "evidence_missing": [],
                    "claims_the_product_must_not_make": [],
                    "what_would_make_this_ready": "",
                    "evidence_links_or_files": [],
                    "signed_at": "",
                },
            }
        )
    return {
        "status": "go_live_input_templates_ready",
        "generated_at": report["generated_at"],
        "input_folder": "external_inputs/",
        "template_count": len(templates),
        "allowed_decisions": HUMAN_READY_INPUT_DECISIONS,
        "templates": templates,
        "how_to_use": [
            "Send the reviewer brief PDF first.",
            "Ask each person to answer only their area.",
            "Save each returned answer as one JSON file in external_inputs/ using the matching record_template.",
            "Rerun scripts/run_external_validation_requirements.py --input-dir external_inputs.",
            "Use system_review_graph/go_live_input_readiness_report.json to see whether go live is ready or what is still missing.",
        ],
        "proof_boundary": "Templates are ready. They are not approvals until real people return signed or dated inputs.",
    }


def load_go_live_input_records(input_dir: Path) -> list[dict[str, Any]]:
    if not input_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            rows.append(
                {
                    "review_area": "invalid",
                    "source_file": path.name,
                    "decision": "need_more_evidence",
                    "top_issues": [f"Could not read input JSON: {exc}"],
                    "evidence_missing": ["valid JSON input record"],
                }
            )
            continue
        if isinstance(payload, dict):
            payload["source_file"] = path.name
            rows.append(payload)
    return rows


def evaluate_go_live_input_records(
    records: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    accepted_by_area: dict[str, dict[str, Any]] = {}
    received_by_area: dict[str, list[dict[str, Any]]] = {row["review_area"]: [] for row in GO_LIVE_INPUT_REQUESTS}
    for record in records:
        area = str(record.get("review_area") or "")
        if area not in received_by_area:
            continue
        received_by_area[area].append(record)
        decision = str(record.get("decision") or "")
        has_minimum_identity = bool(record.get("reviewer_name") or record.get("approver"))
        has_signed_date = bool(record.get("signed_at") or record.get("decided_at"))
        has_scope = bool(record.get("scope_reviewed") or record.get("launch_scope"))
        if decision in READY_INPUT_DECISIONS and has_minimum_identity and has_signed_date and has_scope:
            accepted_by_area.setdefault(area, record)
    missing_inputs = [
        {
            "review_area": item["review_area"],
            "plain_title": item["plain_title"],
            "who_to_ask": item["who_to_ask"],
            "simple_question": item["simple_question"],
            "minimum_input": item["minimum_input"],
        }
        for item in GO_LIVE_INPUT_REQUESTS
        if item["review_area"] not in accepted_by_area
    ]
    ready_area_count = len(accepted_by_area)
    all_areas_ready = ready_area_count == len(GO_LIVE_INPUT_REQUESTS)
    final_decision = accepted_by_area.get("public_go_no_go_approval", {})
    public_launch_ready = all_areas_ready and final_decision.get("decision") == "go_for_public_launch"
    return {
        "status": "go_live_ready_after_real_inputs" if public_launch_ready else "waiting_for_real_inputs_not_ready_yet",
        "generated_at": generated_at,
        "input_record_count": len(records),
        "required_input_count": len(GO_LIVE_INPUT_REQUESTS),
        "ready_input_count": ready_area_count,
        "missing_input_count": len(missing_inputs),
        "public_launch_ready": public_launch_ready,
        "hosted_private_beta_ready": all(
            area in accepted_by_area
            for area in (
                "real_external_expert_reviews",
                "legal_privacy_security_approval",
                "hosted_staging_production_proof",
            )
        ),
        "live_payment_ready": "live_payment_activation" in accepted_by_area,
        "accepted_inputs": [
            {
                "review_area": area,
                "reviewer_name": record.get("reviewer_name") or record.get("approver"),
                "decision": record.get("decision"),
                "signed_at": record.get("signed_at") or record.get("decided_at"),
                "source_file": record.get("source_file"),
            }
            for area, record in sorted(accepted_by_area.items())
        ],
        "missing_inputs": missing_inputs,
        "next_step": (
            "Go live can be prepared for the exact approved scope."
            if public_launch_ready
            else "Collect the missing real-person inputs, save them under external_inputs/, and rerun this script."
        ),
        "proof_boundary": "This report changes to go-live-ready only when real dated inputs are attached. It does not approve launch by itself.",
    }


def render_go_live_input_requests(templates: dict[str, Any], readiness: dict[str, Any]) -> str:
    request_lines = []
    for item in templates["templates"]:
        request_lines.append(
            f"""## {item["plain_title"]}

Who to ask: {item["who_to_ask"]}

Question: {item["simple_question"]}

Ready answer: {item["ready_answer"]}

Minimum input needed:
{chr(10).join(f"- {field}" for field in item["minimum_input"])}
"""
        )
    return f"""# Go Live Input Requests

Status: `{readiness["status"]}`

This is the simple intake plan for real people. Send the short reviewer brief
first. When answers come back, save each answer as a JSON file in
`external_inputs/` using the matching template in
`system_review_graph/go_live_input_templates.json`, then rerun:

```bash
python3 scripts/run_external_validation_requirements.py --input-dir external_inputs
```

## Current Go Live State

- Public launch ready: `{readiness["public_launch_ready"]}`
- Ready inputs received: `{readiness["ready_input_count"]}` of `{readiness["required_input_count"]}`
- Missing inputs: `{readiness["missing_input_count"]}`

## Inputs To Collect

{chr(10).join(request_lines)}

## Once Inputs Are Received

1. Save each response as one JSON file in `external_inputs/`.
2. Rerun the command above.
3. Open `system_review_graph/go_live_input_readiness_report.json`.
4. If status is `go_live_ready_after_real_inputs`, use the exact approved launch scope from the final go-live input.
5. If status is `waiting_for_real_inputs_not_ready_yet`, collect only the missing items shown in that report.
"""


def render_external_validation_requirements(report: dict[str, Any]) -> str:
    gate_lines = []
    for gate in report["gates"]:
        gate_lines.append(
            f"| `{gate['gate_id']}` | `{gate['status']}` | {gate['owner']} | {gate['next_valid_move']} |"
        )
    data_lines = []
    for row in report["required_data_catalog"]:
        data_lines.append(
            f"| `{row['category_id']}` | {row['owner']} | `{row['storage_artifact']}` | {', '.join(row['blocks'])} |"
        )
    source_lines = []
    for source in report["source_anchors"]:
        source_lines.append(
            f"- `{source['source_id']}` - {source['publisher']}: [{source['name']}]({source['url']})"
        )
    template_lines = []
    for template in report["collection_templates"]:
        template_lines.append(
            f"- `{template['template_id']}`: {', '.join(template['required_fields'])}"
        )
    return f"""# External Validation Requirements

Status: `{report["status"]}`

Generated: `{report["generated_at"]}`

Checked source date: `{report["checked_at"]}`

This is the master real-world evidence checklist for Trade Readiness Copilot.
It gathers what the project needs before hosted private beta, public launch,
live payments, qualified customs/trade claims, real user claims, buyer/supplier
validation, or public go/no-go approval.

## Current Decision

- Public launch ready: `{report["public_launch_ready"]}`
- Hosted private beta ready: `{report["hosted_private_beta_ready"]}`
- Live payment ready: `{report["live_payment_ready"]}`
- Qualified trade claims ready: `{report["qualified_trade_claims_ready"]}`
- Buyer/supplier validation ready: `{report["buyer_supplier_validation_ready"]}`
- AI-simulated review can open gates: `{report["simulated_ai_review_can_open_gate"]}`

## Gates

| Gate | Status | Owner | Next valid move |
| --- | --- | --- | --- |
{chr(10).join(gate_lines)}

## Required Project Data

| Data category | Owner | Current artifact target | Blocks |
| --- | --- | --- | --- |
{chr(10).join(data_lines)}

## Collection Templates

{chr(10).join(template_lines)}

## Source Anchors

{chr(10).join(source_lines)}

## Unsafe Shortcuts Rejected

{chr(10).join(f"- {item}" for item in report["unsafe_shortcuts_rejected"])}

## Proof Boundary

{report["proof_boundary"]}
"""


def _plain_text_report_lines(report: dict[str, Any]) -> list[str]:
    lines = [
        "External Validation Requirements",
        f"Status: {report['status']}",
        f"Generated: {report['generated_at']}",
        f"Checked source date: {report['checked_at']}",
        "",
        "Current decision",
        f"- Public launch ready: {report['public_launch_ready']}",
        f"- Hosted private beta ready: {report['hosted_private_beta_ready']}",
        f"- Live payment ready: {report['live_payment_ready']}",
        f"- Qualified trade claims ready: {report['qualified_trade_claims_ready']}",
        f"- Buyer/supplier validation ready: {report['buyer_supplier_validation_ready']}",
        f"- AI-simulated review can open gates: {report['simulated_ai_review_can_open_gate']}",
        "",
        "Gate summary",
    ]
    for gate in report["gates"]:
        lines.extend(
            [
                "",
                f"{gate['name']} ({gate['gate_id']})",
                f"Status: {gate['status']}",
                f"Owner: {gate['owner']}",
                f"Why needed: {gate['why_project_needs_it']}",
                "Required reviewers/owners:",
                *[f"- {item}" for item in gate["required_reviewers_or_owners"]],
                "Required evidence:",
                *[f"- {item}" for item in gate["required_evidence"]],
                "Required data fields:",
                f"- {', '.join(gate['required_data_fields'])}",
                f"Minimum acceptance: {gate['minimum_acceptance']}",
                "Blocking conditions:",
                *[f"- {item}" for item in gate["blocking_conditions"]],
                f"Cannot claim until: {gate['cannot_claim_until']}",
                f"Next valid move: {gate['next_valid_move']}",
                f"Source IDs: {', '.join(gate['source_ids'])}",
            ]
        )
    lines.extend(["", "Required project data"])
    for row in report["required_data_catalog"]:
        lines.extend(
            [
                "",
                f"{row['category_id']} - owner: {row['owner']}",
                f"Artifact target: {row['storage_artifact']}",
                f"Blocks: {', '.join(row['blocks'])}",
                f"Minimum fields: {', '.join(row['minimum_fields'])}",
                f"Refresh rule: {row['refresh_rule']}",
            ]
        )
    lines.extend(["", "Collection templates"])
    for template in report["collection_templates"]:
        lines.extend(
            [
                "",
                template["template_id"],
                f"Required fields: {', '.join(template['required_fields'])}",
                f"Valid decisions: {', '.join(template['valid_decisions'])}",
            ]
        )
    lines.extend(["", "Source anchors"])
    for source in report["source_anchors"]:
        lines.extend(
            [
                "",
                f"{source['source_id']} - {source['publisher']}",
                source["name"],
                source["url"],
                f"Project use: {source['project_use']}",
            ]
        )
    lines.extend(
        [
            "",
            "Unsafe shortcuts rejected",
            *[f"- {item}" for item in report["unsafe_shortcuts_rejected"]],
            "",
            "Proof boundary",
            report["proof_boundary"],
        ]
    )
    return lines


def _reviewer_brief_lines(report: dict[str, Any]) -> list[str]:
    return [
        "Trade Readiness Copilot - Reviewer Brief",
        "Status: built for review, not approved for public launch",
        "",
        "Short version",
        "The local product is built enough to review, but it is not approved for public launch, hosted private beta, live payments, customs/trade claims, or buyer/supplier validation.",
        "",
        "What I need from you",
        "Please review only your area. You do not need to audit the whole repo.",
        "Reply with one decision: looks okay for my area, not ready yet, I need more evidence, not my area, or send to a different reviewer.",
        "If it is not ready, list the top issues, what evidence is missing, and what would make it safe to approve.",
        "Please also say what the product must not claim in your area.",
        "",
        "What is not approved yet",
        "- Public launch",
        "- Hosted private beta with real customer data",
        "- Legal/privacy/security approval",
        "- Customs, tariff, CFIA, sanctions, or trade-readiness claims",
        "- Live payment activation",
        "- Real user/private beta outcome claims",
        "- Buyer or supplier validation claims",
        "- Final public go/no-go approval",
        "",
        "Best review match",
        "- Product/UX: Can target users understand the flow and the claims that are not approved yet?",
        "- Security: Are uploads, auth, AI, storage, logs, and deployment controls safe enough for hosted beta?",
        "- Privacy/legal: Do notices, terms, data handling, retention, deletion, and incident steps match real flows?",
        "- Customs/trade: Does any language imply tariff/customs/CFIA/import/export advice that needs a broker or specialist?",
        "- DevOps: Is there enough hosted staging/production evidence, monitoring, backup, rollback, and support ownership?",
        "- Payments: Is live checkout, webhook, tax/refund/support, and billing language ready?",
        "- Buyer/supplier/commercial: Is there real counterpart evidence, not just a plausible idea?",
        "- Launch owner: Are all review areas evidenced enough to make a public go/no-go decision?",
        "",
        "Fast response template",
        "Decision:",
        "Scope reviewed:",
        "Top issues:",
        "Evidence missing:",
        "Claims the product must not make:",
        "What would make this ready for my approval:",
        "",
        "Detailed appendix",
        "Use external_validation_requirements.pdf for the full evidence checklist, source links, data fields, and collection templates.",
        "",
        "Important note",
        "This brief lists what is still needed. It does not prove outside approval, legal/privacy/security signoff, customs/trade review, hosted production proof, live payment activation, private-beta outcome, buyer/supplier validation, or public go/no-go.",
    ]


def _go_live_input_request_lines(templates: dict[str, Any], readiness: dict[str, Any]) -> list[str]:
    lines = [
        "Trade Readiness Copilot - Go Live Input Requests",
        f"Status: {readiness['status']}",
        "",
        "What this is",
        "This is the short collection list for real people. Once these answers are received and saved, the same script can say whether go live is ready for the exact approved scope.",
        "",
        "Current state",
        f"- Public launch ready: {readiness['public_launch_ready']}",
        f"- Ready inputs received: {readiness['ready_input_count']} of {readiness['required_input_count']}",
        f"- Missing inputs: {readiness['missing_input_count']}",
        "",
        "How to use this",
        "1. Send the reviewer brief PDF first.",
        "2. Ask each person to answer only their area.",
        "3. Save each response in external_inputs/ using the matching JSON template.",
        "4. Rerun scripts/run_external_validation_requirements.py --input-dir external_inputs.",
        "5. Use the go-live readiness report to see whether launch is ready or what is still missing.",
        "",
        "Inputs to collect",
    ]
    for item in templates["templates"]:
        lines.extend(
            [
                "",
                item["plain_title"],
                f"Who to ask: {item['who_to_ask']}",
                f"Question: {item['simple_question']}",
                f"Ready answer: {item['ready_answer']}",
                "Minimum input needed:",
                *[f"- {field}" for field in item["minimum_input"]],
            ]
        )
    return lines


def _write_reportlab_pdf(report: dict[str, Any], path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SmallBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="External Validation Requirements",
    )

    def draw_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(0.55 * inch, 0.32 * inch, "Trade Readiness Copilot - External Validation Requirements")
        canvas.drawRightString(7.95 * inch, 0.32 * inch, f"Page {document.page}")
        canvas.restoreState()

    story: list[Any] = [
        Paragraph("External Validation Requirements", styles["Title"]),
        Paragraph(
            "Shareable reviewer PDF for Trade Readiness Copilot. This gathers the real evidence, reviewers, data, open issues, and next steps needed before private beta, public launch, payments, trade claims, buyer/supplier validation, or public go/no-go.",
            styles["BodyText"],
        ),
        Spacer(1, 8),
    ]
    summary_rows = [
        ["Field", "Value"],
        ["Status", report["status"]],
        ["Generated", report["generated_at"]],
        ["Checked source date", report["checked_at"]],
        ["Gate count", str(report["gate_count"])],
        ["Source anchors", str(report["source_count"])],
        ["Evidence requirements", str(report["evidence_requirement_count"])],
        ["Public launch ready", str(report["public_launch_ready"])],
        ["Hosted private beta ready", str(report["hosted_private_beta_ready"])],
        ["Live payment ready", str(report["live_payment_ready"])],
    ]
    summary_table = Table(summary_rows, colWidths=[1.65 * inch, 5.0 * inch], repeatRows=1)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 10), Paragraph("Gate Summary", styles["Heading2"])])
    gate_rows: list[list[Any]] = [["Gate", "Status", "Owner", "Next valid move"]]
    for gate in report["gates"]:
        gate_rows.append(
            [
                Paragraph(gate["gate_id"], styles["SmallBody"]),
                Paragraph(gate["status"], styles["SmallBody"]),
                Paragraph(gate["owner"], styles["SmallBody"]),
                Paragraph(gate["next_valid_move"], styles["SmallBody"]),
            ]
        )
    gate_table = Table(gate_rows, colWidths=[1.65 * inch, 1.55 * inch, 1.1 * inch, 2.35 * inch], repeatRows=1)
    gate_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([gate_table, PageBreak()])
    for gate in report["gates"]:
        story.append(Paragraph(f"{gate['name']} ({gate['gate_id']})", styles["Heading2"]))
        story.append(Paragraph(f"Status: {gate['status']}", styles["SmallHeading"]))
        story.append(Paragraph(f"Owner: {gate['owner']}", styles["SmallBody"]))
        story.append(Paragraph(f"Why needed: {gate['why_project_needs_it']}", styles["SmallBody"]))
        for heading, values in (
            ("Required reviewers/owners", gate["required_reviewers_or_owners"]),
            ("Required evidence", gate["required_evidence"]),
            ("Required data fields", gate["required_data_fields"]),
            ("Blocking conditions", gate["blocking_conditions"]),
            ("Approval artifacts", gate["approval_artifacts"]),
        ):
            story.append(Paragraph(heading, styles["SmallHeading"]))
            for value in values:
                story.append(Paragraph(f"- {value}", styles["SmallBody"]))
        story.append(Paragraph(f"Minimum acceptance: {gate['minimum_acceptance']}", styles["SmallBody"]))
        story.append(Paragraph(f"Cannot claim until: {gate['cannot_claim_until']}", styles["SmallBody"]))
        story.append(Paragraph(f"Refresh rule: {gate['refresh_rule']}", styles["SmallBody"]))
        story.append(Paragraph(f"Source IDs: {', '.join(gate['source_ids'])}", styles["SmallBody"]))
        story.append(Spacer(1, 8))
    story.append(PageBreak())
    story.append(Paragraph("Required Project Data Catalog", styles["Heading2"]))
    for row in report["required_data_catalog"]:
        story.append(Paragraph(row["category_id"], styles["SmallHeading"]))
        story.append(Paragraph(f"Owner: {row['owner']}", styles["SmallBody"]))
        story.append(Paragraph(f"Artifact target: {row['storage_artifact']}", styles["SmallBody"]))
        story.append(Paragraph(f"Blocks: {', '.join(row['blocks'])}", styles["SmallBody"]))
        story.append(Paragraph(f"Minimum fields: {', '.join(row['minimum_fields'])}", styles["SmallBody"]))
        story.append(Paragraph(f"Refresh rule: {row['refresh_rule']}", styles["SmallBody"]))
    story.append(PageBreak())
    story.append(Paragraph("Collection Templates", styles["Heading2"]))
    for template in report["collection_templates"]:
        story.append(Paragraph(template["template_id"], styles["SmallHeading"]))
        story.append(Paragraph(f"Required fields: {', '.join(template['required_fields'])}", styles["SmallBody"]))
        story.append(Paragraph(f"Valid decisions: {', '.join(template['valid_decisions'])}", styles["SmallBody"]))
    story.append(Paragraph("Source Anchors", styles["Heading2"]))
    for source in report["source_anchors"]:
        story.append(Paragraph(f"{source['source_id']} - {source['publisher']}", styles["SmallHeading"]))
        story.append(Paragraph(f"{source['name']}: {source['url']}", styles["SmallBody"]))
        story.append(Paragraph(f"Project use: {source['project_use']}", styles["SmallBody"]))
    story.append(Paragraph("Unsafe Shortcuts Rejected", styles["Heading2"]))
    for item in report["unsafe_shortcuts_rejected"]:
        story.append(Paragraph(f"- {item}", styles["SmallBody"]))
    story.append(Paragraph("Proof Boundary", styles["Heading2"]))
    story.append(Paragraph(report["proof_boundary"], styles["BodyText"]))
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)


def _write_reportlab_go_live_inputs_pdf(templates: dict[str, Any], readiness: dict[str, Any], path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="InputBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=4,
        )
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Go Live Input Requests",
    )

    def draw_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(0.6 * inch, 0.32 * inch, "Trade Readiness Copilot - Go Live Input Requests")
        canvas.drawRightString(7.9 * inch, 0.32 * inch, f"Page {document.page}")
        canvas.restoreState()

    story: list[Any] = [
        Paragraph("Go Live Input Requests", styles["Title"]),
        Paragraph(
            "A short collection list for the real approvals and evidence needed before go live. Once these answers are received, save them and rerun the input check.",
            styles["InputBody"],
        ),
        Spacer(1, 8),
    ]
    status_rows = [
        ["Current question", "Answer"],
        ["Public launch ready now?", str(readiness["public_launch_ready"])],
        ["Ready inputs received", f"{readiness['ready_input_count']} of {readiness['required_input_count']}"],
        ["Missing inputs", str(readiness["missing_input_count"])],
        ["Next step", readiness["next_step"]],
    ]
    table = Table(status_rows, colWidths=[2.2 * inch, 4.3 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
            ]
        )
    )
    story.extend([table, Spacer(1, 10), Paragraph("Inputs To Collect", styles["Heading2"])])
    input_rows: list[list[Any]] = [["Area", "Who to ask", "Question"]]
    for item in templates["templates"]:
        input_rows.append(
            [
                Paragraph(item["plain_title"], styles["InputBody"]),
                Paragraph(item["who_to_ask"], styles["InputBody"]),
                Paragraph(item["simple_question"], styles["InputBody"]),
            ]
        )
    input_table = Table(input_rows, colWidths=[1.65 * inch, 2.2 * inch, 2.65 * inch], repeatRows=1)
    input_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend(
        [
            input_table,
            Spacer(1, 10),
            Paragraph("How To Use Returned Inputs", styles["Heading2"]),
            Paragraph("Save each response as one JSON file in external_inputs/.", styles["InputBody"]),
            Paragraph("Run: python3 scripts/run_external_validation_requirements.py --input-dir external_inputs", styles["InputBody"]),
            Paragraph("Open system_review_graph/go_live_input_readiness_report.json for the launch decision state.", styles["InputBody"]),
        ]
    )
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)


def _write_reportlab_brief_pdf(report: dict[str, Any], path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BriefBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BriefSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.5,
            spaceAfter=3,
        )
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="External Validation Reviewer Brief",
    )

    def draw_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(0.6 * inch, 0.32 * inch, "Trade Readiness Copilot - Reviewer Brief")
        canvas.drawRightString(7.9 * inch, 0.32 * inch, f"Page {document.page}")
        canvas.restoreState()

    story: list[Any] = [
        Paragraph("External Validation Reviewer Brief", styles["Title"]),
        Paragraph(
            "A short, plain-English brief for busy reviewers. The detailed checklist is still available as the companion appendix PDF.",
            styles["BriefBody"],
        ),
        Spacer(1, 8),
    ]
    status_rows: list[list[Any]] = [
        ["Question", "Current answer"],
        [Paragraph("Can this be publicly launched now?", styles["BriefSmall"]), Paragraph("No", styles["BriefSmall"])],
        [Paragraph("Can it take live payments now?", styles["BriefSmall"]), Paragraph("No", styles["BriefSmall"])],
        [Paragraph("Can it claim legal or trade approval now?", styles["BriefSmall"]), Paragraph("No", styles["BriefSmall"])],
        [
            Paragraph("What can reviewers do now?", styles["BriefSmall"]),
            Paragraph("Review the scoped package and send a short decision plus missing evidence.", styles["BriefSmall"]),
        ],
    ]
    table = Table(status_rows, colWidths=[2.6 * inch, 3.9 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.extend(
        [
            table,
            Spacer(1, 10),
            Paragraph("What I Need From You", styles["Heading2"]),
            Paragraph("Please review only your area. You do not need to audit the whole repo.", styles["BriefBody"]),
            Paragraph(
                "Reply with one decision: looks okay for my area, not ready yet, I need more evidence, not my area, or send to a different reviewer.",
                styles["BriefBody"],
            ),
            Paragraph(
                "If it is not ready, list the top issues, what evidence is missing, and what would make it safe to approve. Also say what the product must not claim in your area.",
                styles["BriefBody"],
            ),
            Paragraph("The Eight Review Areas", styles["Heading2"]),
        ]
    )
    plain_gate_rows: list[list[Any]] = [["Review area", "Plain-language question"]]
    plain_questions = {
        "real_external_expert_reviews": "Have real named reviewers checked the right scope?",
        "legal_privacy_security_approval": "Is customer data handling, security, AI use, retention, deletion, and incident response acceptable?",
        "qualified_customs_trade_review": "Does a qualified broker/trade reviewer approve what the product says and does not say?",
        "hosted_staging_production_proof": "Is there real hosted staging/production evidence, not just localhost?",
        "live_payment_activation": "Are live checkout, webhooks, tax/refund/support, and billing language ready?",
        "real_users_private_beta_outcomes": "Have real target users completed the flow without unsafe misunderstanding?",
        "buyer_supplier_validation": "Have real buyers/suppliers/importers/exporters validated a real problem and workflow?",
        "public_go_no_go_approval": "Has a named owner reviewed all evidence and made a launch decision?",
    }
    for gate in report["gates"]:
        plain_gate_rows.append(
            [
                Paragraph(gate["name"], styles["BriefSmall"]),
                Paragraph(plain_questions[gate["gate_id"]], styles["BriefSmall"]),
            ]
        )
    gate_table = Table(plain_gate_rows, colWidths=[2.3 * inch, 4.2 * inch], repeatRows=1)
    gate_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend(
        [
            gate_table,
            Spacer(1, 10),
            Paragraph("Fast Response Template", styles["Heading2"]),
            Paragraph("Decision:", styles["BriefBody"]),
            Paragraph("Scope reviewed:", styles["BriefBody"]),
            Paragraph("Top issues:", styles["BriefBody"]),
            Paragraph("Evidence missing:", styles["BriefBody"]),
            Paragraph("Claims the product must not make:", styles["BriefBody"]),
            Paragraph("What would make this ready for my approval:", styles["BriefBody"]),
            PageBreak(),
            Paragraph("What To Ignore", styles["Heading2"]),
            Paragraph(
                "You do not need to review unrelated code, old package zips, or every generated artifact. Focus on the role-specific packet and the claim boundary for your area.",
                styles["BriefBody"],
            ),
            Paragraph("Important Note", styles["Heading2"]),
            Paragraph(
                "This brief lists what is still needed. It does not prove outside approval, legal/privacy/security signoff, customs/trade review, hosted production proof, live payment activation, private-beta outcome, buyer/supplier validation, or public go/no-go.",
                styles["BriefBody"],
            ),
        ]
    )
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_simple_pdf_from_lines(lines: list[str], path: Path) -> None:
    # Minimal valid PDF fallback for environments that do not have reportlab.
    wrapped_lines: list[str] = []
    for line in lines:
        if not line:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(line, width=92) or [""])
    lines_per_page = 54
    pages = [wrapped_lines[index : index + lines_per_page] for index in range(0, len(wrapped_lines), lines_per_page)]
    objects: list[str] = []
    pages_obj_id = 2
    font_obj_id = 3
    page_ids: list[int] = []
    content_ids: list[int] = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    objects.append("")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for page in pages:
        page_id = len(objects) + 1
        content_id = page_id + 1
        page_ids.append(page_id)
        content_ids.append(content_id)
        objects.append(
            f"<< /Type /Page /Parent {pages_obj_id} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_obj_id} 0 R >> >> /Contents {content_id} 0 R >>"
        )
        content_lines = ["BT", "/F1 9 Tf", "54 744 Td", "12 TL"]
        for line in page:
            content_lines.append(f"({_escape_pdf_text(line)}) Tj")
            content_lines.append("T*")
        content_lines.append("ET")
        content = "\n".join(content_lines)
        objects.append(f"<< /Length {len(content.encode('latin-1', 'replace'))} >>\nstream\n{content}\nendstream")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_obj_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    pdf = "%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf.encode("latin-1", "replace")))
        pdf += f"{index} 0 obj\n{obj}\nendobj\n"
    xref_offset = len(pdf.encode("latin-1", "replace"))
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    path.write_bytes(pdf.encode("latin-1", "replace"))


def _write_simple_pdf(report: dict[str, Any], path: Path) -> None:
    _write_simple_pdf_from_lines(_plain_text_report_lines(report), path)


def _write_simple_brief_pdf(report: dict[str, Any], path: Path) -> None:
    _write_simple_pdf_from_lines(_reviewer_brief_lines(report), path)


def _write_simple_go_live_inputs_pdf(templates: dict[str, Any], readiness: dict[str, Any], path: Path) -> None:
    _write_simple_pdf_from_lines(_go_live_input_request_lines(templates, readiness), path)


def write_external_validation_pdf(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _write_reportlab_pdf(report, path)
    except ModuleNotFoundError:
        _write_simple_pdf(report, path)
    return path


def write_go_live_input_requests_pdf(templates: dict[str, Any], readiness: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _write_reportlab_go_live_inputs_pdf(templates, readiness, path)
    except ModuleNotFoundError:
        _write_simple_go_live_inputs_pdf(templates, readiness, path)
    return path


def render_external_validation_reviewer_brief(report: dict[str, Any]) -> str:
    return "\n".join(_reviewer_brief_lines(report)) + "\n"


def write_external_validation_reviewer_brief_pdf(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _write_reportlab_brief_pdf(report, path)
    except ModuleNotFoundError:
        _write_simple_brief_pdf(report, path)
    return path


def write_external_validation_requirements(
    root: Path,
    generated_at: str | None = None,
    input_dir: Path | None = None,
) -> dict[str, Any]:
    report = build_external_validation_requirements(generated_at)
    evidence = build_evidence_requirements_payload(report)
    templates = build_go_live_input_templates(report)
    input_records = load_go_live_input_records(input_dir or (root / "external_inputs"))
    input_readiness = evaluate_go_live_input_records(input_records, report["generated_at"])
    errors = validate_external_validation_requirements(report)
    if errors:
        raise ValueError("; ".join(errors))
    srg = root / "system_review_graph"
    docs = root / "docs"
    srg.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    (srg / "external_validation_requirements_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (srg / "external_validation_evidence_requirements.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (srg / "go_live_input_templates.json").write_text(
        json.dumps(templates, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (srg / "go_live_input_readiness_report.json").write_text(
        json.dumps(input_readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (docs / "EXTERNAL_VALIDATION_REQUIREMENTS.md").write_text(
        render_external_validation_requirements(report),
        encoding="utf-8",
    )
    (docs / "EXTERNAL_VALIDATION_REVIEWER_BRIEF.md").write_text(
        render_external_validation_reviewer_brief(report),
        encoding="utf-8",
    )
    (docs / "GO_LIVE_INPUT_REQUESTS.md").write_text(
        render_go_live_input_requests(templates, input_readiness),
        encoding="utf-8",
    )
    pdf_path = write_external_validation_pdf(report, root / "output" / "pdf" / "external_validation_requirements.pdf")
    brief_pdf_path = write_external_validation_reviewer_brief_pdf(
        report,
        root / "output" / "pdf" / "external_validation_reviewer_brief.pdf",
    )
    input_pdf_path = write_go_live_input_requests_pdf(
        templates,
        input_readiness,
        root / "output" / "pdf" / "go_live_input_requests.pdf",
    )
    return {
        "status": report["status"],
        "gate_count": report["gate_count"],
        "source_count": report["source_count"],
        "evidence_requirement_count": report["evidence_requirement_count"],
        "required_data_category_count": report["required_data_category_count"],
        "go_live_input_status": input_readiness["status"],
        "ready_input_count": input_readiness["ready_input_count"],
        "missing_input_count": input_readiness["missing_input_count"],
        "public_launch_ready": report["public_launch_ready"],
        "hosted_private_beta_ready": report["hosted_private_beta_ready"],
        "live_payment_ready": report["live_payment_ready"],
        "pdf_path": str(pdf_path),
        "brief_pdf_path": str(brief_pdf_path),
        "input_pdf_path": str(input_pdf_path),
    }
