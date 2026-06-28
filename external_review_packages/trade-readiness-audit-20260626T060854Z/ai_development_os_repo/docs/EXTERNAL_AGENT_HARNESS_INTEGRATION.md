# External Agent Harness Integration

AI Development OS can use external agent harnesses such as Everything Claude
Code (ECC) as acceleration layers. They are optional operators around the
workflow, not replacements for repo truth, GitHub history, generated artifacts,
tests, System Review Graph, code-review graph contracts, blocker rows, or human
approval gates.

## Current Harness Decision

| Harness | Source | License | Decision | Use |
|---|---|---|---|---|
| Everything Claude Code (ECC) | `https://github.com/affaan-m/ECC` | MIT | adopt optional patterns | skills, commands, hooks, worktree lifecycle, verification loops, security scan, cross-harness packaging |

ECC is useful because it packages real agentic delivery mechanics: specialist
agents, reusable skills, legacy slash commands, hook profiles, managed loops,
model routing, security scanning, and deterministic harness audits. Those
patterns can help a product team move from prompt to a working vertical slice
quickly, including the "same-day product build" style the user referenced.

The integration rule is selective adoption. Do not copy the whole external repo
into AI Development OS, do not let external harness commands overwrite local
instructions, and do not treat social proof or repo popularity as proof that a
product is done.

## Integration Modes

| Mode | Meaning | Allowed Effects |
|---|---|---|
| observe | inspect the external harness, map patterns, and write a packet | read-only local artifacts |
| project_local_optional | install or copy selected harness surfaces inside one product repo | requires explicit operator approval and security scan |
| operator_global_optional | operator installs a global plugin or config outside the repo | outside AI Development OS control; must be recorded as a blocker or assumption |

Use `observe` by default. Escalate only when the product needs a concrete
external harness capability and the operator approves it.

## Required Packet

Before a worker uses an external harness for product delivery, generate:

```text
system_review_graph/external_harness_integration_packet.json
```

The packet must include:

- harness id, source, license, inspected ref, and decision
- selected integration mode
- adopted patterns
- command mapping into AI Development OS
- security and install gates
- blocked claims
- proof boundary
- next valid move

The packet is a coordination artifact. It does not prove the external harness
is installed, safe, current, or sufficient.

## Pattern Map

| External Pattern | AI Development OS Mapping |
|---|---|
| thin vertical slice MVP orchestration | `/ados:prompt-to-product`, `/ados:lane`, product slice stage |
| managed autonomous loop with stop condition | `/ados:goal`, scheduler plan, eval loops |
| deterministic harness audit | `/ados:harness-intake`, proof/eval blocker rows |
| model route by task risk | complexity router and development strategy router |
| verification loop | `/ados:proof`, CI jobs, product project check |
| security scan / AgentShield | external harness safety check before install or commit |
| skills and agent catalogs | optional acceleration inputs in lane packets |
| hooks | optional local guardrails; Codex proof still comes from tests and artifacts |
| memory persistence | Ruflo or repo-local memory summaries, never repo truth |

## Eight-Hour Product Mode

Same-day product building is allowed when the target can be proven locally. Use
it for S0-S2 product slices and for the first internal operator loop of larger
products. The flow is:

1. Normalize the idea and classify complexity.
2. Run repo intake, research/data routing, and development strategy routing.
3. Pick one thin vertical slice that a user can actually operate.
4. Emit a lane packet with owned files, forbidden files, proof commands, and a
   handoff.
5. Use ECC-style skills, commands, hooks, or audit loops only as accelerators.
6. Run tests, smoke checks, generated artifact checks, and security checks.
7. Keep external gates closed with blocker rows and continuation plans.

This mode must not turn into a fake completion claim. Buyer demand, current
country rules, legal/compliance approval, supplier readiness, data rights,
contracts, public launch, financial advice, and production deployment remain
external evidence or human approval gates.

## Adoption Gates

Before installing or copying an external harness surface into a product repo:

- verify source URL and license
- record the exact commit, release, or package version inspected
- choose only the needed skills, commands, hooks, or rules
- run local tests and the AI Development OS validators
- run a security scan when config, hooks, MCPs, or permissions change
- avoid duplicate hook/plugin installs
- preserve existing `AGENTS.md` and repo instructions
- write a blocker row for any install, credential, paid API, or network-write
  requirement that is not approved

## Disallowed

- wholesale importing hundreds of external skills into this repo without a
  scoped need
- letting external harness docs override AI Development OS proof boundaries
- using external commands to push, publish, deploy, pay, contact people, or
  mutate third-party systems without explicit operator intent
- treating Claude-only hooks as Codex proof
- claiming "fully operational" or "launch ready" because an MVP loop passed
- storing secrets, private data rows, or unsupported completion claims in
  coordination memory

## Proof Boundary

External harnesses can improve speed, consistency, security posture, and
operator ergonomics. The final proof still comes from the product repo:
source changes, tests, generated artifacts, graph context, blocker ledgers,
screenshots when useful, GitHub branch state, and human/external approvals
where required.
