# Prompt-To-Product Product Automation Case Study

This example shows how to demonstrate AI Development OS to a product team.

## Scenario

A Venture Studio or product operator submits this idea:

```text
Build a supplier risk copilot for import/export operators. It should gather
supplier data, check country requirements, identify certification gaps, and
produce a readiness view before a buyer depends on it.
```

This is not a simple local app. It needs current supplier data, official
country/import/export sources, likely contracts, and expert validation before
serious claims.

## Automated Flow

Run the AI Development OS coordinator:

```bash
python3 scripts/agentic_workflow_orchestrator.py repo-intake \
  --idea-source intelligence-hub \
  --target-repo future-product-repo \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py research-plan \
  --problem "Supplier risk copilot for import/export operators" \
  --domain manufacturing \
  --data-need "supplier data, official country import export rules, certifications, tariffs, contracts" \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py strategy-plan \
  --idea "Supplier risk copilot for import/export operators" \
  --field manufacturing \
  --country US \
  --out-dir system_review_graph

python3 scripts/agentic_workflow_orchestrator.py prompt-to-product \
  --name supplier-risk-copilot \
  --idea "Supplier risk copilot for import/export operators" \
  --field manufacturing \
  --country US \
  --idea-source intelligence-hub \
  --target-repo future-product-repo \
  --out-dir system_review_graph
```

## What People Should See

The generated artifacts should show:

- repo intake selects the idea source and product target repo
- research/data routing includes official sources, structured data, deep
  research, and expert/user validation
- development strategy routing includes manufacturing, cross-border supply
  chain, and contract-dependent gates when the idea requires them
- prompt-to-product emits a normalized contract, lanes, proof requirements, and
  a next valid move

## Product Explanation

Use this explanation in a demo:

```text
The product does not send a broad prompt directly to an agent. It first creates
machine-readable packets. Those packets decide which repo owns the work, what
research or data is required, which development mode applies, which agents can
work, and what proof is required. If supplier data, country rules, contracts, or
experts are missing, the product shows that as a blocker instead of pretending
the app is launch-ready.
```

## Expected Readiness State

For this scenario, the correct state is usually:

```text
ready_with_external_gates
```

That means software lanes can start, but product claims remain blocked until
the real external inputs are collected:

- supplier data and freshness
- official country/import/export rules
- certification requirements
- tariff/customs evidence
- contract or licensing review
- qualified expert or buyer validation

## First Implementation Lane

The first useful lane should usually be local and proofable:

```text
Build the operator readiness view using fixtures, generated blocker rows, and
sample country/supplier records. Do not claim live supplier correctness until
the data route and official-source route are proven.
```

That lets the product show value quickly while keeping real-world claims behind
the correct gates.
