# What We Are Building

Trade Readiness Copilot is a blocked-safe product for people preparing import
or export work before they talk to buyers, brokers, freight forwarders,
operators, or experts.

The product helps a user:

- start with only a product idea
- upload trade PDFs for bounded local triage
- confirm extracted fields
- see missing evidence
- see blocked claims
- download starter, missing-evidence, buyer, broker, and expert-review reports
- save packet history locally
- create scoped expert/operator review work
- generate ChatGPT-safe summaries without private file contents

The product must never imply:

- customs approval
- tariff confirmation
- CFIA clearance
- legal advice
- supplier verification
- buyer validation
- ready-to-ship status
- public launch approval

## System Context

The intended full system path is:

```text
Intelligence Hub / Venture Studio idea generation
-> AI Development OS coordination
-> system review graph and code-review graph context
-> agents/worktrees/GitHub/Ruflo execution
-> standalone product repo
-> operator/customer app
-> external expert review
-> launch gates
```

This repo is the standalone product repo and local proof surface. The broader
operating system can coordinate ideas and agents, but this repo is responsible
for the product truth, local app, generated reports, tests, review packages,
and launch-gate blockers.

## Current Product Promise

```text
Before you import or export, know what is missing.
```

That promise is intentionally narrower than import/export advice. It gives the
user a next valid move, not approval.
