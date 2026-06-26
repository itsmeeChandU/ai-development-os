# Web Research Source Log

Status: `wave_1_ai_assisted_sources_recorded`

Record the exact sources checked by each AI-assisted reviewer. Keep this
separate from `external_review_findings/` unless a real qualified reviewer
has provided the decision.

## Seed Sources

### AI Safety/Prompt Injection Review

- OWASP LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
  - use: Prompt-injection and model-input/output risk review anchor.
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
  - use: AI risk framing, governance, measurement, and monitoring review anchor.

### Billing/Payment Review

- Stripe go-live checklist: https://docs.stripe.com/get-started/checklist/go-live
  - use: Live checkout, webhook, support, refund, and payment activation review anchor.

### DevOps/Production Readiness Review

- Canadian Centre for Cyber Security baseline controls: https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations
  - use: Hosted private-beta operations, access control, backup, monitoring, and incident-response review anchor.

### Privacy/Legal Review

- Office of the Privacy Commissioner of Canada PIPEDA guidance: https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/
  - use: Canadian privacy-law self-check anchor for notices, consent, access, retention, and safeguards.

### Security/Public Upload Review

- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
  - use: Public upload, validation, storage, malware, and access-control review anchor.

### Trade-Boundary/Customs-Language Review

- CBSA importing commercial goods: https://www.cbsa-asfc.gc.ca/import/menu-eng.html
  - use: Canadian import/customs boundary and official-source language anchor.
- CFIA importing food, plants, or animals: https://inspection.canada.ca/en/importing-food-plants-animals
  - use: Food/agriculture import-control boundary anchor for report wording.

## Wave 1 Run Records

These records are AI-assisted simulated reviews. They are not real
qualified external approval.

### UX/Product Usability Review

```json
{
  "finding_file": "ai_assisted_review/simulated_findings/WAVE_1_UX_PRODUCT_REVIEW.json",
  "model_or_agent_used": "Codex GPT-5 simulated reviewer",
  "notes": "blocked",
  "queries_or_sources_checked": [
    "README.md",
    "docs/GO_LIVE_READINESS.md",
    "system_review_graph/operator_dashboard.html",
    "system_review_graph/customer_readiness_report.md",
    "system_review_graph/public_trade_readiness_manifest.json"
  ],
  "reviewer_role": "UX/Product Usability Review",
  "searched_at": "2026-06-26T14:36:31Z",
  "source_urls": []
}
```

### Security/Public Upload Review

```json
{
  "finding_file": "ai_assisted_review/simulated_findings/WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.json",
  "model_or_agent_used": "Codex GPT-5 simulated reviewer",
  "notes": "blocked",
  "queries_or_sources_checked": [
    "docs/SECURITY_PRIVACY.md",
    "docs/DEPLOYMENT.md",
    "system_review_graph/public_upload_policy.json",
    "system_review_graph/auth_rbac_matrix.json",
    "src/importer_source_readiness/operator_app.py"
  ],
  "reviewer_role": "Security/Public Upload Review",
  "searched_at": "2026-06-26T14:36:31Z",
  "source_urls": [
    "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html"
  ]
}
```

### Privacy/Legal Review

```json
{
  "finding_file": "ai_assisted_review/simulated_findings/WAVE_1_PRIVACY_LEGAL_REVIEW.json",
  "model_or_agent_used": "Codex GPT-5 simulated reviewer",
  "notes": "blocked",
  "queries_or_sources_checked": [
    "REVIEW_USE_TERMS.md",
    "docs/AI_DATA_POLICY.md",
    "docs/SECURITY_PRIVACY.md",
    "system_review_graph/ai_data_policy.json",
    "system_review_graph/deletion_requests.json"
  ],
  "reviewer_role": "Privacy/Legal Review",
  "searched_at": "2026-06-26T14:36:31Z",
  "source_urls": [
    "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/"
  ]
}
```

### AI Safety/Prompt Injection Review

```json
{
  "finding_file": "ai_assisted_review/simulated_findings/WAVE_1_AI_SAFETY_REVIEW.json",
  "model_or_agent_used": "Codex GPT-5 simulated reviewer",
  "notes": "blocked",
  "queries_or_sources_checked": [
    "docs/AI_DATA_POLICY.md",
    "system_review_graph/ai_model_router.json",
    "system_review_graph/redaction_pipeline.json",
    "system_review_graph/manual_no_ai_workflow.json",
    "tests/test_operator_app.py"
  ],
  "reviewer_role": "AI Safety/Prompt Injection Review",
  "searched_at": "2026-06-26T14:36:31Z",
  "source_urls": [
    "https://genai.owasp.org/llmrisk/llm01-prompt-injection/",
    "https://www.nist.gov/itl/ai-risk-management-framework"
  ]
}
```

### DevOps/Production Readiness Review

```json
{
  "finding_file": "ai_assisted_review/simulated_findings/WAVE_1_DEVOPS_PRODUCTION_READINESS_REVIEW.json",
  "model_or_agent_used": "Codex GPT-5 simulated reviewer",
  "notes": "blocked",
  "queries_or_sources_checked": [
    "Dockerfile",
    "compose.yaml",
    ".env.example",
    "docs/DEPLOYMENT.md",
    "system_review_graph/deployment_readiness_report.json"
  ],
  "reviewer_role": "DevOps/Production Readiness Review",
  "searched_at": "2026-06-26T14:36:31Z",
  "source_urls": [
    "https://www.cyber.gc.ca/en/guidance/baseline-cyber-security-controls-small-and-medium-organizations"
  ]
}
```

## Run Log Template

```json
{
  "reviewer_role": "",
  "model_or_agent_used": "",
  "searched_at": "",
  "queries_or_sources_checked": [],
  "source_urls": [],
  "notes": "",
  "finding_file": "ai_assisted_review/simulated_findings/ROLE.json"
}
```
