from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import build_continuation_plan, build_external_gate_report, evaluate_cards, load_cards, load_json


class ContinuationTests(unittest.TestCase):
    def _plan(self) -> dict:
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
        return build_continuation_plan(
            readiness=readiness,
            external=external,
            generated_at="2026-06-25T00:00:00+00:00",
        )

    def test_ready_with_external_gates_requires_continuation(self) -> None:
        plan = self._plan()

        self.assertEqual(plan["status"], "startup_in_progress")
        self.assertEqual(plan["software_loop_status"], "complete")
        self.assertEqual(plan["local_operator_status"], "operator_ready_internal")
        self.assertTrue(plan["must_continue"])
        self.assertIn("fully_operational", plan["closed_claims"])
        self.assertIn("Local software completion is not startup completion", plan["proof_boundary"])

    def test_continuation_lanes_cover_external_work(self) -> None:
        plan = self._plan()

        lane_ids = {lane["id"] for lane in plan["lanes"]}
        self.assertGreaterEqual(plan["lane_count"], 7)
        self.assertIn("buyer-validation", lane_ids)
        self.assertIn("qualified-compliance-review", lane_ids)
        self.assertIn("country-matrix-review", lane_ids)
        self.assertIn("source-rights-freshness", lane_ids)
        self.assertIn("contract-terms", lane_ids)
        self.assertIn("restricted-party-screening", lane_ids)
        self.assertIn("launch-approval", lane_ids)

        blocked_lanes = [lane for lane in plan["lanes"] if lane["status"] == "blocked_external_input"]
        self.assertGreaterEqual(len(blocked_lanes), 5)
        for lane in blocked_lanes:
            self.assertTrue(lane["required_evidence"])
            self.assertTrue(lane["next_valid_move"])
            self.assertIn("python3", lane["proof_command"])


if __name__ == "__main__":
    unittest.main()
