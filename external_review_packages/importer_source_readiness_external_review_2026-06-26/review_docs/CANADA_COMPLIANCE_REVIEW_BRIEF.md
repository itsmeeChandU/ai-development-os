# Canada Compliance Review Brief

## Review Goal

Review whether the product correctly frames Canadian import/export, customs,
tariff, food import, sanctions, broker review, and claim boundaries.

## Important Boundary

The product does not claim customs, tariff, CFIA, legal, or import/export
advice readiness. It only routes reference sources and blockers.

## Canadian Reference Surfaces

The product currently references:

- CBSA CARM
- CBSA importing commercial goods
- CBSA Customs Tariff 2026
- CFIA AIRS
- Global Affairs Canada import controls
- Justice Laws Import Control List
- Canadian sanctions list
- ISED Trade Data Online
- Canadian Importers Database
- CBSA Licensed Customs Brokers
- BizPaL
- PIPEDA reference
- Canadian Centre for Cyber Security baseline controls
- BDC financial planning template

Review source rows in:

```text
sources/importer-source-readiness-copilot/data/canada_tool_registry.json
sources/importer-source-readiness-copilot/data/official_source_registry.json
sources/importer-source-readiness-copilot/data/country_requirements_matrix.json
```

## Questions

1. Are the selected Canadian references appropriate?
2. Are any required official sources missing?
3. Are claim boundaries strong enough?
4. Is the country requirements matrix structured correctly?
5. What additional fields are needed for real broker/compliance review?
6. What evidence is needed before any tariff or HS-code claim?
7. What evidence is needed before any CFIA or food import claim?
8. What evidence is needed before sanctions/restricted-party clearance?
9. What would a licensed customs broker need in the review packet?

## Output Requested

Please identify:

- blocking compliance issues
- missing source categories
- wording that could imply unauthorized advice
- exact evidence needed for controlled private beta
- exact evidence needed for public launch
