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

from importer_source_readiness.production_trade_data_catalog_engine import (
    STATUS,
    build_production_trade_data_catalog_engine,
    write_production_trade_data_catalog_engine_artifacts,
)


class ProductionTradeDataCatalogEngineTests(unittest.TestCase):
    def test_trade_data_catalog_builds_query_templates_without_values_or_claims(self) -> None:
        manifest = build_production_trade_data_catalog_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertGreaterEqual(manifest["template_count"], 7)
        self.assertGreaterEqual(manifest["browse_card_count"], 5)
        self.assertGreaterEqual(manifest["query_work_order_count"], 120)
        self.assertGreaterEqual(manifest["source_route_count"], 20)
        self.assertEqual(manifest["missing_registry_sources"], [])
        self.assertFalse(manifest["values_loaded"])
        self.assertFalse(manifest["numeric_values_shown"])
        self.assertFalse(manifest["recommendations_created"])
        self.assertFalse(manifest["demand_claimed"])
        self.assertFalse(manifest["profitability_claimed"])
        self.assertFalse(manifest["buyer_validation_claimed"])
        self.assertFalse(manifest["supplier_verification_claimed"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertIn("guaranteed_demand", manifest["blocked_claims"])
        self.assertIn("buyer_validated", manifest["blocked_claims"])

    def test_templates_cover_import_export_leads_regulated_and_market_access_paths(self) -> None:
        manifest = build_production_trade_data_catalog_engine(ROOT)
        templates = {row["template_id"]: row for row in manifest["query_templates"]}

        for template_id in {
            "canada_imports_by_product_origin",
            "canada_exports_by_product_destination",
            "origin_country_comparison_for_canada",
            "canadian_importer_lead_lookup",
            "regulated_goods_source_overlay",
            "market_access_comparison",
            "global_context_fallback",
        }:
            self.assertIn(template_id, templates)

        self.assertIn("ised-trade-data-online", templates["canada_imports_by_product_origin"]["primary_source_ids"])
        self.assertIn("statcan-wds", templates["canada_exports_by_product_destination"]["primary_source_ids"])
        self.assertIn("canada-cid", templates["canadian_importer_lead_lookup"]["primary_source_ids"])
        self.assertIn("cfia-airs", templates["regulated_goods_source_overlay"]["primary_source_ids"])
        self.assertTrue(all(row["values_loaded"] is False for row in manifest["query_templates"]))
        self.assertTrue(all(row["allowed_to_show_numeric_values"] is False for row in manifest["query_templates"]))

    def test_work_orders_are_tied_to_discovery_lanes_and_require_dated_rows(self) -> None:
        manifest = build_production_trade_data_catalog_engine(ROOT)
        work_orders = manifest["query_work_orders"]

        lane_ids = {row["lane_id"] for row in work_orders}
        self.assertIn("IN-to-CA", lane_ids)
        self.assertIn("VN-to-CA", lane_ids)
        self.assertIn("CA-to-US", lane_ids)
        self.assertIn("GENERIC-to-CA", lane_ids)

        self.assertTrue(all(row["manual_query_ready"] is True for row in work_orders))
        self.assertTrue(all(row["approved_connector_ready"] is False for row in work_orders))
        self.assertTrue(all(row["values_loaded"] is False for row in work_orders))
        self.assertTrue(all(row["dated_dataset_row_attached"] is False for row in work_orders))
        self.assertTrue(all("dated_dataset_row_attached" not in row["allowed_output_before_ingestion"] for row in work_orders))
        self.assertTrue(all("source_routes" in row["allowed_output_before_ingestion"] for row in work_orders))

    def test_writer_creates_catalog_artifacts(self) -> None:
        manifest = build_production_trade_data_catalog_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_trade_data_catalog_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_templates = json.loads(paths["templates"].read_text(encoding="utf-8"))
            written_work_orders = json.loads(paths["work_orders"].read_text(encoding="utf-8"))
            written_cards = json.loads(paths["browse_cards"].read_text(encoding="utf-8"))
            written_policy = json.loads(paths["ingestion_policy"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_templates["status"], "production_trade_data_query_templates_ready")
            self.assertEqual(written_work_orders["status"], "production_trade_data_query_work_orders_ready_no_values_loaded")
            self.assertEqual(written_cards["status"], "production_trade_data_browse_cards_ready")
            self.assertEqual(written_policy["status"], "trade_data_ingestion_policy_ready_fail_closed")
            self.assertIn("Production Trade Data Catalog Engine", written_doc)
            self.assertIn("Numeric values shown: false", written_doc)


if __name__ == "__main__":
    unittest.main()
