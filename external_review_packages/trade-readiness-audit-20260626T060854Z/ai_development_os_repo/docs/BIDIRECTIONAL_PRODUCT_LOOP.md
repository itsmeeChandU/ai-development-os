# Bidirectional Product Loop

AI product development should run in both directions.

## Top Down: Idea To Product

Use this when starting from a startup idea.

1. Idea
2. User
3. Pain
4. Promise
5. First workflow
6. Data needed
7. Interfaces needed
8. Prototype
9. Proof
10. Launch surface

Prompt:

```text
Take this idea from top down. Identify the target user, first painful workflow,
minimum useful product, data/API needs, UI surface, backend modules, tests, and
proof gates. Then implement the first working slice.
```

## Bottom Up: Existing System To Product

Use this when a repo already exists or a product is half-built.

1. Code graph
2. Data graph
3. Flow graph
4. Broken predicates
5. Existing assets that can be reused
6. Highest leverage product slice
7. Missing data/tools/resources
8. Implementation
9. Proof

Prompt:

```text
Start bottom up. Audit the current repo, data, generated artifacts, tests,
external integrations, and UI. Identify what can already support a usable
product, what is blocked, and what single product loop should be completed
first. Implement that loop with tests and artifacts.
```

## Reverse: Product To Idea

Use this after a prototype exists.

1. Inspect what the product actually does.
2. Identify who it is really useful for.
3. Remove claims the product does not prove.
4. Find the strongest workflow.
5. Rewrite the startup idea around the working product.

Prompt:

```text
Reverse the product back into the idea. Inspect the implemented product,
generated artifacts, UI, tests, and data. Tell me what startup this actually
is, what claims are proven, what claims are not, and what should be built next.
```

## The Loop

```text
idea -> product -> proof -> observed product -> refined idea -> sharper product
```

Do not freeze the original idea too early. AI can generate fast prototypes,
but the product that emerges may reveal a better wedge.

