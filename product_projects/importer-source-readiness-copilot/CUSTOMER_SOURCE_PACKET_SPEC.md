# Customer Source Packet Spec

The first customer workflow is Canada-first importer/source readiness for one
packet. The local app proves the workflow with fixture-backed data and generated
reports. Hosted auth, organization isolation, file upload storage, real expert
review, and live official-source refresh remain later gates.

## Intake Fields

- packet name
- customer id
- organization id
- product name
- product category
- HS code if known
- origin country
- destination country
- supplier name
- supplier country
- source URL
- source type
- intended use
- documents or evidence references
- notes

## Customer Routes

```text
/source-packets
/source-packets/new
/source-packets/:id
/source-packets/:id/evidence
/source-packets/:id/readiness
/source-packets/:id/readiness-report
/source-packets/:id/export
```

## Customer-Visible Statuses

```text
draft
submitted
needs_more_evidence
needs_operator_review
needs_expert_review
blocked_missing_evidence
blocked_stale_source
blocked_reference_only
ready_for_internal_review
ready_for_expert_review
ready_for_private_beta_review
closed
```

## Blocked Claims

The report must keep these claims closed until scoped evidence exists:

```text
tariff_confirmed
cfia_compliant
supplier_recommended
buyer_validated
ready_to_import
public_launch_ready
customs_or_tariff_advice_ready
legal_or_compliance_approved
```

## Done Condition For This Slice

A local user can create or view one source packet, inspect evidence, see blocked
claims, and export a safe readiness report without the product giving customs,
tariff, CFIA, legal, supplier, buyer, or launch approval.
