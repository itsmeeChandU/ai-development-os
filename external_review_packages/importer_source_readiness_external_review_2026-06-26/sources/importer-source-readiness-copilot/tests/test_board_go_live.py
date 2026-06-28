from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import (  # noqa: E402
    build_board_go_live_readiness,
    build_continuation_plan,
    build_external_gate_report,
    build_vc_pitch_readiness,
    evaluate_cards,
    load_cards,
    load_json,
)


class BoardGoLiveTests(unittest.TestCase):
    def _report(self) -> dict:
        readiness = evaluate_cards(
            load_cards(ROOT / "data" / "sample_source_cards.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        external = build_external_gate_report(
            country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
            evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        continuation = build_continuation_plan(
            readiness=readiness,
            external=external,
            generated_at="2026-06-25T00:00:00+00:00",
        )
        vc_pitch = build_vc_pitch_readiness(
            readiness=readiness,
            external=external,
            continuation=continuation,
            investor_evidence=load_json(ROOT / "data" / "investor_evidence.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )
        return build_board_go_live_readiness(
            readiness=readiness,
            external=external,
            continuation=continuation,
            vc_pitch=vc_pitch,
            canada_tools=load_json(ROOT / "data" / "canada_tool_registry.json"),
            expert_reviews=load_json(ROOT / "data" / "expert_review_simulations.json"),
            launch_controls=load_json(ROOT / "data" / "launch_controls.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

    def test_board_go_live_candidate_for_canada_with_human_gates(self) -> None:
        report = self._report()

        self.assertEqual(report["status"], "board_go_live_candidate_with_human_approval_gates")
        self.assertEqual(report["primary_market"], "Canada")
        self.assertTrue(report["implementation_complete_for_board_review"])
        self.assertTrue(report["canadian_tools_ready"])
        self.assertTrue(report["simulated_expert_reviews_ready"])
        self.assertTrue(report["launch_controls_ready"])
        self.assertGreaterEqual(report["human_approval_gate_count"], 10)
        self.assertIn("customs_or_tariff_advice_ready", report["closed_claims"])
        self.assertIn("not public launch approval", report["proof_boundary"])

    def test_canadian_tool_registry_has_required_categories(self) -> None:
        report = self._report()

        missing = report["canadian_tool_status"]["missing_categories"]
        categories = set(report["canadian_tool_status"]["provided_categories"])
        self.assertEqual(missing, [])
        self.assertIn("customs_accounting", categories)
        self.assertIn("tariff_classification", categories)
        self.assertIn("food_import_requirements", categories)
        self.assertIn("financial_planning", categories)
        self.assertIn("privacy", categories)
        self.assertIn("cybersecurity", categories)

    def test_missing_expert_review_blocks_board_status(self) -> None:
        report = self._report()
        reviews = [row for row in report["simulated_expert_reviews"] if row["id"] != "legal-privacy"]

        blocked = build_board_go_live_readiness(
            readiness={"status": "ready_with_external_gates", "rows": []},
            external={"status": "ready_with_external_gates", "unsafe_gates": {}},
            continuation={"status": "startup_in_progress", "must_continue": True},
            vc_pitch={"status": "vc_pitch_ready_with_diligence_gates"},
            canada_tools=load_json(ROOT / "data" / "canada_tool_registry.json"),
            expert_reviews=reviews,
            launch_controls=load_json(ROOT / "data" / "launch_controls.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

        self.assertEqual(blocked["status"], "board_go_live_blocked")
        self.assertIn("legal-privacy", blocked["expert_review_status"]["missing_reviews"])


if __name__ == "__main__":
    unittest.main()
