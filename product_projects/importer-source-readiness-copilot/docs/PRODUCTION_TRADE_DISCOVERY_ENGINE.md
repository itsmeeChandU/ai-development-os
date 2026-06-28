# Production Trade Discovery Engine

Status: `production_trade_discovery_engine_ready_beginner_research_routed_no_opportunity_claims`

Trade discovery is browse-and-prepare logic. It can show source-routed categories, country lanes, questions, and evidence gaps. It cannot tell a user what product is best, prove demand, confirm profit, validate buyers, verify suppliers, approve customs/CFIA status, or make shipment decisions.

## Requirement Audit

Existing market intelligence starts after a product/packet exists; beginner users also need product, country, and import/export browsing before packet creation.

## Beginner Flows

### Browse goods Canada imports

Help a user choose a product family and origin country to research before making a packet.

- Source routes: 5
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

### Browse goods Canada exports

Help a Canadian exporter explore product families and destination markets safely.

- Source routes: 4
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

### Compare origin countries into Canada

Show which origin-country lanes need official source and evidence checks before a user commits.

- Source routes: 4
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

### Check if goods may be regulated

Warn users early when food, plant, animal, seafood, health, chemical, or controlled goods need review.

- Source routes: 4
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

### Prepare buyer questions

Help an exporter ask a potential buyer/importer the right readiness questions.

- Source routes: 3
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

### Prepare supplier questions

Help an importer or exporter request evidence from a supplier before relying on them.

- Source routes: 3
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

### Create a starter packet without documents

Turn early browsing into a useful packet even when the user has no files.

- Source routes: 4
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

### Prepare for expert or broker review

Package the unresolved questions so a broker, trade consultant, or reviewer can answer the exact scope.

- Source routes: 4
- Recommendation claimed: false
- Claims opened: false
- Safe copy: Use this to choose what to research next. It does not decide what you should buy, sell, import, or export.

## Category Families

- `food_agri_seafood`: Food, agriculture, and seafood (4 source routes; opportunity claim false).
- `apparel_textiles`: Apparel and textiles (4 source routes; opportunity claim false).
- `home_furniture_goods`: Furniture and home goods (3 source routes; opportunity claim false).
- `machinery_parts_tools`: Machinery, tools, and industrial parts (3 source routes; opportunity claim false).
- `electronics_components`: Electronics and components (4 source routes; opportunity claim false).
- `automotive_parts`: Automotive parts (3 source routes; opportunity claim false).
- `health_beauty_cosmetics`: Health, beauty, and cosmetics (4 source routes; opportunity claim false).
- `chemicals_cleaning_materials`: Chemicals, cleaning products, and materials (4 source routes; opportunity claim false).
- `building_materials`: Building materials (3 source routes; opportunity claim false).
- `packaging_paper_printed_goods`: Packaging, paper, and printed goods (3 source routes; opportunity claim false).
- `metals_minerals_raw_materials`: Metals, minerals, and raw materials (4 source routes; opportunity claim false).
- `general_consumer_goods`: General consumer goods (3 source routes; opportunity claim false).
- `services_not_merchandise_scope`: Services and digital products (1 source routes; opportunity claim false).

## Country Lanes

- `IN-to-CA`: India to Canada as `import_into_canada` (reference_only; recommendation false).
- `VN-to-CA`: Vietnam to Canada as `import_into_canada` (reference_only; recommendation false).
- `US-to-CA`: United States to Canada as `import_into_canada` (reference_only; recommendation false).
- `MX-to-CA`: Mexico to Canada as `import_into_canada` (reference_only; recommendation false).
- `CN-to-CA`: China to Canada as `import_into_canada` (reference_only; recommendation false).
- `BD-to-CA`: Bangladesh to Canada as `import_into_canada` (reference_only; recommendation false).
- `TR-to-CA`: Turkey to Canada as `import_into_canada` (reference_only; recommendation false).
- `BR-to-CA`: Brazil to Canada as `import_into_canada` (reference_only; recommendation false).
- `EU-to-CA`: European Union to Canada as `import_into_canada` (reference_only; recommendation false).
- `UK-to-CA`: United Kingdom to Canada as `import_into_canada` (reference_only; recommendation false).
- `UAE-to-CA`: United Arab Emirates to Canada as `import_into_canada` (reference_only; recommendation false).
- `CA-to-US`: Canada to United States as `export_from_canada` (reference_only; recommendation false).
- `CA-to-EU`: Canada to European Union as `export_from_canada` (reference_only; recommendation false).
- `GENERIC-to-CA`: Generic or unsupported country to Canada as `import_into_canada` (generic; recommendation false).

## Closed Gates

- Best product claim: false
- Market opportunity claim: false
- Demand claim: false
- Profitability claim: false
- Buyer validation claim: false
- Supplier verification claim: false
- Customs/CFIA approval claim: false
- Public launch ready: false
