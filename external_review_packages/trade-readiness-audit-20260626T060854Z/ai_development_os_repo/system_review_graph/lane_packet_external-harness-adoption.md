# Lane Packet

```json
{
  "generated_at": "2026-06-26T01:25:25+00:00",
  "goal": "Evaluate optional same-day product harness patterns",
  "handoff_required_fields": [
    "lane",
    "branch_or_worktree",
    "changed_files",
    "commands_run",
    "generated_artifacts",
    "blockers",
    "unsafe_or_external_gates",
    "next_valid_move",
    "commit",
    "push_state"
  ],
  "kind": "lane_packet",
  "lane": {
    "allowed_files": [
      "AGENTS.md",
      "README.md",
      "docs/**",
      "manifests/**",
      "scripts/**",
      "templates/**",
      "system_review_graph/external_harness_integration_packet.*"
    ],
    "branch": "codex/external-harness-adoption-20260626",
    "forbidden_files": [
      "LICENSE",
      "NOTICE.md",
      "CONTRIBUTOR_TERMS.md",
      "DCO.txt",
      "product_projects/**/src/**"
    ],
    "goal": "Evaluate optional external agent harnesses such as ECC, map useful same-day-product patterns, and keep adoption behind proof and security gates.",
    "handoff_required_fields": [
      "lane",
      "branch_or_worktree",
      "changed_files",
      "commands_run",
      "generated_artifacts",
      "blockers",
      "unsafe_or_external_gates",
      "next_valid_move",
      "commit",
      "push_state"
    ],
    "handoff_template": "templates/EXTERNAL_HARNESS_ADOPTION.md",
    "id": "external-harness-adoption",
    "mode": "architect",
    "proof_commands": [
      "python3 scripts/agentic_workflow_orchestrator.py harness-intake --harness ecc --install-mode observe --target-repo ai-development-os --goal \"Evaluate optional same-day product harness patterns\" --out-dir system_review_graph",
      "python3 scripts/workflow_manifest_check.py",
      "python3 scripts/agentic_workflow_orchestrator.py validate",
      "python3 scripts/agentic_workflow_orchestrator.py automation-check",
      "python3 scripts/ai_dev_os_check.py",
      "python3 scripts/self_test_flow.py"
    ],
    "remote": "https://github.com/itsmeeChandU/ai-development-os.git",
    "repo_id": "ai-development-os",
    "repo_role": "coordinator_layer",
    "target_branch": "main",
    "worktree": "/Users/chandu/.codex/worktrees/ai-dev-os-workflow/ai-development-os-external-harness-adoption",
    "worktree_commands": [
      "git fetch origin",
      "git worktree add /Users/chandu/.codex/worktrees/ai-dev-os-workflow/ai-development-os-external-harness-adoption -b codex/external-harness-adoption-20260626 origin/main"
    ]
  },
  "unsafe_or_external_gates": "closed unless explicit user intent and repo proof open them",
  "worker_prompt": "Read AGENTS.md and the lane packet. Work only inside allowed_files, avoid forbidden_files, run proof_commands, refresh generated artifacts when applicable, and write a handoff or blocker row."
}
```
