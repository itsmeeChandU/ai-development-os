# Public Trade Readiness Guide

Trade Readiness Copilot is the public product surface. Importer Source
Readiness Copilot is the internal readiness/blocker engine.

## Public Flow

1. Open the app with `python3 scripts/serve_operator_app.py`.
2. Use `/tools` to choose import readiness, export readiness, buyer/broker
   packet building, document analysis, missing evidence checking, or PDF
   report generation.
3. Use `/trade-check` or `/tools/export-readiness`.
4. Select trade direction, origin, destination, product/category, HS code if
   known, exporter, Canadian buyer/importer, importer of record, and Incoterms.
5. Upload at least one PDF and accept the AI/data notice.
6. Review the result page at `/public/packets/:id/result`.
7. Download the draft readiness PDF, buyer-ready packet, or broker review
   packet.
8. Delete uploaded local files or create an account for a saved workspace.

## Export-To-Canada Mode

Foreign exporters can create an Export-to-Canada packet. The product separates:

- exporter-side readiness: origin-country and document readiness, including
  product specs, commercial documents, certificates, proof of origin, and
  country-specific evidence that may need review
- importer-side readiness: Canadian buyer/importer, importer of record,
  Incoterms, CBSA/CARM, CFIA/AIRS when relevant, import controls,
  restricted-party screening, and broker/expert review

If the Canadian buyer/importer handles import, the product prepares a
buyer-ready export packet and questions. If the exporter may sell delivered
into Canada, use DDP, or act as importer of record/non-resident importer, the
product marks that as higher responsibility and requires broker/compliance
review.

## Boundaries

The product never outputs approval, tariff confirmation, CFIA clearance, legal
advice, customs advice, buyer validation, shipment readiness, supplier
recommendation, trade-agreement preference confirmation, or launch readiness.
AI may structure evidence when allowed, but qualified people and current
official evidence remain required for external decisions.

## Machine Artifacts

- `system_review_graph/public_trade_readiness_manifest.json`
- `system_review_graph/exporter_mode_requirements.json`
- `system_review_graph/public_report_types.json`
- `system_review_graph/public_upload_policy.json`
- `system_review_graph/requirements_traceability_matrix.json`
