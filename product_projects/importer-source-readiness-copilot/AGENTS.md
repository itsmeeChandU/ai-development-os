# Agent Instructions

This is a standalone AI Development OS product project.

## Product

- name: importer-source-readiness-copilot
- type: dataapp
- idea: Build a blocked-safe importer/exporter source readiness copilot for product operators using fixture data, official-source placeholders, country requirement gaps, and explicit external-gate blockers.

## First Read

Before meaningful work, read:

1. `README.md`
2. `docs/STARTUP_BRIEF.md`
3. `docs/INSTRUCTION_CONTRACT.md`
4. `docs/DELIVERY_ESTIMATE.md`
5. `docs/ARCHITECTURE_OVERVIEW.md`
6. `docs/WORK_PACKAGE.md`
7. `docs/PRODUCT_AUTOMATION_RUNBOOK.md`
8. `docs/PRODUCT_STATUS.md`
9. `system_review_graph/README.md`
10. `system_review_graph/STATE_RECONSTRUCTION_REPORT.md`

## Operating Rules

- Treat this repo as truth; treat prompts and generated packets as claims until verified.
- Fill the startup brief and instruction contract before broad implementation.
- Keep the first useful product loop small enough to test locally.
- Use fixture data until real data rights, credentials, freshness, and source lineage are proven.
- Keep external effects closed by default: no paid calls, live sends, legal claims, production deploys, or public launch claims without explicit approval and proof.
- Write missing data, API, expert, legal, procurement, or compliance inputs as blocker rows with `next_valid_move`.
- Every implementation lane needs allowed files, forbidden files, proof commands, generated artifacts, and a handoff.
- Do not claim completion without code/data changes where required, tests or smoke checks, generated artifacts, blockers, and next valid move.

## Proof Defaults

Start with local checks:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_readiness.py
python3 scripts/check_product.py
```

Add stronger proof commands as the project grows.
