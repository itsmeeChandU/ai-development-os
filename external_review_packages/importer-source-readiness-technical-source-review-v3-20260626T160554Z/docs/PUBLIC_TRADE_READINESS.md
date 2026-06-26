# Public Trade Readiness Guide

Trade Readiness Copilot is the public product surface. Importer Source
Readiness Copilot is the internal readiness/blocker engine.

## Public Flow

1. Open the app with `python3 scripts/serve_operator_app.py`.
2. Use `/start` when the user has no documents and needs a beginner starter
   checklist.
3. Use `/tools` to choose import readiness, export readiness, buyer/broker
   packet building, document analysis, missing evidence checking, or PDF
   report generation.
4. Use `/opportunities` for signal-only opportunity research prompts, or
   `/reports/sample` to inspect the PDF-first report set.
5. Use `/pricing` or `/billing` to inspect local credit gates before heavy
   OCR, AI, source-monitoring, private-AI, or agent/API work.
6. Use `/trade-check`, `/tools/document-check`, or `/tools/export-readiness`.
7. Select trade direction, origin, destination, product/category, HS code if
   known, exporter, Canadian buyer/importer, importer of record, and Incoterms.
8. Upload at least one PDF and accept the AI/data notice. Uploaded PDFs are
   stored under generated quarantine names, triaged for native text/OCR need,
   and not directly served as public files.
9. Confirm extracted metadata at `/public/packets/:id/confirm`.
10. Review the result page at `/public/packets/:id/result`.
11. Download the starter checklist, draft readiness PDF, missing evidence PDF,
   buyer-ready packet, or broker review packet.
12. Use `/packets/:id/source-monitoring` to inspect stale-source impact and
    `/packets/:id/safe-summary` for external AI drafting text.
13. Use the ChatGPT-safe summary only for drafting questions, then delete
    uploaded local files or create an account for a saved workspace.

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

## Intelligence Hub Policy Monitor

The product now generates a database-style source monitor contract:

- `system_review_graph/intelligence_hub_policy_monitor.json`
- `system_review_graph/policy_source_snapshots.json`
- `system_review_graph/policy_change_impact_report.json`
- `system_review_graph/policy_intelligence.sqlite`

This contract maps official Canadian sources to packets, snapshot hashes,
change classifiers, packet impact rows, and stale-source blockers. It is a
bridge for Intelligence Hub-style source monitoring. It does not prove current
tariff, CFIA, import permit, sanctions, buyer, supplier, legal, or commercial
readiness.

## Machine Artifacts

- `system_review_graph/public_trade_readiness_manifest.json`
- `system_review_graph/exporter_mode_requirements.json`
- `system_review_graph/public_report_types.json`
- `system_review_graph/public_upload_policy.json`
- `system_review_graph/requirements_traceability_matrix.json`
- `system_review_graph/intelligence_hub_policy_monitor.json`
- `system_review_graph/completion_platform_manifest.json`
- `system_review_graph/country_coverage_report.json`
- `system_review_graph/opportunity_scanner_report.json`
- `system_review_graph/transport_readiness_report.json`
- `system_review_graph/billing_credit_controls.json`
- `system_review_graph/agent_api_manifest.json`
- `system_review_graph/traffic_pages_manifest.json`
