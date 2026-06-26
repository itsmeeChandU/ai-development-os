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
from importer_source_readiness.completion_platform import build_completion_platform, write_completion_platform_artifacts
from importer_source_readiness.source_packet_workflow import build_customer_workflow, load_json_list


class CompletionPlatformTests(unittest.TestCase):
    def _payload(self) -> dict:
        official_sources = load_json(ROOT / "data" / "official_source_registry.json")
        workflow = build_customer_workflow(
            source_packets=load_json_list(ROOT / "data" / "customer_source_packets.json"),
            evidence_items=load_json_list(ROOT / "data" / "evidence_ledger.json"),
            official_sources=official_sources,
            generated_at="2026-06-25T00:00:00+00:00",
        )
        return build_completion_platform(workflow, official_sources)

    def test_completion_platform_contracts_are_fail_closed(self) -> None:
        payload = self._payload()

        self.assertEqual(payload["status"], "completion_platform_contracts_ready_with_external_gates")
        self.assertEqual(payload["country_coverage"]["status"], "country_coverage_ready_with_claim_gates")
        self.assertEqual(payload["opportunity_scanner"]["status"], "opportunity_scanner_ready_with_research_gates")
        self.assertEqual(payload["transport_readiness"]["status"], "transport_readiness_ready_with_forwarder_gates")
        self.assertEqual(payload["billing_credit_controls"]["status"], "billing_credit_controls_ready_local_no_live_checkout")
        self.assertEqual(payload["agent_api_manifest"]["status"], "agent_api_manifest_ready_scoped_and_metered")
        self.assertEqual(payload["traffic_pages_manifest"]["status"], "traffic_pages_manifest_ready")

        self.assertGreaterEqual(payload["opportunity_scanner"]["signal_count"], 1)
        for signal in payload["opportunity_scanner"]["signals"]:
            self.assertEqual(signal["opportunity_signal"], "possible opportunity signal")
            self.assertEqual(signal["recommendation_claim"], "blocked")
            self.assertEqual(signal["buyer_validation"], "missing")

        canada = next(row for row in payload["country_coverage"]["countries"] if row["country"] == "Canada")
        self.assertFalse(canada["can_make_country_specific_claims"])
        self.assertGreaterEqual(canada["coverage_tier"], 1)

        transport_row = payload["transport_readiness"]["rows"][0]
        self.assertIn("forwarder", transport_row["missing_transport_inputs"])
        self.assertIn("shipment_ready", payload["transport_readiness"]["blocked_claims"])

        billing = payload["billing_credit_controls"]
        self.assertFalse(billing["live_checkout_enabled"])
        self.assertTrue(any(row["free_plan_behavior"] == "blocked_requires_upgrade" for row in billing["billable_actions"]))

        agent = payload["agent_api_manifest"]
        forbidden = set(agent["forbidden_tools"])
        self.assertIn("approve_import", forbidden)
        self.assertIn("confirm_tariff", forbidden)
        self.assertTrue(all(row["can_open_claim_gate"] is False for row in agent["allowed_tools"]))
        self.assertGreaterEqual(len(payload["traffic_pages_manifest"]["pages"]), 10)

    def test_completion_platform_artifacts_are_written(self) -> None:
        payload = self._payload()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_completion_platform_artifacts(payload, root)

            for name in (
                "completion_platform_manifest.json",
                "country_coverage_report.json",
                "opportunity_scanner_report.json",
                "transport_readiness_report.json",
                "billing_credit_controls.json",
                "agent_api_manifest.json",
                "traffic_pages_manifest.json",
            ):
                self.assertTrue((root / "system_review_graph" / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
