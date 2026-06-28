# Security And Privacy Review Brief

## Review Goal

Review the local operator app and process for privacy, security, operations,
and deployment readiness.

## Current State

- Local HTTP app only.
- No authentication.
- No user accounts.
- No production deployment.
- No live external sends.
- No paid actions.
- No credentials required.
- Fixture/reference data only.

## Questions

1. What security controls are needed before private beta?
2. What privacy notices or data handling terms are needed before real user data?
3. What audit logging should exist?
4. What access control should exist?
5. What backup/restore or incident response process is needed?
6. What should be changed before this is hosted?
7. What PIPEDA or Canadian privacy issues should be reviewed?
8. What support and rollback process is required?

## Files To Inspect

- `sources/importer-source-readiness-copilot/src/importer_source_readiness/operator_app.py`
- `sources/importer-source-readiness-copilot/scripts/serve_operator_app.py`
- `sources/importer-source-readiness-copilot/data/canada_tool_registry.json`
- `evidence/board_packet/launch_control_checklist.md`

## Expected Finding

The product should not be deployed to external users without auth, access
control, privacy review, data handling policy, logs, support coverage, and
rollback ownership.
