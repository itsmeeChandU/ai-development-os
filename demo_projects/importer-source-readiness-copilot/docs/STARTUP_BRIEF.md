# Startup Brief

## Idea

Build a blocked-safe importer/exporter source readiness copilot for product
operators.

## Source

The idea is based on Intelligence Hub's `IQ-0197` importer/exporter
source-proof packet for frozen tuna fillet readiness. The original lane
attached official/source orientation and explicitly kept customs, tariff,
procurement, buyer, payment, legal, and launch claims closed.

## Target User

Product operators who need to decide whether an importer/exporter source packet
can become internal product work.

## Pain

Source-oriented product ideas are easy to overclaim. A single official source
or fixture row can be mistaken for customs advice, buyer validation, supplier
recommendation, or launch readiness.

## Wedge

Start with a local fixture evaluator that turns source cards into readiness
states and blocker rows. This proves the control surface before any external
data, external send, or legal/compliance claim is allowed.

## First Useful Product

A CLI that reads source cards, emits `ready_with_external_gates`, and writes a
machine-readable readiness report with blocker rows.

## Must-Have Workflows

- load source cards
- check unsafe external counters
- detect missing official-source, freshness, buyer, legal, and contract gates
- write a JSON readiness report
- run unit tests without network access

## Data Needed

Current demo:

- local fixture source cards
- official-source URL placeholders

Production later:

- current official source records
- country requirements matrix
- source rights and freshness policy
- qualified legal/compliance review
- buyer/no-fit/payment evidence rows

## External APIs Needed

None for this demo.

## Risks

- accidental customs/import/export advice claims
- unsupported supplier recommendations
- unsupported buyer validation
- stale source rows
- external sends or paid actions being opened too early

## Claims We Are Not Allowed To Make Yet

- customs or tariff correctness
- supplier recommendation
- buyer demand or PMF
- legal/compliance readiness
- launch readiness
- source freshness beyond fixture proof

## Done When

- tests pass
- `scripts/run_demo.py` writes `system_review_graph/demo_readiness_report.json`
- report status is `ready_with_external_gates`
- unsafe external counters remain zero
- blockers name the next valid move
