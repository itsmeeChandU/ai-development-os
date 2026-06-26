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

Proof boundary: document processing does not verify authenticity, classify tariffs, clear CFIA/customs requirements, validate buyers, or approve shipments.
