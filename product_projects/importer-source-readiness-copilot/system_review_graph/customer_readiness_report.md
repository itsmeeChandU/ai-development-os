# Importer Source Readiness Report

Packet: Frozen tuna Canada source packet
Status: Internal operator ready - external claims blocked
Customer-visible status: blocked_stale_source

## Summary

This packet is not ready for external action. It needs more evidence, operator review, or qualified expert review before any customs, tariff, supplier, buyer, CFIA, legal, or launch claim can be made.

## Blockers

- evidence freshness is stale or not proven: Refresh the official source and record accessed_at, last_verified_at, and content hash.
- evidence freshness is stale or not proven: Refresh the official source and record accessed_at, last_verified_at, and content hash.
- evidence freshness is stale or not proven: Refresh the official source and record accessed_at, last_verified_at, and content hash.
- restricted_party_screening_status is missing or incomplete: Complete restricted-party screening.
- qualified_review_status is missing or incomplete: Request qualified import/compliance review.
- buyer_validation_status is missing or incomplete: Collect dated buyer/operator feedback.
- contract_status is missing or incomplete: Attach source-rights or commercial terms.

## Blocked Claims

- tariff_confirmed
- cfia_compliant
- supplier_recommended
- buyer_validated
- ready_to_import
- public_launch_ready
- customs_or_tariff_advice_ready
- legal_or_compliance_approved

## Next Valid Move

Refresh the official source and record accessed_at, last_verified_at, and content hash.

## Boundary

Customer source-packet workflow is local-first and fixture-backed. It produces safe readiness reports and blockers, not import approval, tariff confirmation, CFIA clearance, supplier recommendations, buyer validation, legal advice, or launch approval.
