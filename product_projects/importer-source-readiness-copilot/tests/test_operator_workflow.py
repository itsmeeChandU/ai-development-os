from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import build_operator_workflow, load_json, render_dashboard, write_operator_workflow


class OperatorWorkflowTests(unittest.TestCase):
    def _workflow(self) -> dict:
        return build_operator_workflow(
            readiness=load_json(ROOT / "system_review_graph" / "readiness_report.json"),
            external=load_json(ROOT / "system_review_graph" / "external_gate_report.json"),
            continuation=load_json(ROOT / "system_review_graph" / "continuation_plan.json"),
            board=load_json(ROOT / "system_review_graph" / "board_go_live_readiness_report.json"),
            canada_tools=load_json(ROOT / "data" / "canada_tool_registry.json"),
            generated_at="2026-06-25T00:00:00+00:00",
        )

    def test_operator_workflow_builds_complete_queue(self) -> None:
        workflow = self._workflow()

        self.assertEqual(workflow["status"], "operator_workflow_ready_internal")
        self.assertTrue(workflow["operator_can_use_now"])
        self.assertGreaterEqual(workflow["work_queue_count"], 20)
        self.assertTrue(workflow["unsafe_gates_closed"])

        row_types = set(workflow["work_queue_counts_by_type"])
        self.assertIn("source_card_review", row_types)
        self.assertIn("external_evidence_gate", row_types)
        self.assertIn("continuation_lane", row_types)
        self.assertIn("human_approval_gate", row_types)

        top = workflow["work_queue"][0]
        self.assertEqual(top["type"], "human_approval_gate")
        self.assertIn("not prove", workflow["proof_boundary"])

    def test_source_rows_include_canadian_tool_references(self) -> None:
        workflow = self._workflow()
        source_rows = [row for row in workflow["work_queue"] if row["type"] == "source_card_review"]

        self.assertGreaterEqual(len(source_rows), 2)
        for row in source_rows:
            tool_ids = {tool["id"] for tool in row["canadian_tool_refs"]}
            self.assertIn("cbsa-import-commercial-goods", tool_ids)
            self.assertIn("cbsa-customs-tariff-2026", tool_ids)
            self.assertIn("cfia-airs", tool_ids)

    def test_dashboard_renders_operator_queue(self) -> None:
        readiness = load_json(ROOT / "system_review_graph" / "readiness_report.json")
        external = load_json(ROOT / "system_review_graph" / "external_gate_report.json")
        workflow = self._workflow()

        html = render_dashboard(readiness, external, operator_workflow=workflow)

        self.assertIn("Operator Work Queue", html)
        self.assertIn("Canada Tools", html)
        self.assertIn("approval required", html)

    def test_writer_outputs_json(self) -> None:
        workflow = self._workflow()
        with tempfile.TemporaryDirectory() as tmp:
            output = write_operator_workflow(workflow, Path(tmp) / "operator_workflow_report.json")
            loaded = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(loaded["status"], "operator_workflow_ready_internal")
        self.assertIn("work_queue", loaded)


if __name__ == "__main__":
    unittest.main()
