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

from importer_source_readiness.production_reports_engine import (
    REPORT_TYPES,
    STATUS,
    WATERMARK,
    build_production_reports_engine,
    write_production_reports_engine_artifacts,
)


class ProductionReportsEngineTests(unittest.TestCase):
    def test_manifest_registers_all_required_report_types_and_formats(self) -> None:
        manifest = build_production_reports_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["report_type_count"], 12)
        self.assertEqual(manifest["report_type_count"], len(REPORT_TYPES))
        expected_report_records = manifest["packet_count"] * len(REPORT_TYPES)
        self.assertGreaterEqual(manifest["packet_count"], 1)
        self.assertEqual(manifest["report_record_count"], expected_report_records)
        self.assertEqual(manifest["export_record_count"], expected_report_records * 3)
        self.assertTrue(manifest["html_preview_supported"])
        self.assertTrue(manifest["pdf_export_supported"])
        self.assertTrue(manifest["json_export_supported"])
        self.assertTrue(manifest["version_history_supported"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["live_payment_ready"])

    def test_report_records_keep_blocked_claims_citations_watermark_and_review_status(self) -> None:
        manifest = build_production_reports_engine(ROOT)
        expected_types = {
            "starter_trade_readiness_packet",
            "market_opportunity_brief",
            "buyer_ready_packet",
            "supplier_document_request",
            "broker_review_packet",
            "missing_evidence_report",
            "blocked_claims_report",
            "country_source_map",
            "source_freshness_report",
            "expert_review_summary",
            "executive_decision_report",
            "audit_export",
        }
        actual_types = {row["report_type"] for row in manifest["report_records"]}

        self.assertEqual(actual_types, expected_types)
        for record in manifest["report_records"]:
            self.assertEqual(record["watermark"], WATERMARK)
            self.assertEqual(record["review_status"], "not_reviewed")
            self.assertEqual(record["formats"], ["json", "html", "pdf"])
            self.assertTrue(record["blocked_claim_section_included"])
            self.assertFalse(record["can_hide_blocked_claims"])
            self.assertGreater(record["blocked_claim_count"], 0)
            self.assertGreater(record["citation_count"], 0)
            self.assertTrue(record["source_citations"])
            self.assertTrue(record["evidence_citations"])
            self.assertFalse(record["claims_opened"])
            self.assertFalse(record["external_effects_created"])

    def test_exports_reference_existing_paths_and_preserve_claim_boundaries(self) -> None:
        manifest = build_production_reports_engine(ROOT)

        for export in manifest["export_records"]:
            self.assertIn(export["format"], {"json", "html", "pdf"})
            self.assertEqual(export["status"], "export_ready_local")
            self.assertEqual(export["watermark"], WATERMARK)
            self.assertEqual(export["review_status"], "not_reviewed")
            self.assertTrue(export["blocked_claim_section_included"])
            self.assertFalse(export["claims_opened"])
            self.assertFalse(export["external_effects_created"])

    def test_writer_creates_json_html_pdf_exports_and_manifest_artifacts(self) -> None:
        manifest = build_production_reports_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_reports_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_catalog = json.loads(paths["catalog"].read_text(encoding="utf-8"))
            written_exports = json.loads(paths["exports"].read_text(encoding="utf-8"))
            written_citations = json.loads(paths["citations"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_catalog["status"], "production_report_catalog_ready")
            self.assertEqual(written_exports["status"], "production_report_exports_ready_cited")
            self.assertEqual(written_citations["status"], "production_report_citations_ready")
            self.assertIn("Production Reports Engine", written_doc)
            self.assertEqual(len(written_exports["written_report_paths"]), manifest["report_record_count"])

            first_paths = written_exports["written_report_paths"][0]
            self.assertTrue((root / first_paths["json"]).exists())
            self.assertIn("<h2>Blocked Claims</h2>", (root / first_paths["html"]).read_text(encoding="utf-8"))
            self.assertTrue((root / first_paths["pdf"]).read_bytes().startswith(b"%PDF"))

    def test_citation_records_cover_sources_and_evidence(self) -> None:
        manifest = build_production_reports_engine(ROOT)
        citation_types = {row["citation_type"] for row in manifest["citation_records"]}

        self.assertIn("source", citation_types)
        self.assertIn("evidence", citation_types)
        for row in manifest["citation_records"]:
            self.assertIn("report_id", row)
            self.assertIn(row["citation_type"], {"source", "evidence"})


if __name__ == "__main__":
    unittest.main()
