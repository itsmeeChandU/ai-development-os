# Instruction Contract

## Goal

Create a complete local product loop that evaluates importer/exporter source
readiness from fixtures and keeps all external gates closed.

## Current-State Claims

| Claim | Status | Evidence |
|---|---|---|
| Intelligence Hub can supply a source-proof import/export idea | proven | `built/importer_export_source_proof_packet/packet.py` in Intelligence Hub |
| The product can run without external data | proven | `data/sample_source_cards.json` |
| The product can produce blocker rows | proven by test target | `src/importer_source_readiness/readiness.py` |

## Constraints

- no network calls
- no external sends
- no paid actions
- no customs, tariff, legal, supplier, buyer, or launch claims
- use fixture data only
- make blocker rows machine-readable

## Non-Goals

- production web UI
- real importer lookup refresh
- contract signing workflow
- qualified legal/compliance review
- buyer discovery automation

## Evidence Required

- unit tests
- CLI smoke run
- generated readiness report
- blocker rows with `next_valid_move`

## Scope

Allowed files:

- `src/importer_source_readiness/**`
- `tests/**`
- `scripts/run_readiness.py`
- `data/sample_source_cards.json`
- `docs/**`
- `system_review_graph/**`
- `handoffs/**`

Forbidden without new approval:

- external API clients
- live send integrations
- payment integrations
- legal/compliance advice text

## Safety Gates

| Gate | State | Reason |
|---|---|---|
| external sends | closed | local product loop must be fixture-only |
| paid actions | closed | no commercial operation allowed |
| customs/tariff advice | closed | requires qualified review and official current source proof |
| buyer validation claims | closed | no dated buyer evidence |
| launch readiness | closed | external evidence missing |

## Next Action

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_readiness.py
```
