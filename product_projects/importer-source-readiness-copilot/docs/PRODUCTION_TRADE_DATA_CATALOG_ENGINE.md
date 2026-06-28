# Production Trade Data Catalog Engine

Status: `production_trade_data_catalog_engine_ready_query_plans_no_values_loaded`

The trade-data catalog creates query plans, browse cards, input requirements, and work orders. It does not show numeric trade values, rank products as best, prove demand, prove profit, validate buyers, or approve trade action until dated rows and review evidence exist.

## Browse Cards

### Browse imports into Canada

Start with what Canada appears to import, then narrow by product family and origin country.

- Query templates: 2
- Values loaded: false
- Recommendation claimed: false
- Next valid move: Choose a product family and origin lane, then attach dated import rows.

### Browse exports from Canada

Start with what Canada appears to export, then narrow by destination and access questions.

- Query templates: 2
- Values loaded: false
- Recommendation claimed: false
- Next valid move: Choose a destination and product family, then attach dated export rows.

### Compare origin countries

Compare lanes without calling one best or approved.

- Query templates: 2
- Values loaded: false
- Recommendation claimed: false
- Next valid move: Select the lane that deserves evidence collection and expert questions.

### Find possible importer leads

Find possible lead sources after a product family is selected.

- Query templates: 1
- Values loaded: false
- Recommendation claimed: false
- Next valid move: Record the lead source and move through buyer evidence levels.

### Check regulated-goods risk

Spot food, plant, animal, controlled, or restricted-country questions early.

- Query templates: 2
- Values loaded: false
- Recommendation claimed: false
- Next valid move: Attach source snapshot and route to qualified review if risk tags appear.

## Query Templates

- `canada_imports_by_product_origin`: Canada imports by product and origin (import_into_canada).
- `canada_exports_by_product_destination`: Canada exports by product and destination (export_from_canada).
- `origin_country_comparison_for_canada`: Origin-country comparison for Canada (import_into_canada).
- `canadian_importer_lead_lookup`: Possible Canadian importer leads (import_into_canada).
- `regulated_goods_source_overlay`: Regulated goods source overlay (both).
- `market_access_comparison`: Market access comparison (both).
- `global_context_fallback`: Global trade context fallback (both).

## Closed Gates

- Numeric values shown: false
- Recommendations created: false
- Demand claimed: false
- Profitability claimed: false
- Buyer validation claimed: false
- Supplier verification claimed: false
- Claims opened: false
