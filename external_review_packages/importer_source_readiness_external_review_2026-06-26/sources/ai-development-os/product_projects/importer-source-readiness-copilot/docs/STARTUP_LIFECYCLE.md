# Startup Lifecycle

## Current Stage

- lifecycle status: `board_go_live_candidate_with_human_approval_gates`
- current thesis: Canadian import/export operators need a blocked-safe source-readiness copilot before making supplier, buyer, customs, tariff, or launch claims.
- target user/operator: founder, sourcing operator, trade/compliance reviewer, and board/private-beta owner.
- first useful workflow: review source cards, country gates, evidence blockers, generated screenshots, continuation lanes, investor packet, and board go-live packet.
- current product slice: local fixture-backed source-readiness loop with generated operator dashboard and screenshot gallery.
- next valid move: collect dated buyer/operator feedback and qualified Canadian customs/compliance review while launch claims stay closed.

## Stage Evidence

| Stage | Status | Artifact | Proof / Blocker | Next Valid Move |
|---|---|---|---|---|
| idea intake | complete | `docs/STARTUP_BRIEF.md` | Intelligence Hub source-proof idea captured | refine thesis after real operator feedback |
| research routing | complete with gates | `system_review_graph/research_data_plan.json` | Canada official-source lane exists | add repeatable official-source refresh proof |
| R&D exploration | active | `research/`, `simulation/`, `data/*.json` | fixture and Canadian tool registry prove local loop only | run qualified review and data-source experiments |
| product slice | complete locally | `docs/WORK_PACKAGE.md` | source readiness, external gates, dashboard, screenshots, continuation, pitch, and board packets exist | validate with operators |
| implementation | complete locally | `src/`, `scripts/`, `tests/` | `python3 scripts/check_product.py` passes | keep proof gates green as evidence changes |
| operator evidence | ready | `system_review_graph/operator_screenshot_manifest.json` | generated dashboard screenshot is visible in operator surface | add screenshots for future user flows |
| validation | blocked externally | `system_review_graph/continuation_plan.json` | buyer/operator, contract, data, expert, and launch gates remain open | collect dated evidence rows |
| VC readiness | ready with diligence | `system_review_graph/vc_pitch_readiness_report.json` | private conversation packet exists | use diligence lanes honestly |
| board/private beta | candidate with human gates | `system_review_graph/board_go_live_readiness_report.json` | board packet exists; human approvals remain open | board approves or redirects controlled beta |
| launch/operate | not approved | `board/launch_control_checklist.md` | public launch and production deployment claims closed | approve owners, controls, support, and rollback |
| learning loop | active | `handoffs/ESTIMATE_VS_ACTUAL.md` | handoff captures proof and blockers | update thesis after real reviews |

## R&D Loops

| Hypothesis | Experiment | Artifact | Result | Decision | Next Valid Move |
|---|---|---|---|---|---|
| Canadian source readiness can be reviewed without unsafe external action | fixture-backed source cards plus country/evidence gate reports | `system_review_graph/readiness_report.json`, `system_review_graph/external_gate_report.json` | local loop passes with external gates visible | continue | add real buyer/operator evidence |
| Operators need visual proof of generated surfaces | capture dashboard screenshot and index it in a manifest | `system_review_graph/operator_screenshot_manifest.json` | dashboard renders screenshot gallery | continue | add screenshots for additional operator flows |
| Board review can happen before public launch | generate Canada tools, expert simulations, launch controls, and board packet | `system_review_graph/board_go_live_readiness_report.json`, `board/*.md` | candidate state reached with human gates visible | continue | assign approval owners |

## Proof Boundary

AI can create first-pass product, research, R&D, screenshots, and operator
packets. Real buyer demand, Canadian customs/compliance approval, legal/privacy
approval, financial approval, data rights, contracts, public launch approval,
and qualified subject truth remain evidence lanes or blockers until proven.
