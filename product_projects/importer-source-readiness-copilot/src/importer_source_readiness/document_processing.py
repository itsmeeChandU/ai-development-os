"""PDF triage helpers for public trade-readiness uploads."""

from __future__ import annotations

import hashlib
import io
import re
from typing import Any

MAX_PUBLIC_PDF_PAGES = 25


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fallback_text(content: bytes) -> str:
    decoded = content.decode("latin-1", errors="ignore")
    chunks = re.findall(r"\(([^()]{3,300})\)", decoded)
    text = " ".join(chunk.strip() for chunk in chunks if chunk.strip())
    if not text:
        printable = re.sub(r"[^A-Za-z0-9 .,;:/#()_-]+", " ", decoded)
        text = re.sub(r"\s+", " ", printable).strip()
    return text[:4000]


def _pypdf_extract(content: bytes) -> tuple[int | None, str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None, "", "pypdf_unavailable"
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = len(reader.pages)
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:5]).strip()
        return pages, text[:4000], "pypdf"
    except Exception as exc:
        return None, "", f"pypdf_error:{type(exc).__name__}"


def triage_pdf_upload(filename: str, content: bytes, *, content_type: str = "application/pdf") -> dict[str, Any]:
    """Return bounded PDF triage metadata without making approval claims."""

    looks_like_pdf = content.startswith(b"%PDF")
    parsed_pages, parsed_text, parser = _pypdf_extract(content) if looks_like_pdf else (None, "", "not_pdf")
    fallback_text = _fallback_text(content) if looks_like_pdf and not parsed_text else ""
    text = parsed_text or fallback_text
    estimated_pages = parsed_pages or max(1, content.count(b"/Type /Page"))
    has_native_text = bool(text.strip())
    if not looks_like_pdf:
        extraction_status = "rejected_not_pdf"
    elif estimated_pages > MAX_PUBLIC_PDF_PAGES:
        extraction_status = "blocked_page_limit"
    elif has_native_text:
        extraction_status = "native_text_extracted_needs_confirmation"
    else:
        extraction_status = "ocr_recommended_needs_confirmation"
    confidence = "medium" if has_native_text and parser == "pypdf" else "low"
    if not looks_like_pdf or estimated_pages > MAX_PUBLIC_PDF_PAGES:
        confidence = "blocked"
    return {
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(content),
        "sha256": _sha256_bytes(content),
        "looks_like_pdf": looks_like_pdf,
        "parser": parser,
        "page_count_estimate": estimated_pages,
        "max_pages_allowed": MAX_PUBLIC_PDF_PAGES,
        "has_native_text": has_native_text,
        "native_text_excerpt": text[:1200],
        "ocr_recommended": looks_like_pdf and not has_native_text,
        "extraction_status": extraction_status,
        "extraction_confidence": confidence,
        "user_confirmation_required": looks_like_pdf,
        "proof_boundary": (
            "PDF triage extracts local metadata/text for draft review only. It does not prove document "
            "authenticity, completeness, customs/tariff correctness, CFIA clearance, or legal compliance."
        ),
    }
