# Strategy Research Playbook

AI agents can code quickly, but product direction still needs disciplined
thinking. Use research to improve the product path, not to delay building.

## Research Rules

- Research only a specific decision, risk, or capability gap.
- Prefer primary sources, official docs, and actively maintained open-source repos.
- Record date checked, license, maturity, adoption reason, and rejection reason.
- Convert useful research into code, data, tests, docs, or blocker rows.
- Do not let interesting research become a substitute for a working product loop.

## Thinking Tools

### Jobs To Be Done

Use when the target user or product promise is fuzzy.

Questions:

- What progress is the user trying to make?
- What situation triggers the need?
- What current workaround proves pain?
- What would make the user switch?

Source to start from: https://www.christenseninstitute.org/theory/jobs-to-be-done/

### Wardley Mapping

Use when a product needs strategy, build-vs-buy decisions, or ecosystem clarity.

Questions:

- Who is the user?
- What value chain serves them?
- Which parts are novel, custom, productized, or commodity?
- Where should the agent build, integrate, buy, or ignore?

Sources to start from:

- https://learnwardleymapping.com/
- https://github.com/wardley-maps-community/awesome-wardley-maps

### Shape Up

Use when the work is too big and needs a bounded product slice.

Questions:

- What appetite does this deserve?
- What is the shaped pitch?
- What is the rabbit hole?
- What is the circuit breaker?

Source to start from: https://basecamp.com/shapeup

### Toyota Kata

Use when the project has many blockers and needs short learning loops.

Questions:

- What is the target condition?
- What is the current condition?
- What obstacle is in the way now?
- What is the next experiment?

Sources to start from:

- https://www-personal.umich.edu/~mrother/Homepage.html
- https://www.nist.gov/mep/toyota-kata-helps-create-a-continuous-improvement-mindset

### First Principles And Inversion

Use when the project feels overcomplicated.

Questions:

- What must be true for the product to be useful tomorrow?
- What can be removed without hurting that outcome?
- What would make this fail?
- Which test or artifact would reveal that failure fastest?

## Research To Build Pipeline

Every research note should become one of:

- dependency adopted in `manifests/tool_registry.yaml`
- rejected dependency with reason
- new module contract
- data/source loader requirement
- proof gate
- blocker row
- test case
- operator/readiness panel

## Research Record Prompt

```text
Research only the missing capability named below. Use primary/official sources
when possible. Return options, licenses, maturity, adoption risk, and the exact
repo files that should change if we adopt the option. Do not recommend a tool
unless it closes a proven product gap.
```

