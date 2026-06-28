from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import (  # noqa: E402
    build_continuation_plan,
    build_external_gate_report,
    build_vc_pitch_readiness,
    evaluate_cards,
    load_cards,
    load_json,
)


class InvestorReadinessTests(unittest.TestCase):
    def test_vc_pitch_ready_with_diligence_gates(self) -> None:
        readiness = evaluate_cards(load_cards(ROOT / "data" / "sample_source_cards.json"))
        external = build_external_gate_report(
            country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
            evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
        )
        continuation = build_continuation_plan(readiness=readiness, external=external)
        report = build_vc_pitch_readiness(
            readiness=readiness,
            external=external,
            continuation=continuation,
            investor_evidence=load_json(ROOT / "data" / "investor_evidence.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "vc_pitch_ready_with_diligence_gates")
        self.assertTrue(report["demo_ready"])
        self.assertTrue(report["continuation_ready"])
        self.assertTrue(report["evidence_ready"])
        self.assertGreaterEqual(len(report["diligence_lanes"]), 6)
        self.assertIn("fully_operational", report["closed_claims"])
        self.assertIn("not an offering document", report["draft_funding_ask"]["boundary"])

    def test_investor_evidence_needs_claim_boundaries(self) -> None:
        readiness = evaluate_cards(load_cards(ROOT / "data" / "sample_source_cards.json"))
        external = build_external_gate_report(
            country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
            evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
        )
        continuation = build_continuation_plan(readiness=readiness, external=external)
        evidence = load_json(ROOT / "data" / "investor_evidence.json")
        evidence[0] = {**evidence[0], "claim_boundary": ""}

        report = build_vc_pitch_readiness(
            readiness=readiness,
            external=external,
            continuation=continuation,
            investor_evidence=evidence,
            generated_at="2026-06-25T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "vc_pitch_blocked")
        self.assertFalse(report["evidence_ready"])
        self.assertIn("wto-global-trade-outlook-2025", report["evidence_status"]["malformed_rows"])


if __name__ == "__main__":
    unittest.main()
