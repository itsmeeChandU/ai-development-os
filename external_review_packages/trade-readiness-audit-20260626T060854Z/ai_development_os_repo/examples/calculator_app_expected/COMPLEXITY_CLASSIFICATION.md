# Complexity Classification

## Level

- selected level: S0/S1
- reason: local self-contained app with no external data, no credentials, no hardware, no regulated claims
- escalation triggers: persistence, auth, payments, external APIs, deployment, accessibility certification

## Required Process

| Process Step | Required | Reason |
|---|---|---|
| instruction contract | light | enough to capture features |
| state reconstruction | no | new local app |
| system review graph | no | small scope |
| delivery estimate | light | minutes/hours range |
| tool decision record | no | use existing app stack |
| simulation/bench proof | no | not physical |
| compliance review | no | not regulated |

## Smallest Valid Proof

Run the app locally and verify arithmetic operations with a focused test or
browser smoke check.

## Next Action

Implement the UI and calculator logic, then run focused tests.

