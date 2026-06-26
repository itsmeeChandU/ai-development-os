# Product Review Report

## Current Label

Local all-stage product implementation with external gates. The product is
usable as a local/private-beta candidate, but it is not public-launch,
commercially, legally, customs, tariff, CFIA, buyer, supplier, payment, or
shipment ready without human/external evidence.

## What The Product Does

Trade Readiness Copilot helps an importer, exporter, operator, or reviewer turn
a product idea or trade document pile into a bounded readiness packet.

- Beginner start creates real missing-evidence packets from product-only inputs
  or example starts such as exporter furniture, food import, and document-only
  flows.
- PDF quick check accepts bounded PDF uploads, stores generated quarantine
  filenames, extracts native text when available, flags OCR_REQUIRED for scanned
  PDFs, blocks encrypted/invalid/oversized PDFs, estimates OCR credits, and
  requires user confirmation before draft fields become packet context.
- Result pages show readiness lanes, uploaded document triage, missing evidence,
  buyer/broker questions, blocked claims, report exports, source refresh, safe
  AI summary, and delete-files controls.
- Workspace, operator, admin, scoped expert-review, audit, RBAC, AI policy,
  no-AI/manual fallback, redaction preview, and deletion-request surfaces are
  implemented for local/private-beta review.
- Intelligence Hub style policy monitoring defines source snapshots, scheduled
  monitoring jobs, robots/terms/manual-only fields, stale-packet blockers, and
  a SQLite contract while live fetch remains closed.
- Completion-stage contracts cover opportunity signals, country coverage tiers,
  transport/forwarder packets, billing/credit metering, agent/API tools,
  traffic pages, research execution, expert network, team workspace, and launch
  operations.

## Canada-Focused Support

Canada is the primary implemented country path. The product provides Canadian
reference routing and Canada-focused import/export readiness blockers, but it
does not claim current Canadian legal, customs, tariff, CFIA, import permit,
buyer, supplier, or shipment correctness. Those claims require official source
refresh, qualified review, and user/customer evidence.

## Proof Loop

Latest local proof:

```text
python3 -m py_compile src/importer_source_readiness/*.py scripts/*.py
python3 -m unittest discover -s tests -p 'test_*.py' -> 65 tests OK
python3 scripts/run_policy_intelligence.py -> PASS
python3 scripts/run_completion_platform.py -> PASS
python3 scripts/run_product_operations.py -> PASS
python3 scripts/audit_external_package.py --root . -> PASS
python3 scripts/check_product.py -> Product check: PASS
```

Local browser smoke:

```text
http://127.0.0.1:8767/
/start
/trade-check
/opportunities
/country-coverage
/transport-readiness
/pricing
/agent-api
/workspace
/expert-network
/launch-operations
/healthz
```

All returned HTTP 200 in local smoke testing.

## Review Boundaries

The correct review finding is not "fully launch ready." The correct finding is:
local product implementation is ready for private review with explicit external
gates. Human reviewers should inspect product usability, upload/privacy/security
controls, source-monitoring permissions, Canadian trade-compliance boundaries,
expert-review workflow, pricing/metering gates, and the generated reports before
any hosted or public use.

## Start The App

```bash
python3 scripts/serve_operator_app.py --host 127.0.0.1 --port 8767
```

Open `http://127.0.0.1:8767/`.
