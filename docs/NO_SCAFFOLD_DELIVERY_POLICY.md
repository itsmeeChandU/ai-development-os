# No Scaffold Delivery Policy

This repository may contain generator templates, sample projects, and review
packets. Those are allowed only as inputs to real work. They are not completion.

## Hard Rule

Do not mark a lane, product, go-live review, or external review as complete
when the delivered state is only a scaffold, template, placeholder, mock,
simulated review, generated packet, or checklist.

Completion requires the working code/data path, the generated truth artifacts,
and focused proof commands that consume those artifacts. If an external person,
buyer, hosted service, payment account, customs reviewer, legal reviewer, or
production owner is still required, the state must stay explicitly not ready.

## Banned As Completion Evidence

- scaffolded code or generated project skeletons
- placeholder source rows or placeholder documents
- mock, dummy, or simulated evidence
- AI-simulated external reviews
- review packets, PDFs, or email-ready briefs by themselves
- templates for future input collection
- local-only smoke tests when hosted proof is required
- pushed commits without runtime or evidence proof

## Allowed Only With Boundaries

Generator templates may exist in `templates/`, examples, and
`scripts/scaffold_project.py`. They are allowed because this repo is also an
operating kit. They cannot be cited as a finished product.

Fixture placeholders may exist only when the generated reports and blocker
ledgers say they are fixture-only, unsafe to bypass, and not usable for external
claims.

Simulated reviews may exist only when they are labeled simulated, cannot open
approval, and produce follow-up work rather than launch permission.

Go-live input templates may exist only as collection forms. They must not open
public launch, hosted private beta, live payment, legal, privacy, security,
customs, buyer, supplier, or qualified approval states.

## Required Audit

Before a completion or go-live claim, run:

```bash
python3 scripts/no_scaffold_audit.py --check
```

The audit must pass with zero disallowed scaffold markers. Any scaffold-like
artifact must be classified as one of:

- generator template only
- review intake only
- fixture blocker evidence
- simulated review with approval closed
- policy language

Anything else is a product blocker, not a delivery.

