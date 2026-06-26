# Security/Public Upload Review Packet

Status: `ready_to_send_to_external_reviewer`
Wave: `1`

## Review Boundary

The attached product is locally implemented with external gates. Your decision
must not be treated as legal, customs, tariff, freight, security, privacy,
payment, buyer, production, or public-launch approval unless your role
explicitly covers that claim and your findings say so.

## Ask

Review file upload, quarantine, auth/RBAC, scoped expert links, deletion controls, and public route exposure.

Required decision: Public upload, file handling, auth/RBAC, and deployment security decision.

## Review These Artifacts

- `docs/SECURITY_PRIVACY.md`
- `docs/DEPLOYMENT.md`
- `system_review_graph/public_upload_policy.json`
- `system_review_graph/auth_rbac_matrix.json`
- `src/importer_source_readiness/operator_app.py`

## Finding Format

Return every issue with:

`finding_id`, `reviewer_role`, `severity`, `affected_stage`,
`affected_file_or_artifact`, `issue`, `owner`, `required_fix`,
`retest_command`, `blocks_private_beta`, `blocks_public_launch`.

Severity: `P0` unsafe or blocks private beta, `P1` blocks public launch,
`P2` fix before broader beta, `P3` improvement.

## Retest Command

```bash
python3 -m unittest tests/test_operator_app.py tests/test_document_processing.py
```

## Gate

- blocks private beta: `true`
- blocks public launch: `true`
- next valid move: Send Wave 1 security packet, collect structured findings, fix every P0 before hosted private beta.
