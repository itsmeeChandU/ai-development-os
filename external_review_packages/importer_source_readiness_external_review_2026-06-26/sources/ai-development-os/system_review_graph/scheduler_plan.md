# Scheduler Plan

```json
{
  "entries": [
    {
      "cadence": "before every lane and merge",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine branch_freshness_check --out-dir system_review_graph",
      "effectful": false,
      "id": "branch_freshness_check",
      "proof_output": "branch freshness row in handoff",
      "trigger": "lane_start or merge_start"
    },
    {
      "cadence": "before lane assignment and after contract changes",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine context_bundle_refresh --out-dir system_review_graph",
      "effectful": false,
      "id": "context_bundle_refresh",
      "proof_output": "repo_context_bundle path or missing-context blocker",
      "trigger": "srg_manifest or code_review_graph_contract changes"
    },
    {
      "cadence": "daily or before final handoff",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine stale_blocker_sweep --out-dir system_review_graph",
      "effectful": false,
      "id": "stale_blocker_sweep",
      "proof_output": "current blocker table",
      "trigger": "goal checkpoint"
    },
    {
      "cadence": "before completion claims for product/startup work",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine startup_continuation_sweep --out-dir system_review_graph",
      "effectful": false,
      "id": "startup_continuation_sweep",
      "proof_output": "system_review_graph/continuation_plan.json",
      "trigger": "readiness or external-gate status is ready_with_external_gates"
    },
    {
      "cadence": "before investor pitch claims",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine vc_pitch_readiness_sweep --out-dir system_review_graph",
      "effectful": false,
      "id": "vc_pitch_readiness_sweep",
      "proof_output": "system_review_graph/vc_pitch_readiness_report.json",
      "trigger": "product needs VC pitch readiness"
    },
    {
      "cadence": "before go-live, board, private beta, or launch-readiness claims",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine board_go_live_readiness_sweep --out-dir system_review_graph",
      "effectful": false,
      "id": "board_go_live_readiness_sweep",
      "proof_output": "system_review_graph/board_go_live_readiness_report.json",
      "trigger": "product needs board go-live readiness"
    },
    {
      "cadence": "overnight when requested and safe",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine nightly_eval_loop --out-dir system_review_graph",
      "effectful": false,
      "id": "nightly_eval_loop",
      "proof_output": "eval report with command results",
      "trigger": "long-running goal with bounded proof commands"
    },
    {
      "cadence": "on CI failure",
      "command": "python3 scripts/agentic_workflow_orchestrator.py routine-report --routine ci_failure_triage --out-dir system_review_graph",
      "effectful": false,
      "id": "ci_failure_triage",
      "proof_output": "CI blocker or verified fix branch",
      "trigger": "GitHub check failure"
    }
  ],
  "generated_at": "2026-06-25T16:46:22+00:00",
  "kind": "scheduler_plan",
  "proof_boundary": "This is a scheduler plan, not a daemon. It is safe to commit and can be handed to an external runner.",
  "scheduler": "operator, cron, CI, or Codex goal loop can call these commands"
}
```
