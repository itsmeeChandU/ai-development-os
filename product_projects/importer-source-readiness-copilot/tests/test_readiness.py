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

from importer_source_readiness import evaluate_cards, load_cards, write_report


class ReadinessTests(unittest.TestCase):
    def test_fixture_report_keeps_external_gates_closed(self) -> None:
        cards = load_cards(ROOT / "data" / "sample_source_cards.json")
        report = evaluate_cards(cards)

        self.assertEqual(report["status"], "ready_with_external_gates")
        self.assertEqual(report["row_count"], 2)
        self.assertGreater(report["blocker_count"], 0)
        self.assertEqual(report["blocked_unsafe_rows"], 0)

        blocker_modules = {row["module"] for row in report["blockers"]}
        self.assertIn("buyer_validation", blocker_modules)
        self.assertIn("legal_compliance", blocker_modules)
        self.assertIn("commercial_contract", blocker_modules)

        for row in report["rows"]:
            self.assertEqual(row["unsafe_counters"]["external_sends_run"], 0)
            self.assertEqual(row["unsafe_counters"]["paid_actions_run"], 0)

    def test_unsafe_external_counter_blocks_work(self) -> None:
        cards = load_cards(ROOT / "data" / "sample_source_cards.json")
        cards[0]["external_sends_run"] = 1

        report = evaluate_cards(cards)

        self.assertEqual(report["status"], "blocked_unsafe")
        self.assertEqual(report["blocked_unsafe_rows"], 1)
        unsafe_blockers = [
            blocker
            for blocker in report["blockers"]
            if blocker["module"] == "unsafe_external_gate"
        ]
        self.assertEqual(len(unsafe_blockers), 1)

    def test_report_writer_outputs_json(self) -> None:
        cards = load_cards(ROOT / "data" / "sample_source_cards.json")
        report = evaluate_cards(cards)

        with tempfile.TemporaryDirectory() as tmp:
            output = write_report(report, Path(tmp) / "report.json")
            loaded = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(loaded["status"], "ready_with_external_gates")
        self.assertIn("proof_boundary", loaded)


if __name__ == "__main__":
    unittest.main()
