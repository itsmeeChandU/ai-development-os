# Complexity Classification

## Level

- selected level: S4
- reason: hardware, operating-system, firmware, simulation, procurement, lab, and field-operation dimensions exist
- escalation triggers: safety-critical field use, regulated domain, medical/financial/legal claims

## Required Process

| Process Step | Required | Reason |
|---|---|---|
| instruction contract | yes | prompt has uncertainty and broad scope |
| state reconstruction | yes | current hardware/product state is unknown |
| system review graph | yes | multiple domains and dependencies |
| delivery estimate | yes | hardware and software paths diverge |
| tool decision record | yes | OS/simulation/hardware tools need selection |
| simulation/bench proof | yes | local proof before procurement and lab |
| compliance review | yes | field device may have safety/security constraints |

## Smallest Valid Proof

Simulation-first architecture with hardware research rows, OS choice blockers,
tool decisions, and a mocked sensor-to-console flow.

## Next Action

Create hardware candidate table and select simulation path with QEMU or Renode.

