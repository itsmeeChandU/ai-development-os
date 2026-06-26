# Start Here

Status: `development_complete_local_go_live_contract; external_validation_pending`

This repository is the standalone Trade Readiness Copilot product. It is a
blocked-safe import/export readiness checker whose public promise is:

```text
Before you import or export, know what is missing.
```

## What To Review First

1. `WHAT_WE_ARE_BUILDING.md`
2. `CURRENT_SLICE_VS_TARGET_PRODUCT.md`
3. `FINAL_GO_LIVE_HANDOFF.md`
4. `docs/GO_LIVE_READINESS.md`
5. `docs/EXTERNAL_REVIEW_PROCESS.md`
6. `system_review_graph/final_go_live_decision_report.json`
7. `system_review_graph/all_stage_readiness_report.json`
8. `system_review_graph/external_review_findings_report.json`

## Current Truth

The local Stage 0-18 implementation is complete and reviewable. Public launch
is not approved. Hosted private beta is not approved. External claims remain
blocked until real reviewer, staging, privacy/security/legal, beta-user, and
owner-approval evidence exists.

## Allowed Decisions

Use these labels only:

- `approve_within_scope`
- `block`
- `needs_more_evidence`
- `out_of_scope`
- `wrong_reviewer_type`

## Do Not Treat This As

- customs advice
- tariff advice
- CFIA approval
- legal/privacy approval
- security approval
- supplier verification
- buyer validation
- payment activation approval
- production deployment approval
- public launch approval

## Proof Commands

```bash
python3 -m py_compile src/importer_source_readiness/*.py scripts/*.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/audit_external_package.py --root .
python3 scripts/check_product.py
python3 scripts/run_final_go_live_review.py
```
