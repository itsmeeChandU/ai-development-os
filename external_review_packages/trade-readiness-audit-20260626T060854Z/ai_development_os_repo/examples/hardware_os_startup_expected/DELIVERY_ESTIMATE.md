# Delivery Estimate

## Product Goal

Simulation-first edge OS product path with hardware research, architecture,
agent lane split, and proof blockers.

## Lane Plan

| Lane | Goal | Tools/Data Needed | Proof Command | Estimate | Risk |
|---|---|---|---|---|---|
| instruction-normalization | stabilize prompt into execution contract | templates | review artifact | <1 day AI | low |
| hardware-os | choose candidate board/OS path | datasheets, Zephyr/Yocto/Buildroot docs | research record | 1-3 days AI | hardware unknown |
| simulation-bench | emulate or mock device flow | QEMU/Renode/mocks | simulation command | 2-5 days AI | model fidelity |
| backend-control-plane | local queue, sync API, event model | runtime stack | focused tests | 2-5 days AI | data model unknown |
| UI-operator-console | show device status/logs/config | browser tests | screenshot/smoke | 1-3 days AI | UX unknown |
| compliance-safety | identify standards and hazards | standards research | blocker rows | 1-2 days AI | domain unknown |

## Timeline

| Path | Estimate | Assumptions |
|---|---|---|
| AI agent path | 1-3 weeks to simulation prototype | no physical hardware required for first proof |
| human team path | 1-3 months to comparable prototype | embedded, backend, UI, QA, and PM coordination |

