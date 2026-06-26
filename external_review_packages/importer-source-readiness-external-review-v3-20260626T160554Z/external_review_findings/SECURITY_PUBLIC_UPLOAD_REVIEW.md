# Security/Public Upload Review

Status: `pending_external_review`
Wave: `1`
Severity floor: `P0`
Affected stage: `hosted_private_beta`

## Scope

Review file upload, quarantine, auth/RBAC, scoped expert links, deletion controls, and public route exposure.

## Primary Artifacts

- `docs/SECURITY_PRIVACY.md`
- `docs/DEPLOYMENT.md`
- `system_review_graph/public_upload_policy.json`
- `system_review_graph/auth_rbac_matrix.json`
- `src/importer_source_readiness/operator_app.py`

## Required Decision

Public upload, file handling, auth/RBAC, and deployment security decision.

## Finding Row Schema

Every finding must include:

- `finding_id`
- `reviewer_role`
- `severity`
- `affected_stage`
- `affected_file_or_artifact`
- `issue`
- `owner`
- `required_fix`
- `retest_command`
- `blocks_private_beta`
- `blocks_public_launch`

Severity guide:

- `P0`: Unsafe or blocks private beta.
- `P1`: Blocks public launch or stronger trade/payment claims.
- `P2`: Fix before broader beta.
- `P3`: Improvement.

## Findings

No external findings have been submitted yet.

Use this exact row shape when findings are received:

```json
{
  "finding_id": "SECURITY_PUBLIC_UPLOAD-001",
  "reviewer_role": "Security/Public Upload Review",
  "severity": "P0",
  "affected_stage": "hosted_private_beta",
  "affected_file_or_artifact": "",
  "issue": "",
  "owner": "security reviewer",
  "required_fix": "",
  "retest_command": "python3 -m unittest tests/test_operator_app.py tests/test_document_processing.py",
  "blocks_private_beta": true,
  "blocks_public_launch": true
}
```

## Gate

- blocks private beta: `true`
- blocks public launch: `true`
- gate state until actual review is recorded: `closed`
- next valid move: Send Wave 1 security packet, collect structured findings, fix every P0 before hosted private beta.
