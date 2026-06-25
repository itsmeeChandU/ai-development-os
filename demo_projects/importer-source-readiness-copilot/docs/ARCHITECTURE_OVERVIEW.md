# Architecture Overview

## System Shape

```text
data/sample_source_cards.json
        |
        v
src/importer_source_readiness/readiness.py
        |
        v
system_review_graph/demo_readiness_report.json
```

## Modules

| Module | Responsibility |
|---|---|
| `data/sample_source_cards.json` | fixture source and gate rows |
| `src/importer_source_readiness/readiness.py` | evaluate source cards and produce blocker rows |
| `scripts/run_demo.py` | CLI entrypoint and report writer |
| `tests/test_readiness.py` | proof for blocked-safe behavior |
| `system_review_graph/` | generated packets, reports, blockers, handoff evidence |

## Data Flow

1. Load source-card fixtures.
2. Evaluate unsafe counters.
3. Check official-source, freshness, buyer, legal, and contract gates.
4. Emit row-level status.
5. Flatten blockers into a report.
6. Write report to `system_review_graph/demo_readiness_report.json`.

## Status Rules

| Status | Meaning |
|---|---|
| `ready` | all local and external gates proven |
| `ready_with_external_gates` | local logic works but external evidence is still missing |
| `blocked_unsafe` | an unsafe external counter or unsupported claim opened |

The expected demo status is `ready_with_external_gates`.

## Proof Boundary

The architecture proves local fixture evaluation only. It does not prove
customs, tariff, supplier, buyer, legal, payment, launch, or market readiness.
