# External Validation Requirements

Status: `external_validation_requirements_ready_all_real_world_gates_blocked`

Generated: `2026-06-28T15:02:50Z`

Checked source date: `2026-06-27`

This is the master real-world evidence checklist for Trade Readiness Copilot.
It gathers what the project needs before hosted private beta, public launch,
live payments, qualified customs/trade claims, real user claims, buyer/supplier
validation, or public go/no-go approval.

## Current Decision

- Public launch ready: `False`
- Hosted private beta ready: `False`
- Live payment ready: `False`
- Qualified trade claims ready: `False`
- Buyer/supplier validation ready: `False`
- AI-simulated review can open gates: `False`

## Gates

| Gate | Status | Owner | Next valid move |
| --- | --- | --- | --- |
| `real_external_expert_reviews` | `blocked_waiting_for_real_named_reviewers` | founder | Send executive and technical packages to Wave 1 reviewers, record decisions, and convert every finding into a blocker row. |
| `legal_privacy_security_approval` | `blocked_waiting_for_qualified_approval` | privacy_security_owner | Assemble the data map, threat model, upload controls proof, incident process, privacy notice, and AI processor inventory for qualified review. |
| `qualified_customs_trade_review` | `blocked_waiting_for_broker_or_trade_specialist` | trade_compliance_owner | Prepare one dated broker packet per sample packet and request scoped language approval from a qualified customs/trade reviewer. |
| `hosted_staging_production_proof` | `blocked_waiting_for_real_hosted_environment` | devops_owner | Provision staging, deploy exact commit, run smoke/security/upload/privacy/backup/rollback checks, and attach evidence. |
| `live_payment_activation` | `blocked_waiting_for_payment_account_and_policy_proof` | billing_owner | Keep live checkout disabled; complete Stripe live-mode configuration and payment policy proof after staged security/privacy approval. |
| `real_users_private_beta_outcomes` | `blocked_waiting_for_real_user_sessions` | product_research_owner | After Wave 1 and staging proof, run five structured private-beta sessions and convert every issue into a blocker or fixed proof row. |
| `buyer_supplier_validation` | `blocked_waiting_for_real_market_counterparties` | commercial_validation_owner | Run structured interviews with target importers/exporters/brokers and record the evidence without opening recommendation claims. |
| `public_go_no_go_approval` | `blocked_waiting_for_named_decision_owner` | launch_decision_owner | Do not hold public go/no-go until the other seven gates have real evidence; keep launch state blocked-safe. |

## Required Project Data

| Data category | Owner | Current artifact target | Blocks |
| --- | --- | --- | --- |
| `business_identity_and_contacts` | founder | `system_review_graph/external_validation_requirements_report.json` | public_go_no_go_approval, live_payment_activation, legal_privacy_security_approval |
| `product_scope_and_claim_boundaries` | product_owner | `system_review_graph/claims_gate_matrix.json` | qualified_customs_trade_review, public_go_no_go_approval |
| `official_source_registry` | research_owner | `data/official_source_registry.json` | qualified_customs_trade_review, buyer_supplier_validation, public_go_no_go_approval |
| `customer_document_and_upload_data` | privacy_security_owner | `system_review_graph/public_upload_manifest.json` | legal_privacy_security_approval, hosted_staging_production_proof |
| `ai_data_processing_and_redaction` | ai_data_owner | `system_review_graph/ai_data_policy.json` | legal_privacy_security_approval, real_external_expert_reviews |
| `privacy_legal_records` | privacy_legal_owner | `docs/SECURITY_PRIVACY.md` | legal_privacy_security_approval, public_go_no_go_approval |
| `security_operational_records` | security_owner | `system_review_graph/deployment_readiness_report.json` | legal_privacy_security_approval, hosted_staging_production_proof, public_go_no_go_approval |
| `hosted_environment_records` | devops_owner | `system_review_graph/deployment_readiness_report.json` | hosted_staging_production_proof, real_users_private_beta_outcomes, public_go_no_go_approval |
| `trade_customs_records` | trade_compliance_owner | `system_review_graph/country_coverage_report.json` | qualified_customs_trade_review, buyer_supplier_validation, public_go_no_go_approval |
| `sanctions_and_party_screening` | trade_compliance_owner | `system_review_graph/external_validation_evidence_requirements.json` | qualified_customs_trade_review, buyer_supplier_validation |
| `payment_billing_records` | billing_owner | `system_review_graph/billing_credit_controls.json` | live_payment_activation, public_go_no_go_approval |
| `private_beta_user_outcomes` | product_research_owner | `system_review_graph/private_beta_smoke_test_plan.json` | real_users_private_beta_outcomes, public_go_no_go_approval |
| `buyer_supplier_validation_records` | commercial_validation_owner | `system_review_graph/team_workspace_report.json` | buyer_supplier_validation, qualified_customs_trade_review, public_go_no_go_approval |
| `support_incident_and_deletion_records` | support_owner | `system_review_graph/launch_operations_report.json` | hosted_staging_production_proof, legal_privacy_security_approval, public_go_no_go_approval |
| `accessibility_and_content_quality` | product_owner | `system_review_graph/external_validation_requirements_report.json` | real_users_private_beta_outcomes, public_go_no_go_approval |
| `public_launch_decision_records` | launch_decision_owner | `system_review_graph/final_go_live_decision_report.json` | public_go_no_go_approval |

## Collection Templates

- `external_review_decision_record`: reviewer_name, role, qualification_basis, scope, commit_sha, package_sha256, findings, decision, signed_at
- `legal_privacy_security_approval_record`: approver, scope, privacy_notice_version, data_map_version, security_tests, approved_controls, unresolved_findings, decision, signed_at
- `customs_trade_review_record`: reviewer, credential, product_category, hs_code_candidate, origin, destination, official_sources, assumptions, approved_claims, blocked_claims, decision
- `hosted_environment_proof_record`: environment, url, commit_sha, build_digest, tls, secrets, storage, logs, monitoring, backup_restore, rollback, smoke_result, approver
- `payment_activation_record`: stripe_mode, product_ids, price_ids, checkout_url, webhook_events, tax_decision, refund_policy, support_contact, test_result, activation_decision
- `private_beta_outcome_record`: participant_id, segment, consent, tasks, completion, issues, misunderstood_claims, support_events, privacy_concerns, decision
- `buyer_supplier_validation_record`: counterparty_id, role, permission_scope, problem, current_workaround, documents_shared, willingness_signal, price_signal, objections, screening_result
- `public_go_no_go_record`: release_commit, production_url, gate_statuses, unresolved_blockers, accepted_risks, support_owner, rollback_owner, decision, approver, decided_at

## Source Anchors

- `cbsa-commercial-import` - Canada Border Services Agency: [Import commercial goods into Canada](https://www.cbsa-asfc.gc.ca/import/menu-eng.html)
- `cbsa-customs-tariff` - Canada Border Services Agency: [Customs Tariff](https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/menu-eng.html)
- `cbsa-advance-rulings` - Canada Border Services Agency: [Advance rulings for tariff classification](https://www.cbsa-asfc.gc.ca/import/ar-da/menu-eng.html)
- `cfia-importing-food-plants-animals` - Canadian Food Inspection Agency: [Importing food, plants or animals](https://inspection.canada.ca/en/importing-food-plants-animals)
- `cfia-airs` - Canadian Food Inspection Agency: [Automated Import Reference System](https://inspection.canada.ca/en/importing-food-plants-animals/airs)
- `cfia-food-licences` - Canadian Food Inspection Agency: [Food licences](https://inspection.canada.ca/en/food-licences)
- `gac-sanctions` - Global Affairs Canada: [Canadian sanctions](https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/index.aspx?lang=eng)
- `gac-consolidated-sanctions-list` - Global Affairs Canada: [Consolidated Canadian Autonomous Sanctions List](https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/consolidated-consolide.aspx?lang=eng)
- `gac-trade-controls` - Global Affairs Canada: [Export and import controls](https://www.international.gc.ca/controls-controles/index.aspx?lang=eng)
- `opc-pipeda-principles` - Office of the Privacy Commissioner of Canada: [PIPEDA fair information principles](https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/)
- `opc-breach-reporting` - Office of the Privacy Commissioner of Canada: [Privacy breaches at your business](https://www.priv.gc.ca/en/privacy-topics/business-privacy/breaches-and-safeguards/privacy-breaches-at-your-business/gd_pb_201810/)
- `cccs-baseline-controls` - Canadian Centre for Cyber Security: [Baseline cyber security controls for small and medium organizations](https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations)
- `nist-csf-2` - National Institute of Standards and Technology: [Cybersecurity Framework](https://www.nist.gov/cyberframework)
- `cisa-secure-by-design` - Cybersecurity and Infrastructure Security Agency: [Secure by Design](https://www.cisa.gov/securebydesign)
- `owasp-file-upload` - OWASP: [File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- `owasp-asvs` - OWASP: [Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/)
- `owasp-llm01-prompt-injection` - OWASP GenAI Security Project: [LLM01: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- `stripe-go-live` - Stripe: [Go-live checklist](https://docs.stripe.com/get-started/checklist/go-live)
- `stripe-webhooks` - Stripe: [Webhooks](https://docs.stripe.com/webhooks)
- `stripe-testing` - Stripe: [Testing](https://docs.stripe.com/testing)
- `stripe-security` - Stripe: [Security at Stripe](https://docs.stripe.com/security)
- `govuk-user-research` - GOV.UK Service Manual: [User research](https://www.gov.uk/service-manual/user-research)
- `govuk-service-standard` - GOV.UK Service Manual: [Service Standard](https://www.gov.uk/service-manual/service-standard)
- `govuk-service-assessments` - GOV.UK Service Manual: [Service assessments](https://www.gov.uk/service-manual/service-assessments)
- `nng-five-users` - Nielsen Norman Group: [Why You Only Need to Test with 5 Users](https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/)
- `yc-talk-to-users` - Y Combinator: [How to Talk to Users](https://www.ycombinator.com/library/gx-how-to-talk-to-users)
- `w3c-wcag-22` - W3C: [Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/)
- `california-ccpa` - California Department of Justice: [California Consumer Privacy Act](https://oag.ca.gov/privacy/ccpa)

## Unsafe Shortcuts Rejected

- AI-assisted simulated review as approval
- localhost proof as hosted production proof
- Stripe test mode as live payment activation
- generic web search as legal/privacy/security/customs approval
- founder self-test as real user validation
- buyer interest as buyer validation without dated evidence and claim boundaries

## Proof Boundary

This artifact gathers requirements and current source anchors. It does not prove any external approval, legal/privacy/security signoff, qualified customs/trade review, hosted production proof, live payment activation, private-beta outcome, buyer/supplier validation, or public go/no-go.
