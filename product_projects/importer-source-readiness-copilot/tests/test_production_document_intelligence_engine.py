from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_document_intelligence_engine import (
    REQUIRED_TRADE_DOCUMENT_CLASSES,
    SAMPLE_LIBRARY_STATUS,
    STATUS,
    SYNTHETIC_FIXTURES,
    build_production_document_intelligence_engine,
    ensure_parser_qa_documents,
    write_production_document_intelligence_engine_artifacts,
)


class ProductionDocumentIntelligenceEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        ensure_parser_qa_documents(ROOT)

    def test_document_engine_builds_pipeline_records_and_keeps_claims_closed(self) -> None:
        manifest = build_production_document_intelligence_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertGreaterEqual(manifest["pipeline_stage_count"], 16)
        self.assertEqual(manifest["document_class_count"], len(REQUIRED_TRADE_DOCUMENT_CLASSES))
        self.assertGreaterEqual(manifest["official_sample_document_count"], 3)
        self.assertGreaterEqual(manifest["source_route_only_sample_count"], 3)
        self.assertEqual(manifest["synthetic_parser_fixture_count"], len(SYNTHETIC_FIXTURES))
        self.assertGreaterEqual(manifest["document_record_count"], len(SYNTHETIC_FIXTURES) + 3)
        self.assertGreater(manifest["extracted_field_count"], 0)
        self.assertEqual(manifest["parser_qa_status"], "production_document_parser_qa_ready_fixture_expectations_checked")
        self.assertEqual(manifest["parser_qa_fixture_count"], len(SYNTHETIC_FIXTURES))
        self.assertEqual(manifest["parser_qa_passed_count"], len(SYNTHETIC_FIXTURES))
        self.assertEqual(manifest["parser_qa_needs_rule_count"], 0)
        self.assertTrue(manifest["parser_qa_all_fixtures_passed"])
        self.assertEqual(manifest["sample_library_status"], SAMPLE_LIBRARY_STATUS)
        self.assertEqual(manifest["sample_library_official_pdf_count"], 3)
        self.assertGreaterEqual(manifest["sample_library_source_route_only_count"], 4)
        self.assertEqual(manifest["sample_library_synthetic_fixture_count"], len(SYNTHETIC_FIXTURES))
        self.assertFalse(manifest["sample_library_claims_opened"])
        self.assertFalse(manifest["real_uploads_enabled"])
        self.assertFalse(manifest["malware_scan_proven"])
        self.assertFalse(manifest["object_storage_ready"])
        self.assertTrue(manifest["parser_outputs_are_draft"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertIn("document_authenticity_verified", manifest["blocked_claims"])
        self.assertIn("customs_ready", manifest["blocked_claims"])
        self.assertIn("supplier_verified", manifest["blocked_claims"])

        stages = {row["stage"] for row in manifest["pipeline_stages"]}
        for stage in (
            "upload_intake",
            "file_signature_check",
            "quarantine",
            "malware_scan",
            "ocr_text_extraction",
            "document_classification",
            "field_extraction",
            "user_confirmation",
            "evidence_ledger_mapping",
            "redaction_preview",
            "ai_optional_analysis",
            "report_usage",
        ):
            self.assertIn(stage, stages)

    def test_sample_library_separates_official_pdfs_source_routes_and_synthetic_fixtures(self) -> None:
        manifest = build_production_document_intelligence_engine(ROOT)
        records = manifest["document_records"]
        source_records = manifest["source_records"]
        sample_library = manifest["sample_library"]

        sample_levels = {row.get("sample_level") for row in records}
        self.assertIn("official_pdf_downloaded", sample_levels)
        self.assertIn("synthetic_parser_fixture", sample_levels)
        self.assertEqual(sample_library["status"], SAMPLE_LIBRARY_STATUS)
        self.assertFalse(sample_library["claims_opened"])
        self.assertEqual(sample_library["customer_evidence_allowed_count"], 0)
        self.assertIn("CA", sample_library["country_coverage"])
        self.assertIn("IN", sample_library["country_coverage"])
        self.assertIn("VN", sample_library["country_coverage"])
        self.assertIn("GENERIC", sample_library["country_coverage"])
        self.assertTrue(any(row["source_id"] == "cbsa-ci1-canada-customs-invoice" for row in source_records))
        self.assertTrue(any(row["source_id"] == "india-dgft-appendices-anf" for row in source_records))
        self.assertTrue(any(row["source_id"] == "vietnam-customs-portal" for row in source_records))

        official = [row for row in records if row.get("sample_level") == "official_pdf_downloaded"]
        self.assertTrue(all(row["sample_form_only"] for row in official))
        self.assertTrue(all(row["can_support_customer_claims"] is False for row in records))
        library_rows = sample_library["rows"]
        official_library_rows = [row for row in library_rows if row["sample_level"] == "official_pdf_downloaded"]
        route_only_rows = [row for row in library_rows if row["sample_level"] == "official_source_route_only"]
        synthetic_rows = [row for row in library_rows if row["sample_level"] == "synthetic_parser_fixture"]
        self.assertEqual(len(official_library_rows), 3)
        self.assertGreaterEqual(len(route_only_rows), 4)
        self.assertEqual(len(synthetic_rows), len(SYNTHETIC_FIXTURES))
        self.assertTrue(all(row["file_metadata"]["local_file_present"] for row in official_library_rows))
        self.assertTrue(all(row["file_metadata"]["sha256"] for row in official_library_rows))
        self.assertTrue(all(row["file_metadata"]["pdf_header_present"] for row in official_library_rows))
        self.assertTrue(all(row["customer_evidence_allowed"] is False for row in library_rows))
        self.assertTrue(all(row["claims_opened"] is False for row in library_rows))
        self.assertTrue(any(row["source_id"] == "vietnam-customs-portal" for row in route_only_rows))
        self.assertTrue(any(row["source_id"] == "india-dgft-appendices-anf" for row in route_only_rows))

        covered_classes = {row["classification"]["type"] for row in records}
        required = {row["document_class"] for row in REQUIRED_TRADE_DOCUMENT_CLASSES}
        self.assertTrue(required.issubset(covered_classes))

    def test_extracted_fields_have_provenance_confirmation_and_claim_boundaries(self) -> None:
        manifest = build_production_document_intelligence_engine(ROOT)

        self.assertTrue(manifest["extracted_fields"])
        for field in manifest["extracted_fields"]:
            for key in (
                "document_id",
                "page_or_section",
                "extracted_value",
                "confidence",
                "provenance",
                "user_confirmation_status",
                "claim_boundary",
            ):
                self.assertIn(key, field)
            self.assertEqual(field["supports_claims"], [])
            self.assertIn("document_authenticity_verified", field["blocked_claims"])

        synthetic_fields = [
            field
            for field in manifest["extracted_fields"]
            if "synthetic" in field["document_id"]
        ]
        self.assertTrue(synthetic_fields)
        self.assertTrue(
            any(field["user_confirmation_status"] == "needs_user_confirmation" for field in synthetic_fields)
        )

    def test_parser_qa_matrix_checks_expected_fields_per_fixture(self) -> None:
        manifest = build_production_document_intelligence_engine(ROOT)
        matrix = manifest["parser_qa_matrix"]

        self.assertEqual(matrix["status"], "production_document_parser_qa_ready_fixture_expectations_checked")
        self.assertEqual(matrix["fixture_count"], len(SYNTHETIC_FIXTURES))
        self.assertEqual(matrix["passed_count"], len(SYNTHETIC_FIXTURES))
        self.assertEqual(matrix["needs_rule_count"], 0)
        self.assertTrue(matrix["all_fixtures_passed"])
        for row in matrix["rows"]:
            self.assertEqual(row["status"], "parser_qa_passed")
            self.assertEqual(row["missing_fields"], [])
            self.assertFalse(row["claims_opened"])
            self.assertFalse(row["can_support_customer_claims"])

    def test_writer_creates_manifest_pipeline_fields_and_doc(self) -> None:
        ensure_parser_qa_documents(ROOT)
        manifest = build_production_document_intelligence_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_document_intelligence_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_pipeline = json.loads(paths["pipeline"].read_text(encoding="utf-8"))
            written_fields = json.loads(paths["fields"].read_text(encoding="utf-8"))
            written_parser_qa = json.loads(paths["parser_qa"].read_text(encoding="utf-8"))
            written_sample_library = json.loads(paths["sample_library"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_pipeline["status"], "production_document_pipeline_ready_local_controls_gates_closed")
            self.assertEqual(written_fields["status"], "production_document_extracted_fields_ready_draft_only")
            self.assertEqual(written_parser_qa["status"], "production_document_parser_qa_ready_fixture_expectations_checked")
            self.assertEqual(written_parser_qa["needs_rule_count"], 0)
            self.assertEqual(written_sample_library["status"], SAMPLE_LIBRARY_STATUS)
            self.assertEqual(written_sample_library["customer_evidence_allowed_count"], 0)
            self.assertTrue(written_fields["parser_outputs_are_draft"])
            self.assertIn("Production Document Intelligence Engine", written_doc)
            self.assertIn("Parser QA fixtures passed", written_doc)
            self.assertIn("Sample Library", written_doc)
            self.assertIn("Real uploads enabled: false", written_doc)


if __name__ == "__main__":
    unittest.main()
