# Go-Live Readiness

## Current Label

```text
local all-stage product implementation with external gates
```

The product is complete for the local private-beta candidate scope. It is not
public-production ready, legally ready, customs/tariff ready, CFIA ready,
buyer validated, supplier verified, commercially proven, payment live, or
shipment ready.

## Product Promise

```text
Before you import or export, know what is missing.
```

Customer-facing pages, reports, APIs, and operator artifacts must keep this
promise. They must not imply approval, compliance, tariff confirmation, CFIA
clearance, supplier verification, buyer validation, legal advice, customs
advice, shipment readiness, or public launch approval.

## Completed Local Runbook

The machine-readable source of truth is:

```text
system_review_graph/all_stage_readiness_report.json
```

That artifact represents Stage 0 plus Stages 1-18:

| Stage | Local Status | Boundary |
|---|---|---|
| 0. Freeze product promise | implemented locally | stronger claims require qualified review |
| 1. Beginner Start UX | implemented locally | real beginner usability still needs beta users |
| 2. PDF quick check | implemented locally | hosted upload security review still required |
| 3. Field confirmation and missing evidence | implemented locally | real user comprehension still needs smoke testing |
| 4. Customer-grade reports | implemented locally | report-language review still required |
| 5. Public upload hardening | implemented locally with security gate | hosted sandbox/malware/rate-limit signoff still required |
| 6. AI/no-AI controls | implemented locally fail-closed | live AI provider use still requires approval |
| 7. Saved workspace/account path | implemented locally for private beta | hosted identity/privacy review still required |
| 8. External expert review stage | local packets and queues implemented | real qualified findings still required |
| 9. Policy/source monitoring | implemented locally with refresh gates | live official-source refresh policy still required |
| 10. Country coverage logic | implemented locally with claim gates | country-specific claims require Tier 5 support |
| 11. Opportunity scanner | implemented as signal-only research lane | no demand/profit/buyer proof yet |
| 12. Transport readiness lane | implemented as forwarder questions | no route/cost/shipment approval |
| 13. Billing and credits | implemented locally with no checkout | payment activation still blocked |
| 14. Agent/API layer | implemented locally and scoped | public API keys/effects still blocked |
| 15. UX and usability | locally audited | five-user usability test still required |
| 16. Production deployment readiness | local stack and docs ready | real hosting/ops/security owners still required |
| 17. Private beta | local controls and checklist ready | real beta users and outcomes still required |
| 18. Public go-live | safe subset defined | explicit go/no-go owner approval still required |

## Proof Commands

```bash
python3 -m py_compile src/importer_source_readiness/*.py scripts/*.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_policy_intelligence.py
python3 scripts/run_completion_platform.py
python3 scripts/run_product_operations.py
python3 scripts/audit_external_package.py --root .
python3 scripts/check_product.py
```

Expected local result:

```text
Product check: PASS
status=ready_with_external_gates
startup_status=startup_in_progress
all_stages=all_local_stages_implemented_with_external_gates
unsafe_gates=closed
```

## External Gates

These gates remain closed until dated evidence and owners approve them:

- production hosting, TLS, secrets, backups, monitoring, support, rollback,
  and incident response
- public upload security/privacy/legal review
- qualified customs, tariff, CFIA, sanctions, legal, privacy, and compliance
  review
- real expert findings for the scoped review packet
- real beginner, document-holding, operator, reviewer, broker, or freight
  forwarder smoke-test outcomes
- buyer validation, supplier verification, revenue, PMF, commercial contracts,
  and payment activation
- public go-live owner approval

## Next Valid Move

Run the local proof gate, freeze the review package, collect external findings,
fix critical findings, run private-beta smoke tests, and only then hold a
go/no-go review for the safe public subset.
