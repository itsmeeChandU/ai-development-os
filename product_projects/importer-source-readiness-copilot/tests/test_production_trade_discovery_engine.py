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

from importer_source_readiness.production_trade_discovery_engine import (
    STATUS,
    build_production_trade_discovery_engine,
    write_production_trade_discovery_engine_artifacts,
)


class ProductionTradeDiscoveryEngineTests(unittest.TestCase):
    def test_discovery_engine_closes_beginner_browse_gap_without_claims(self) -> None:
        manifest = build_production_trade_discovery_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertGreaterEqual(manifest["category_count"], 12)
        self.assertGreaterEqual(manifest["country_lane_count"], 12)
        self.assertGreaterEqual(manifest["beginner_flow_count"], 8)
        self.assertGreaterEqual(manifest["dataset_route_count"], 6)
        self.assertGreaterEqual(manifest["source_route_count"], 70)
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["recommendation_claimed"])
        self.assertFalse(manifest["market_opportunity_claimed"])
        self.assertFalse(manifest["demand_claimed"])
        self.assertFalse(manifest["profitability_claimed"])
        self.assertFalse(manifest["buyer_validation_claimed"])
        self.assertFalse(manifest["supplier_verification_claimed"])
        self.assertFalse(manifest["customs_approval_claimed"])
        self.assertFalse(manifest["cfia_approval_claimed"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertEqual(manifest["missing_registry_sources"], [])
        self.assertIn("best_product_to_import", manifest["blocked_claims"])
        self.assertIn("guaranteed_demand", manifest["blocked_claims"])
        self.assertIn("buyer_validated", manifest["blocked_claims"])

    def test_discovery_sources_cover_canada_import_export_and_country_lanes(self) -> None:
        manifest = build_production_trade_discovery_engine(ROOT)
        source_ids = {row["source_id"] for row in manifest["source_records"]}
        for source_id in {
            "ised-trade-data-online",
            "canada-cid",
            "statcan-wds",
            "cbsa-import-commercial-goods",
            "cfia-airs",
            "gac-sanctions",
            "canada-trade-commissioner-export-guide",
            "gac-export-controls",
            "world-bank-wits",
            "itc-trade-map",
            "itc-market-access-map",
            "wco-harmonized-system",
        }:
            self.assertIn(source_id, source_ids)

        flow_ids = {row["flow_id"] for row in manifest["beginner_flows"]}
        self.assertIn("browse_canada_imports", flow_ids)
        self.assertIn("browse_canada_exports", flow_ids)
        self.assertIn("compare_origin_lanes_to_canada", flow_ids)
        self.assertIn("check_regulated_goods_early", flow_ids)

        lane_ids = {row["lane_id"] for row in manifest["country_lanes"]}
        for lane_id in {"IN-to-CA", "VN-to-CA", "US-to-CA", "MX-to-CA", "CN-to-CA", "EU-to-CA", "CA-to-US", "GENERIC-to-CA"}:
            self.assertIn(lane_id, lane_ids)

        self.assertTrue(all(row["trade_values_loaded"] is False for row in manifest["country_lanes"]))
        self.assertTrue(all(row["recommendation_claimed"] is False for row in manifest["country_lanes"]))
        self.assertTrue(all(row["recommendation_claimed"] is False for row in manifest["category_families"]))
        self.assertTrue(all(row["values_loaded"] is False for row in manifest["dataset_routes"]))

    def test_writer_creates_manifest_and_review_artifacts(self) -> None:
        manifest = build_production_trade_discovery_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_trade_discovery_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_categories = json.loads(paths["categories"].read_text(encoding="utf-8"))
            written_lanes = json.loads(paths["country_lanes"].read_text(encoding="utf-8"))
            written_flows = json.loads(paths["beginner_flows"].read_text(encoding="utf-8"))
            written_sources = json.loads(paths["sources"].read_text(encoding="utf-8"))
            written_audit = json.loads(paths["audit"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_categories["status"], "production_trade_discovery_categories_ready_source_routed")
            self.assertEqual(written_lanes["status"], "production_trade_discovery_country_lanes_ready_reference_only")
            self.assertEqual(written_flows["status"], "production_trade_discovery_beginner_flows_ready")
            self.assertEqual(written_sources["status"], "production_trade_discovery_sources_registered")
            self.assertEqual(written_audit["status"], "gap_closed_for_local_research_routed_discovery")
            self.assertIn("Production Trade Discovery Engine", written_doc)
            self.assertIn("Best product claim: false", written_doc)


if __name__ == "__main__":
    unittest.main()
