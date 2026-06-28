from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import build_external_gate_report, load_json, render_dashboard


class ExternalGateTests(unittest.TestCase):
    def test_external_gate_report_names_real_stoppers(self) -> None:
        report = build_external_gate_report(
            country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
            evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ready_with_external_gates")
        self.assertGreaterEqual(report["blocker_count"], 10)
        modules = {row["module"] for row in report["blockers"]}
        self.assertIn("tariff_classification", modules)
        self.assertIn("food_safety", modules)
        self.assertIn("buyer_validation", modules)
        self.assertIn("commercial_contract", modules)
        self.assertIn("launch_readiness", modules)

    def test_official_sources_have_claim_boundaries(self) -> None:
        sources = load_json(ROOT / "data" / "official_source_registry.json")
        self.assertGreaterEqual(len(sources), 5)
        for source in sources:
            self.assertTrue(source["url"].startswith("https://"))
            self.assertIn("Reference source only", source["claim_boundary"])

    def test_operator_dashboard_renders_blockers(self) -> None:
        readiness = load_json(ROOT / "system_review_graph" / "readiness_report.json")
        external = build_external_gate_report(
            country_matrix=load_json(ROOT / "data" / "country_requirements_matrix.json"),
            evidence_packets=load_json(ROOT / "data" / "evidence_packets.json"),
            official_sources=load_json(ROOT / "data" / "official_source_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

        html = render_dashboard(readiness, external)

        self.assertIn("Importer Source Readiness Copilot", html)
        self.assertIn("External Gate Blockers", html)
        self.assertIn("All unsafe gates are closed", html)


if __name__ == "__main__":
    unittest.main()
