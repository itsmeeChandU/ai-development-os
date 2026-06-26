# Run Results

This file records the expected local proof loop for review packages and
external reviewers.

## Commands

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_readiness.py
python3 scripts/run_external_gates.py
python3 scripts/plan_continuation.py
python3 scripts/build_vc_pitch_packet.py
python3 scripts/build_board_go_live_packet.py
python3 scripts/run_customer_workflow.py
python3 scripts/run_policy_intelligence.py
python3 scripts/run_operator_workflow.py
python3 scripts/export_operator_dashboard.py
python3 scripts/audit_external_package.py --root .
python3 scripts/check_product.py
```

## Expected Result

The product remains internally usable with external claims blocked:

```text
status=ready_with_external_gates
customer_workflow_status=customer_workflow_ready_internal
customer_blocker_groups=4
customer_store=ready
runtime_status=private_beta_candidate_with_external_human_gates
public_surface_status=public_quick_check_ready_local_with_external_gates
runtime_users=4
ai_policy_status=ai_data_policy_ready
ai_router_status=ai_model_router_ready
requirements_traceability>=31
policy_monitor=intelligence_hub_policy_monitor_ready_with_external_refresh_gates
review_requests=1
audit_events=3
deployment_status=deployable_local_stack_ready_with_external_hosting_gates
operator_workflow_status=operator_workflow_ready_internal
startup_status=startup_in_progress
unsafe_gates=closed
```

Latest local proof also verifies customer packet prototype status, grouped
blockers, evidence quality, AI simulated review runs, scoped expert-review
requests, AI data policy, model routing, redaction previews, no-AI/manual
fallback, requirements traceability, auth/RBAC and organization isolation,
audit events, report exports, deployment health surfaces, and the expanded
SQLite workflow store. The current proof also verifies the public Trade
Readiness Copilot route contract, no-login PDF upload quick check, draft
readiness/buyer/broker PDF generation, delete-files control, exporter mode
requirements, public upload policy, beginner no-documents starter mode, PDF
triage and confirmation, ChatGPT-safe summary, the Intelligence Hub
policy/source monitor contract, the policy intelligence SQLite store, and
fail-closed export-to-Canada claims.

Any failure should become a blocker row or a targeted repair before review.
