# Qualified Customs Trade Review Proof

Status: `qualified_customs_trade_review_intake_ready_real_review_evidence_required_claims_closed`

This validates scoped customs/trade review evidence only. It does not confirm tariff treatment, approve CFIA/admissibility, act as a customs broker, approve shipment, or approve public launch.

## Current Result

- Review records received: 0
- Accepted review records: 0
- Missing evidence categories: 14
- Customs/trade reviewed by evidence: false
- Tariff confirmed by review evidence: false
- CFIA approved by review evidence: false
- Customs ready by review evidence: false
- Shipment ready by review evidence: false
- Claims opened by intake: false

## Drop Paths

- `external_inputs/qualified_customs_trade_review.json`
- `external_inputs/qualified_customs_trade_reviews/*.json`

## Gate Matrix

| Evidence | Status | Blocks Review |
| --- | --- | --- |
| Review scope, product, and lane | `missing_real_customs_trade_review_evidence` | `true` |
| Reviewer identity, qualification, and scope | `missing_real_customs_trade_review_evidence` | `true` |
| CBSA importer obligations review | `missing_real_customs_trade_review_evidence` | `true` |
| Broker boundary and importer responsibility | `missing_real_customs_trade_review_evidence` | `true` |
| HS candidate and classification boundary | `missing_real_customs_trade_review_evidence` | `true` |
| Customs tariff/treatment review | `missing_real_customs_trade_review_evidence` | `true` |
| Origin, preference, and origin-document review | `missing_real_customs_trade_review_evidence` | `true` |
| Regulated goods and CFIA/AIRS review | `missing_real_customs_trade_review_evidence` | `true` |
| Sanctions and import/export controls review | `missing_real_customs_trade_review_evidence` | `true` |
| Required documents and accounting review | `missing_real_customs_trade_review_evidence` | `true` |
| Incoterms, importer of record, and responsibility path | `missing_real_customs_trade_review_evidence` | `true` |
| Allowed and blocked claim language | `missing_real_customs_trade_review_evidence` | `true` |
| Unresolved findings and next actions | `missing_real_customs_trade_review_evidence` | `true` |
| Reviewer signed scope decision | `missing_real_customs_trade_review_evidence` | `true` |

## Source Anchors

- Canada Border Services Agency: Importing commercial goods into Canada (https://www.cbsa-asfc.gc.ca/import/menu-eng.html)
- Canada Border Services Agency: Licensed customs brokers (https://www.cbsa-asfc.gc.ca/services/cb-cd/cb-cd-eng.html)
- Canada Border Services Agency: Canadian Customs Tariff 2026 (https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/2026/menu-eng.html)
- Canadian Food Inspection Agency: Automated Import Reference System (https://inspection.canada.ca/en/importing-food-plants-animals/airs)
- Global Affairs Canada: Canadian sanctions (https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/current-actuelles.aspx)
- Global Affairs Canada: Export and import controls (https://www.international.gc.ca/controls-controles/index.aspx)
- World Customs Organization: Harmonized System (https://www.wcoomd.org/en/topics/nomenclature/overview/what-is-the-harmonized-system.aspx)
- International Chamber of Commerce: Incoterms 2020 (https://iccwbo.org/business-solutions/incoterms-rules/incoterms-2020/)
- Directorate General of Foreign Trade: Importer Exporter Code (https://www.dgft.gov.in/CP/?opt=iec-profile-management)
