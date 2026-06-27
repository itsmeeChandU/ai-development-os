from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from importer_source_readiness.final_go_live import (
    build_current_external_gate_research,
    build_final_go_live_decision,
    build_private_beta_smoke_test_plan,
    build_reviewer_wave_execution_plan,
    write_final_go_live_artifacts,
)

PACKAGE_SCRIPT = ROOT / "scripts" / "package_external_review.py"
spec = importlib.util.spec_from_file_location("package_external_review", PACKAGE_SCRIPT)
assert spec and spec.loader
package_external_review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package_external_review)

AUDIT_SCRIPT = ROOT / "scripts" / "audit_external_package.py"
audit_spec = importlib.util.spec_from_file_location("audit_external_package", AUDIT_SCRIPT)
assert audit_spec and audit_spec.loader
audit_external_package = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit_external_package)


class FinalGoLiveTests(unittest.TestCase):
    def test_final_decision_completes_local_contract_without_opening_launch(self) -> None:
        result = build_final_go_live_decision(ROOT, "2026-06-26T00:00:00Z")

        self.assertEqual(result["status"], "local_go_live_contract_complete_public_launch_blocked")
        self.assertTrue(result["local_contract_complete"])
        self.assertFalse(result["public_launch_ready"])
        self.assertFalse(result["hosted_private_beta_ready"])
        self.assertTrue(result["unsafe_gates_closed"])
        self.assertIn("public_launch_approved", result["must_not_claim"])
        self.assertGreaterEqual(len(result["public_launch_blockers"]), 6)

    def test_external_gate_research_uses_dated_primary_source_anchors(self) -> None:
        result = build_current_external_gate_research("2026-06-26T00:00:00Z")

        self.assertEqual(result["status"], "current_external_gate_research_ready")
        self.assertGreaterEqual(result["source_count"], 8)
        urls = {row["source_url"] for row in result["source_anchors"]}
        self.assertIn("https://www.cbsa-asfc.gc.ca/import/menu-eng.html", urls)
        self.assertIn("https://inspection.canada.ca/en/importing-food-plants-animals", urls)
        self.assertIn("https://docs.stripe.com/get-started/checklist/go-live", urls)
        self.assertIn("public_launch_ready", result["blocked_claims"])

    def test_reviewer_and_private_beta_plans_stay_blocked_until_real_evidence(self) -> None:
        reviewer_plan = build_reviewer_wave_execution_plan("2026-06-26T00:00:00Z")
        smoke_plan = build_private_beta_smoke_test_plan("2026-06-26T00:00:00Z")

        self.assertEqual(reviewer_plan["status"], "reviewer_wave_execution_plan_ready")
        self.assertEqual(reviewer_plan["wave_count"], 3)
        self.assertIn("blocks_hosted_private_beta", reviewer_plan["wave_1_gate"])
        self.assertEqual(
            smoke_plan["status"],
            "private_beta_smoke_test_plan_ready_blocked_until_wave_1_and_staging",
        )
        self.assertIn("real Wave 1 review decisions received", smoke_plan["blocked_until"])

    def test_writer_creates_final_handoff_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "system_review_graph").mkdir()
            for name, payload in {
                "all_stage_readiness_report.json": {
                    "status": "all_local_stages_implemented_with_external_gates",
                    "stage_count": 19,
                    "implemented_stage_count": 19,
                    "go_live_state_count": 18,
                },
                "continuation_plan.json": {"must_continue": True},
                "external_review_findings_report.json": {
                    "status": "external_review_ready_findings_pending",
                    "required_review_count": 9,
                    "completed_review_count": 0,
                    "pending_review_count": 9,
                },
                "ai_assisted_external_review_findings_report.json": {
                    "status": "ai_assisted_wave_1_reviewed_with_blockers",
                    "simulated_finding_count": 5,
                    "private_beta_blocking_findings": 5,
                },
            }.items():
                (root / "system_review_graph" / name).write_text(
                    __import__("json").dumps(payload),
                    encoding="utf-8",
                )
            (root / "system_review_graph" / "external_review_blocker_ledger.jsonl").write_text(
                "{}\n",
                encoding="utf-8",
            )

            result = write_final_go_live_artifacts(root, "2026-06-26T00:00:00Z")

            self.assertEqual(result["status"], "local_go_live_contract_complete_public_launch_blocked")
            self.assertTrue((root / "FINAL_GO_LIVE_HANDOFF.md").exists())
            self.assertTrue((root / "system_review_graph" / "final_go_live_decision_report.json").exists())
            self.assertTrue((root / "system_review_graph" / "current_external_gate_research.json").exists())

    def test_package_builder_creates_auditable_executive_and_technical_zips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            result = package_external_review.package_review_bundles(ROOT, output_dir, stamp="20260626T000000Z")

            executive = Path(result["executive"]["path"])
            technical = Path(result["technical"]["path"])
            executive_sha = Path(result["executive"]["sha256_path"])
            technical_sha = Path(result["technical"]["sha256_path"])
            self.assertTrue(executive.exists())
            self.assertTrue(technical.exists())
            self.assertTrue(executive_sha.exists())
            self.assertTrue(technical_sha.exists())
            self.assertTrue(executive_sha.read_text(encoding="utf-8").startswith(result["executive"]["sha256"]))
            self.assertTrue(technical_sha.read_text(encoding="utf-8").startswith(result["technical"]["sha256"]))
            self.assertEqual(audit_external_package.audit_zip(executive), [])
            self.assertEqual(audit_external_package.audit_zip(technical), [])
            with zipfile.ZipFile(executive) as archive:
                names = set(archive.namelist())
            self.assertTrue(any(name.endswith("START_HERE.md") for name in names))
            self.assertTrue(any(name.endswith("system_review_graph/final_go_live_decision_report.json") for name in names))
            self.assertTrue(any(name.endswith("output/pdf/external_validation_requirements.pdf") for name in names))
            self.assertTrue(any(name.endswith("output/pdf/external_validation_reviewer_brief.pdf") for name in names))
            self.assertTrue(any(name.endswith("output/pdf/go_live_input_requests.pdf") for name in names))
            with zipfile.ZipFile(technical) as archive:
                tech_names = set(archive.namelist())
            self.assertTrue(any(name.endswith("src/importer_source_readiness/final_go_live.py") for name in tech_names))
            self.assertTrue(any(name.endswith("src/importer_source_readiness/external_validation_research.py") for name in tech_names))
            self.assertFalse(any("public_uploads/" in name for name in tech_names))


if __name__ == "__main__":
    unittest.main()
