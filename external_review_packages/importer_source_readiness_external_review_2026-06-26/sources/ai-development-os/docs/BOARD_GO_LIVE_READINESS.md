# Board Go-Live Readiness

## Rule

Board go-live readiness is stronger than VC pitch readiness and still weaker
than public launch approval.

A product reaches this stage when the implementation is complete enough for a
board or operator group to decide whether to approve a controlled private beta.
The product must have jurisdiction-specific tools, current-source evidence,
simulated expert-agent review lanes, launch controls, and explicit human
approval gates.

It must not claim public launch, production deployment, legal advice, financial
advice, customs/tariff advice, regulated compliance, buyer validation, revenue,
PMF, supplier recommendation, or external operational readiness until qualified
humans or authorized owners approve those gates with dated evidence.

## Required Artifact

Product repos must write:

```text
system_review_graph/board_go_live_readiness_report.json
```

The board-ready status is:

```text
board_go_live_candidate_with_human_approval_gates
```

## Required Board Packet

Product repos should generate:

```text
board/board_go_live_brief.md
board/expert_review_packet.md
board/launch_control_checklist.md
board/financial_operating_model.md
```

The packet should be good enough for a board to review what the AI-built
system completed, assign human owners, and approve or reject controlled private
beta. It is not an approval by itself.

## Required Evidence

The machine report should include:

- primary market or jurisdiction
- jurisdiction-specific official tools and source links
- simulated expert review lanes
- launch controls
- human approval gates
- closed claims
- allowed next stage
- proof boundary

For Canada-focused products, the tool surface should include the relevant
Canadian official or quasi-official sources for the product: CBSA/CARM,
Customs Tariff, CFIA AIRS, Global Affairs import/export controls, sanctions,
ISED trade data, Canadian Importers Database, BizPaL, PIPEDA/privacy, Canadian
Cyber Centre baseline controls, and financial planning references when funding
or runway claims are discussed.

## Human Approval Gates

AI model subject synthesis can act as a first-pass expert review, but the
following remain human approval gates before public or external claims:

- qualified compliance or customs/trade reviewer
- legal/privacy reviewer
- finance/accounting/founder approval
- data/source rights owner
- security/operations owner
- buyer/operator validation
- board or launch owner

Open gates are acceptable at board review if they are visible and assigned.
They are not acceptable as hidden completion claims.
