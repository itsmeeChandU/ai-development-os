# Trade Readiness Packet Spec

The customer workflow is Canada-first import/export readiness for a trade
packet. Public users see Trade Readiness Copilot: choose a tool, upload PDFs,
run a quick check, preview missing evidence, download a draft PDF, and delete
uploaded files. The internal engine keeps source-packet workflow state,
generated artifacts, SQLite runtime store, local session auth, organization
isolation, evidence metadata validation, scoped expert-review links, audit
events, and safe report exports. Real external hosting, qualified human review,
malware scanning, and live infrastructure remain human/external gates.

## Intake Fields

- packet name
- customer id
- organization id
- product name
- product category
- trade direction (`import`, `export`, `both`, `unknown`)
- HS code if known
- origin country
- destination country
- exporter country
- importer country
- exporter business name
- Canadian buyer/importer name
- importer of record (`buyer`, `importer`, `exporter`, `broker`, `unknown`)
- exporter of record
- Incoterms or delivery responsibility
- supplier name
- supplier country
- manufacturer name
- source URL
- source type
- intended use
- documents or evidence references
- notes
- evidence sensitivity level
- evidence AI processing mode
- redaction-required flag
- product documents
- commercial documents
- certificates
- proof of origin
- shipping method
- food/health/quality documents
- source/supplier documents
- contract or purchase order

## Customer Routes

```text
/
/tools
/trade-check
/tools/import-readiness
/tools/export-readiness
/tools/buyer-broker-packet
/tools/canadian-references
/public/packets/:id/result
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
/settings/ai-data-policy
/privacy
/terms
/ai-use
/data-retention
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
/api/orgs/current/ai-policy
/api/orgs/current/ai-policy/test-model-endpoint
/api/evidence/:evidenceId/ai-permission
/api/public/quick-check
/api/public/packets/:id/refresh-official-sources
/api/public/packets/:id/reports/draft.pdf
/api/public/packets/:id/reports/buyer.pdf
/api/public/packets/:id/reports/broker.pdf
/api/public/packets/:id/delete-files
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
ready_to_export_to_canada
canadian_importer_confirmed
export_documentation_complete
trade_agreement_preference_confirmed
public_launch_ready
customs_or_tariff_advice_ready
legal_or_compliance_approved
```

## Readiness Lanes

Every packet can expose two customer-readable lanes:

```text
exporter_side_readiness
importer_side_readiness
```

For an India-to-Canada exporter, the exporter-side lane tracks India/source
documents such as product specs, certificates, proof of origin, and
country-specific evidence that may need expert review. The importer-side lane
tracks Canadian buyer/importer, importer of record, Incoterms, CBSA/CARM,
CFIA/AIRS when relevant, import controls, restricted-party screening, and
broker/expert review. Both lanes remain blocked until evidence and qualified
review support any external claim.

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
Generate Buyer Packet
Generate Broker Review Packet
Delete Uploaded Files
```

Source refresh records `accessed_at`, `last_verified_at`, `content_hash`,
HTTP status, source change status, refresh actor, and refresh run ID. A refresh
can close stale-source proof only. It cannot approve import, tariff, CFIA,
supplier, buyer, legal, or launch claims.

AI review records include model mode, route decisions, redaction status,
retention flags, validation result, and output JSON. AI review can create
blockers and next valid moves only. Evidence can be switched to `no_ai` through
`/api/evidence/:evidenceId/ai-permission`, which rebuilds the workflow and
returns the new route decision.
