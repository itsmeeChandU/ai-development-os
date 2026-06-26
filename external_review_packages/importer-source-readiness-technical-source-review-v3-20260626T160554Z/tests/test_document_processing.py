from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.document_processing import triage_pdf_upload


class DocumentProcessingTests(unittest.TestCase):
    def test_triage_extracts_native_text_fields_hash_and_confirmation(self) -> None:
        content = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Page >> endobj\n"
            b"2 0 obj << /Length 160 >> stream\n"
            b"BT (Commercial Invoice number INV-1234) Tj "
            b"(HS code: 0902.30) Tj "
            b"(origin: India) Tj "
            b"(destination: Canada) Tj ET\n"
            b"endstream\n"
            b"endobj\n%%EOF\n"
        )

        result = triage_pdf_upload("invoice.pdf", content)

        self.assertTrue(result["looks_like_pdf"])
        self.assertTrue(result["has_native_text"])
        self.assertEqual(result["extraction_status"], "native_text_extracted_needs_confirmation")
        self.assertEqual(result["document_processing_mode"], "native_text")
        self.assertEqual(result["extracted_fields"]["hs_code"], "0902.30")
        self.assertEqual(result["extracted_fields"]["invoice_or_reference"], "INV-1234")
        self.assertIn("India", result["extracted_fields"]["country_mentions"])
        self.assertEqual(result["ocr_blocker"]["status"], "not_required")
        self.assertEqual(result["cost_estimate"]["estimated_credits"], 0)
        self.assertTrue(result["user_confirmation_required"])
        self.assertEqual(len(result["sha256"]), 64)

    def test_triage_flags_ocr_and_blocks_invalid_or_encrypted_pdfs(self) -> None:
        scanned = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Page /Resources << /XObject << /Im1 2 0 R >> >> >> endobj\n"
            b"2 0 obj << /Subtype /Image /Width 10 /Height 10 >> endobj\n"
            b"%%EOF\n"
        )
        scanned_result = triage_pdf_upload("scan.pdf", scanned)
        self.assertEqual(scanned_result["extraction_status"], "ocr_required_needs_confirmation")
        self.assertEqual(scanned_result["document_processing_mode"], "ocr_required")
        self.assertTrue(scanned_result["ocr_required"])
        self.assertEqual(scanned_result["ocr_blocker"]["status"], "OCR_REQUIRED")
        self.assertTrue(scanned_result["cost_estimate"]["requires_user_approval"])

        encrypted = b"%PDF-1.4\n1 0 obj << /Type /Page >> endobj\ntrailer << /Encrypt 2 0 R >>\n%%EOF\n"
        encrypted_result = triage_pdf_upload("locked.pdf", encrypted)
        self.assertEqual(encrypted_result["extraction_status"], "blocked_encrypted_pdf")
        self.assertEqual(encrypted_result["document_processing_mode"], "blocked")

        invalid_result = triage_pdf_upload("not.pdf", b"not a pdf")
        self.assertEqual(invalid_result["extraction_status"], "rejected_not_pdf")
        self.assertFalse(invalid_result["looks_like_pdf"])


if __name__ == "__main__":
    unittest.main()
