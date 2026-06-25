# Operator Guide

## Purpose

Use this product to decide whether an importer/exporter source packet is safe
for internal product work, blocked on evidence, or unsafe because an external
gate opened.

## Daily Local Proof

```bash
python3 scripts/check_product.py
```

This command runs unit tests, regenerates readiness and external-gate reports,
exports the operator dashboard, and verifies that unsafe gates remain closed.

## Operator Surface

Open:

```text
system_review_graph/operator_dashboard.html
```

The dashboard shows readiness status, external-gate status, official source
references, blockers, and next valid moves.

## What Is Stopping External Use

The current stopping surface is generated in:

```text
system_review_graph/external_gate_report.json
```

External use stays blocked until these records are updated with real evidence:

- `data/country_requirements_matrix.json`
- `data/evidence_packets.json`
- `data/official_source_registry.json`

## Gates That Cannot Be Fabricated

- qualified customs/import/export review
- qualified food safety or legal/compliance review
- written commercial/source/data contracts
- buyer or operator validation
- repeatable source-rights and freshness proof
- public launch approval

Do not set a gate to `verified` unless dated evidence is attached and the
responsible owner can defend it.
