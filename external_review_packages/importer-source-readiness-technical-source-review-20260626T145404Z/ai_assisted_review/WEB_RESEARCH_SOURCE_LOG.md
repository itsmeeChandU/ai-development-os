# Web Research Source Log

Status: `ready_for_ai_assisted_review`

Record the exact sources checked by each AI-assisted reviewer. Keep this
separate from `external_review_findings/` unless a real qualified reviewer
has provided the decision.

## Seed Sources

### AI Safety/Prompt Injection Review

- OWASP LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
  - use: Prompt-injection and model-input/output risk review anchor.
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
  - use: AI risk framing, governance, measurement, and monitoring review anchor.

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
