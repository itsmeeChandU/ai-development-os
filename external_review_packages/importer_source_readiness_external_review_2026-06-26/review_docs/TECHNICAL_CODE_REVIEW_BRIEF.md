# Technical Code Review Brief

## Scope

Review the product implementation in:

```text
sources/importer-source-readiness-copilot/
```

Also review the helper repos only as supporting process/context:

```text
sources/ai-development-os/
sources/system-review-graph/
sources/code-review-graph-private/
```

## Product Architecture

Main product modules:

- `src/importer_source_readiness/readiness.py`
- `src/importer_source_readiness/external_gates.py`
- `src/importer_source_readiness/continuation.py`
- `src/importer_source_readiness/investor_readiness.py`
- `src/importer_source_readiness/board_readiness.py`
- `src/importer_source_readiness/operator_workflow.py`
- `src/importer_source_readiness/operator_report.py`
- `src/importer_source_readiness/operator_app.py`
- `src/importer_source_readiness/operator_screenshots.py`

Main scripts:

- `scripts/check_product.py`
- `scripts/serve_operator_app.py`
- `scripts/run_readiness.py`
- `scripts/run_external_gates.py`
- `scripts/run_operator_workflow.py`
- `scripts/plan_continuation.py`
- `scripts/build_vc_pitch_packet.py`
- `scripts/build_board_go_live_packet.py`

Main tests:

- `tests/test_readiness.py`
- `tests/test_external_gates.py`
- `tests/test_continuation.py`
- `tests/test_investor_readiness.py`
- `tests/test_board_go_live.py`
- `tests/test_operator_workflow.py`
- `tests/test_operator_app.py`
- `tests/test_operator_screenshots.py`

## Questions

1. Is the code structure clear enough for another engineer to extend?
2. Are the status names and blocker semantics consistent?
3. Are unsafe gates impossible to bypass accidentally?
4. Is the local HTTP app safe and appropriately scoped?
5. Are generated artifacts deterministic enough for review?
6. Are tests meaningful, or do they only assert fixture shape?
7. What should be refactored before adding real data ingestion?
8. What should be changed before deploying to a private beta environment?

## Expected Proof Commands

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_product.py
python3 scripts/serve_operator_app.py --no-open
```

## Known Technical Boundaries

- No database yet.
- No authentication yet.
- No production deployment configuration yet.
- No real external API ingestion yet.
- No customer-facing workflow yet.
- Current data is fixture/reference oriented.

These are expected review findings, but please prioritize which ones block
private beta versus public launch.
