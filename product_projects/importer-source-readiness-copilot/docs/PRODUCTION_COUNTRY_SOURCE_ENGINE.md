# Production Country Source Engine

Status: `production_country_source_engine_ready_reference_packs_claim_gates_closed`

This engine converts the official-source registry and dated refresh records into country packs, source lifecycle rows, and packet source-impact decisions.

## Proof Boundary

This engine turns researched official-source routes into country/source logic. It does not prove current law, tariff treatment, CFIA approval, sanctions clearance, buyer validation, supplier verification, hosted readiness, or public launch approval.

## Country Packs

### CA-import

- Coverage: `reference_only`
- Direction: `import`
- Sources present: broker_directory, buyer_importer_discovery, customs_import_process, import_controls, regulated_goods, sanctions_restricted_party, tariff_orientation, trade_data
- Sources missing: none
- Reviewer required: true
- External claims opened: false

### IN-export

- Coverage: `reference_only`
- Direction: `export`
- Sources present: customs_reference, export_policy, import_export_code, origin_export_controls
- Sources missing: none
- Reviewer required: true
- External claims opened: false

### VN-demo-origin

- Coverage: `reference_only`
- Direction: `export`
- Sources present: none
- Sources missing: customs_reference, origin_export_controls, supplier_registry
- Reviewer required: true
- External claims opened: false

### GENERIC-fallback

- Coverage: `generic`
- Direction: `generic`
- Sources present: official_reference
- Sources missing: none
- Reviewer required: true
- External claims opened: false


## Source Lifecycle

- `cbsa-carm`: buyer_importer_discovery / `not_checked`.
- `cbsa-import-commercial-goods`: customs_import_process / `checked_current_reference_only`.
- `cbsa-customs-tariff-2026`: tariff_orientation / `not_checked`.
- `cfia-airs`: regulated_goods / `checked_current_reference_only`.
- `gac-import-controls`: import_controls / `not_checked`.
- `justice-import-control-list`: import_controls / `not_checked`.
- `canada-sanctions`: sanctions_restricted_party / `not_checked`.
- `ised-trade-data-online`: trade_data / `not_checked`.
- `canada-cid`: buyer_importer_discovery / `checked_current_reference_only`.
- `cbsa-licensed-customs-brokers`: broker_directory / `not_checked`.
- `itc-market-access-map`: market_access_comparison / `not_checked`.
- `india-dgft-foreign-trade-policy`: export_policy, import_export_code, origin_export_controls / `not_checked`.
- `india-cbic-customs`: customs_reference / `not_checked`.
- `gac-sanctions`: sanctions_restricted_party / `not_checked`.
- `world-bank-wits`: global_trade_data / `not_checked`.
- `itc-trade-map`: buyer_importer_discovery / `not_checked`.
- `wco-harmonized-system`: hs_code_doctrine / `not_checked`.
- `icc-incoterms-2020`: responsibility_path / `not_checked`.
- `opc-pipeda-principles`: trade_data / `not_checked`.
- `owasp-file-upload`: import_controls / `not_checked`.
- `owasp-llm01-prompt-injection`: official_reference / `not_checked`.
- `nist-ai-rmf`: official_reference / `not_checked`.
- `stripe-go-live`: official_reference / `not_checked`.

## Packet Impacts

- `packet-frozen-tuna-canada-001`: source_checking_or_reviewer_ready_reference_only; next move: Refresh unchecked sources, preserve reference-only wording, and route the packet to scoped expert review.

## Closed Gates

- External effects created: false
- Claims opened: false
- Public launch ready: false
- Hosted private beta ready: false
- Live payment ready: false
