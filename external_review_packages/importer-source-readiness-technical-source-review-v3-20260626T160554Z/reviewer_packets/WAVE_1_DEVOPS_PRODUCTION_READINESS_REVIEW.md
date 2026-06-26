# DevOps/Production Readiness Review Packet

Status: `ready_to_send_to_external_reviewer`
Wave: `1`

## Review Boundary

The attached product is locally implemented with external gates. Your decision
must not be treated as legal, customs, tariff, freight, security, privacy,
payment, buyer, production, or public-launch approval unless your role
explicitly covers that claim and your findings say so.

## Ask

Review Docker/Compose, env contract, deployment readiness, health routes, logging, and external hosting gaps.

Required decision: Hosted private-beta readiness decision for infrastructure, config, secrets, logging, and rollback.

## Review These Artifacts

- `Dockerfile`
- `compose.yaml`
- `.env.example`
- `docs/DEPLOYMENT.md`
- `system_review_graph/deployment_readiness_report.json`

## Finding Format

Return every issue with:

`finding_id`, `reviewer_role`, `severity`, `affected_stage`,
`affected_file_or_artifact`, `issue`, `owner`, `required_fix`,
`retest_command`, `blocks_private_beta`, `blocks_public_launch`.

Severity: `P0` unsafe or blocks private beta, `P1` blocks public launch,
`P2` fix before broader beta, `P3` improvement.

## Retest Command

```bash
python3 scripts/check_product.py
```

## Gate

- blocks private beta: `true`
- blocks public launch: `true`
- next valid move: Send Wave 1 DevOps packet, collect structured findings, fix every P0 before hosted private beta.
