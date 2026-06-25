# Architecture Overview

## System Shape

```text
data/sample_source_cards.json
data/country_requirements_matrix.json
data/evidence_packets.json
data/official_source_registry.json
data/canada_tool_registry.json
data/expert_review_simulations.json
data/launch_controls.json
        |
        v
src/importer_source_readiness/readiness.py
src/importer_source_readiness/external_gates.py
src/importer_source_readiness/continuation.py
src/importer_source_readiness/investor_readiness.py
src/importer_source_readiness/board_readiness.py
src/importer_source_readiness/operator_report.py
src/importer_source_readiness/operator_screenshots.py
        |
        v
system_review_graph/readiness_report.json
system_review_graph/external_gate_report.json
system_review_graph/continuation_plan.json
system_review_graph/vc_pitch_readiness_report.json
system_review_graph/board_go_live_readiness_report.json
system_review_graph/operator_screenshot_manifest.json
system_review_graph/operator_dashboard.html
system_review_graph/operator_screenshots/*.png
investor/*.md
board/*.md
```

## Modules

| Module | Responsibility |
|---|---|
| `data/sample_source_cards.json` | fixture source and gate rows |
| `data/country_requirements_matrix.json` | country-specific requirement review rows |
| `data/evidence_packets.json` | buyer, expert, contract, source-rights, and launch evidence gates |
| `data/official_source_registry.json` | official source references and claim boundaries |
| `data/canada_tool_registry.json` | Canadian official tools for board/go-live review |
| `data/expert_review_simulations.json` | AI-simulated expert review lanes with human approval gates |
| `data/launch_controls.json` | controlled private beta and go-live approval controls |
| `src/importer_source_readiness/readiness.py` | evaluate source cards and produce blocker rows |
| `src/importer_source_readiness/external_gates.py` | evaluate country and evidence gates |
| `src/importer_source_readiness/continuation.py` | convert external blockers into required continuation lanes |
| `src/importer_source_readiness/investor_readiness.py` | build VC pitch readiness and diligence gates |
| `src/importer_source_readiness/board_readiness.py` | build Canada-focused board/go-live candidate readiness |
| `src/importer_source_readiness/operator_report.py` | render static operator dashboard |
| `src/importer_source_readiness/operator_screenshots.py` | index operator-generated screenshot artifacts for dashboard review |
| `scripts/run_readiness.py` | CLI entrypoint and report writer |
| `scripts/run_external_gates.py` | external-gate report writer |
| `scripts/export_operator_dashboard.py` | dashboard exporter |
| `scripts/plan_continuation.py` | continuation plan writer |
| `scripts/build_vc_pitch_packet.py` | investor packet and pitch readiness writer |
| `scripts/build_board_go_live_packet.py` | board packet and go-live candidate writer |
| `tests/test_readiness.py` | proof for blocked-safe behavior |
| `tests/test_external_gates.py` | proof for external-gate and dashboard behavior |
| `tests/test_continuation.py` | proof that externally gated status keeps work in progress |
| `tests/test_investor_readiness.py` | proof that pitch status keeps diligence and claim gates visible |
| `tests/test_board_go_live.py` | proof that Canada board/go-live candidate status keeps human approval gates visible |
| `tests/test_operator_screenshots.py` | proof that screenshot artifacts are indexed and rendered without replacing generated truth |
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
9. Convert blockers into `system_review_graph/continuation_plan.json`.
10. Convert pitch evidence into `system_review_graph/vc_pitch_readiness_report.json`.
11. Write investor pitch, one-pager, demo, and diligence artifacts.
12. Convert Canadian tools, expert simulations, and launch controls into
    `system_review_graph/board_go_live_readiness_report.json`.
13. Write board go-live brief, expert review packet, launch checklist, and
    financial operating model.
14. Index operator screenshots in
    `system_review_graph/operator_screenshot_manifest.json`.
15. Render `system_review_graph/operator_dashboard.html` with the screenshot
    gallery and generated proof boundary.

## Status Rules

| Status | Meaning |
|---|---|
| `ready` | all local and external gates proven |
| `ready_with_external_gates` | local logic works but external evidence is still missing |
| `blocked_unsafe` | an unsafe external counter or unsupported claim opened |

The expected local product status is `ready_with_external_gates`.
That is not a final startup status. If either gate report is
`ready_with_external_gates`, the continuation plan must say
`startup_in_progress` and `must_continue: true`.

The expected investor status is `vc_pitch_ready_with_diligence_gates`. It
means a private VC pitch is supported by a demo, sources, and diligence lanes;
it does not mean the product is launch ready or externally operational.

The expected board status is
`board_go_live_candidate_with_human_approval_gates`. It means the Canada-focused
implementation can be placed in front of a board for controlled-private-beta
decisioning. It does not mean public launch, production deployment, customs,
tariff, CFIA, legal, financial, buyer, revenue, or PMF proof.

## Proof Boundary

The architecture proves local fixture evaluation only. It does not prove
customs, tariff, supplier, buyer, legal, payment, launch, or market readiness.
