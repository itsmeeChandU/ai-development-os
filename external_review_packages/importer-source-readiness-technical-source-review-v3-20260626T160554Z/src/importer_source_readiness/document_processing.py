"""PDF triage helpers for public trade-readiness uploads."""

from __future__ import annotations

import hashlib
import io
import re
import zlib
from typing import Any

MAX_PUBLIC_PDF_PAGES = 25
PDF_TEXT_EXCERPT_LIMIT = 4000


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
    hs_match = re.search(r"\b(?:HS|HTS|tariff)\s*(?:code|classification)?[:#\s-]*([0-9]{4}(?:[.\s-]?[0-9]{2}){0,2})\b", text, re.I)
    invoice_match = re.search(r"\b(?:invoice|proforma)\s*(?:no\.?|number|#)?[:\s-]*([A-Z0-9][A-Z0-9._/-]{2,40})", text, re.I)
    country_label = r"(?:origin|country of origin|destination|ship to|from)"
    country_matches = sorted(
        {
            match.group(1).strip()
            for match in re.finditer(
                rf"\b{country_label}\s*[:\-]\s*([A-Za-z][A-Za-z .]{{1,40}}?)(?=\s+{country_label}\s*[:\-]|$)",
                text,
                re.I,
            )
        }
    )
    return {
        "hs_code": hs_match.group(1).replace(" ", "").replace("-", ".") if hs_match else "",
        "invoice_or_reference": invoice_match.group(1) if invoice_match else "",
        "country_mentions": country_matches[:6],
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
    text = parsed_text or fallback_text
    fallback_pages, page_count_source = _page_count(content)
    estimated_pages = parsed_pages or fallback_pages
    has_native_text = bool(text.strip())
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
    fields = _field_candidates(text)
    field_confidence = {
        key: ("medium" if value else "not_found")
        for key, value in fields.items()
    }
    parse_confidence_score = 0.0
    if confidence == "high":
        parse_confidence_score = 0.85
    elif confidence == "medium":
        parse_confidence_score = 0.62
    elif confidence == "low":
        parse_confidence_score = 0.25
    ocr_required = looks_like_pdf and not has_native_text and not encrypted and estimated_pages <= MAX_PUBLIC_PDF_PAGES
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
        "ocr_required": ocr_required,
        "ocr_recommended": ocr_required,
        "extraction_status": extraction_status,
        "extraction_confidence": confidence,
        "parse_confidence_score": parse_confidence_score,
        "document_processing_mode": "native_text" if has_native_text else "ocr_required" if ocr_required else "blocked" if confidence == "blocked" else "metadata_only",
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
