# Product Automation Runbook

Use this template when integrating AI Development OS into a specific product,
product factory, or internal operator workflow.

## Product

- name:
- owner:
- repo:
- default branch:
- product category:
- field:
- country or jurisdictions:
- user or buyer:
- first useful product loop:

## Automation Trigger

- trigger type: product UI / API call / GitHub issue / Venture Studio idea / manual operator
- trigger source:
- input artifact path:
- output directory:
- external effects allowed by default: no

## Input Contract

```json
{
  "name": "",
  "idea": "",
  "field": "",
  "country": "",
  "idea_source": "",
  "target_repo": "",
  "external_effects_allowed": false,
  "proof_required": []
}
```

## Required Packets

| Packet | Command | Output | Passing Condition |
|---|---|---|---|
| repo intake | `repo-intake` | `system_review_graph/internal_repo_intake_packet.json` | source and target repo selected or blocked |
| research/data plan | `research-plan` | `system_review_graph/research_data_plan.json` | research depth and data routes selected |
| strategy plan | `strategy-plan` | `system_review_graph/development_strategy_plan.json` | development mode and external gates selected |
| prompt-to-product | `prompt-to-product` | `system_review_graph/prompt_to_product_packet.json` | normalized contract and lane plan emitted |
| lane packet | `lane-packet` | `system_review_graph/lane_packet_<lane>.json` | owned files, forbidden files, and proof commands present |
| continuation plan | product-specific proof command | `system_review_graph/continuation_plan.json` | `ready_with_external_gates` routes to `startup_in_progress` and next evidence lanes |
| VC pitch readiness | product-specific proof command | `system_review_graph/vc_pitch_readiness_report.json` | private pitch state has sources, claim boundaries, and diligence lanes |
| board go-live readiness | product-specific proof command | `system_review_graph/board_go_live_readiness_report.json` | controlled private beta candidate has jurisdiction tools, expert lanes, launch controls, and human approval gates |

## Commands

```bash
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py automation-check

python3 scripts/agentic_workflow_orchestrator.py repo-intake \
  --idea-source "" \
  --target-repo "" \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py research-plan \
  --problem "" \
  --domain "" \
  --data-need "" \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py strategy-plan \
  --idea "" \
  --field "" \
  --country "" \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py prompt-to-product \
  --name "" \
  --idea "" \
  --field "" \
  --country "" \
  --idea-source "" \
  --target-repo "" \
  --out-dir system_review_graph
```

## Agent Lanes

| Lane | Mode | Allowed Files | Forbidden Files | Proof Commands | Handoff |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## External Gates

| Gate | Required Evidence | Owner | Current State | Next Valid Move |
|---|---|---|---|---|
| current web facts | dated links and source notes | research | closed |  |
| official-source review | official docs, rules, or standards | research/compliance | closed |  |
| structured data/API | source contract, credentials, freshness policy | data | closed |  |
| human expert/user validation | dated feedback and corrections | product owner | closed |  |
| contract/commercial terms | written terms and qualified review | legal/operations | closed |  |

## CI Proof

```bash
python3 scripts/ai_dev_os_check.py
python3 scripts/workflow_manifest_check.py
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py automation-check
python3 scripts/eval_suite.py --manifest manifests/agentic_execution_manifest.json --out system_review_graph/eval_report.ci.json
python3 scripts/blocker_ledger.py validate --input system_review_graph/blockers.jsonl --allow-missing --out system_review_graph/blocker_ledger_report.ci.json
python3 scripts/self_test_flow.py
```

## Operator Surface

- latest branch:
- latest commit:
- latest packet:
- latest proof report:
- continuation plan:
- VC pitch report:
- board go-live report:
- readiness state: ready / ready_with_external_gates / blocked
- continuation state: startup_in_progress / externally_operational_candidate / launch_ready
- pitch state: vc_pitch_ready_with_diligence_gates / vc_pitch_blocked / not_applicable
- board state: board_go_live_candidate_with_human_approval_gates / board_go_live_blocked / not_applicable
- open blockers:
- next valid move:
- unsafe gates:

## Handoff

- changed files:
- commands run:
- generated artifacts:
- proof results:
- blockers:
- continuation status:
- external gates:
- next valid move:

## Startup Continuation Rule

If readiness is `ready_with_external_gates`, the product is not fully done or
operational. Write `system_review_graph/continuation_plan.json` with
`status: startup_in_progress`, `must_continue: true`, lane owners, required
evidence, blocker references, proof commands, and closed premature claims.

## VC Pitch Readiness Rule

If the product needs to be pitched to investors, write
`system_review_graph/vc_pitch_readiness_report.json` plus `investor/*.md`.
Keep diligence lanes visible and keep revenue, PMF, buyer validation,
compliance, financing, launch, customs/tariff, and supplier-readiness claims
closed unless proven.

## Board Go-Live Readiness Rule

If the product needs to reach board go-live review, write
`system_review_graph/board_go_live_readiness_report.json` plus `board/*.md`.
Keep jurisdiction-specific tools, simulated expert lanes, launch controls, and
human approval gates visible. Public launch, production deployment, legal,
financial, compliance, buyer, revenue, PMF, and supplier claims remain closed
unless proven and approved.
