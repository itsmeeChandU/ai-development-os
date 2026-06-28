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

from importer_source_readiness.production_market_intelligence_engine import (
    MARKET_METRICS,
    STATUS,
    build_production_market_intelligence_engine,
    write_production_market_intelligence_engine_artifacts,
)


class ProductionMarketIntelligenceEngineTests(unittest.TestCase):
    def test_market_engine_creates_source_routed_metric_records_without_claims(self) -> None:
        manifest = build_production_market_intelligence_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["metric_count"], len(MARKET_METRICS))
        self.assertEqual(manifest["market_signal_count"], len(MARKET_METRICS))
        self.assertGreaterEqual(manifest["dataset_connector_count"], 7)
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["live_payment_ready"])
        self.assertIn("profitable_market", manifest["blocked_claims"])
        self.assertIn("guaranteed_demand", manifest["blocked_claims"])
        self.assertIn("buyer_validated", manifest["blocked_claims"])

        signals = {row["metric"]: row for row in manifest["signals"]}
        self.assertEqual(set(signals), set(MARKET_METRICS))
        self.assertIn("ised-trade-data-online", {route["source_id"] for route in signals["destination_import_value"]["source_routes"]})
        self.assertIn("itc-market-access-map", {route["source_id"] for route in signals["market_access_barriers"]["source_routes"]})
        self.assertIn("canada-cid", {route["source_id"] for route in signals["buyer_importer_lead_routes"]["source_routes"]})
        self.assertTrue(all(signal["value_status"] == "not_ingested_dataset_required" for signal in manifest["signals"]))
        self.assertTrue(all(signal["claims_opened"] is False for signal in manifest["signals"]))

    def test_market_packet_caps_scores_until_dataset_and_buyer_evidence_exist(self) -> None:
        manifest = build_production_market_intelligence_engine(ROOT)
        market_packet = manifest["packet_runs"][0]["market_packet"]

        self.assertEqual(market_packet["status"], "market_packet_ready_research_only")
        self.assertEqual(market_packet["signal_count"], len(MARKET_METRICS))
        self.assertLessEqual(market_packet["market_signal_score"], market_packet["market_signal_score_cap"])
        self.assertFalse(market_packet["can_claim_market_demand"])
        self.assertFalse(market_packet["can_claim_profitability"])
        self.assertFalse(market_packet["can_claim_buyer_validation"])
        self.assertIn("buyer_validated", market_packet["blocked_claims"])

    def test_writer_creates_manifest_signals_connectors_and_doc(self) -> None:
        manifest = build_production_market_intelligence_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_market_intelligence_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_signals = json.loads(paths["signals"].read_text(encoding="utf-8"))
            written_connectors = json.loads(paths["connectors"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_signals["status"], "production_market_signals_ready_research_only")
            self.assertEqual(written_connectors["status"], "production_market_dataset_connectors_registered_not_ingesting")
            self.assertIn("Production Market Intelligence Engine", written_doc)
            self.assertIn("Can claim demand: false", written_doc)


if __name__ == "__main__":
    unittest.main()
