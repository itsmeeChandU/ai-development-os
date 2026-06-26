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

from importer_source_readiness.source_packet_workflow import (
    BLOCKED_CLAIMS,
    SAFE_DISPLAY_STATUS,
    build_customer_workflow,
    build_evidence_ledger,
    load_json_list,
    markdown_report,
    write_json,
)
from importer_source_readiness import load_json


class SourcePacketWorkflowTests(unittest.TestCase):
    def test_customer_packet_workflow_blocks_external_claims(self) -> None:
        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

        self.assertEqual(workflow["status"], "customer_workflow_ready_internal")
        self.assertEqual(workflow["display_status"], SAFE_DISPLAY_STATUS)
        self.assertEqual(workflow["packet_count"], 1)
        self.assertGreaterEqual(workflow["evidence_count"], 3)
        self.assertGreater(workflow["blocker_count"], 0)
        packet = workflow["packets"][0]
        self.assertIn(packet["customer_visible_status"], {"blocked_stale_source", "needs_expert_review", "needs_operator_review"})
        for claim in BLOCKED_CLAIMS:
            self.assertIn(claim, packet["blocked_claims"])

    def test_evidence_ledger_explains_reference_only_and_stale_sources(self) -> None:
        ledger = build_evidence_ledger(load_json_list(ROOT / "data" / "evidence_ledger.json"))

        self.assertEqual(ledger["status"], "evidence_ledger_ready_internal")
        statuses = set(ledger["counts_by_status"])
        self.assertTrue({"blocked_reference_only", "blocked_stale_source", "needs_expert_review"} & statuses)
        self.assertIn("No evidence, no claim", ledger["rule"])

    def test_markdown_report_uses_safe_status_language(self) -> None:
        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        packet_id = workflow["packets"][0]["packet_id"]
        report = markdown_report(workflow, packet_id)

        self.assertIn(SAFE_DISPLAY_STATUS, report)
        self.assertIn("Blocked Claims", report)
        self.assertIn("tariff_confirmed", report)
        self.assertNotIn("safe_to_import", report)

    def test_json_writer_outputs_generated_artifact(self) -> None:
        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = write_json(workflow, Path(tmp) / "customer_readiness_report.json")
            loaded = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(loaded["status"], "customer_workflow_ready_internal")


if __name__ == "__main__":
    unittest.main()
