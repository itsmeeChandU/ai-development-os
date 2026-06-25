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
python3 scripts/plan_continuation.py
python3 scripts/build_vc_pitch_packet.py
python3 scripts/build_board_go_live_packet.py
python3 scripts/check_product.py
```

The product CLI writes:

```text
system_review_graph/readiness_report.json
system_review_graph/external_gate_report.json
system_review_graph/continuation_plan.json
system_review_graph/vc_pitch_readiness_report.json
system_review_graph/board_go_live_readiness_report.json
system_review_graph/blockers.jsonl
system_review_graph/operator_dashboard.html
investor/vc_pitch_deck.md
investor/one_pager.md
investor/demo_script.md
investor/diligence_room_index.md
board/board_go_live_brief.md
board/expert_review_packet.md
board/launch_control_checklist.md
board/financial_operating_model.md
```

## Expected State

The expected local product status is:

```text
ready_with_external_gates
```

That means the local product logic works, but final product claims remain
blocked until real external evidence exists.

`ready_with_external_gates` is never a final startup status. The product check
also writes `system_review_graph/continuation_plan.json`; that plan must say
`startup_in_progress`, `must_continue: true`, and list the next buyer,
compliance, country, data, contract, screening, and launch evidence lanes.

The expected investor-pitch status is:

```text
vc_pitch_ready_with_diligence_gates
```

That means the product has a private VC conversation packet, evidence-backed
claim boundaries, and a demo script. It still does not prove launch readiness,
revenue, product-market fit, buyer validation, supplier readiness, or legal /
customs / tariff readiness.

The expected board/go-live status is:

```text
board_go_live_candidate_with_human_approval_gates
```

That means the Canada-focused implementation is ready for board review and a
controlled-private-beta decision. The AI-built system has simulated product,
Canadian trade compliance, financial, legal/privacy, data, and security/ops
review lanes, plus a Canadian tool registry and launch controls. It still
requires human approval before public launch, production deployment,
legal/financial/customs/tariff/CFIA claims, buyer validation, or spend
commitments.

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
- public go-live or production deployment approval
- Canadian legal/privacy/finance/compliance signoff

## Next Valid Move

Use `system_review_graph/operator_dashboard.html` as the operator surface.
Use `system_review_graph/continuation_plan.json` as the continuation surface.
Use `investor/vc_pitch_deck.md` and `investor/one_pager.md` for private VC
conversations. Use `board/board_go_live_brief.md` and
`system_review_graph/board_go_live_readiness_report.json` for board review.
The product can now show exactly what is stopping external use and which lane
must move next. To open any external claim gate, attach dated evidence to
`data/evidence_packets.json`, verify country rows in
`data/country_requirements_matrix.json`, and rerun
`python3 scripts/check_product.py`.
