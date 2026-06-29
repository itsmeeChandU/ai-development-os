# Document Processing

The document pipeline is PDF-first and fail-closed. It helps users understand what was uploaded and what is missing before involving buyers, brokers, or experts.

## Flow

1. Public upload accepts PDFs only.
2. Files are stored in a quarantine folder with generated names.
3. Direct file serving is disabled.
4. The local triage estimates pages, hashes the file, detects native text, and flags OCR needs.
5. Extracted metadata remains draft-only until the user confirms it.
6. Missing evidence and unsafe claims remain blockers.

## Public Outputs

- Starter Checklist PDF
- Missing Evidence Checklist PDF
- Draft Trade Readiness Report PDF
- Buyer-Ready Packet PDF
- Broker/Freight-Forwarder Packet PDF
- ChatGPT-safe summary

## Generated Artifacts

- `system_review_graph/public_upload_policy.json`
- `system_review_graph/public_upload_manifest.json`
- `system_review_graph/public_report_types.json`
- `system_review_graph/production_document_intelligence_manifest.json`
- `system_review_graph/production_document_pipeline.json`
- `system_review_graph/production_document_extracted_fields.json`
- `data/official_sample_documents/canada/*.pdf`
- `data/parser_qa_documents/*.pdf`
- `system_review_graph/production_document_sample_library.json`

## Expected Document Set

The production document engine tracks the common trade-document set a business
owner may need to collect: commercial invoice, packing list, certificate of
origin, bill of lading, airway bill, product specification, lab certificate,
phytosanitary or health certificate, purchase order, contract, and inspection
report.

Official CBSA/CFIA sample PDFs are used only to orient the parser and reviewer
questions. Filled parser QA PDFs are synthetic test documents only. Neither
official samples nor synthetic fixtures are customer evidence, authenticity
proof, customs approval, CFIA clearance, buyer validation, or supplier
verification.

The sample library separates three kinds of records:

- official Canada PDF samples stored locally for parser orientation
- India/Vietnam/Canada official source routes where no stable local sample PDF
  is treated as verified
- synthetic filled PDFs used only for parser regression tests

Every sample-library row keeps customer-evidence and approval claims closed.

Proof boundary: document processing does not verify authenticity, classify tariffs, clear CFIA/customs requirements, validate buyers, or approve shipments.
