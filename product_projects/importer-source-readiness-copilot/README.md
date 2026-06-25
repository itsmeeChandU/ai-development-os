# Importer Source Readiness Copilot

Importer Source Readiness Copilot is a standalone product repo generated from
an Intelligence Hub importer/exporter source-proof lane. Its first completed
loop is a local, blocked-safe readiness engine for source cards.

## Product Goal

Help product operators decide whether an importer/exporter source packet is
ready for internal product work, still blocked on external evidence, or unsafe
because an external-effect gate opened.

This product is intentionally blocked-safe. It does not make customs, tariff,
supplier, buyer, legal, payment, market, launch, or import/export advice
claims.

## Why This Project

The product exists because source-oriented import/export ideas are easy to
overclaim. The completed local loop turns source cards into readiness status,
machine-readable blockers, and a clear next valid move before any external
action is allowed.

The current implementation is intentionally local-first. It uses fixtures to
prove product control logic while external data, contracts, compliance review,
buyer validation, and launch claims stay closed.

## Run

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_readiness.py
python3 scripts/run_external_gates.py
python3 scripts/export_operator_dashboard.py
python3 scripts/check_product.py
```

The product CLI writes:

```text
system_review_graph/readiness_report.json
system_review_graph/external_gate_report.json
system_review_graph/blockers.jsonl
system_review_graph/operator_dashboard.html
```

## Expected State

The expected local product status is:

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
- qualified broker/expert review
- source rights and refresh policy
- public launch claims
- paid actions
- external sends
- customs/tariff/import-export advice

## Next Valid Move

Use `system_review_graph/operator_dashboard.html` as the operator surface.
The product can now show exactly what is stopping external use. To open any
external claim gate, attach dated evidence to `data/evidence_packets.json`,
verify country rows in `data/country_requirements_matrix.json`, and rerun
`python3 scripts/check_product.py`.
