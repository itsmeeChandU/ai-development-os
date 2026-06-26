"""PDF triage helpers for public trade-readiness uploads."""

from __future__ import annotations

import hashlib
import io
import re
import zlib
from typing import Any

MAX_PUBLIC_PDF_PAGES = 25
PDF_TEXT_EXCERPT_LIMIT = 4000

TRADE_DOCUMENT_TYPES = {
    "commercial_invoice": {
        "label": "Commercial invoice",
        "keywords": ["commercial invoice", "invoice number", "invoice no", "proforma", "amount", "buyer", "seller"],
        "expected_fields": ["invoice_or_reference", "hs_code", "origin_country", "destination_country", "buyer_or_importer", "supplier_or_exporter", "amounts"],
    },
    "packing_list": {
        "label": "Packing list",
        "keywords": ["packing list", "carton", "gross weight", "net weight", "packages", "pieces"],
        "expected_fields": ["quantities", "origin_country", "destination_country", "buyer_or_importer", "supplier_or_exporter"],
    },
    "certificate_of_origin": {
        "label": "Certificate of origin",
        "keywords": ["certificate of origin", "country of origin", "origin criterion", "chamber of commerce"],
        "expected_fields": ["origin_country", "destination_country", "hs_code", "supplier_or_exporter"],
    },
    "product_specification": {
        "label": "Product specification",
        "keywords": ["product specification", "specification", "ingredients", "composition", "material", "dimensions"],
        "expected_fields": ["product_description", "hs_code", "origin_country"],
    },
    "transport_document": {
        "label": "Transport document",
        "keywords": ["bill of lading", "air waybill", "awb", "freight", "carrier", "vessel", "port of loading", "port of discharge"],
        "expected_fields": ["origin_country", "destination_country", "quantities", "buyer_or_importer", "supplier_or_exporter"],
    },
}


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _decode_pdf_literal(value: str) -> str:
    """Decode a bounded subset of PDF literal-string escapes."""

    def replace_octal(match: re.Match[str]) -> str:
        try:
            return chr(int(match.group(1), 8))
        except ValueError:
            return ""

    value = re.sub(r"\\([0-7]{1,3})", replace_octal, value)
    replacements = {
        r"\n": "\n",
        r"\r": "\r",
        r"\t": "\t",
        r"\b": "",
        r"\f": "",
        r"\(": "(",
        r"\)": ")",
        r"\\": "\\",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _decode_hex_string(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", value)
    if len(cleaned) % 2:
        cleaned += "0"
    if not cleaned:
        return ""
    try:
        data = bytes.fromhex(cleaned)
    except ValueError:
        return ""
    for encoding in ("utf-16-be", "utf-8", "latin-1"):
        try:
            text = data.decode(encoding, errors="ignore")
        except Exception:
            continue
        printable = re.sub(r"\s+", " ", text).strip()
        if printable:
            return printable
    return ""


def _strings_from_pdf_text(raw: bytes) -> str:
    decoded = raw.decode("latin-1", errors="ignore")
    chunks = [_decode_pdf_literal(chunk) for chunk in re.findall(r"\(([^()]{1,300})\)", decoded)]
    chunks.extend(_decode_hex_string(chunk) for chunk in re.findall(r"<([0-9A-Fa-f\s]{6,600})>", decoded))
    text = " ".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())
    text = re.sub(r"\s+", " ", text).strip()
    return text[:PDF_TEXT_EXCERPT_LIMIT]


def _clean_extracted_text(text: str) -> str:
    cleaned = "".join(char if char.isprintable() or char.isspace() else " " for char in text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Remove long runs of isolated glyph fragments that commonly come from embedded fonts.
    cleaned = re.sub(r"(?:\b[A-Za-z]\b\s*){8,}", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()[:PDF_TEXT_EXCERPT_LIMIT]


def _text_quality(raw_text: str, cleaned_text: str) -> dict[str, Any]:
    raw_len = max(1, len(raw_text))
    printable_count = sum(1 for char in raw_text if char.isprintable() or char.isspace())
    printable_ratio = round(printable_count / raw_len, 3)
    word_tokens = re.findall(r"\b[A-Za-z][A-Za-z]{2,}\b", cleaned_text)
    lower = cleaned_text.lower()
    signal_terms = sorted(
        {
            term
            for term in [
                "invoice",
                "proforma",
                "packing",
                "certificate",
                "origin",
                "destination",
                "buyer",
                "supplier",
                "exporter",
                "importer",
                "hs code",
                "tariff",
                "incoterms",
                "bill of lading",
            ]
            if term in lower
        }
    )
    usable = bool(cleaned_text) and printable_ratio >= 0.72 and (len(word_tokens) >= 4 or bool(signal_terms))
    reason = "usable_native_text" if usable else "native_text_missing_or_not_human_readable"
    if raw_text and printable_ratio < 0.72:
        reason = "low_printable_text_ratio"
    elif cleaned_text and len(word_tokens) < 4 and not signal_terms:
        reason = "insufficient_trade_language"
    return {
        "status": "usable" if usable else "not_usable",
        "reason": reason,
        "printable_ratio": printable_ratio,
        "word_count": len(word_tokens),
        "signal_terms": signal_terms,
    }


def _stream_payloads(content: bytes) -> list[tuple[bytes, bool]]:
    payloads: list[tuple[bytes, bool]] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", content, flags=re.DOTALL):
        header = content[max(0, match.start() - 400) : match.start()]
        payload = match.group(1)
        is_flate = b"/FlateDecode" in header or b"/Fl" in header
        payloads.append((payload, is_flate))
    return payloads


def _native_text_from_streams(content: bytes) -> tuple[str, list[str]]:
    notes: list[str] = []
    fragments: list[str] = []
    for payload, is_flate in _stream_payloads(content):
        raw = payload
        if is_flate:
            try:
                raw = zlib.decompress(payload)
                notes.append("flate_stream_decoded")
            except zlib.error:
                notes.append("flate_stream_decode_failed")
                continue
        text = _strings_from_pdf_text(raw)
        if text:
            fragments.append(text)
    joined = re.sub(r"\s+", " ", " ".join(fragments)).strip()
    return joined[:PDF_TEXT_EXCERPT_LIMIT], sorted(set(notes))


def _fallback_text(content: bytes) -> str:
    stream_text, _notes = _native_text_from_streams(content)
    if stream_text:
        return stream_text
    text = _strings_from_pdf_text(content)
    return text[:PDF_TEXT_EXCERPT_LIMIT]


def _page_count(content: bytes) -> tuple[int, str]:
    count = len(re.findall(rb"/Type\s*/Page\b", content))
    if count:
        return count, "page_objects"
    fallback = content.count(b"/Type /Page")
    return max(1, fallback), "fallback_page_tokens"


def _field_candidates(text: str) -> dict[str, Any]:
    stop_with_delimiter = (
        r"(?:HS|HTS|tariff|invoice|proforma|origin|country of origin|destination|ship to|from|"
        r"supplier|seller|exporter|buyer|importer|consignee|incoterms|"
        r"product|description|goods|amount|total|quantity|weight|date)"
        r"\s*(?:code|classification|no\.?|number|#)?\s*[:#\-]"
    )
    stop_pattern = rf"(?:(?:{stop_with_delimiter})|\b(?:EXW|FCA|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b)"

    def labeled_value(labels: str, *, allow_number_word: bool = False) -> str:
        number_word = r"(?:no\.?|number|#)?" if allow_number_word else ""
        match = re.search(
            rf"\b(?:{labels})\s*{number_word}\s*[:#\-]?\s*([A-Za-z0-9 .,&'/-]{{2,100}}?)(?=\s+{stop_pattern}|$)",
            text,
            re.I,
        )
        if not match:
            return ""
        value = re.sub(r"\s+", " ", match.group(1)).strip(" .,-")
        return value[:80]

    hs_match = re.search(r"\b(?:HS|HTS|tariff)\s*(?:code|classification)?[:#\s-]*([0-9]{4}(?:[.\s-]?[0-9]{2}){0,2})\b", text, re.I)
    invoice_match = re.search(r"\b(?:invoice|proforma)\s*(?:no\.?|number|#)?[:\s-]*([A-Z0-9][A-Z0-9._/-]{2,40})", text, re.I)
    country_matches = sorted(
        {
            value
            for value in [
                labeled_value(r"origin|country of origin|from"),
                labeled_value(r"destination|ship to"),
            ]
            if value
        }
    )
    supplier_value = labeled_value(r"supplier|seller|exporter")
    buyer_value = labeled_value(r"buyer|importer|consignee|ship to")
    incoterms = sorted(set(re.findall(r"\b(EXW|FCA|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b", text, re.I)))
    dates = sorted(
        set(
            re.findall(
                r"\b(?:20[0-9]{2}[-/][01]?[0-9][-/][0-3]?[0-9]|[0-3]?[0-9][- ][A-Za-z]{3,9}[- ]20[0-9]{2})\b",
                text,
            )
        )
    )
    amounts = sorted(set(re.findall(r"\b(?:USD|CAD|INR|EUR|\$)\s?[0-9][0-9,]*(?:\.[0-9]{2})?\b", text, re.I)))
    quantities = sorted(set(re.findall(r"\b[0-9][0-9,.]*\s?(?:kg|kgs|kilograms|cartons|boxes|pcs|pieces|units|cases)\b", text, re.I)))
    product_value = labeled_value(r"product|description|goods")
    return {
        "hs_code": hs_match.group(1).replace(" ", "").replace("-", ".") if hs_match else "",
        "invoice_or_reference": invoice_match.group(1) if invoice_match else "",
        "country_mentions": country_matches[:6],
        "supplier_or_exporter": supplier_value,
        "buyer_or_importer": buyer_value,
        "incoterms": [value.upper() for value in incoterms[:6]],
        "dates": dates[:6],
        "amounts": amounts[:6],
        "quantities": quantities[:6],
        "product_description": product_value,
    }


def _guess_document_type(filename: str, text: str) -> dict[str, Any]:
    haystack = f"{filename} {text}".lower()
    scored = []
    for doc_type, config in TRADE_DOCUMENT_TYPES.items():
        hits = [keyword for keyword in config["keywords"] if keyword in haystack]
        if hits:
            scored.append((len(hits), doc_type, hits))
    if not scored:
        return {
            "type": "unknown_trade_document",
            "label": "Unknown trade document",
            "confidence": "low",
            "signals": [],
            "expected_fields": ["hs_code", "origin_country", "destination_country", "buyer_or_importer", "supplier_or_exporter"],
        }
    score, doc_type, hits = sorted(scored, reverse=True)[0]
    return {
        "type": doc_type,
        "label": TRADE_DOCUMENT_TYPES[doc_type]["label"],
        "confidence": "high" if score >= 2 else "medium",
        "signals": hits,
        "expected_fields": TRADE_DOCUMENT_TYPES[doc_type]["expected_fields"],
    }


def _present_field_summary(fields: dict[str, Any]) -> list[str]:
    labels = {
        "hs_code": "HS/tariff code",
        "invoice_or_reference": "invoice/reference",
        "country_mentions": "country mentions",
        "supplier_or_exporter": "supplier/exporter",
        "buyer_or_importer": "buyer/importer",
        "incoterms": "Incoterms",
        "dates": "dates",
        "amounts": "amounts",
        "quantities": "quantities",
        "product_description": "product description",
    }
    facts = []
    for key, label in labels.items():
        value = fields.get(key)
        if isinstance(value, list):
            if value:
                facts.append(f"{label}: {', '.join(str(item) for item in value[:4])}")
        elif value:
            facts.append(f"{label}: {value}")
    return facts


def _missing_field_summary(fields: dict[str, Any], expected_fields: list[str]) -> list[str]:
    labels = {
        "hs_code": "HS/tariff code",
        "invoice_or_reference": "invoice/reference number",
        "origin_country": "origin country",
        "destination_country": "destination country",
        "buyer_or_importer": "buyer/importer name",
        "supplier_or_exporter": "supplier/exporter name",
        "incoterms": "Incoterms",
        "amounts": "commercial amount",
        "quantities": "quantity/weight",
        "product_description": "product description",
    }
    missing = []
    for key in expected_fields:
        if key in {"origin_country", "destination_country"}:
            if not fields.get("country_mentions"):
                missing.append(labels[key])
            continue
        value = fields.get(key)
        if not value:
            missing.append(labels.get(key, key.replace("_", " ")))
    return missing


def _document_intelligence(
    *,
    filename: str,
    extraction_status: str,
    confidence: str,
    text_quality: dict[str, Any],
    fields: dict[str, Any],
    document_type: dict[str, Any],
    ocr_required: bool,
) -> dict[str, Any]:
    facts = _present_field_summary(fields)
    missing = _missing_field_summary(fields, list(document_type.get("expected_fields") or []))
    if confidence == "blocked":
        summary = "The file was rejected or blocked before document intelligence could be produced."
        safe_use = "Do not use this upload as packet evidence until the blocker is resolved."
        next_valid_move = "Upload an unlocked PDF within the local page limit."
    elif ocr_required or text_quality.get("status") != "usable":
        summary = (
            "The PDF was stored as evidence, but this local parser could not read enough human-meaningful "
            "native text to extract business facts."
        )
        safe_use = "Use only the filename, hash, page count, and upload metadata until OCR or a digital-text PDF is provided."
        next_valid_move = "Approve OCR or upload a searchable PDF, then confirm extracted fields."
    else:
        doc_label = str(document_type.get("label") or "trade document")
        summary = f"Detected a likely {doc_label.lower()} and extracted draft fields for confirmation."
        safe_use = "Use these fields only as draft packet context; they do not prove authenticity or compliance."
        next_valid_move = "Confirm or correct the extracted fields before sharing buyer, broker, or expert packets."
    return {
        "status": "document_intelligence_ready" if facts and text_quality.get("status") == "usable" else "document_intelligence_needs_input",
        "filename": filename,
        "detected_document_type": document_type,
        "extraction_status": extraction_status,
        "confidence": confidence,
        "text_quality": text_quality,
        "facts_used": facts,
        "missing_or_unconfirmed_fields": missing[:12],
        "summary": summary,
        "safe_use": safe_use,
        "next_valid_move": next_valid_move,
        "claim_boundary": "Document intelligence organizes uploaded evidence for draft review only; qualified review and current official sources are still required.",
    }


def _pypdf_extract(content: bytes) -> tuple[int | None, str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None, "", "pypdf_unavailable"
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = len(reader.pages)
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:5]).strip()
        return pages, text[:PDF_TEXT_EXCERPT_LIMIT], "pypdf"
    except Exception as exc:
        return None, "", f"pypdf_error:{type(exc).__name__}"


def triage_pdf_upload(filename: str, content: bytes, *, content_type: str = "application/pdf") -> dict[str, Any]:
    """Return bounded PDF triage metadata without making approval claims."""

    looks_like_pdf = content.startswith(b"%PDF")
    encrypted = looks_like_pdf and b"/Encrypt" in content[:200_000]
    eof_present = looks_like_pdf and b"%%EOF" in content[-2048:]
    image_count = len(re.findall(rb"/Subtype\s*/Image\b", content))
    text_object_count = len(re.findall(rb"\bBT\b", content))
    parsed_pages, parsed_text, parser = _pypdf_extract(content) if looks_like_pdf and not encrypted else (None, "", "encrypted" if encrypted else "not_pdf")
    fallback_text = _fallback_text(content) if looks_like_pdf and not parsed_text else ""
    raw_text = parsed_text or fallback_text
    text = _clean_extracted_text(raw_text)
    text_quality = _text_quality(raw_text, text)
    fallback_pages, page_count_source = _page_count(content)
    estimated_pages = parsed_pages or fallback_pages
    has_native_text = text_quality["status"] == "usable"
    scanned_like = looks_like_pdf and not has_native_text and image_count >= max(1, estimated_pages)
    if not looks_like_pdf:
        extraction_status = "rejected_not_pdf"
    elif encrypted:
        extraction_status = "blocked_encrypted_pdf"
    elif estimated_pages > MAX_PUBLIC_PDF_PAGES:
        extraction_status = "blocked_page_limit"
    elif has_native_text:
        extraction_status = "native_text_extracted_needs_confirmation"
    elif scanned_like:
        extraction_status = "ocr_required_needs_confirmation"
    else:
        extraction_status = "no_extractable_text_needs_confirmation"
    confidence = "high" if has_native_text and parser == "pypdf" else "medium" if has_native_text else "low"
    if not looks_like_pdf or encrypted or estimated_pages > MAX_PUBLIC_PDF_PAGES:
        confidence = "blocked"
    parser_notes = []
    if looks_like_pdf and not eof_present:
        parser_notes.append("pdf_eof_marker_missing_or_truncated")
    stream_text, stream_notes = _native_text_from_streams(content) if looks_like_pdf and not parsed_text else ("", [])
    if stream_text and not parsed_text:
        parser_notes.append("text_recovered_from_content_stream")
    parser_notes.extend(stream_notes)
    fields = _field_candidates(text if has_native_text else "")
    field_confidence = {
        key: ("medium" if value else "not_found")
        for key, value in fields.items()
    }
    document_type = _guess_document_type(filename, text if has_native_text else "")
    parse_confidence_score = 0.0
    if confidence == "high":
        parse_confidence_score = 0.85
    elif confidence == "medium":
        parse_confidence_score = 0.62
    elif confidence == "low":
        parse_confidence_score = 0.25
    ocr_required = looks_like_pdf and not has_native_text and not encrypted and estimated_pages <= MAX_PUBLIC_PDF_PAGES
    document_intelligence = _document_intelligence(
        filename=filename,
        extraction_status=extraction_status,
        confidence=confidence,
        text_quality=text_quality,
        fields=fields,
        document_type=document_type,
        ocr_required=ocr_required,
    )
    return {
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(content),
        "sha256": _sha256_bytes(content),
        "looks_like_pdf": looks_like_pdf,
        "encrypted": encrypted,
        "eof_present": eof_present,
        "parser": parser,
        "page_count_estimate": estimated_pages,
        "page_count_source": "pypdf" if parsed_pages is not None else page_count_source,
        "max_pages_allowed": MAX_PUBLIC_PDF_PAGES,
        "image_count": image_count,
        "text_object_count": text_object_count,
        "has_native_text": has_native_text,
        "native_text_excerpt": text[:1200],
        "text_quality": text_quality,
        "ocr_required": ocr_required,
        "ocr_recommended": ocr_required,
        "extraction_status": extraction_status,
        "extraction_confidence": confidence,
        "parse_confidence_score": parse_confidence_score,
        "document_processing_mode": "native_text" if has_native_text else "ocr_required" if ocr_required else "blocked" if confidence == "blocked" else "metadata_only",
        "document_type_guess": document_type,
        "document_intelligence": document_intelligence,
        "extracted_fields": fields,
        "field_confidence": field_confidence,
        "parser_notes": sorted(set(parser_notes)),
        "ocr_blocker": {
            "status": "OCR_REQUIRED" if ocr_required else "not_required",
            "reason": "No native text was extracted from the PDF; use OCR before field extraction." if ocr_required else "",
            "next_valid_move": "Ask the user to approve OCR cost or upload a digital-text PDF." if ocr_required else "",
            "external_charge_created": False,
        },
        "cost_estimate": {
            "ocr_pages": estimated_pages if ocr_required else 0,
            "estimated_credits": estimated_pages * 2 if ocr_required else 0,
            "requires_user_approval": bool(ocr_required),
            "external_charge_created": False,
        },
        "user_confirmation_required": looks_like_pdf,
        "proof_boundary": (
            "PDF triage extracts local metadata/text for draft review only. It does not prove document "
            "authenticity, completeness, customs/tariff correctness, CFIA clearance, or legal compliance."
        ),
    }
