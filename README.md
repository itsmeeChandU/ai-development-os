# AI Development OS

An open-source operating kit for shipping software with AI agents without
repeating the usual failure mode: too much chat, not enough repo truth.

This repo is designed for the next agent. It gives them a concrete process,
tool registry, task templates, system-review graph, and proof gates so a vague
startup idea can become a working product through auditable AI-native loops.

## Core Idea

AI agents do not work like human developers. They need the repo to carry the
truth:

- clear task contracts
- code, data, flow, and resource audits
- system review graph before implementation
- file-level ownership boundaries
- generated artifacts that prove current state
- focused tests and launch gates
- handoff packets for every worker

The goal is not to write more instructions. The goal is to make the next agent
able to discover what matters, decide how much instruction is needed, and prove
progress in files.

Users do not need to write perfect prompts. The agent should normalize messy
instructions into a stable contract, verify current-state claims, estimate the
delivery path, and then execute proof loops.

## Fast Start

```bash
python3 scripts/ai_dev_os_check.py
python3 scripts/scaffold_project.py --name my-startup --idea "One sentence idea"
```

Then open the generated project and give Codex or another agent:

```text
Read AGENTS.md, docs/INSTRUCTION_NORMALIZATION.md,
docs/STATE_RECONSTRUCTION.md, docs/SYSTEM_REVIEW_GRAPH.md,
docs/AGENTIC_COMPANY_MODEL.md, and templates/DELIVERY_ESTIMATE.md.
Reconstruct the actual current product state, estimate the architecture and
lane plan, then turn the idea into a working product using the AILM loop. Do
not stop at docs: implement code, tests, data flows, generated artifacts, and a
handoff.
```

## AILM Loop

AILM means AI Lifecycle Management:

1. Intake: clarify the idea, user, promise, constraints, and non-goals.
2. Normalize: convert imperfect instructions into an execution contract.
3. Audit: inspect code, data, workflow, risks, and external resources.
4. Reconstruct: convert prompt, repo, data, and runtime evidence into current state.
5. Estimate: produce architecture, lane plan, tool/data needs, and timeline.
6. Instrument: create reports, generated artifacts, and tests.
7. Lane split: assign bounded agents with owned files and proof commands.
8. Make: implement code/data/UI/integration slices.
9. Verify: run focused tests, lint, generated report checks, and smoke tests.
10. Launch: produce a single operator surface with current truth and blockers.
11. Monitor: keep recurring checks, stale-artifact alerts, and handoffs.

## What This Repo Contains

- `AGENTS.md`: durable instructions for future agents.
- `CONTRIBUTING.md`, `CONTRIBUTOR_TERMS.md`, and `DCO.txt`: contribution rules that preserve open-source and dual-license optionality.
- `GOVERNANCE.md`, `SECURITY.md`, `DISCLAIMER.md`, and `TRADEMARKS.md`: project control, reporting, responsibility, and association boundaries.
- `docs/INSTRUCTION_NORMALIZATION.md`: how agents convert imperfect instructions into execution contracts.
- `docs/COMPLEXITY_ROUTER.md`: when to use light flow versus full company/complex-product flow.
- `docs/AGENTIC_COMPANY_MODEL.md`: AI-native company operating model.
- `docs/DELIVERY_ESTIMATION.md`: architecture, lane, cost, and timeline estimation.
- `docs/AI_NATIVE_DELIVERY.md`: how to run AI-native development at scale.
- `docs/AGENTIC_WORKFLOW_INTEGRATION.md`: durable GitHub/Ruflo/worktree/SRG/code-review graph workflow.
- `docs/SYSTEM_REVIEW_GRAPH.md`: the audit graph pattern that worked.
- `docs/STATE_RECONSTRUCTION.md`: how to recover actual product state from a prompt and repo truth.
- `docs/AI_LIFECYCLE.md`: AI-native lifecycle, different from human SDLC.
- `docs/BIDIRECTIONAL_PRODUCT_LOOP.md`: top-down, bottom-up, and product-to-idea loops.
- `docs/PROMPT_TO_PRODUCT.md`: when a simple prompt is enough and when tools/data are required.
- `docs/COMPLEX_PRODUCT_PLAYBOOK.md`: hardware/OS/regulated/physical-world product workflow.
- `docs/TOOL_BREEDING_GROUND.md`: staged tool ecosystem for complex products.
- `docs/STRATEGY_RESEARCH_PLAYBOOK.md`: product strategy research patterns for agents.
- `docs/TOOLCHAIN.md`: curated open-source tool stack with links.
- `docs/OPEN_SOURCE_RESOURCES.md`: researched links and what each resource is for.
- `docs/RESEARCH_INTAKE.md`: how to add new tools without guessing.
- `docs/CODEX_USAGE.md`: how to use Codex, worktrees, skills, MCP, and subagents.
- `manifests/tool_registry.yaml`: machine-readable tool registry.
- `manifests/agent_lanes.yaml`: default multi-agent lanes.
- `manifests/agentic_workflow_manifest.json`: machine-readable coordinator workflow for agents and LLMs.
- `manifests/agentic_execution_manifest.json`: slash-command, routine, CI, eval, and lane-packet contract.
- `templates/*`: prompts/specs/handoffs for agents.
- `scripts/ai_dev_os_check.py`: validates this operating kit.
- `scripts/agentic_workflow_orchestrator.py`: validates and emits multi-repo execution plans.
- `scripts/scaffold_project.py`: creates a new AI-native project skeleton.
- `.github/*`: issue, PR, and CI community health files.
- `examples/*`: self-test prompts for tiny and complex products.

## License

AI Development OS is public under `AGPL-3.0-or-later` with an attribution
notice. Derivative public versions and hosted/network versions must keep the
same copyleft posture and preserve:

```text
Built with AI Development OS by Sai Chandra.
```

See `LICENSE`, `NOTICE.md`, and `docs/LICENSING.md`.

If someone wants a private/proprietary derivative, attribution changes,
closed-source hosted use, official association, or partner/commercial terms,
they need a separate written license or agreement from Sai Chandra. See
`docs/COMMERCIAL_AND_ASSOCIATION.md` and `TRADEMARKS.md`.

Derivative product owners are responsible for their own products, claims,
data, deployments, compliance, and outcomes. See `DISCLAIMER.md`.

## Default Rule

If the agent cannot prove a claim from code, data, tests, generated artifacts,
or cited research, it must call it a blocker and write the next valid move.

For complex products, local software completion is not enough. Hardware,
firmware/OS, simulation, bench validation, procurement, compliance, and field
operation must each have evidence or blocker rows.

## Multi-Repo Execution

For durable agentic delivery, validate the workflow contract and emit a bounded
lane plan before spawning workers:

```bash
python3 scripts/workflow_manifest_check.py
python3 scripts/agentic_workflow_orchestrator.py validate
python3 scripts/agentic_workflow_orchestrator.py emit \
  --goal "Build the first verified product loop" \
  --out-dir system_review_graph
```

The emitted plan is a machine-readable coordination surface. It does not replace
source inspection, tests, generated artifacts, or GitHub branch proof.
