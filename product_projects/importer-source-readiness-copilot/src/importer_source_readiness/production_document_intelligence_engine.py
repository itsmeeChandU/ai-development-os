"""Production document intelligence engine.

This module upgrades local PDF triage into a production-shaped document
pipeline. It uses real repo artifacts and an official CBSA sample form, but it
keeps customer-file, malware, storage, AI, authenticity, and compliance claims
closed until production controls and qualified review exist.
"""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .document_processing import TRADE_DOCUMENT_TYPES, triage_pdf_upload


STATUS = "production_document_intelligence_engine_ready_local_pipeline_security_gates_closed"
PARSER_QA_STATUS = "production_document_parser_qa_ready_fixture_expectations_checked"
SAMPLE_LIBRARY_STATUS = "production_document_sample_library_ready_source_boundaries_closed"

CBSA_CI1_SOURCE_ID = "cbsa-ci1-canada-customs-invoice"
CBSA_CI1_URL = "https://www.cbsa-asfc.gc.ca/publications/forms-formulaires/ci1.pdf"

OFFICIAL_SAMPLE_DOCUMENTS: tuple[dict[str, Any], ...] = (
    {
        "source_id": CBSA_CI1_SOURCE_ID,
        "country_code": "CA",
        "filename": "canada/cbsa-ci1-canada-customs-invoice.pdf",
        "url": CBSA_CI1_URL,
        "document_class": "commercial_invoice",
        "source_owner": "Canada Border Services Agency",
        "sample_level": "official_pdf_downloaded",
    },
    {
        "source_id": "cbsa-a8a-b-cargo-control-document",
        "country_code": "CA",
        "filename": "canada/cbsa-a8a-b-cargo-control-document.pdf",
        "url": "https://www.cbsa-asfc.gc.ca/publications/forms-formulaires/a8a-b.pdf",
        "document_class": "bill_of_lading",
        "source_owner": "Canada Border Services Agency",
        "sample_level": "official_pdf_downloaded",
    },
    {
        "source_id": "cfia-5272-documentation-review-request",
        "country_code": "CA",
        "filename": "canada/cfia-5272-documentation-review-request.pdf",
        "url": "https://inspection.canada.ca/sites/default/files/legacy/DAM/DAM-form-forme/STAGING/text-texte/c5272_re_1369400657637_eng.pdf",
        "document_class": "phytosanitary_or_health_certificate",
        "source_owner": "Canadian Food Inspection Agency",
        "sample_level": "official_pdf_downloaded",
    },
)

SOURCE_ROUTE_ONLY_SAMPLES: tuple[dict[str, Any], ...] = (
    {
        "source_id": "india-dgft-appendices-anf",
        "country_code": "IN",
        "url": "https://www.dgft.gov.in/CP/?opt=appendices-and-anf",
        "document_class": "certificate_of_origin",
        "source_owner": "Directorate General of Foreign Trade",
        "sample_level": "official_source_route_only",
        "availability_status": "dynamic_page_no_stable_pdf_download_verified",
    },
    {
        "source_id": "india-cbic-customs-forms",
        "country_code": "IN",
        "url": "https://www.cbic.gov.in/",
        "document_class": "shipping_bill_or_bill_of_entry",
        "source_owner": "Central Board of Indirect Taxes and Customs",
        "sample_level": "official_source_route_only",
        "availability_status": "official_route_recorded_pdf_download_not_verified",
    },
    {
        "source_id": "vietnam-customs-portal",
        "country_code": "VN",
        "url": "https://www.customs.gov.vn/",
        "document_class": "customs_declaration_route",
        "source_owner": "General Department of Vietnam Customs",
        "sample_level": "official_source_route_only",
        "availability_status": "official_portal_recorded_pdf_download_not_verified",
    },
    {
        "source_id": "cbsa-b3b-commented-menu-route",
        "country_code": "CA",
        "url": "https://www.cbsa-asfc.gc.ca/publications/forms-formulaires/menu-eng.html",
        "document_class": "customs_coding_form_route",
        "source_owner": "Canada Border Services Agency",
        "sample_level": "official_source_route_only",
        "availability_status": "current_forms_menu_comments_out_b3b_pdf_row",
    },
)

SYNTHETIC_FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "filename": "synthetic-commercial-invoice-canada.pdf",
        "country_code": "CA",
        "document_class": "commercial_invoice",
        "text": "Commercial Invoice number INV-QA-001 HS code: 0902.30 origin: India destination: Canada buyer: Maple Import Foods Inc supplier: Example Exporter Pvt Ltd FOB amount USD 12500 product: Organic turmeric powder date 2026-06-28",
    },
    {
        "filename": "synthetic-packing-list-india-export.pdf",
        "country_code": "IN",
        "document_class": "packing_list",
        "text": "Packing List reference PL-QA-002 origin: India destination: Canada supplier: Example Exporter Pvt Ltd buyer: Maple Import Foods Inc product: Organic turmeric powder quantity 100 cartons gross weight 1200 kg net weight 1100 kg",
    },
    {
        "filename": "synthetic-certificate-of-origin-india.pdf",
        "country_code": "IN",
        "document_class": "certificate_of_origin",
        "text": "Certificate of Origin number CO-QA-003 country of origin: India destination: Canada HS code: 0910.30 exporter: Example Exporter Pvt Ltd buyer: Maple Import Foods Inc",
    },
    {
        "filename": "synthetic-bill-of-lading-vietnam.pdf",
        "country_code": "VN",
        "document_class": "bill_of_lading",
        "text": "Bill of Lading BL-QA-004 carrier: Example Ocean Line port of loading: Ho Chi Minh City port of discharge: Vancouver origin: Vietnam destination: Canada supplier: Example Seafood Supplier buyer: Maple Import Foods Inc quantity 40 cartons",
    },
    {
        "filename": "synthetic-airway-bill-generic.pdf",
        "country_code": "GENERIC",
        "document_class": "airway_bill",
        "text": "Air Waybill AWB-QA-005 carrier: Example Air Cargo shipper: Example Exporter consignee: Maple Import Foods Inc origin: India destination: Canada product: Sample spices quantity 12 boxes",
    },
    {
        "filename": "synthetic-product-specification-vietnam-seafood.pdf",
        "country_code": "VN",
        "document_class": "product_specification",
        "text": "Product Specification product: Frozen tuna fillet composition: tuna intended use: food import origin: Vietnam destination: Canada HS code: 030487 product dimensions and packaging 10 kg cartons",
    },
    {
        "filename": "synthetic-lab-certificate-food.pdf",
        "country_code": "GENERIC",
        "document_class": "lab_certificate",
        "text": "Lab Certificate certificate number LAB-QA-007 lab name: Example Accredited Lab product: Frozen tuna fillet test method: microbiology result: pass sample date 2026-06-28 origin: Vietnam",
    },
    {
        "filename": "synthetic-health-certificate-vietnam.pdf",
        "country_code": "VN",
        "document_class": "phytosanitary_or_health_certificate",
        "text": "Health Certificate number HC-QA-008 issuing authority: Example Veterinary Authority product: Frozen tuna fillet origin: Vietnam destination: Canada exporter: Example Seafood Supplier",
    },
    {
        "filename": "synthetic-purchase-order-canada-buyer.pdf",
        "country_code": "CA",
        "document_class": "purchase_order",
        "text": "Purchase Order PO-QA-009 buyer: Maple Import Foods Inc supplier: Example Exporter Pvt Ltd product: Organic turmeric powder quantity 100 cartons amount CAD 18000 destination: Canada",
    },
    {
        "filename": "synthetic-contract-incoterms.pdf",
        "country_code": "GENERIC",
        "document_class": "contract",
        "text": "Sales Contract contract number SC-QA-010 buyer: Maple Import Foods Inc supplier: Example Exporter Pvt Ltd product: Organic turmeric powder incoterms: FOB payment terms: 30 percent advance balance before shipment governing terms: Ontario commercial law amount USD 12500 date 2026-06-28",
    },
    {
        "filename": "synthetic-inspection-report-supplier.pdf",
        "country_code": "GENERIC",
        "document_class": "inspection_report",
        "text": "Inspection Report IR-QA-011 inspection body: Example Inspection Services supplier: Example Seafood Supplier product: Frozen tuna fillet result: passed inspection date 2026-06-28 prior shipment evidence attached",
    },
)

DOCUMENT_BLOCKED_CLAIMS = (
    "document_authenticity_verified",
    "document_complete",
    "customs_ready",
    "tariff_confirmed",
    "cfia_approved",
    "origin_confirmed",
    "buyer_validated",
    "supplier_verified",
    "shipment_approved",
)

SAMPLE_LIBRARY_BLOCKED_CLAIMS = (
    "official_form_current_law",
    "document_required_for_lane",
    "document_authenticity_verified",
    "document_complete",
    "customs_ready",
    "tariff_confirmed",
    "cfia_approved",
    "origin_confirmed",
    "buyer_validated",
    "supplier_verified",
    "shipment_approved",
)

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "origin_country": ("country_mentions",),
    "destination_country": ("country_mentions",),
    "product": ("product_description",),
    "parties": ("parties", "buyer_or_importer", "supplier_or_exporter"),
    "shipper": ("shipper", "supplier_or_exporter"),
    "consignee": ("consignee", "buyer_or_importer"),
}

REQUIRED_TRADE_DOCUMENT_CLASSES: tuple[dict[str, Any], ...] = (
    {
        "document_class": "commercial_invoice",
        "label": "Commercial invoice",
        "source_basis": "CBSA CI1 official sample form and common trade-document requirements",
        "expected_fields": ["invoice_or_reference", "buyer_or_importer", "supplier_or_exporter", "origin_country", "destination_country", "amounts"],
    },
    {
        "document_class": "packing_list",
        "label": "Packing list",
        "source_basis": "Common shipment-document package",
        "expected_fields": ["quantities", "weights", "packages", "product_description"],
    },
    {
        "document_class": "certificate_of_origin",
        "label": "Certificate of origin",
        "source_basis": "Origin evidence route; not proof without review",
        "expected_fields": ["origin_country", "hs_code", "supplier_or_exporter"],
    },
    {
        "document_class": "bill_of_lading",
        "label": "Bill of lading",
        "source_basis": "Transport-document route",
        "expected_fields": ["carrier", "port_of_loading", "port_of_discharge", "buyer_or_importer", "supplier_or_exporter"],
    },
    {
        "document_class": "airway_bill",
        "label": "Airway bill",
        "source_basis": "Transport-document route",
        "expected_fields": ["carrier", "origin_country", "destination_country", "shipper", "consignee"],
    },
    {
        "document_class": "product_specification",
        "label": "Product specification",
        "source_basis": "Product-document route",
        "expected_fields": ["product_description", "composition", "intended_use", "hs_code"],
    },
    {
        "document_class": "lab_certificate",
        "label": "Lab certificate",
        "source_basis": "Product testing evidence route",
        "expected_fields": ["test_method", "result", "lab_name", "sample_date"],
    },
    {
        "document_class": "phytosanitary_or_health_certificate",
        "label": "Phytosanitary or health certificate",
        "source_basis": "CFIA-regulated product evidence route",
        "expected_fields": ["issuing_authority", "product", "origin_country", "certificate_number"],
    },
    {
        "document_class": "purchase_order",
        "label": "Purchase order",
        "source_basis": "Buyer evidence route",
        "expected_fields": ["buyer_or_importer", "supplier_or_exporter", "product_description", "amounts"],
    },
    {
        "document_class": "contract",
        "label": "Contract",
        "source_basis": "Commercial responsibility evidence route",
        "expected_fields": ["parties", "incoterms", "payment_terms", "governing_terms"],
    },
    {
        "document_class": "inspection_report",
        "label": "Inspection report",
        "source_basis": "Supplier/product evidence route",
        "expected_fields": ["inspection_body", "inspection_date", "result", "product_description"],
    },
)

PIPELINE_STAGES: tuple[dict[str, Any], ...] = (
    {
        "stage": "upload_intake",
        "control": "PDF-only intake with user notice and local rate-limit policy",
        "status": "local_policy_ready_hosted_auth_required",
        "gate": "real_uploads_blocked_until_hosted_security_privacy_review",
    },
    {
        "stage": "extension_allowlist",
        "control": "Allowlisted PDF extension and content-type policy",
        "status": "local_policy_ready",
        "gate": "hosted_validation_must_repeat_server_side",
    },
    {
        "stage": "file_signature_check",
        "control": "PDF magic-byte and EOF checks through bounded parser",
        "status": "local_parser_ready",
        "gate": "signature_check_is_not_malware_scan",
    },
    {
        "stage": "generated_filename",
        "control": "Generated quarantine names instead of direct user filenames",
        "status": "local_policy_ready",
        "gate": "private_object_storage_required_for_real_files",
    },
    {
        "stage": "size_and_page_limit",
        "control": "5 MB and 25-page public quick-check limits",
        "status": "local_policy_ready",
        "gate": "limits_need_hosted_enforcement",
    },
    {
        "stage": "quarantine",
        "control": "No direct file serving from quarantine paths",
        "status": "local_policy_ready",
        "gate": "object_storage_and_access_policy_not_proven",
    },
    {
        "stage": "malware_scan",
        "control": "Malware scan is required before real customer-file handling",
        "status": "external_gate_required_not_proven",
        "gate": "real_uploads_blocked_until_malware_scanner_proof",
    },
    {
        "stage": "ocr_text_extraction",
        "control": "Native text extraction first; OCR requires explicit approval and cost gate",
        "status": "local_parser_ready_ocr_external_gate_closed",
        "gate": "ocr_outputs_are_draft",
    },
    {
        "stage": "document_classification",
        "control": "Document type detection from text and filename signals",
        "status": "local_classifier_ready_draft_only",
        "gate": "classification_is_not_authenticity_or_compliance_proof",
    },
    {
        "stage": "field_extraction",
        "control": "Extracted field rows with provenance and confidence",
        "status": "local_extractor_ready_draft_only",
        "gate": "parser_extraction_is_draft_evidence",
    },
    {
        "stage": "confidence_scoring",
        "control": "Parser confidence score and field confidence labels",
        "status": "local_scoring_ready",
        "gate": "confidence_score_cannot_open_claims",
    },
    {
        "stage": "user_confirmation",
        "control": "All user-facing extracted fields require confirmation before packet use",
        "status": "local_confirmation_gate_ready",
        "gate": "unconfirmed_fields_block_claims",
    },
    {
        "stage": "evidence_ledger_mapping",
        "control": "Each document becomes a bounded EvidenceItem-style record",
        "status": "local_mapping_ready",
        "gate": "evidence_mapping_does_not_verify_document",
    },
    {
        "stage": "redaction_preview",
        "control": "Sensitive field categories are named before AI or sharing",
        "status": "local_redaction_preview_ready",
        "gate": "production_redaction_requires_review",
    },
    {
        "stage": "ai_optional_analysis",
        "control": "AI is optional, labeled, policy-bound, and unable to open gates",
        "status": "policy_ready_external_provider_review_required",
        "gate": "ai_cannot_open_document_claims",
    },
    {
        "stage": "report_usage",
        "control": "Reports carry draft/review/final watermarks and blocked-claim sections",
        "status": "local_report_route_ready",
        "gate": "reports_must_keep_blocked_claims_visible",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return slug or "document"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_present(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    return bool(_text(value))


def _source_by_id(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_text(source.get("id")): source for source in sources if _text(source.get("id"))}


def _doc_class_from_filename(filename: str) -> dict[str, Any]:
    lowered = filename.lower()
    if "commercial" in lowered and "invoice" in lowered:
        document_class = "commercial_invoice"
    elif "invoice" in lowered:
        document_class = "commercial_invoice"
    elif "packing" in lowered:
        document_class = "packing_list"
    elif "origin" in lowered:
        document_class = "certificate_of_origin"
    elif "product" in lowered and ("spec" in lowered or "specification" in lowered):
        document_class = "product_specification"
    elif "lab" in lowered or "certificate-food" in lowered:
        document_class = "lab_certificate"
    elif "health" in lowered or "phytosanitary" in lowered:
        document_class = "phytosanitary_or_health_certificate"
    elif "purchase-order" in lowered or "po-" in lowered:
        document_class = "purchase_order"
    elif "contract" in lowered:
        document_class = "contract"
    elif "inspection" in lowered:
        document_class = "inspection_report"
    elif "airway" in lowered or "air-waybill" in lowered or "awb" in lowered:
        document_class = "airway_bill"
    elif "bill-of-lading" in lowered or "bol" in lowered:
        document_class = "bill_of_lading"
    elif "supplier" in lowered:
        document_class = "supplier_profile"
    else:
        document_class = "unknown_trade_document"
    required = {row["document_class"]: row for row in REQUIRED_TRADE_DOCUMENT_CLASSES}
    if document_class in required:
        row = required[document_class]
        return {
            "type": row["document_class"],
            "label": row["label"],
            "confidence": "medium",
            "signals": ["filename"],
            "expected_fields": row["expected_fields"],
        }
    if document_class == "supplier_profile":
        return {
            "type": "supplier_profile",
            "label": "Supplier profile",
            "confidence": "medium",
            "signals": ["filename"],
            "expected_fields": [
                "supplier_or_exporter",
                "business_registration",
                "export_registration_or_license",
                "product_description",
                "commercial_reference",
            ],
        }
    return {
        "type": "unknown_trade_document",
        "label": "Unknown trade document",
        "confidence": "low",
        "signals": [],
        "expected_fields": ["hs_code", "origin_country", "destination_country", "buyer_or_importer", "supplier_or_exporter"],
    }


def _document_class_contract(document_class: str, *, confidence: str = "high", signal: str = "declared_sample_class") -> dict[str, Any]:
    required = {row["document_class"]: row for row in REQUIRED_TRADE_DOCUMENT_CLASSES}
    row = required.get(document_class)
    if not row:
        return _doc_class_from_filename(document_class)
    return {
        "type": row["document_class"],
        "label": row["label"],
        "confidence": confidence,
        "signals": [signal],
        "expected_fields": row["expected_fields"],
    }


def _redaction_categories(field_name: str) -> list[str]:
    mapping = {
        "buyer_or_importer": ["buyer_names"],
        "supplier_or_exporter": ["supplier_names"],
        "amounts": ["prices"],
        "invoice_or_reference": ["ids"],
        "dates": ["sensitive_notes"],
        "product_description": ["sensitive_notes"],
    }
    return mapping.get(field_name, [])


def _field_records(
    *,
    document_id: str,
    packet_id: str,
    extraction: dict[str, Any],
    provenance: str,
    confirmation_status: str,
    claim_boundary: str,
) -> list[dict[str, Any]]:
    fields = extraction.get("extracted_fields", {})
    confidence = extraction.get("field_confidence", {})
    rows = []
    for field_name, value in fields.items():
        if not _is_present(value):
            continue
        rows.append(
            {
                "field_id": f"field:{document_id}:{field_name}",
                "document_id": document_id,
                "packet_id": packet_id,
                "field_name": field_name,
                "page_or_section": "document_text_or_metadata",
                "extracted_value": value,
                "confidence": confidence.get(field_name, extraction.get("extraction_confidence", "low")),
                "provenance": provenance,
                "user_confirmation_status": confirmation_status,
                "claim_boundary": claim_boundary,
                "redaction_categories": _redaction_categories(field_name),
                "supports_claims": [],
                "blocked_claims": list(DOCUMENT_BLOCKED_CLAIMS),
            }
        )
    return rows


def _field_present(expected: str, fields_by_name: dict[str, Any]) -> bool:
    names = FIELD_ALIASES.get(expected, (expected,))
    return any(_is_present(fields_by_name.get(name)) for name in names)


def _field_gaps(document_type: dict[str, Any], fields: list[dict[str, Any]]) -> list[str]:
    fields_by_name = {row["field_name"]: row.get("extracted_value") for row in fields}
    missing = []
    for expected in document_type.get("expected_fields", []):
        if not _field_present(expected, fields_by_name):
            missing.append(expected)
    return missing


def _record_from_triage(
    *,
    packet_id: str,
    filename: str,
    source_kind: str,
    storage_status: str,
    triage: dict[str, Any],
    source_url: str = "",
    source_id: str = "",
    local_path: str = "",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    document_id = f"document:{packet_id}:{_slug(filename)}"
    if source_kind == "official_sample_form":
        confirmation_status = "sample_form_not_user_evidence"
        provenance = "official_sample_form_reference"
    elif source_kind == "public_upload_manifest":
        confirmation_status = "needs_user_confirmation"
        provenance = "parser_draft_manifest"
    else:
        confirmation_status = "needs_user_confirmation"
        provenance = "parser_draft"
    claim_boundary = (
        "Document parsing organizes draft evidence only. It does not prove authenticity, completeness, "
        "customs/tariff correctness, CFIA clearance, buyer validation, supplier verification, or shipment approval."
    )
    fields = _field_records(
        document_id=document_id,
        packet_id=packet_id,
        extraction=triage,
        provenance=provenance,
        confirmation_status=confirmation_status,
        claim_boundary=claim_boundary,
    )
    document_type = triage.get("document_type_guess") or _doc_class_from_filename(filename)
    if document_type.get("type") == "unknown_trade_document" or document_type.get("confidence") == "low":
        document_type = _doc_class_from_filename(filename)
    record = {
        "document_id": document_id,
        "packet_id": packet_id,
        "filename": filename,
        "source_kind": source_kind,
        "source_id": source_id,
        "source_url": source_url,
        "local_path": local_path,
        "storage_status": storage_status,
        "quarantine_status": "quarantined_local_metadata" if source_kind == "public_upload_manifest" else "sample_reference" if source_kind == "official_sample_form" else "not_quarantined",
        "file_signature_status": "pdf_signature_checked" if triage.get("looks_like_pdf") else "not_pdf_or_not_available",
        "malware_scan_status": "not_proven_external_gate_required",
        "document_processing_mode": triage.get("document_processing_mode", "metadata_only"),
        "extraction_status": triage.get("extraction_status", "metadata_only"),
        "classification": document_type,
        "field_count": len(fields),
        "field_gaps": _field_gaps(document_type, fields),
        "user_confirmation_required": triage.get("user_confirmation_required", True),
        "parser_outputs_are_draft": True,
        "can_support_customer_claims": False,
        "blocked_claims": list(DOCUMENT_BLOCKED_CLAIMS),
        "next_valid_move": (
            "Confirm extracted fields and obtain qualified review before using the document in buyer, broker, or expert packets."
            if fields
            else "Attach the actual document file or obtain a searchable copy before extraction can support packet review."
        ),
        "claim_boundary": claim_boundary,
    }
    return record, fields


def _record_from_declared_missing_document(packet: dict[str, Any], filename: str) -> dict[str, Any]:
    packet_id = _text(packet.get("packet_id"))
    document_id = f"document:{packet_id}:{_slug(filename)}"
    document_type = _doc_class_from_filename(filename)
    return {
        "document_id": document_id,
        "packet_id": packet_id,
        "filename": filename,
        "source_kind": "packet_declared_document",
        "source_id": "",
        "source_url": "",
        "local_path": "",
        "storage_status": "declared_missing_file",
        "quarantine_status": "missing_not_quarantined",
        "file_signature_status": "not_available",
        "malware_scan_status": "not_proven_external_gate_required",
        "document_processing_mode": "not_available",
        "extraction_status": "declared_missing_file",
        "classification": document_type,
        "field_count": 0,
        "field_gaps": list(document_type.get("expected_fields", [])),
        "user_confirmation_required": True,
        "parser_outputs_are_draft": True,
        "can_support_customer_claims": False,
        "blocked_claims": list(DOCUMENT_BLOCKED_CLAIMS),
        "next_valid_move": "Attach the actual document file, then run signature, scan, quarantine, extraction, and user confirmation.",
        "claim_boundary": "A document filename in a packet is not evidence. The actual file, provenance, scan result, extraction, confirmation, and review are required.",
    }


def _public_upload_records(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    for packet in manifest.get("packets", []):
        packet_id = _text(packet.get("packet_id"))
        for file_row in packet.get("files", []):
            filename = _text(file_row.get("original_filename")) or _text(file_row.get("filename")) or "public-upload.pdf"
            document, field_rows = _record_from_triage(
                packet_id=packet_id,
                filename=filename,
                source_kind="public_upload_manifest",
                storage_status="public_upload_manifest_metadata_only_file_not_present",
                triage=file_row,
                local_path=_text(file_row.get("relative_path")),
            )
            document["delete_route"] = packet.get("delete_route", "")
            document["expires_at"] = packet.get("expires_at", "")
            documents.append(document)
            fields.extend(field_rows)
    return documents, fields


def _official_sample_records(root: Path, source_registry: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    base = root / "data" / "official_sample_documents"
    for sample in OFFICIAL_SAMPLE_DOCUMENTS:
        sample_path = base / sample["filename"]
        if not sample_path.exists():
            continue
        triage = triage_pdf_upload(sample_path.name, sample_path.read_bytes())
        source = source_registry.get(sample["source_id"], {})
        document, field_rows = _record_from_triage(
            packet_id=f"official-sample-{sample['country_code'].lower()}-{_slug(sample['document_class'])}",
            filename=sample_path.name,
            source_kind="official_sample_form",
            storage_status="local_official_sample_form_downloaded",
            triage=triage,
            source_url=_text(source.get("url")) or sample["url"],
            source_id=sample["source_id"],
            local_path=str(sample_path.relative_to(root)),
        )
        document["source_owner"] = source.get("name", sample["source_owner"])
        document["country_code"] = sample["country_code"]
        document["sample_level"] = sample["sample_level"]
        document["classification"] = _document_class_contract(
            sample["document_class"],
            confidence="high",
            signal="official_sample_document_class",
        )
        document["field_gaps"] = _field_gaps(document["classification"], field_rows)
        document["sample_form_only"] = True
        document["next_valid_move"] = "Use this official sample only to improve classification and reviewer questions; do not treat it as customer evidence."
        documents.append(document)
        fields.extend(field_rows)
    return documents, fields


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _simple_text_pdf(text: str) -> bytes:
    lines = [line.strip() for line in re.split(r"\s{2,}|\n", text) if line.strip()]
    if len(lines) == 1:
        words = lines[0].split()
        lines = [" ".join(words[index : index + 10]) for index in range(0, len(words), 10)]
    stream_lines = ["BT", "/F1 10 Tf", "50 760 Td"]
    for index, line in enumerate(lines[:32]):
        if index:
            stream_lines.append("0 -16 Td")
        stream_lines.append(f"({_pdf_escape(line)}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="ignore")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >> endobj\n",
        b"4 0 obj << /Length " + str(len(stream)).encode("ascii") + b" >> stream\n" + stream + b"\nendstream\nendobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)
    xref_offset = len(output)
    output.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n")
    output.extend(str(xref_offset).encode("ascii"))
    output.extend(b"\n%%EOF\n")
    return bytes(output)


def ensure_parser_qa_documents(repo_root: Path) -> list[Path]:
    out_dir = repo_root / "data" / "parser_qa_documents"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fixture in SYNTHETIC_FIXTURES:
        path = out_dir / fixture["filename"]
        path.write_bytes(_simple_text_pdf(fixture["text"]))
        written.append(path)
    return written


def _synthetic_fixture_records(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    base = root / "data" / "parser_qa_documents"
    for fixture in SYNTHETIC_FIXTURES:
        path = base / fixture["filename"]
        if not path.exists():
            continue
        triage = triage_pdf_upload(path.name, path.read_bytes())
        document, field_rows = _record_from_triage(
            packet_id=f"parser-qa-{fixture['country_code'].lower()}-{_slug(fixture['document_class'])}",
            filename=path.name,
            source_kind="synthetic_parser_fixture",
            storage_status="local_synthetic_parser_fixture",
            triage=triage,
            local_path=str(path.relative_to(root)),
        )
        document["country_code"] = fixture["country_code"]
        document["declared_document_class"] = fixture["document_class"]
        document["classification"] = _document_class_contract(
            fixture["document_class"],
            confidence="high",
            signal="synthetic_parser_fixture_class",
        )
        document["field_gaps"] = _field_gaps(document["classification"], field_rows)
        document["sample_level"] = "synthetic_parser_fixture"
        document["can_support_customer_claims"] = False
        document["next_valid_move"] = "Use this filled sample only for parser QA; replace with real user evidence and review before customer use."
        documents.append(document)
        fields.extend(field_rows)
    return documents, fields


def _pdf_file_metadata(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "local_path": str(path.relative_to(root)),
        "local_file_present": True,
        "file_size_bytes": len(data),
        "sha256": _sha256(path),
        "pdf_header_present": data.startswith(b"%PDF"),
        "pdf_eof_present": data.rstrip().endswith(b"%%EOF"),
    }


def _build_document_sample_library(
    root: Path,
    source_registry: dict[str, dict[str, Any]],
    documents: list[dict[str, Any]],
    fields: list[dict[str, Any]],
) -> dict[str, Any]:
    fields_by_document: dict[str, list[dict[str, Any]]] = {}
    for field in fields:
        fields_by_document.setdefault(field["document_id"], []).append(field)

    sample_document_map = {
        document["document_id"]: document
        for document in documents
        if document.get("sample_level") in {"official_pdf_downloaded", "synthetic_parser_fixture"}
    }
    rows: list[dict[str, Any]] = []
    official_base = root / "data" / "official_sample_documents"
    parser_base = root / "data" / "parser_qa_documents"

    for sample in OFFICIAL_SAMPLE_DOCUMENTS:
        source = source_registry.get(sample["source_id"], {})
        sample_path = official_base / sample["filename"]
        packet_id = f"official-sample-{sample['country_code'].lower()}-{_slug(sample['document_class'])}"
        document_id = f"document:{packet_id}:{_slug(sample_path.name)}"
        document = sample_document_map.get(document_id, {})
        rows.append(
            {
                "sample_id": sample["source_id"],
                "country_code": sample["country_code"],
                "document_class": sample["document_class"],
                "sample_level": sample["sample_level"],
                "source_kind": "official_sample_form",
                "source_id": sample["source_id"],
                "source_name": source.get("name", sample["source_owner"]),
                "source_owner": sample["source_owner"],
                "source_url": source.get("url", sample["url"]),
                "source_accessed_at": source.get("accessed_at", ""),
                "retrieval_status": "local_pdf_present" if sample_path.exists() else "missing_local_pdf",
                "file_metadata": _pdf_file_metadata(sample_path, root) if sample_path.exists() else {"local_file_present": False},
                "document_id": document.get("document_id", ""),
                "extracted_field_count": len(fields_by_document.get(document.get("document_id", ""), [])),
                "parser_orientation_allowed": True,
                "customer_evidence_allowed": False,
                "can_support_customer_claims": False,
                "claims_opened": False,
                "blocked_claims": list(SAMPLE_LIBRARY_BLOCKED_CLAIMS),
                "claim_boundary": source.get(
                    "claim_boundary",
                    "Official sample form only; not customer evidence or approval.",
                ),
                "next_valid_move": "Use for parser orientation and reviewer-question design only; attach real user evidence and scoped review before any customer claim.",
            }
        )

    for sample in SOURCE_ROUTE_ONLY_SAMPLES:
        source = source_registry.get(sample["source_id"], {})
        rows.append(
            {
                "sample_id": sample["source_id"],
                "country_code": sample["country_code"],
                "document_class": sample["document_class"],
                "sample_level": sample["sample_level"],
                "source_kind": "official_source_route_only",
                "source_id": sample["source_id"],
                "source_name": source.get("name", sample["source_owner"]),
                "source_owner": sample["source_owner"],
                "source_url": source.get("url", sample["url"]),
                "source_accessed_at": source.get("accessed_at", ""),
                "availability_status": sample["availability_status"],
                "retrieval_status": "route_recorded_no_local_pdf",
                "file_metadata": {"local_file_present": False},
                "parser_orientation_allowed": False,
                "customer_evidence_allowed": False,
                "can_support_customer_claims": False,
                "claims_opened": False,
                "blocked_claims": list(SAMPLE_LIBRARY_BLOCKED_CLAIMS),
                "claim_boundary": source.get(
                    "claim_boundary",
                    "Source route only; no local official sample PDF was verified.",
                ),
                "next_valid_move": "Before adding parser orientation for this lane, download a stable official/public sample file or record a manual-review-only source route.",
            }
        )

    for fixture in SYNTHETIC_FIXTURES:
        path = parser_base / fixture["filename"]
        packet_id = f"parser-qa-{fixture['country_code'].lower()}-{_slug(fixture['document_class'])}"
        document_id = f"document:{packet_id}:{_slug(path.name)}"
        document = sample_document_map.get(document_id, {})
        rows.append(
            {
                "sample_id": path.stem,
                "country_code": fixture["country_code"],
                "document_class": fixture["document_class"],
                "sample_level": "synthetic_parser_fixture",
                "source_kind": "synthetic_parser_fixture",
                "source_id": "",
                "source_name": "Local deterministic parser QA fixture",
                "source_owner": "Trade Readiness Copilot test fixture",
                "source_url": "",
                "source_accessed_at": "",
                "retrieval_status": "local_synthetic_pdf_present" if path.exists() else "missing_synthetic_pdf",
                "file_metadata": _pdf_file_metadata(path, root) if path.exists() else {"local_file_present": False},
                "document_id": document.get("document_id", ""),
                "extracted_field_count": len(fields_by_document.get(document.get("document_id", ""), [])),
                "parser_orientation_allowed": True,
                "customer_evidence_allowed": False,
                "can_support_customer_claims": False,
                "claims_opened": False,
                "blocked_claims": list(SAMPLE_LIBRARY_BLOCKED_CLAIMS),
                "claim_boundary": "Synthetic filled fixture for parser regression only; it is not official, customer, buyer, supplier, customs, CFIA, or shipment evidence.",
                "next_valid_move": "Keep in regression tests; replace with real uploaded evidence and scoped review before customer claims.",
            }
        )

    official_pdf_rows = [row for row in rows if row["sample_level"] == "official_pdf_downloaded"]
    source_route_rows = [row for row in rows if row["sample_level"] == "official_source_route_only"]
    synthetic_rows = [row for row in rows if row["sample_level"] == "synthetic_parser_fixture"]
    missing_files = [
        row["sample_id"]
        for row in rows
        if row["sample_level"] != "official_source_route_only" and not row["file_metadata"].get("local_file_present")
    ]
    countries = sorted({row["country_code"] for row in rows})
    return {
        "generated_at": _now(),
        "status": SAMPLE_LIBRARY_STATUS,
        "sample_count": len(rows),
        "official_pdf_count": len(official_pdf_rows),
        "source_route_only_count": len(source_route_rows),
        "synthetic_fixture_count": len(synthetic_rows),
        "country_coverage": countries,
        "document_classes": sorted({row["document_class"] for row in rows}),
        "missing_file_count": len(missing_files),
        "missing_files": missing_files,
        "all_file_backed_samples_present": not missing_files,
        "parser_orientation_sample_count": sum(1 for row in rows if row["parser_orientation_allowed"]),
        "customer_evidence_allowed_count": sum(1 for row in rows if row["customer_evidence_allowed"]),
        "claims_opened": False,
        "external_effects_created": False,
        "blocked_claims": list(SAMPLE_LIBRARY_BLOCKED_CLAIMS),
        "rows": rows,
        "proof_boundary": (
            "The sample library records official/public source routes and local parser fixtures. "
            "It proves sample provenance and parser-orientation coverage only; it does not prove that any "
            "document is required, complete, authentic, current law, customs-ready, CFIA-approved, or shipment-ready."
        ),
    }


def _evidence_rows(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for document in documents:
        if document["source_kind"] == "official_sample_form":
            evidence_type = "official_sample_document"
            provenance = "official_sample_form_reference"
            freshness = "current_reference_checked_locally"
        elif document["storage_status"] == "declared_missing_file":
            evidence_type = "document_gap"
            provenance = "user_declared_filename_only"
            freshness = "unknown"
        else:
            evidence_type = "document"
            provenance = "parser_draft"
            freshness = "unknown"
        rows.append(
            {
                "evidence_id": f"evidence:{document['document_id']}",
                "document_id": document["document_id"],
                "packet_id": document["packet_id"],
                "type": evidence_type,
                "provenance": provenance,
                "freshness": freshness,
                "supports_claims": [],
                "blocked_claims": document["blocked_claims"],
                "review_required": True,
                "claim_boundary": document["claim_boundary"],
                "next_valid_move": document["next_valid_move"],
            }
        )
    return rows


def _redaction_previews(documents: list[dict[str, Any]], fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields_by_document: dict[str, list[dict[str, Any]]] = {}
    for field in fields:
        fields_by_document.setdefault(field["document_id"], []).append(field)
    previews = []
    for document in documents:
        categories = sorted({category for field in fields_by_document.get(document["document_id"], []) for category in field["redaction_categories"]})
        previews.append(
            {
                "document_id": document["document_id"],
                "packet_id": document["packet_id"],
                "redaction_required": bool(categories),
                "redaction_categories": categories,
                "redaction_status": "preview_required_before_ai_or_sharing" if categories else "not_required",
                "production_redaction_proven": False,
            }
        )
    return previews


def _parser_qa_matrix(documents: list[dict[str, Any]], fields: list[dict[str, Any]]) -> dict[str, Any]:
    fields_by_document: dict[str, list[dict[str, Any]]] = {}
    for field in fields:
        fields_by_document.setdefault(field["document_id"], []).append(field)
    rows = []
    for document in documents:
        if document.get("source_kind") != "synthetic_parser_fixture":
            continue
        doc_fields = fields_by_document.get(document["document_id"], [])
        fields_by_name = {row["field_name"]: row.get("extracted_value") for row in doc_fields}
        expected_fields = list(document.get("classification", {}).get("expected_fields", []))
        missing_fields = [field for field in expected_fields if not _field_present(field, fields_by_name)]
        extracted_fields = sorted(
            field_name
            for field_name, value in fields_by_name.items()
            if _is_present(value)
        )
        rows.append(
            {
                "document_id": document["document_id"],
                "filename": document["filename"],
                "country_code": document.get("country_code"),
                "document_class": document.get("classification", {}).get("type"),
                "expected_fields": expected_fields,
                "extracted_fields": extracted_fields,
                "missing_fields": missing_fields,
                "status": "parser_qa_passed" if not missing_fields else "parser_qa_needs_parser_rule",
                "can_support_customer_claims": False,
                "claims_opened": False,
                "next_valid_move": (
                    "Keep this fixture in regression tests."
                    if not missing_fields
                    else "Add parser rules or improve the fixture text for the missing fields."
                ),
            }
        )
    passed = sum(1 for row in rows if row["status"] == "parser_qa_passed")
    return {
        "status": PARSER_QA_STATUS,
        "fixture_count": len(rows),
        "passed_count": passed,
        "needs_rule_count": len(rows) - passed,
        "all_fixtures_passed": passed == len(rows) and bool(rows),
        "rows": rows,
        "claims_opened": False,
        "external_effects_created": False,
        "proof_boundary": (
            "Parser QA proves only local extraction behavior on official samples and synthetic filled fixtures. "
            "It does not prove uploaded document authenticity, completeness, customs readiness, CFIA clearance, "
            "buyer validation, supplier verification, or shipment approval."
        ),
    }


def _pipeline_policy(upload_policy: dict[str, Any], ai_policy: dict[str, Any], manual_no_ai: dict[str, Any]) -> dict[str, Any]:
    return {
        "accepted_file_types": upload_policy.get("accepted_file_types", ["application/pdf"]),
        "max_bytes": upload_policy.get("max_bytes", 5_242_880),
        "max_pages_per_pdf": upload_policy.get("max_pages_per_pdf", 25),
        "direct_file_serving": upload_policy.get("direct_file_serving", False),
        "generated_storage_names": upload_policy.get("generated_storage_names", True),
        "ocr_cost_gate": upload_policy.get("ocr_cost_gate", {}),
        "ai_policy_status": ai_policy.get("status", "unknown"),
        "manual_no_ai_supported": bool(manual_no_ai.get("ai_disabled_supported", True)),
        "real_uploads_enabled": False,
        "hosted_uploads_enabled": False,
        "external_effects_created": False,
        "claim_boundary": "Document controls are local proof only; hosted upload, AI, and storage readiness require security/privacy review.",
    }


def build_production_document_intelligence_engine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    packets = _load_json(root / "data" / "customer_source_packets.json", [])
    sources = _source_by_id(_load_json(root / "data" / "official_source_registry.json", []))
    upload_policy = _load_json(root / "system_review_graph" / "public_upload_policy.json", {})
    public_upload_manifest = _load_json(root / "system_review_graph" / "public_upload_manifest.json", {})
    ai_policy = _load_json(root / "system_review_graph" / "ai_data_policy.json", {})
    redaction_pipeline = _load_json(root / "system_review_graph" / "redaction_pipeline.json", {})
    manual_no_ai = _load_json(root / "system_review_graph" / "manual_no_ai_workflow.json", {})

    documents: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []
    for packet in packets:
        for filename in packet.get("documents", []):
            documents.append(_record_from_declared_missing_document(packet, filename))

    upload_documents, upload_fields = _public_upload_records(public_upload_manifest)
    sample_documents, sample_fields = _official_sample_records(root, sources)
    synthetic_documents, synthetic_fields = _synthetic_fixture_records(root)
    documents.extend(upload_documents)
    documents.extend(sample_documents)
    documents.extend(synthetic_documents)
    fields.extend(upload_fields)
    fields.extend(sample_fields)
    fields.extend(synthetic_fields)

    evidence = _evidence_rows(documents)
    redactions = _redaction_previews(documents, fields)
    parser_qa = _parser_qa_matrix(documents, fields)
    sample_library = _build_document_sample_library(root, sources, documents, fields)
    categories = {row["classification"]["type"] for row in documents}

    return {
        "generated_at": _now(),
        "status": STATUS,
        "product": "Trade Readiness Copilot",
        "pipeline_stage_count": len(PIPELINE_STAGES),
        "document_class_count": len(REQUIRED_TRADE_DOCUMENT_CLASSES),
        "document_record_count": len(documents),
        "extracted_field_count": len(fields),
        "evidence_record_count": len(evidence),
        "redaction_preview_count": len(redactions),
        "parser_qa_status": parser_qa["status"],
        "parser_qa_fixture_count": parser_qa["fixture_count"],
        "parser_qa_passed_count": parser_qa["passed_count"],
        "parser_qa_needs_rule_count": parser_qa["needs_rule_count"],
        "parser_qa_all_fixtures_passed": parser_qa["all_fixtures_passed"],
        "sample_library_status": sample_library["status"],
        "sample_library_count": sample_library["sample_count"],
        "sample_library_official_pdf_count": sample_library["official_pdf_count"],
        "sample_library_source_route_only_count": sample_library["source_route_only_count"],
        "sample_library_synthetic_fixture_count": sample_library["synthetic_fixture_count"],
        "sample_library_country_coverage": sample_library["country_coverage"],
        "sample_library_claims_opened": sample_library["claims_opened"],
        "pipeline_policy": _pipeline_policy(upload_policy, ai_policy, manual_no_ai),
        "pipeline_stages": list(PIPELINE_STAGES),
        "required_trade_document_classes": list(REQUIRED_TRADE_DOCUMENT_CLASSES),
        "source_records": [
            *[
                {
                    "source_id": sample["source_id"],
                    "source_name": sources.get(sample["source_id"], {}).get("name", sample["source_owner"]),
                    "country_code": sample["country_code"],
                    "url": sources.get(sample["source_id"], {}).get("url", sample["url"]),
                    "source_kind": "official_sample_form",
                    "sample_level": sample["sample_level"],
                    "document_class": sample["document_class"],
                    "product_use": "classifier and reviewer-question reference only",
                    "claim_boundary": sources.get(sample["source_id"], {}).get(
                        "claim_boundary",
                        "Sample form only; not customer evidence or import approval.",
                    ),
                }
                for sample in OFFICIAL_SAMPLE_DOCUMENTS
            ],
            *[
                {
                    "source_id": sample["source_id"],
                    "source_name": sources.get(sample["source_id"], {}).get("name", sample["source_owner"]),
                    "country_code": sample["country_code"],
                    "url": sources.get(sample["source_id"], {}).get("url", sample["url"]),
                    "source_kind": "official_source_route_only",
                    "sample_level": sample["sample_level"],
                    "document_class": sample["document_class"],
                    "availability_status": sample["availability_status"],
                    "product_use": "country source routing and future sample-form lookup",
                    "claim_boundary": sources.get(sample["source_id"], {}).get(
                        "claim_boundary",
                        "Source route only; no local official sample PDF was verified.",
                    ),
                }
                for sample in SOURCE_ROUTE_ONLY_SAMPLES
            ],
            {
                "source_id": "owasp-file-upload",
                "source_name": sources.get("owasp-file-upload", {}).get("name", "OWASP File Upload Cheat Sheet"),
                "url": sources.get("owasp-file-upload", {}).get("url", ""),
                "source_kind": "security_control_reference",
                "product_use": "upload pipeline and hosted-control gate reference",
                "claim_boundary": sources.get("owasp-file-upload", {}).get("claim_boundary", ""),
            },
        ],
        "document_records": documents,
        "extracted_fields": fields,
        "evidence_records": evidence,
        "redaction_previews": redactions,
        "parser_qa_matrix": parser_qa,
        "sample_library": sample_library,
        "ai_analysis_policy": {
            "ai_optional": True,
            "ai_outputs_can_open_gates": False,
            "manual_no_ai_supported": bool(manual_no_ai.get("ai_disabled_supported", True)),
            "provider_review_required": True,
            "prompt_injection_review_required": True,
            "redaction_categories": redaction_pipeline.get("categories", []),
        },
        "category_coverage": sorted(categories),
        "official_sample_document_count": len(sample_documents),
        "source_route_only_sample_count": len(SOURCE_ROUTE_ONLY_SAMPLES),
        "synthetic_parser_fixture_count": len(synthetic_documents),
        "real_uploads_enabled": False,
        "malware_scan_proven": False,
        "object_storage_ready": False,
        "parser_outputs_are_draft": True,
        "external_effects_created": False,
        "claims_opened": False,
        "public_launch_ready": False,
        "blocked_claims": list(DOCUMENT_BLOCKED_CLAIMS),
        "proof_boundary": (
            "Document intelligence now has a production-shaped local pipeline, official sample-form routing, "
            "document records, extracted field provenance, evidence mapping, redaction previews, and closed gates. "
            "It still does not prove hosted upload security, malware scanning, private object storage, AI-provider "
            "safety, document authenticity, customs/tariff correctness, CFIA clearance, buyer validation, supplier "
            "verification, shipment approval, or public launch readiness."
        ),
    }


def render_document_intelligence_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Production Document Intelligence Engine",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This engine turns uploads and document references into draft evidence records with provenance and closed claim gates.",
        "",
        "## Proof Boundary",
        "",
        payload["proof_boundary"],
        "",
        "## Pipeline",
        "",
    ]
    for stage in payload["pipeline_stages"]:
        lines.append(f"- `{stage['stage']}`: {stage['status']} ({stage['gate']}).")
    lines.extend(["", "## Document Classes", ""])
    for document_class in payload["required_trade_document_classes"]:
        lines.append(f"- `{document_class['document_class']}`: {document_class['label']}.")
    lines.extend(["", "## Records", ""])
    lines.append(f"- Document records: {payload['document_record_count']}")
    lines.append(f"- Extracted fields: {payload['extracted_field_count']}")
    lines.append(f"- Evidence records: {payload['evidence_record_count']}")
    lines.append(f"- Redaction previews: {payload['redaction_preview_count']}")
    lines.append(f"- Parser QA fixtures passed: {payload['parser_qa_passed_count']} of {payload['parser_qa_fixture_count']}")
    lines.extend(["", "## Sample Library", ""])
    lines.append(f"- Status: `{payload['sample_library_status']}`")
    lines.append(f"- Official PDF samples: {payload['sample_library_official_pdf_count']}")
    lines.append(f"- Official source-route-only rows: {payload['sample_library_source_route_only_count']}")
    lines.append(f"- Synthetic parser fixtures: {payload['sample_library_synthetic_fixture_count']}")
    lines.append(f"- Country coverage: {', '.join(payload['sample_library_country_coverage'])}")
    lines.append("- Customer evidence allowed from samples: false")
    lines.extend(["", "## Source Records", ""])
    for source in payload["source_records"]:
        lines.append(f"- `{source['source_id']}`: {source['url']}")
    lines.extend(
        [
            "",
            "## Closed Gates",
            "",
            "- Real uploads enabled: false",
            "- Malware scan proven: false",
            "- Private object storage ready: false",
            "- Parser outputs are draft: true",
            "- Claims opened: false",
            "- Public launch ready: false",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_document_intelligence_engine_artifacts(payload: dict[str, Any], repo_root: Path) -> dict[str, Path]:
    graph = repo_root / "system_review_graph"
    docs = repo_root / "docs"
    graph.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    manifest_path = graph / "production_document_intelligence_manifest.json"
    pipeline_path = graph / "production_document_pipeline.json"
    fields_path = graph / "production_document_extracted_fields.json"
    parser_qa_path = graph / "production_document_parser_qa_matrix.json"
    sample_library_path = graph / "production_document_sample_library.json"
    doc_path = docs / "PRODUCTION_DOCUMENT_INTELLIGENCE_ENGINE.md"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pipeline_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_document_pipeline_ready_local_controls_gates_closed",
                "pipeline_policy": payload["pipeline_policy"],
                "pipeline_stage_count": payload["pipeline_stage_count"],
                "pipeline_stages": payload["pipeline_stages"],
                "document_record_count": payload["document_record_count"],
                "document_records": payload["document_records"],
                "evidence_record_count": payload["evidence_record_count"],
                "evidence_records": payload["evidence_records"],
                "redaction_preview_count": payload["redaction_preview_count"],
                "redaction_previews": payload["redaction_previews"],
                "claims_opened": False,
                "external_effects_created": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    fields_path.write_text(
        json.dumps(
            {
                "generated_at": payload["generated_at"],
                "status": "production_document_extracted_fields_ready_draft_only",
                "extracted_field_count": payload["extracted_field_count"],
                "extracted_fields": payload["extracted_fields"],
                "parser_outputs_are_draft": True,
                "blocked_claims": payload["blocked_claims"],
                "claims_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    parser_qa_path.write_text(json.dumps(payload["parser_qa_matrix"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sample_library_path.write_text(json.dumps(payload["sample_library"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    doc_path.write_text(render_document_intelligence_markdown(payload), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "pipeline": pipeline_path,
        "fields": fields_path,
        "parser_qa": parser_qa_path,
        "sample_library": sample_library_path,
        "doc": doc_path,
    }
