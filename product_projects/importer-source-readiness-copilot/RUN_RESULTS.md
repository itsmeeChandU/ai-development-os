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
operator_workflow_status=operator_workflow_ready_internal
startup_status=startup_in_progress
```

Any failure should become a blocker row or a targeted repair before review.
