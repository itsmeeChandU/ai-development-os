from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_persistence import (
    STATUS,
    TABLE_ORDER,
    build_production_persistence_snapshot,
    inspect_sqlite_proof_store,
    write_production_persistence_artifacts,
)


class ProductionPersistenceTests(unittest.TestCase):
    def test_snapshot_maps_current_artifacts_into_domain_rows(self) -> None:
        snapshot = build_production_persistence_snapshot(ROOT)

        self.assertEqual(snapshot["status"], STATUS)
        self.assertEqual(snapshot["validation_error_count"], 0)
        self.assertEqual(snapshot["table_order"], list(TABLE_ORDER))
        self.assertGreaterEqual(snapshot["row_counts"]["trade_readiness_packets"], 1)
        self.assertGreaterEqual(snapshot["row_counts"]["evidence_items"], 3)
        self.assertGreaterEqual(snapshot["row_counts"]["source_records"], 20)
        self.assertGreaterEqual(snapshot["row_counts"]["source_snapshots"], 20)
        self.assertGreaterEqual(snapshot["row_counts"]["decision_scores"], 6)
        self.assertGreaterEqual(snapshot["row_counts"]["reports"], 12)
        self.assertGreaterEqual(snapshot["row_counts"]["audit_events"], 3)
        self.assertFalse(snapshot["hosted_postgres_ready"])
        self.assertFalse(snapshot["production_migration_applied"])
        self.assertFalse(snapshot["external_claims_opened"])
        self.assertFalse(snapshot["public_launch_ready"])

        packet = snapshot["rows"]["trade_readiness_packets"][0]
        self.assertEqual(packet["claim_boundary_status"], "external_claims_closed")
        self.assertIn(packet["state"], {"reviewer_ready", "source_checking", "document_reviewing"})
        self.assertTrue(all(row["organization_id"] for row in snapshot["rows"]["decision_scores"]))
        self.assertTrue(all(row["can_show_claim"] in {0, 1} for row in snapshot["rows"]["claim_gate_mappers"]))

    def test_writer_creates_json_sqlite_store_and_doc(self) -> None:
        snapshot = build_production_persistence_snapshot(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_persistence_artifacts(snapshot, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            row_counts = json.loads(paths["row_counts"].read_text(encoding="utf-8"))
            doc = paths["doc"].read_text(encoding="utf-8")
            store = inspect_sqlite_proof_store(paths["sqlite"])

            self.assertEqual(written["status"], STATUS)
            self.assertEqual(row_counts["status"], STATUS)
            self.assertEqual(store["manifest"]["status"], STATUS)
            self.assertIn("Production Persistence", doc)
            self.assertEqual(store["table_counts"]["trade_readiness_packets"], snapshot["row_counts"]["trade_readiness_packets"])
            self.assertEqual(store["table_counts"]["source_records"], snapshot["row_counts"]["source_records"])

            with sqlite3.connect(paths["sqlite"]) as conn:
                external_claim_boundaries = conn.execute(
                    "select count(*) from trade_readiness_packets where claim_boundary_status != 'external_claims_closed'"
                ).fetchone()[0]
                missing_orgs = conn.execute(
                    "select count(*) from decision_scores where organization_id = ''"
                ).fetchone()[0]
            self.assertEqual(external_claim_boundaries, 0)
            self.assertEqual(missing_orgs, 0)


if __name__ == "__main__":
    unittest.main()
