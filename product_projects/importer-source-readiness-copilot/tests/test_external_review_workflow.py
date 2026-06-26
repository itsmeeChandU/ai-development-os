from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from importer_source_readiness.external_review import (
    FINDING_FIELDS,
    REVIEW_ROLES,
    build_ai_assisted_findings_report,
    build_ai_assisted_review_plan,
    build_ai_assisted_simulated_reviews,
    build_external_review_blocker_rows,
    build_external_review_findings_report,
    write_external_review_artifacts,
)


class ExternalReviewWorkflowTests(unittest.TestCase):
    def test_report_keeps_external_reviews_pending(self) -> None:
        report = build_external_review_findings_report("2026-06-26T00:00:00Z")

        self.assertEqual(report["status"], "external_review_ready_findings_pending")
        self.assertFalse(report["actual_external_review_completed"])
        self.assertEqual(report["required_review_count"], 9)
        self.assertEqual(report["completed_review_count"], 0)
        self.assertEqual(report["pending_review_count"], 9)
        self.assertFalse(report["public_launch_ready"])
        self.assertFalse(report["hosted_private_beta_ready"])
        self.assertTrue(report["private_beta_blocked_until_wave_1_complete"])
        self.assertTrue(report["unsafe_gates_closed"])
        self.assertTrue(report["solo_ai_assisted_review_supported"])
        self.assertEqual(set(report["finding_schema"]), set(FINDING_FIELDS))
        self.assertEqual(len(report["reviewer_roles"]), len(REVIEW_ROLES))

    def test_ai_assisted_plan_supports_solo_review_without_opening_gates(self) -> None:
        report = build_external_review_findings_report("2026-06-26T00:00:00Z")
        plan = build_ai_assisted_review_plan(report)

        self.assertEqual(plan["status"], "ai_assisted_external_review_ready")
        self.assertEqual(plan["wave_1_simulated_review_status"], "ai_assisted_wave_1_reviewed_with_blockers")
        self.assertTrue(plan["solo_developer_mode"])
        self.assertFalse(plan["human_equivalent_approval"])
        self.assertFalse(plan["can_open_private_beta_gate"])
        self.assertFalse(plan["can_open_public_launch_gate"])
        self.assertTrue(plan["can_reduce_findings_before_real_review"])
        self.assertEqual(plan["simulated_review_count"], 5)
        self.assertEqual(plan["simulated_finding_count"], 5)
        self.assertEqual(plan["required_role_count"], 9)
        self.assertIn("security-public-upload", plan["research_anchors"])
        self.assertIn("ai-safety", plan["research_anchors"])
        self.assertIn("devops-production-readiness", plan["research_anchors"])
        self.assertIn("billing-payment", plan["research_anchors"])

    def test_ai_assisted_wave_1_findings_are_simulated_blockers(self) -> None:
        reviews = build_ai_assisted_simulated_reviews("2026-06-26T00:00:00Z")
        report = build_ai_assisted_findings_report("2026-06-26T00:00:00Z")

        self.assertEqual(len(reviews), 5)
        self.assertEqual(report["status"], "ai_assisted_wave_1_reviewed_with_blockers")
        self.assertEqual(report["simulated_review_count"], 5)
        self.assertEqual(report["simulated_finding_count"], 5)
        self.assertEqual(report["real_external_review_count"], 0)
        self.assertFalse(report["human_equivalent_approval"])
        self.assertFalse(report["can_open_private_beta_gate"])
        self.assertFalse(report["can_open_public_launch_gate"])
        self.assertEqual(report["private_beta_blocking_findings"], 5)
        for review in reviews:
            self.assertEqual(review["review_origin"], "ai_assisted_simulated_review")
            self.assertTrue(review["human_followup_required"])
            self.assertEqual(review["verdict"], "blocked")
            for finding in review["findings"]:
                self.assertEqual(finding["review_origin"], "ai_assisted_simulated_review")
                self.assertTrue(finding["blocks_private_beta"])
                self.assertTrue(finding["blocks_public_launch"])
                self.assertTrue(finding["human_followup_required"])
                self.assertEqual(finding["model_or_agent_used"], "Codex GPT-5 simulated reviewer")
                for field in FINDING_FIELDS:
                    self.assertIn(field, finding)

    def test_blocker_rows_are_closed_and_schema_complete(self) -> None:
        report = build_external_review_findings_report("2026-06-26T00:00:00Z")
        blockers = build_external_review_blocker_rows(report)

        self.assertEqual(len(blockers), 9)
        self.assertEqual(sum(1 for row in blockers if row["blocks_private_beta"]), 5)
        self.assertTrue(all(row["blocks_public_launch"] for row in blockers))
        self.assertTrue(all(row["gate"] == "closed" for row in blockers))
        self.assertTrue(all(row["unsafe_to_bypass"] for row in blockers))
        for row in blockers:
            for field in FINDING_FIELDS:
                self.assertIn(field, row)

    def test_writer_creates_reviewer_packets_and_finding_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_external_review_artifacts(root)

            self.assertEqual(result["status"], "external_review_ready_findings_pending")
            self.assertTrue((root / "docs" / "EXTERNAL_REVIEW_PROCESS.md").exists())
            self.assertTrue((root / "EXTERNAL_REVIEW_SUMMARY.md").exists())
            self.assertTrue((root / "system_review_graph" / "external_review_blocker_ledger.jsonl").exists())
            self.assertTrue((root / "system_review_graph" / "ai_assisted_external_review_plan.json").exists())
            self.assertTrue((root / "system_review_graph" / "ai_assisted_external_review_findings_report.json").exists())
            self.assertTrue((root / "reviewer_packets" / "WAVE_1_SECURITY_PUBLIC_UPLOAD_REVIEW.md").exists())
            self.assertTrue((root / "external_review_findings" / "SECURITY_PUBLIC_UPLOAD_REVIEW.md").exists())
            self.assertTrue((root / "ai_assisted_review" / "AI_ASSISTED_REVIEW_SUMMARY.md").exists())
            self.assertTrue((root / "ai_assisted_review" / "WEB_RESEARCH_SOURCE_LOG.md").exists())
            self.assertTrue((root / "ai_assisted_review" / "role_prompts" / "WAVE_1_AI_SAFETY_REVIEW.md").exists())
            self.assertTrue((root / "ai_assisted_review" / "simulated_findings" / ".gitkeep").exists())
            self.assertTrue(
                (root / "ai_assisted_review" / "simulated_findings" / "WAVE_1_AI_SAFETY_REVIEW.json").exists()
            )

            summary = json.loads(
                (root / "external_review_findings" / "EXTERNAL_REVIEW_SUMMARY.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(summary["actual_external_review_completed"])
            self.assertEqual(summary["completed_review_count"], 0)
            ai_summary = json.loads(
                (
                    root
                    / "system_review_graph"
                    / "ai_assisted_external_review_findings_report.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(ai_summary["real_external_review_count"], 0)
            self.assertEqual(ai_summary["simulated_review_count"], 5)


if __name__ == "__main__":
    unittest.main()
