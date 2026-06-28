# What We Are Trying To Build

## The Bigger Product

We are building an AI-native venture/product development operating system.

The intended end-to-end flow is:

1. Intelligence Hub or Venture Studio generates a startup/application idea.
2. AI Development OS normalizes the idea into a task contract, research plan,
   development strategy, lane plan, proof gates, and blocker schema.
3. System Review Graph and code-review graph provide bounded context for
   agents so they do not work from vague chat memory.
4. Agents build in isolated lanes, with GitHub as canonical version control and
   Ruflo only as coordination memory.
5. The product repo accumulates real code, tests, generated artifacts, operator
   surfaces, evidence packets, and continuation plans.
6. External reviewers, buyers, subject experts, compliance reviewers, legal,
   finance, security, and board owners inspect the product before external
   claims or launch gates open.
7. Lessons from real review and usage feed the next build cycle.

The goal is not "AI writes some code." The goal is a repeatable product
factory that can move from prompt to working product while keeping evidence,
risks, blockers, and external approval gates visible.

## The Product In This Package

The concrete product slice in this package is:

```text
Importer Source Readiness Copilot
```

It is a Canada-focused internal operator application for importer/exporter
source-readiness review.

It helps an operator inspect:

- source-card readiness
- official-source references
- Canadian import/export and compliance reference tools
- external evidence gates
- blocker rows
- continuation lanes
- human approval gates
- investor/private conversation packet
- board/private-beta packet
- generated screenshots and proof boundaries

## Why This Slice Exists

Importer/exporter source workflows are easy to overclaim. A product like this
can accidentally imply supplier recommendation, buyer validation, customs
advice, tariff advice, CFIA compliance, legal approval, or launch readiness.

This slice proves that the AI-native process can build useful software while
keeping those claims closed until real evidence and qualified people review
them.

## What This Package Should Prove

This package should prove:

- a real product repo exists
- the product has runnable local code
- tests and proof gates pass
- an internal operator app exists
- generated reports and blocker rows exist
- Canada-specific reference tools and boundaries exist
- investor and board packets exist with diligence gates
- the AI Development OS workflow can coordinate product work across helper repos

## What This Package Does Not Prove

This package does not prove:

- customer-facing product readiness
- public launch readiness
- buyer demand or product-market fit
- customs/tariff correctness
- CFIA compliance
- legal/privacy approval
- financial approval
- supplier readiness
- signed contracts or data/source rights
- production deployment approval

Those are the external review gates this package is being sent out to surface
and close.

## What We Need From Reviewers

We need reviewers to say:

- whether the current internal operator product is useful
- what blocks controlled private beta
- what blocks public launch
- what the customer-facing product should become
- what claims must be rewritten or removed
- what evidence, contracts, data, approvals, and controls are required next
