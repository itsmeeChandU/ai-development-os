# AI-Assisted Security/Public Upload Review Prompt

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

- reviewer_role: `Security/Public Upload Review`
- wave: `1`
- severity floor: `P0`
- affected stage: `hosted_private_beta`
- scope: Review file upload, quarantine, auth/RBAC, scoped expert links, deletion controls, and public route exposure.

## Review These Artifacts

- `docs/SECURITY_PRIVACY.md`
- `docs/DEPLOYMENT.md`
- `system_review_graph/public_upload_policy.json`
- `system_review_graph/auth_rbac_matrix.json`
- `src/importer_source_readiness/operator_app.py`

## Suggested Source Anchors

- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

## Task

1. Inspect the artifacts for this role.
2. If web research is useful, use current sources and list exact URLs.
3. Find unsafe claims, missing controls, confusing UX, missing blocker rows, or
   untested behavior.
4. Return only structured findings plus a short verdict.

## Required Output

```json
{
  "review_origin": "ai_assisted_simulated_review",
  "reviewer_role": "Security/Public Upload Review",
  "model_or_agent_used": "",
  "web_sources_checked": [],
  "verdict": "blocked|needs_fixes|no_p0_p1_found",
  "human_followup_required": true,
  "findings": [
    {
      "finding_id": "SECURITY_PUBLIC_UPLOAD-AI-001",
      "reviewer_role": "Security/Public Upload Review",
      "severity": "P0",
      "affected_stage": "hosted_private_beta",
      "affected_file_or_artifact": "",
      "issue": "",
      "owner": "security reviewer",
      "required_fix": "",
      "retest_command": "python3 -m unittest tests/test_operator_app.py tests/test_document_processing.py",
      "blocks_private_beta": true,
      "blocks_public_launch": true,
      "confidence": "low|medium|high",
      "human_followup_required": true
    }
  ]
}
```
