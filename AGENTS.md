# Agent Instructions

This repository is an operating kit for AI-native software delivery. Agents
must optimize for useful shipped systems, not impressive plans.

## First Read

Before meaningful work, read:

1. `README.md`
2. `docs/INSTRUCTION_NORMALIZATION.md`
3. `docs/COMPLEXITY_ROUTER.md`
4. `docs/STATE_RECONSTRUCTION.md`
5. `docs/AGENTIC_COMPANY_MODEL.md`
6. `docs/DELIVERY_ESTIMATION.md`
7. `docs/AI_NATIVE_DELIVERY.md`
8. `docs/PRODUCT_AUTOMATION_GUIDE.md`
9. `docs/SYSTEM_REVIEW_GRAPH.md`
10. `docs/STARTUP_CONTINUATION_RULE.md`
11. `docs/VC_PITCH_READINESS.md`
12. `docs/BOARD_GO_LIVE_READINESS.md`
13. `manifests/tool_registry.yaml`
14. `manifests/agentic_workflow_manifest.json`
15. `manifests/agentic_execution_manifest.json`
16. `manifests/internal_repo_registry.json`
17. `manifests/research_data_router.json`
18. `manifests/development_strategy_router.json`
19. the relevant template in `templates/`

## Operating Rules

- Work from repo truth, not memory or chat summaries.
- Normalize imperfect instructions into goal, constraints, evidence, gates, scope, assumptions, and next action.
- Classify complexity first; keep calculator-scale tasks lightweight and escalate only when the product requires it.
- Treat user-provided current state as claims until verified.
- Produce estimates and architecture overviews before large execution, then compare estimate vs actual.
- Turn fuzzy ideas into a written task contract before implementation.
- Audit code, data, flows, risks, resources, and current artifacts before broad edits.
- Use the system review graph for complex work.
- Prefer small proof loops over giant implementation waves.
- Split parallel work by owned files and modules.
- Every worker needs: goal, allowed files, forbidden files, tests, artifacts, blocker schema, handoff.
- Do not claim completion unless the generated artifact and focused verification prove it.
- If blocked by external state or missing data, create a blocker artifact with `next_valid_move`.
- Keep safety gates simple and binary: no fake proof, no fake fills, no hidden execution, no unsupported claims.
- Do not remove attribution, imply official association, or create proprietary exceptions without a written commercial/association license.
- Do not imply Sai Chandra or AI Development OS is responsible for derivative products built with this toolkit.
- Contributions must follow `CONTRIBUTING.md`, `CONTRIBUTOR_TERMS.md`, and `DCO.txt`.
- For hardware, OS, regulated, or physical-world products, use `docs/COMPLEX_PRODUCT_PLAYBOOK.md` and add simulation/bench/compliance blockers.
- For prompt-to-product work, run repo intake, research/data routing, and development strategy routing before assigning implementation lanes.
- For prompt-to-product work, `ready_with_external_gates` means continue with `system_review_graph/continuation_plan.json`; never report fully done, operational, launch ready, legally ready, customs/tariff ready, supplier ready, buyer validated, or commercially ready while `must_continue` is true.
- For VC pitch readiness, generate `system_review_graph/vc_pitch_readiness_report.json` and investor artifacts; pitch-ready can mean private investor conversation ready with diligence gates, not launch ready or securities/legal/compliance proof.
- For board/go-live readiness, generate `system_review_graph/board_go_live_readiness_report.json` plus `board/*.md`; board-ready means controlled private beta candidate with jurisdiction tools, simulated expert lanes, launch controls, and human approval gates, not public launch or qualified legal/financial/compliance proof.
- Treat AI model subject synthesis as a first-pass hypothesis; current facts, datasets, official rules, contracts, country import/export needs, and final subject direction need evidence, qualified people, or blocker rows.
- For broad tool selection, use `docs/TOOL_BREEDING_GROUND.md` and write a tool decision record before adopting major dependencies.
- Update durable instructions only when a mistake repeats or a workflow becomes stable.

## Definition Of Done

A task is done only when all of these are true:

- code or data changed where required
- tests or checks were added/updated where useful
- generated artifacts reflect current truth
- all known blockers have owner, reason, evidence, and next valid move
- startup/product work with external gates has a continuation plan, or the goal was explicitly scoped as local-only
- VC-pitch work has investor sources, claim boundaries, diligence lanes, and closed premature claims
- board/go-live work has jurisdiction-specific tools, expert-review simulation, launch controls, human approval gates, and closed public-launch/legal/financial/compliance claims
- unsafe or effectful actions remain closed unless explicitly proven and intended
- handoff file names changed files, commands run, results, blockers, and next move

## AI-Native Defaults

- Use Codex worktrees/subagents for parallel work when lanes can be bounded.
- Use MCP/connectors for live external context.
- Use skills for repeatable workflows.
- Use generated reports as truth surfaces.
- Use research only to fill a repo-proven capability gap.
- For durable multi-repo agentic workflow work, use
  `manifests/agentic_workflow_manifest.json` as the machine-readable contract
  and `manifests/agentic_execution_manifest.json` as the runnable command contract,
  the internal repo, research/data, and strategy routers for prompt-to-product
  selection, and `docs/AGENTIC_WORKFLOW_INTEGRATION.md` as the concise human
  guide.
