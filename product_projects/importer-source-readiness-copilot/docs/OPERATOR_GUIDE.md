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
exports the operator dashboard, writes the continuation plan, and verifies that
unsafe gates remain closed. It also writes the VC pitch packet and verifies
that investor-facing claims remain bounded.

## Operator Surface

Open:

```text
system_review_graph/operator_dashboard.html
```

The dashboard shows readiness status, external-gate status, official source
references, blockers, and next valid moves.

Open the continuation plan when deciding what work continues next:

```text
system_review_graph/continuation_plan.json
```

If the readiness or external-gate status is `ready_with_external_gates`, the
continuation status must stay `startup_in_progress`. That is the repo-enforced
signal that the software loop can be useful internally while the startup is not
yet fully operational or launch ready.

Open the investor packet for private VC conversations:

```text
investor/vc_pitch_deck.md
investor/one_pager.md
investor/demo_script.md
investor/diligence_room_index.md
system_review_graph/vc_pitch_readiness_report.json
```

The expected pitch status is `vc_pitch_ready_with_diligence_gates`. It allows a
private investor conversation with clear diligence lanes; it does not open
public launch, revenue, PMF, compliance, supplier, buyer-validation, customs, or
tariff claims.

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

## Daily Continuation Loop

1. Run `python3 scripts/check_product.py`.
2. Read `system_review_graph/continuation_plan.json`.
3. Pick one lane with `status: blocked_external_input`.
4. Collect the lane evidence or write the blocker reason and next valid move.
5. Rerun the proof gate before changing any operational, launch, legal,
   customs, tariff, supplier, buyer, or commercial claim.

## VC Pitch Loop

1. Run `python3 scripts/check_product.py`.
2. Read `system_review_graph/vc_pitch_readiness_report.json`.
3. Use `investor/vc_pitch_deck.md` for the pitch and
   `investor/demo_script.md` for the demo.
4. Keep the diligence lanes open in the conversation rather than hiding them.
5. Do not send fundraising documents as legal or securities documents until
   counsel reviews the terms.
