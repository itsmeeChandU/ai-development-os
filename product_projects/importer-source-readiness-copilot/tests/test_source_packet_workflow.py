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
    expert_review_packet_markdown,
    refresh_packet_sources,
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
        self.assertEqual(workflow["customer_stage_status"], "Customer packet prototype active - real customer use not enabled")
        self.assertEqual(workflow["private_beta_status"], "blocked")
        self.assertEqual(workflow["packet_count"], 1)
        self.assertGreaterEqual(workflow["evidence_count"], 3)
        self.assertGreater(workflow["blocker_count"], 0)
        self.assertGreaterEqual(len(workflow["blocker_groups"]), 4)
        self.assertEqual(workflow["ai_review_runs"][0]["review_type"], "canada_compliance_simulation")
        self.assertIs(workflow["ai_review_runs"][0]["can_open_gate"], False)
        self.assertTrue(workflow["ai_review_runs"][0]["findings"][0]["evidence_used"])
        self.assertEqual(workflow["ai_review_runs"][0]["model_mode"], "metadata_only")
        self.assertTrue(workflow["ai_review_runs"][0]["model_route_decisions"])
        self.assertEqual(workflow["ai_review_runs"][0]["validation_result"]["status"], "fail_closed_validated")
        packet = workflow["packets"][0]
        self.assertEqual(packet["organization_id"], "org-importer-demo")
        self.assertIn(packet["customer_visible_status"], {"blocked_stale_source", "needs_expert_review", "needs_operator_review"})
        self.assertIn("Blocked - source freshness missing", packet["customer_visible_status_label"])
        self.assertIn("Source Freshness", {row["title"] for row in packet["blocker_groups"]})
        self.assertGreaterEqual(packet["evidence_summary"]["missing"], 4)
        self.assertGreaterEqual(packet["evidence_summary"]["ai_allowed"], 1)
        for claim in BLOCKED_CLAIMS:
            self.assertIn(claim, packet["blocked_claims"])

    def test_evidence_ledger_explains_reference_only_and_stale_sources(self) -> None:
        ledger = build_evidence_ledger(load_json_list(ROOT / "data" / "evidence_ledger.json"))

        self.assertEqual(ledger["status"], "evidence_ledger_ready_internal")
        statuses = set(ledger["counts_by_status"])
        self.assertTrue({"blocked_reference_only", "blocked_stale_source", "needs_expert_review"} & statuses)
        self.assertIn("stale", ledger["counts_by_quality"])
        self.assertIs(ledger["rows"][0]["ai_processing_allowed"], True)
        self.assertIn("ai_allowed", ledger["rows"][0]["labels"])
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
        self.assertIn("Tariff/HS classification", report)
        self.assertIn("Missing Evidence", report)
        self.assertNotIn("safe_to_import", report)

    def test_source_refresh_records_hash_and_keeps_external_claims_blocked(self) -> None:
        evidence = load_json_list(ROOT / "data" / "evidence_ledger.json")

        def fake_fetcher(url: str) -> dict[str, object]:
            return {"http_status": 200, "content": f"fresh content for {url}", "error": ""}

        updated, report = refresh_packet_sources(
            packet_id="packet-frozen-tuna-canada-001",
            evidence_items=evidence,
            actor="test",
            generated_at="2026-06-25T00:00:00+00:00",
            fetcher=fake_fetcher,
        )

        self.assertEqual(report["status"], "source_refresh_recorded")
        self.assertGreaterEqual(report["row_count"], 3)
        refreshed = [row for row in updated if row.get("packet_id") == "packet-frozen-tuna-canada-001"]
        self.assertTrue(all(row.get("content_hash") for row in refreshed))
        self.assertTrue(all(row.get("freshness_status") == "source_fresh_reference_only" for row in refreshed))

        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=updated,
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        packet = workflow["packets"][0]
        self.assertNotEqual(packet["customer_visible_status"], "blocked_stale_source")
        self.assertIn("qualified expert review", packet["safe_summary"])

    def test_expert_review_packet_is_scoped_and_not_approval(self) -> None:
        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        packet_id = workflow["packets"][0]["packet_id"]
        packet = expert_review_packet_markdown(workflow, packet_id)

        self.assertIn("Expert Review Packet", packet)
        self.assertIn("Questions For Reviewer", packet)
        self.assertIn("do not open external-world gates", packet)

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
