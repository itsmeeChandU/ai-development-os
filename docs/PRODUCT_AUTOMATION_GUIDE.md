# Product Automation Guide

Use this guide when a product team wants AI Development OS to run inside an
actual product workflow: idea intake, agent routing, worktree/lane assignment,
proof checks, blocker rows, and handoff generation.

This is the product-facing path. The internal architecture docs explain why the
workflow exists. This guide explains how people can use it.

## Audience

- founders turning startup ideas into buildable product loops
- product teams adding AI development automation to an existing repo
- platform engineers wiring agents, GitHub, SRG, and code-review graph outputs
- operators who need a clear readiness and blocker surface

## What The Product Automates

The product should not ask an agent to "just build it" from a raw prompt. It
should convert a user idea into artifacts that agents can execute safely:

1. repo intake: where the idea came from and where code should be built
2. research/data plan: whether model knowledge, web search, official sources,
   datasets, APIs, or experts are required
3. development strategy: which field mode and agents are needed
4. prompt-to-product packet: normalized goal, constraints, proof, lanes, and
   next valid move
5. context bundle: SRG and code-review graph context for bounded source review
6. lane packet: allowed files, forbidden files, proof commands, and handoff
7. proof report: tests, generated artifacts, blockers, and launch state
8. operator screenshot surface: generated screenshots and visual proof manifest
9. continuation plan: required next lanes when the product is only internally
   ready with external gates
10. VC pitch packet: investor-safe claims, demo script, diligence lanes, and
   pitch readiness report
11. board go-live packet: jurisdiction tools, expert-agent review lanes,
    launch controls, human approval gates, and board readiness report

## Minimum Product Integration

Add these pieces to the product or product-factory repo:

- `AGENTS.md`: tells agents how to work in that repo.
- `system_review_graph/`: stores generated packets, proof, and blockers.
- `handoffs/`: stores CI-fix, lane, and review handoffs.
- GitHub remote: canonical branch and proof history.
- optional Ruflo integration: coordination memory only.
- optional SRG context bundle: bounded system-level context.
- optional code-review graph contract: files, modules, symbols, imports, edges,
  tests, generated artifacts, and risk/ownership hints.

The product must treat generated packets as coordination surfaces. Completion
still requires code/data changes, tests, generated artifacts, and branch proof.
For startup-style product work, the product should also maintain
`docs/STARTUP_LIFECYCLE.md` or an equivalent lifecycle artifact that names the
current stage, R&D loops, operator evidence, validation blockers, and next
valid move.
If a product reports `ready_with_external_gates`, completion also requires a
`system_review_graph/continuation_plan.json` artifact that keeps the startup
`startup_in_progress` and names the next evidence lanes.
If a product needs to be pitched to investors, completion also requires
`system_review_graph/vc_pitch_readiness_report.json` plus investor artifacts
with claim boundaries and open diligence lanes.
If a product needs to reach board go-live review, completion also requires
`system_review_graph/board_go_live_readiness_report.json` plus `board/*.md`
with jurisdiction-specific tools, expert simulations, launch controls, and
human approval gates.
If a product has an operator UI, completion also requires an operator-visible
screenshot surface such as `system_review_graph/operator_screenshot_manifest.json`
and screenshot artifacts that the dashboard can render. Screenshots are visual
proof aids; generated reports, tests, blocker ledgers, and approval gates remain
canonical.

## Input Contract

A product UI, API, or operator form should collect this shape:

```json
{
  "name": "supplier-risk-copilot",
  "idea": "Build a supplier risk product for import/export operators.",
  "field": "manufacturing",
  "country": "US",
  "idea_source": "intelligence-hub",
  "target_repo": "future-product-repo",
  "external_effects_allowed": false,
  "proof_required": ["tests", "generated_artifacts", "handoff"]
}
```

Keep `external_effects_allowed` false by default. Network writes, paid APIs,
legal claims, live execution, broker activity, production deploys, and signed
contracts need explicit operator approval plus passing gates.

## Automated Command Flow

Run the commands from the AI Development OS repo or from a product automation
job that has this repo available.

```bash
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py automation-check

python3 scripts/agentic_workflow_orchestrator.py repo-intake \
  --idea-source intelligence-hub \
  --target-repo future-product-repo \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py research-plan \
  --problem "Build a supplier risk product for import/export operators." \
  --domain manufacturing \
  --data-need "supplier data, official country rules, tariffs, certifications, contract terms" \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py strategy-plan \
  --idea "Build a supplier risk product for import/export operators." \
  --field manufacturing \
  --country US \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py prompt-to-product \
  --name supplier-risk-copilot \
  --idea "Build a supplier risk product for import/export operators." \
  --field manufacturing \
  --country US \
  --idea-source intelligence-hub \
  --target-repo future-product-repo \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py emit-slash-commands \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py lane-packet \
  --lane workflow-coordinator \
  --goal "Own the first verified product loop" \
  --out-dir system_review_graph
```

## Product Runtime Pattern

In a product, wire the flow as a state machine:

| State | Product Action | Output |
|---|---|---|
| idea_received | save idea packet and source | immutable intake record |
| repo_selected | run repo intake | repo packet or blocker |
| research_routed | run research/data plan | research gates and data blockers |
| strategy_selected | run strategy plan | development mode and external gates |
| packet_created | run prompt-to-product | product packet and lane plan |
| context_loaded | load SRG/code-review graph | bounded context bundle |
| lane_assigned | create worktree/branch/lane packet | worker handoff |
| proof_running | run tests and artifact checks | proof report |
| blocked_or_ready | publish blocker/readiness state | next valid move |
| operator_visual_proof_ready | publish generated screenshots and manifest | operator screenshot gallery |
| continuation_required | write continuation plan for externally gated work | evidence lanes and closed premature claims |
| vc_pitch_ready | write investor packet and pitch readiness report | private pitch state and diligence lanes |
| board_go_live_candidate | write board packet and go-live readiness report | controlled private beta candidate and human approval gates |

Do not skip from `idea_received` to `lane_assigned` for complex products. The
router is what prevents the product from treating manufacturing, regulated,
data, and contract work as simple app work.

## Agent Assignment

Use the strategy plan to pick agents:

- software-local: architect, surgeon, reviewer
- data/API: research, data, architect, surgeon, reviewer
- AI/ML: research, data, eval, surgeon, reviewer
- regulated/high-stakes: research, compliance, reviewer, qualified expert
- hardware/manufacturing: hardware, procurement, simulation, manufacturing
- cross-border: research, procurement, compliance, operations
- contract-dependent: legal, operations, reviewer

Every worker receives only:

- goal
- allowed files
- forbidden files
- proof commands
- artifact paths
- blocker schema
- handoff format

## External Evidence Rules

AI model knowledge can produce the first hypothesis. It is not final proof for:

- buyer demand
- current prices or availability
- country rules, tariffs, customs, certifications, or sanctions checks
- legal, medical, financial, safety, or compliance claims
- supplier/manufacturer readiness
- signed contracts or partner rights
- product launch claims

For these, the product must collect dated source records, official-source
evidence, datasets/API contracts, qualified expert review, user feedback, or a
blocker row with `next_valid_move`.

## Startup Continuation Rule

`ready_with_external_gates` means the local software loop can be useful
internally. It does not mean the startup is done, operational, launch ready,
commercially ready, legally ready, buyer validated, supplier ready, or
customs/tariff ready.

When this status appears, the product must write
`system_review_graph/continuation_plan.json` with:

- `status: startup_in_progress`
- `must_continue: true`
- evidence lanes for buyer validation, qualified review, country rules, source
  rights/freshness, contracts, restricted-party screening, and launch approval
- `closed_claims` that include `fully_operational`, `launch_ready`, and
  `commercially_ready`
- `next_valid_move` for the next evidence lane

## VC Pitch Readiness Rule

`vc_pitch_ready_with_diligence_gates` means a product is ready for a private VC
conversation with a demo, cited sources, bounded claims, a draft ask, and open
diligence lanes. It does not mean public launch, revenue, product-market fit,
buyer validation, legal/compliance approval, customs/tariff advice readiness,
supplier readiness, or financing documents are complete.

Generate:

- `system_review_graph/vc_pitch_readiness_report.json`
- `investor/vc_pitch_deck.md`
- `investor/one_pager.md`
- `investor/demo_script.md`
- `investor/diligence_room_index.md`

## Board Go-Live Readiness Rule

`board_go_live_candidate_with_human_approval_gates` means a product is ready
for board review and controlled-private-beta decisioning. It does not mean
public launch, production deployment, legal advice, financial advice,
customs/tariff advice, regulated compliance, buyer validation, revenue, PMF, or
supplier readiness.

Generate:

- `system_review_graph/board_go_live_readiness_report.json`
- `board/board_go_live_brief.md`
- `board/expert_review_packet.md`
- `board/launch_control_checklist.md`
- `board/financial_operating_model.md`

## CI And Scheduled Automation

Use CI to keep the automation surface honest:

```bash
python3 scripts/ai_dev_os_check.py
python3 scripts/workflow_manifest_check.py
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py automation-check
python3 scripts/eval_suite.py --manifest manifests/agentic_execution_manifest.json --out system_review_graph/eval_report.ci.json
python3 scripts/blocker_ledger.py validate --input system_review_graph/blockers.jsonl --allow-missing --out system_review_graph/blocker_ledger_report.ci.json
python3 scripts/self_test_flow.py
```

Use scheduled jobs only for safe checks: branch freshness, stale blocker sweep,
context refresh, eval loops, and CI triage. Do not schedule live external
execution unless a product owner explicitly opens that gate.

## Demo Script For People

Use this short explanation when presenting the product flow:

```text
The user gives us a startup or product idea. AI Development OS turns that idea
into a repo intake packet, a research/data plan, a development strategy, and a
lane packet. Agents then work only inside bounded branches with proof commands.
If the product needs current data, official rules, contracts, manufacturing
inputs, or subject experts, the system does not guess. It writes the blocker and
the next valid move. The output is not just code; it is code plus evidence,
blockers, handoffs, and readiness state.
```

## Done Criteria

The product automation is working when:

- a vague idea creates all required packets
- complex ideas route to the right research/data and strategy gates
- lane packets include owned files, forbidden files, and proof commands
- missing data/contracts/experts become blocker rows
- tests and generated artifact checks run in CI
- the operator surface shows ready vs blocked with `next_valid_move`
- operator-generated screenshots are visible through a generated manifest and gallery when UI behavior matters
- externally gated products generate continuation lanes before completion claims
- investor-pitch products generate VC readiness artifacts before pitch claims
- go-live products generate board readiness artifacts before launch claims
- no external effect opens without explicit approval and proof
