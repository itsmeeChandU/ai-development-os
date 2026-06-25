# VC Pitch Readiness

## Rule

VC pitch readiness is not launch readiness.

A product can be ready for a private investor conversation when it has a
demoable proof loop, investor-safe claim boundaries, cited market/regulatory
evidence, a clear ask/use-of-funds draft, and explicit diligence lanes.

It must not claim revenue, product-market fit, buyer validation, legal /
compliance approval, supplier readiness, customs/tariff advice readiness,
public launch readiness, or full operational readiness unless those claims are
proven by repo artifacts and qualified review.

## Required Artifact

Pitch-ready product repos must write:

```text
system_review_graph/vc_pitch_readiness_report.json
```

The artifact must include:

- `status`
- `pitch_mode`
- `demo_ready`
- `continuation_ready`
- `evidence_ready`
- `evidence_status`
- `investor_sources`
- `pitch_claims`
- `draft_funding_ask`
- `diligence_lanes`
- `closed_claims`
- `demo_script`
- `next_valid_move`
- `proof_boundary`

The pitch-ready status is:

```text
vc_pitch_ready_with_diligence_gates
```

## Required Investor Packet

Product repos should generate:

```text
investor/vc_pitch_deck.md
investor/one_pager.md
investor/demo_script.md
investor/diligence_room_index.md
```

The packet should be good enough for a founder to have a private VC
conversation, not to publish as legal, securities, compliance, or launch proof.

## Evidence Rules

Investor claims need source rows with:

- source name
- URL
- access date
- claim
- claim boundary

For current market, regulatory, trade, pricing, or compliance claims, use
current web or official-source evidence. AI model subject synthesis can shape
the thesis, but it is not proof for current market size, law, buyer demand, or
regulated claims.

## Diligence Lanes

At minimum, pitch-ready products should expose these open lanes:

- buyer discovery
- design partner or pilot intent
- qualified compliance review
- data rights and freshness
- business model / willingness-to-pay
- legal and financing review

Open diligence lanes are allowed in a VC pitch if they are visible. They are
not allowed to be hidden behind a fake completion claim.
