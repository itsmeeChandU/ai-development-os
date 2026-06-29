# Production Document Intelligence Engine

Status: `production_document_intelligence_engine_ready_local_pipeline_security_gates_closed`

This engine turns uploads and document references into draft evidence records with provenance and closed claim gates.

## Proof Boundary

Document intelligence now has a production-shaped local pipeline, official sample-form routing, document records, extracted field provenance, evidence mapping, redaction previews, and closed gates. It still does not prove hosted upload security, malware scanning, private object storage, AI-provider safety, document authenticity, customs/tariff correctness, CFIA clearance, buyer validation, supplier verification, shipment approval, or public launch readiness.

## Pipeline

- `upload_intake`: local_policy_ready_hosted_auth_required (real_uploads_blocked_until_hosted_security_privacy_review).
- `extension_allowlist`: local_policy_ready (hosted_validation_must_repeat_server_side).
- `file_signature_check`: local_parser_ready (signature_check_is_not_malware_scan).
- `generated_filename`: local_policy_ready (private_object_storage_required_for_real_files).
- `size_and_page_limit`: local_policy_ready (limits_need_hosted_enforcement).
- `quarantine`: local_policy_ready (object_storage_and_access_policy_not_proven).
- `malware_scan`: external_gate_required_not_proven (real_uploads_blocked_until_malware_scanner_proof).
- `ocr_text_extraction`: local_parser_ready_ocr_external_gate_closed (ocr_outputs_are_draft).
- `document_classification`: local_classifier_ready_draft_only (classification_is_not_authenticity_or_compliance_proof).
- `field_extraction`: local_extractor_ready_draft_only (parser_extraction_is_draft_evidence).
- `confidence_scoring`: local_scoring_ready (confidence_score_cannot_open_claims).
- `user_confirmation`: local_confirmation_gate_ready (unconfirmed_fields_block_claims).
- `evidence_ledger_mapping`: local_mapping_ready (evidence_mapping_does_not_verify_document).
- `redaction_preview`: local_redaction_preview_ready (production_redaction_requires_review).
- `ai_optional_analysis`: policy_ready_external_provider_review_required (ai_cannot_open_document_claims).
- `report_usage`: local_report_route_ready (reports_must_keep_blocked_claims_visible).

## Document Classes

- `commercial_invoice`: Commercial invoice.
- `packing_list`: Packing list.
- `certificate_of_origin`: Certificate of origin.
- `bill_of_lading`: Bill of lading.
- `airway_bill`: Airway bill.
- `product_specification`: Product specification.
- `lab_certificate`: Lab certificate.
- `phytosanitary_or_health_certificate`: Phytosanitary or health certificate.
- `purchase_order`: Purchase order.
- `contract`: Contract.
- `inspection_report`: Inspection report.

## Records

- Document records: 18
- Extracted fields: 110
- Evidence records: 18
- Redaction previews: 18
- Parser QA fixtures passed: 11 of 11

## Source Records

- `cbsa-ci1-canada-customs-invoice`: https://www.cbsa-asfc.gc.ca/publications/forms-formulaires/ci1.pdf
- `cbsa-a8a-b-cargo-control-document`: https://www.cbsa-asfc.gc.ca/publications/forms-formulaires/a8a-b.pdf
- `cfia-5272-documentation-review-request`: https://inspection.canada.ca/sites/default/files/legacy/DAM/DAM-form-forme/STAGING/text-texte/c5272_re_1369400657637_eng.pdf
- `india-dgft-appendices-anf`: https://www.dgft.gov.in/CP/?opt=appendices-and-anf
- `india-cbic-customs-forms`: https://www.cbic.gov.in/
- `vietnam-customs-portal`: https://www.customs.gov.vn/
- `cbsa-b3b-commented-menu-route`: https://www.cbsa-asfc.gc.ca/publications/forms-formulaires/menu-eng.html
- `owasp-file-upload`: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

## Closed Gates

- Real uploads enabled: false
- Malware scan proven: false
- Private object storage ready: false
- Parser outputs are draft: true
- Claims opened: false
- Public launch ready: false
