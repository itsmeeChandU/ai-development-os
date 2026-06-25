# Automation Runtime Report

```json
{
  "blockers": [
    {
      "evidence": "manifests/agentic_execution_manifest.json",
      "gate": "closed",
      "id": "routine:context_bundle_refresh:missing-inputs",
      "issue": "routine needs runtime inputs before execution",
      "module": "automation_runtime",
      "next_valid_move": "Provide SRG_MANIFEST, CODE_REVIEW_GRAPH_CONTRACT.",
      "owner": "context_bundle_refresh",
      "unsafe_to_bypass": true
    },
    {
      "evidence": "manifests/agentic_execution_manifest.json",
      "gate": "closed",
      "id": "routine:ci_failure_triage:missing-inputs",
      "issue": "routine needs runtime inputs before execution",
      "module": "automation_runtime",
      "next_valid_move": "Provide CHECK_NAME, FAILURE_LOG.",
      "owner": "ci_failure_triage",
      "unsafe_to_bypass": true
    }
  ],
  "generated_at": "2026-06-25T16:46:22+00:00",
  "kind": "background_routine_report",
  "proof_boundary": "Routine reports describe safe commands and blockers. Effectful execution still requires explicit operator intent.",
  "routine_count": 8,
  "routines": [
    {
      "allowed_effects": [
        "git fetch",
        "git status",
        "git merge-base checks"
      ],
      "cadence": "before every lane and merge",
      "commands": [
        "git fetch origin --prune",
        "git status --short --branch",
        "git merge-base --is-ancestor origin/main HEAD"
      ],
      "dry_run_default": true,
      "id": "branch_freshness_check",
      "missing_inputs": [],
      "prohibited_effects": [
        "destructive reset",
        "force push without explicit instruction"
      ],
      "proof_output": "branch freshness row in handoff",
      "status": "ready",
      "trigger": "lane_start or merge_start"
    },
    {
      "allowed_effects": [
        "load SRG bundle",
        "emit bounded context JSON"
      ],
      "cadence": "before lane assignment and after contract changes",
      "commands": [
        "system-review-graph load-repo-context-bundle --manifest ${SRG_MANIFEST} --code-review-graph ${CODE_REVIEW_GRAPH_CONTRACT} --agentic-workflow manifests/agentic_execution_manifest.json"
      ],
      "dry_run_default": true,
      "id": "context_bundle_refresh",
      "missing_inputs": [
        "SRG_MANIFEST",
        "CODE_REVIEW_GRAPH_CONTRACT"
      ],
      "prohibited_effects": [
        "copy private data into generated docs"
      ],
      "proof_output": "repo_context_bundle path or missing-context blocker",
      "status": "needs_input",
      "trigger": "srg_manifest or code_review_graph_contract changes"
    },
    {
      "allowed_effects": [
        "read blocker ledgers",
        "mark stale blockers with next_valid_move"
      ],
      "cadence": "daily or before final handoff",
      "commands": [
        "python3 scripts/blocker_ledger.py validate --input system_review_graph/blockers.jsonl --allow-missing"
      ],
      "dry_run_default": true,
      "id": "stale_blocker_sweep",
      "missing_inputs": [],
      "prohibited_effects": [
        "close blocker without evidence"
      ],
      "proof_output": "current blocker table",
      "status": "ready",
      "trigger": "goal checkpoint"
    },
    {
      "allowed_effects": [
        "read generated reports",
        "write continuation plan",
        "write blocker rows"
      ],
      "cadence": "before completion claims for product/startup work",
      "commands": [],
      "dry_run_default": true,
      "id": "startup_continuation_sweep",
      "missing_inputs": [],
      "prohibited_effects": [
        "claim fully operational or launch ready while must_continue is true"
      ],
      "proof_output": "system_review_graph/continuation_plan.json",
      "status": "ready",
      "trigger": "readiness or external-gate status is ready_with_external_gates"
    },
    {
      "allowed_effects": [
        "read generated reports",
        "write investor packet",
        "write VC pitch readiness report"
      ],
      "cadence": "before investor pitch claims",
      "commands": [],
      "dry_run_default": true,
      "id": "vc_pitch_readiness_sweep",
      "missing_inputs": [],
      "prohibited_effects": [
        "claim revenue, PMF, legal, financing, compliance, buyer, supplier, customs, tariff, public launch, or full operational proof without evidence"
      ],
      "proof_output": "system_review_graph/vc_pitch_readiness_report.json",
      "status": "ready",
      "trigger": "product needs VC pitch readiness"
    },
    {
      "allowed_effects": [
        "read generated reports",
        "write board packet",
        "write board go-live readiness report"
      ],
      "cadence": "before go-live, board, private beta, or launch-readiness claims",
      "commands": [],
      "dry_run_default": true,
      "id": "board_go_live_readiness_sweep",
      "missing_inputs": [],
      "prohibited_effects": [
        "claim public launch, production deployment, legal, financial, compliance, buyer, revenue, PMF, supplier, customs, tariff, or regulated proof without qualified human approval"
      ],
      "proof_output": "system_review_graph/board_go_live_readiness_report.json",
      "status": "ready",
      "trigger": "product needs board go-live readiness"
    },
    {
      "allowed_effects": [
        "run idempotent tests",
        "run validators",
        "write eval report"
      ],
      "cadence": "overnight when requested and safe",
      "commands": [
        "python3 scripts/eval_suite.py --manifest manifests/agentic_execution_manifest.json --out system_review_graph/eval_report.json"
      ],
      "dry_run_default": true,
      "id": "nightly_eval_loop",
      "missing_inputs": [],
      "prohibited_effects": [
        "live external execution",
        "paid API usage without budget gate"
      ],
      "proof_output": "eval report with command results",
      "status": "ready",
      "trigger": "long-running goal with bounded proof commands"
    },
    {
      "allowed_effects": [
        "read CI logs",
        "classify failure",
        "write fix lane packet"
      ],
      "cadence": "on CI failure",
      "commands": [
        "python3 scripts/agentic_workflow_orchestrator.py ci-fix --check-name ${CHECK_NAME} --failure-log ${FAILURE_LOG} --out-dir handoffs"
      ],
      "dry_run_default": true,
      "id": "ci_failure_triage",
      "missing_inputs": [
        "CHECK_NAME",
        "FAILURE_LOG"
      ],
      "prohibited_effects": [
        "hide failing checks",
        "weaken tests without a task contract"
      ],
      "proof_output": "CI blocker or verified fix branch",
      "status": "needs_input",
      "trigger": "GitHub check failure"
    }
  ],
  "status": "ready_with_input_blockers"
}
```
