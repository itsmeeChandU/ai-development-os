# Run Results

This file records the expected local proof loop for review packages and
external reviewers.

## Commands

```bash
python3 -m py_compile src/importer_source_readiness/*.py scripts/*.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_readiness.py
python3 scripts/run_external_gates.py
python3 scripts/plan_continuation.py
python3 scripts/build_vc_pitch_packet.py
python3 scripts/build_board_go_live_packet.py
python3 scripts/run_customer_workflow.py
python3 scripts/run_policy_intelligence.py
python3 scripts/run_completion_platform.py
python3 scripts/run_product_operations.py
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
requirements_traceability>=44
policy_monitor=intelligence_hub_policy_monitor_ready_with_external_refresh_gates
completion_platform=all_local_stages_implemented_with_external_gates
all_stages=all_local_stages_implemented_with_external_gates
opportunity_scanner=opportunity_scanner_ready_with_research_gates
country_coverage=country_coverage_ready_with_claim_gates
transport_readiness=transport_readiness_ready_with_forwarder_gates
billing_controls=billing_credit_controls_ready_local_no_live_checkout
agent_api=agent_api_manifest_ready_scoped_and_metered
traffic_pages>=10
research_execution=research_execution_ready_with_evidence_gates
expert_network=expert_network_ready_local_with_human_review_gates
team_workspace=team_workspace_ready_local_with_approval_gates
billing_usage=billing_usage_ledger_ready_local_no_charges
agent_gateway=agent_api_gateway_ready_local_executor_no_external_effects
launch_operations=launch_operations_ready_for_private_beta_review
product_operations=local_product_operations_executed
product_operation_count>=8
review_requests=1
audit_events=3
deployment_status=deployable_local_stack_ready_with_external_hosting_gates
operator_workflow_status=operator_workflow_ready_internal
startup_status=startup_in_progress
unsafe_gates=closed
```

Latest local run:

```text
python3 -m py_compile src/importer_source_readiness/*.py scripts/*.py
python3 -m unittest discover -s tests -p 'test_*.py' -> 65 tests OK
python3 scripts/run_policy_intelligence.py -> intelligence_hub_policy_monitor_ready_with_external_refresh_gates
python3 scripts/run_completion_platform.py -> all_local_stages_implemented_with_external_gates
python3 scripts/run_product_operations.py -> local_product_operations_executed, external_effects_created=false
python3 scripts/audit_external_package.py --root . -> PASS
python3 scripts/check_product.py -> PASS
local app smoke on http://127.0.0.1:8767 -> home/start/trade-check/opportunities/country-coverage/transport/pricing/agent-api/workspace/expert/launch/health all 200
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
fail-closed export-to-Canada claims. It also verifies opportunity-signal
research gates, country coverage tiers, transport question packets,
no-live-checkout billing controls, scoped agent/API rules, traffic-first page
contracts, and the public pages/API routes that expose those artifacts.
The latest hardening pass adds focused tests for dependency-free PDF native
text extraction, OCR_REQUIRED scanned-PDF routing, encrypted/invalid PDF
blocking, public upload rejection paths, user confirmation validation, scoped
expert finding submission, package-audit secret/missing-artifact failures,
scheduled source-monitor permissions, upload audit events, parser sandbox
policy, billing metering dimensions, agent/API confirmation rules, and
beginner example starts that create real packets with unknowns preserved.
The latest proof also verifies all locally implementable stages plus real local
operation execution: data intake snapshot, official-source refresh/research
run, missing-evidence report generation, starter checklist generation,
ChatGPT-safe summary generation, broker/expert packet generation, expert work
orders, local billing reservation with zero external charge, team workspace
activity, launch-control event recording, agent-tool execution, SQLite
persistence refresh, and the operation report consumed by the checker.

Any failure should become a blocker row or a targeted repair before review.
