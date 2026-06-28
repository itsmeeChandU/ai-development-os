# Production Decision Scoring Engine

Status: `production_decision_scoring_engine_ready_no_global_readiness_score`

The scoring engine explains separate capped scores for internal decision preparation. It does not approve imports, exports, tariff treatment, CFIA status, buyers, suppliers, shipments, payments, legal posture, or public launch.

## Summary

- Score types: 6
- Score records: 6
- Single global readiness score created: false
- Approval language allowed: false

## Score Policies

- `market_signal_score`: Shows whether a product-country lane deserves deeper validation. Cap rule: Cap below 60 until dated trade dataset rows, market-access comparison, buyer evidence, and review exist.
- `evidence_completeness_score`: Shows whether packet evidence is complete enough for the current internal stage. Cap rule: Cap below 50 while required packet fields, documents, confirmation, or reviewer evidence are missing.
- `source_freshness_score`: Shows whether official/reference source evidence is fresh enough for internal use. Cap rule: Cap below 40 when critical source evidence is stale, reference-only, not checked, or unreviewed.
- `buyer_supplier_evidence_score`: Shows buyer and supplier evidence strength without validation or verification claims. Cap rule: Cap below 60 until dated buyer interaction evidence, supplier documents, inspection/certificate evidence, and review exist.
- `responsibility_clarity_score`: Shows whether importer of record, Incoterms, and role split are clear. Cap rule: Cap below 40 while importer of record, Incoterms, broker path, or responsibility split are missing.
- `decision_safety_score`: Shows whether it is safe to move beyond internal preparation. Cap rule: Cap below 40 while any forbidden external claim, launch gate, payment gate, or qualified-review lane remains blocked.

## Packet Scores

### packet-frozen-tuna-canada-001

- Lowest label: `red`
- Blocked claim dependencies: 10
- Next valid move: Work the red score blockers first, then refresh source evidence and route scoped claims to reviewers.

- `market_signal_score`: 45/59 `yellow`; Local market signal score is 55/100 before external demand, dataset, and buyer proof.
- `evidence_completeness_score`: 23/49 `red`; 3 evidence rows attached and 10 required items missing.
- `source_freshness_score`: 39/39 `red`; Official/reference sources are routed, but current-source proof and qualified review are still required.
- `buyer_supplier_evidence_score`: 0/59 `red`; Buyer level -1 and supplier level 0 are recorded without validation/verification claims.
- `responsibility_clarity_score`: 30/39 `red`; Confirm importer of record and Incoterms before shipment or buyer claims.
- `decision_safety_score`: 20/39 `red`; 7 blocker rows keep external decisions closed.

## Closed Gates

- Claims opened: false
- External effects created: false
- Public launch ready: false
- Live payment ready: false
