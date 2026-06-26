# Customer Source Packet Spec

The first customer workflow is Canada-first importer/source readiness for one
packet. The local app proves the workflow with generated state, a SQLite
runtime store, local session auth, organization isolation, evidence metadata
validation, scoped expert-review links, audit events, and safe report exports.
Real external hosting, qualified human review, malware scanning, and live
infrastructure remain human/external gates.

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
/
/login
/signup
/onboarding
/dashboard
/packets
/packets/new
/packets/:id
/packets/:id/evidence
/packets/:id/blockers
/packets/:id/readiness
/packets/:id/ai-reviews
/packets/:id/reviews
/packets/:id/reports
/packets/:id/settings
/packets/:id/expert-review-packet
/packets/:id/export
/operator/queue
/operator/packets/:id
/review/:token
/review/:token/evidence
/review/:token/questions
/review/:token/submit
/admin/sources
/admin/gates
/admin/audit
/admin/system-health
```

`/source-packets/*` remains as a compatibility alias for generated artifacts
and older operator links.

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
claims, request review, open a scoped expert packet, export a safe readiness
report, and produce audit/runtime artifacts without the product giving customs,
tariff, CFIA, legal, supplier, buyer, or launch approval.

## Required Actions

```text
Refresh Official Sources
Upload Evidence
Request Operator Review
Run AI Review
Generate Expert Review Packet
Export Readiness Report
```

Source refresh records `accessed_at`, `last_verified_at`, `content_hash`,
HTTP status, source change status, refresh actor, and refresh run ID. A refresh
can close stale-source proof only. It cannot approve import, tariff, CFIA,
supplier, buyer, legal, or launch claims.
