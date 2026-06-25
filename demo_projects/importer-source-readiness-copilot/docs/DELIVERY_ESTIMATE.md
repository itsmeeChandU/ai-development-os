# Delivery Estimate

## Product Goal

Complete a local blocked-safe importer/exporter source readiness copilot.

## AI-Agent Timeline

| Slice | Estimate |
|---|---:|
| scaffold and project contract | 30 minutes |
| fixture data and evaluator | 45 minutes |
| tests and CLI smoke | 30 minutes |
| generated packets and handoff | 30 minutes |

## Human-Team Timeline

For the same local proof slice: 1-2 days.

For production import/export readiness with real sources, country matrices,
contracts, and qualified review: weeks to months, depending on data access and
external reviewers.

## Accelerated By AI

- scaffold
- fixture evaluator
- unit tests
- generated artifacts
- blocker schema
- operator handoff

## Not Eliminated By AI

- official current source review
- country-specific compliance checks
- supplier/buyer validation
- contract review
- qualified import/export/legal expertise

## Done Criteria

- tests pass
- demo CLI writes report
- report status is `ready_with_external_gates`
- unsafe counters remain zero
- standalone GitHub repo status is either pushed or blocked with next valid move
