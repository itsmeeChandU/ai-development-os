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
writes the continuation plan, writes the VC pitch packet, writes the
Canada-focused board/go-live packet, builds the operator work queue, exports
the operator dashboard, and verifies that unsafe gates remain closed.

## Operator Surface

Run:

```bash
python3 scripts/serve_operator_app.py
```

Then open the printed local URL. The server exposes the dashboard plus JSON
routes such as `/api/operator-workflow`, `/api/readiness`, and
`/api/external-gates`.

The generated dashboard artifact is:

```text
system_review_graph/operator_dashboard.html
```

The app shows readiness status, external-gate status, official source
references, blockers, next valid moves, the generated work queue, and the
generated screenshot gallery.

This is the internal operator application. It is not a public customer app,
customs/tariff advice product, supplier marketplace, or external launch surface.

The machine-readable operator queue is:

```text
system_review_graph/operator_workflow_report.json
```

It combines source-card actions, external evidence gates, continuation lanes,
human approval gates, Canadian tool references, closed claims, and proof
commands. Treat it as the daily operating queue.

Operator-generated screenshots are indexed in:

```text
system_review_graph/operator_screenshot_manifest.json
system_review_graph/operator_screenshots/
```

The screenshot gallery is visual evidence only. Generated JSON reports,
blocker ledgers, tests, and human approval gates remain canonical for readiness
claims.

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

Open the board packet for go-live review:

```text
board/board_go_live_brief.md
board/expert_review_packet.md
board/launch_control_checklist.md
board/financial_operating_model.md
system_review_graph/board_go_live_readiness_report.json
```

The expected board status is
`board_go_live_candidate_with_human_approval_gates`. It allows the board to
decide whether a controlled private beta should start. It does not open public
launch, production deployment, legal advice, financial advice, customs/tariff
advice, CFIA compliance, buyer validation, revenue, or PMF claims.

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
- Canadian privacy/PIPEDA and public-claim legal review
- founder/accountant/finance approval for projections, spend, and financing terms
- security/ops approval for deployment, access, incident response, support, and rollback
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

## Board Go-Live Loop

1. Run `python3 scripts/check_product.py`.
2. Read `system_review_graph/board_go_live_readiness_report.json`.
3. Open `board/board_go_live_brief.md` and `board/launch_control_checklist.md`.
4. Treat AI-simulated expert lanes as first-pass review, not final signoff.
5. Board may approve a controlled private beta only after assigning owners for
   Canadian customs/compliance, legal/privacy, finance, data, and security
   approval gates.
