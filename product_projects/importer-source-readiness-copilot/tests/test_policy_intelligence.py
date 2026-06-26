from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import load_json
from importer_source_readiness.policy_intelligence import build_policy_monitor, write_policy_monitor_artifacts
from importer_source_readiness.source_packet_workflow import build_customer_workflow, load_json_list


class PolicyIntelligenceTests(unittest.TestCase):
    def _workflow(self) -> dict:
        return build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

    def test_policy_monitor_maps_sources_to_packets_and_blocks_current_truth_claims(self) -> None:
        monitor = build_policy_monitor(
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            workflow=self._workflow(),
            generated_at="2026-06-25T00:00:00+00:00",
        )

        self.assertEqual(monitor["status"], "intelligence_hub_policy_monitor_ready_with_external_refresh_gates")
        self.assertEqual(monitor["integration_mode"], "database_style_local_contract")
        self.assertGreaterEqual(monitor["monitored_source_count"], 8)
        self.assertGreaterEqual(monitor["packet_impact_count"], 1)
        self.assertGreaterEqual(monitor["stale_source_blocker_count"], 1)
        tags = {tag for source in monitor["monitored_sources"] for tag in source["tags"]}
        self.assertIn("tariff", tags)
        self.assertIn("food_import", tags)
        self.assertEqual(len(monitor["scheduled_jobs"]), monitor["monitored_source_count"])
        self.assertTrue(all("robots_status" in source for source in monitor["monitored_sources"]))
        self.assertTrue(all("terms_status" in source for source in monitor["monitored_sources"]))
        self.assertTrue(all(job["status"] == "defined_not_enabled" for job in monitor["scheduled_jobs"]))
        self.assertFalse(any(job["live_fetch_allowed"] for job in monitor["scheduled_jobs"]))
        self.assertFalse(monitor["external_effects"]["live_fetch_performed"])
        blocker = monitor["stale_source_blockers"][0]
        self.assertEqual(blocker["gate"], "closed")
        self.assertTrue(blocker["unsafe_to_bypass"])

    def test_policy_monitor_writes_sqlite_store(self) -> None:
        monitor = build_policy_monitor(
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            workflow=self._workflow(),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = write_policy_monitor_artifacts(monitor, Path(tmp))
            store_path = Path(tmp) / "system_review_graph" / "policy_intelligence.sqlite"
            self.assertTrue(store_path.exists())
            with sqlite3.connect(store_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute("select name from sqlite_master where type='table'").fetchall()
                }
            self.assertIn("monitored_sources", tables)
            self.assertIn("packet_source_impacts", tables)
            self.assertEqual(result["store"]["tables"]["monitored_sources"], monitor["monitored_source_count"])


if __name__ == "__main__":
    unittest.main()
