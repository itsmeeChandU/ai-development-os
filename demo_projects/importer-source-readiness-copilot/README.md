# Importer Source Readiness Copilot

Fixture-only product demo generated from an Intelligence Hub importer/exporter
source-proof lane.

## Product Goal

Help product operators decide whether an importer/exporter source packet is
ready for internal product work, still blocked on external evidence, or unsafe
because an external-effect gate opened.

This demo is intentionally blocked-safe. It does not make customs, tariff,
supplier, buyer, legal, payment, market, launch, or import/export advice
claims.

## Why This Project

This is a useful test project before larger AI Development OS builds because it
exercises the full prompt-to-product path:

- Intelligence Hub sourced idea
- repo intake
- research/data routing
- development strategy routing
- fixture implementation
- generated readiness report
- blocker rows
- local proof commands
- handoff surface

## Run

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_demo.py
```

The demo writes:

```text
system_review_graph/demo_readiness_report.json
```

## Expected State

The expected demo status is:

```text
ready_with_external_gates
```

That means the local product logic works, but final product claims remain
blocked until real external evidence exists.

## External Gates Kept Closed

- buyer validation
- legal/compliance review
- commercial/source contracts
- current data freshness
- official country/import/export requirements
- paid actions
- external sends
- customs/tariff/import-export advice

## Next Valid Move

Use this demo to test AI Development OS on a bounded product. For a production
version, create a standalone private product repo, wire current official-source
refreshes, add country requirement matrices, and collect qualified review before
any external or public claim.
