from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import load_json
from importer_source_readiness.customer_store import TABLES, inspect_customer_store, write_customer_store
from importer_source_readiness.source_packet_workflow import build_customer_workflow, load_json_list


class CustomerStoreTests(unittest.TestCase):
    def test_customer_workflow_store_has_required_tables(self) -> None:
        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = write_customer_store(workflow, Path(tmp) / "customer_workflow.sqlite")
            report = inspect_customer_store(path)

        self.assertEqual(report["status"], "customer_store_ready")
        self.assertEqual(report["tables"], TABLES)
        self.assertGreaterEqual(report["counts"]["source_packets"], 1)
        self.assertGreaterEqual(report["counts"]["evidence_items"], 3)
        self.assertGreaterEqual(report["counts"]["blockers"], 1)
        self.assertGreaterEqual(report["counts"]["review_runs"], 1)
        self.assertGreaterEqual(report["counts"]["gate_decisions"], 8)


if __name__ == "__main__":
    unittest.main()
