# Architecture Overview

## System Shape

```text
data/sample_source_cards.json
data/country_requirements_matrix.json
data/evidence_packets.json
data/official_source_registry.json
        |
        v
src/importer_source_readiness/readiness.py
src/importer_source_readiness/external_gates.py
src/importer_source_readiness/operator_report.py
        |
        v
system_review_graph/readiness_report.json
system_review_graph/external_gate_report.json
system_review_graph/operator_dashboard.html
```

## Modules

| Module | Responsibility |
|---|---|
| `data/sample_source_cards.json` | fixture source and gate rows |
| `data/country_requirements_matrix.json` | country-specific requirement review rows |
| `data/evidence_packets.json` | buyer, expert, contract, source-rights, and launch evidence gates |
| `data/official_source_registry.json` | official source references and claim boundaries |
| `src/importer_source_readiness/readiness.py` | evaluate source cards and produce blocker rows |
| `src/importer_source_readiness/external_gates.py` | evaluate country and evidence gates |
| `src/importer_source_readiness/operator_report.py` | render static operator dashboard |
| `scripts/run_readiness.py` | CLI entrypoint and report writer |
| `scripts/run_external_gates.py` | external-gate report writer |
| `scripts/export_operator_dashboard.py` | dashboard exporter |
| `tests/test_readiness.py` | proof for blocked-safe behavior |
| `tests/test_external_gates.py` | proof for external-gate and dashboard behavior |
| `system_review_graph/` | generated packets, reports, blockers, handoff evidence |

## Data Flow

1. Load source-card fixtures.
2. Evaluate unsafe counters.
3. Check official-source, freshness, buyer, legal, and contract gates.
4. Emit row-level status.
5. Flatten blockers into a report.
6. Write report to `system_review_graph/readiness_report.json`.
7. Evaluate country, buyer, expert, contract, source-rights, and launch gates.
8. Write `system_review_graph/external_gate_report.json`.
9. Render `system_review_graph/operator_dashboard.html`.

## Status Rules

| Status | Meaning |
|---|---|
| `ready` | all local and external gates proven |
| `ready_with_external_gates` | local logic works but external evidence is still missing |
| `blocked_unsafe` | an unsafe external counter or unsupported claim opened |

The expected local product status is `ready_with_external_gates`.

## Proof Boundary

The architecture proves local fixture evaluation only. It does not prove
customs, tariff, supplier, buyer, legal, payment, launch, or market readiness.
