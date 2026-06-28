# Trade Readiness Copilot Audit Review Package

Prepared: 2026-06-26 UTC

## Scope

This package is for external audit/review of the current prompt-to-product
implementation:

- Public product: Trade Readiness Copilot
- Internal engine: Importer Source Readiness Copilot
- Coordinator repo: AI Development OS
- Use case added in this round: Export-to-Canada readiness for foreign exporters

## Included Snapshots

- `product_repo/`: standalone product repository snapshot
- `ai_development_os_repo/`: AI Development OS snapshot with embedded product
  project and validator updates

Git metadata is excluded. Commit references:

- Product repo: `44824005092e4cc69996a6a6c9f8e95b7fbbf7df`
- AI Development OS: `f93c763384aee36bfee6974db57694d9d18b01a4`

## What To Review First

Product repo:

- `product_repo/README.md`
- `product_repo/docs/PUBLIC_TRADE_READINESS.md`
- `product_repo/CUSTOMER_SOURCE_PACKET_SPEC.md`
- `product_repo/docs/REQUIREMENTS_ANALYSIS.md`
- `product_repo/system_review_graph/public_trade_readiness_manifest.json`
- `product_repo/system_review_graph/exporter_mode_requirements.json`
- `product_repo/system_review_graph/product_runtime_state.json`
- `product_repo/tests/test_operator_app.py`
- `product_repo/tests/test_source_packet_workflow.py`

AI Development OS:

- `ai_development_os_repo/README.md`
- `ai_development_os_repo/AGENTS.md`
- `ai_development_os_repo/manifests/agentic_workflow_manifest.json`
- `ai_development_os_repo/manifests/agentic_execution_manifest.json`
- `ai_development_os_repo/scripts/product_project_check.py`
- `ai_development_os_repo/product_projects/importer-source-readiness-copilot/`

## Current App

The local app was verified in Safari at:

```text
http://127.0.0.1:8766/trade-check
```

The visible quick-check flow includes:

- trade direction selector
- India-to-Canada exporter defaults
- product/category and optional HS code
- exporter and Canadian buyer/importer fields
- importer-of-record and Incoterms selectors
- PDF upload
- AI/data notice
- draft quick-check submission

## Proof Commands Already Passed

Product repo:

```bash
python3 -m py_compile src/importer_source_readiness/*.py scripts/*.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_product.py
git diff --check
```

AI Development OS:

```bash
python3 scripts/product_project_check.py
python3 scripts/ai_dev_os_check.py
python3 scripts/self_test_flow.py
python3 scripts/workflow_manifest_check.py
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py automation-check
python3 scripts/eval_suite.py
python3 scripts/blocker_ledger.py validate --input product_projects/importer-source-readiness-copilot/system_review_graph/blockers.jsonl --out /tmp/ados-product-blockers-public-trade.json
python3 -m py_compile scripts/*.py product_projects/importer-source-readiness-copilot/scripts/*.py product_projects/importer-source-readiness-copilot/src/importer_source_readiness/*.py
git diff --check
```

## Expected Status

- Product status: `ready_with_external_gates`
- Public quick-check status: `public_quick_check_ready_local_with_external_gates`
- AI OS embedded product check: PASS
- VC-pitch status: `vc_pitch_ready_with_diligence_gates`
- Board/go-live status: `board_go_live_candidate_with_human_approval_gates`

## Important Boundaries

This implementation is locally operational and review/pitch-ready with explicit
external gates. It does not claim:

- public launch readiness
- legal advice or legal approval
- customs/tariff advice
- CFIA clearance
- shipment readiness
- buyer validation
- supplier recommendation
- trade-agreement or MoU preference confirmation
- production security/privacy/compliance certification

AI review and AI subject synthesis are first-pass structured assistance only.
Qualified people, current official sources, brokers/compliance reviewers, and
real buyer/operator evidence remain required before external decisions.
