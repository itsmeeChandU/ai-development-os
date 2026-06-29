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

from importer_source_readiness.production_security_privacy_reliability_engine import (
    STATUS,
    build_production_security_privacy_reliability_engine,
    write_production_security_privacy_reliability_engine_artifacts,
)


class ProductionSecurityPrivacyReliabilityEngineTests(unittest.TestCase):
    def test_manifest_defines_controls_vendors_and_closed_gates(self) -> None:
        manifest = build_production_security_privacy_reliability_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertGreaterEqual(manifest["trust_control_count"], 15)
        self.assertGreaterEqual(manifest["research_reference_count"], 9)
        self.assertEqual(manifest["blocked_trust_gate_count"], manifest["trust_gate_count"])
        self.assertFalse(manifest["real_file_uploads_allowed"])
        self.assertFalse(manifest["unrestricted_uploads_enabled"])
        self.assertFalse(manifest["hosted_private_beta_ready"])
        self.assertFalse(manifest["production_trust_approved"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertEqual(
            manifest["legal_privacy_security_approval_evidence_status"],
            "legal_privacy_security_approval_intake_ready_real_approval_evidence_required_claims_closed",
        )
        self.assertEqual(manifest["legal_privacy_security_approval_record_count"], 0)
        self.assertEqual(manifest["legal_privacy_security_accepted_approval_record_count"], 0)
        self.assertEqual(manifest["legal_privacy_security_approval_blocked_gate_count"], 14)
        self.assertFalse(manifest["legal_privacy_security_approved_by_evidence"])
        self.assertFalse(manifest["legal_privacy_security_claims_opened_by_intake"])

        source_ids = {row["source_id"] for row in manifest["research_references"]}
        self.assertIn("opc-pipeda-principles", source_ids)
        self.assertIn("owasp-file-upload", source_ids)
        self.assertIn("nist-sp-800-61r2", source_ids)
        self.assertIn("openai-api-data-controls", source_ids)

        self.assertGreaterEqual(manifest["vendor_record_count"], 6)
        self.assertEqual(manifest["unapproved_vendor_count"], manifest["vendor_record_count"])
        for vendor in manifest["vendor_register"]:
            self.assertFalse(vendor["production_approved"])
            self.assertFalse(vendor["customer_data_allowed"])
            self.assertEqual(vendor["privacy_review_status"], "not_approved")

    def test_local_backup_restore_drill_hashes_real_artifacts(self) -> None:
        manifest = build_production_security_privacy_reliability_engine(ROOT)
        drill = manifest["backup_restore_drill"]

        self.assertEqual(drill["status"], "local_backup_restore_hash_drill_passed")
        self.assertFalse(drill["production_backup_restore_test_passed"])
        self.assertGreaterEqual(drill["existing_artifact_count"], 5)
        self.assertEqual(drill["restored_artifact_count"], drill["existing_artifact_count"])
        self.assertEqual(drill["hash_match_count"], drill["existing_artifact_count"])
        self.assertIn(
            "system_review_graph/customer_workflow.sqlite",
            {row["relative_path"] for row in drill["records"] if row["source_exists"]},
        )

    def test_trust_controls_map_existing_artifacts_without_opening_gates(self) -> None:
        manifest = build_production_security_privacy_reliability_engine(ROOT)
        controls = {row["control_id"]: row for row in manifest["trust_controls"]}

        self.assertTrue(controls["organization_rbac"]["local_evidence_present"])
        self.assertTrue(controls["backup_restore"]["local_evidence_present"])
        self.assertEqual(controls["malware_scanning"]["production_gate_state"], "blocked")
        self.assertEqual(controls["data_residency"]["production_gate_state"], "blocked")
        for gate in manifest["trust_gates"]:
            self.assertEqual(gate["state"], "blocked")
            self.assertFalse(gate["opened_by_local_artifact"])

    def test_writer_creates_phase19_artifacts(self) -> None:
        manifest = build_production_security_privacy_reliability_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_security_privacy_reliability_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            controls = json.loads(paths["controls"].read_text(encoding="utf-8"))
            vendors = json.loads(paths["vendors"].read_text(encoding="utf-8"))
            backup = json.loads(paths["backup_restore"].read_text(encoding="utf-8"))
            doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(controls["status"], "production_trust_control_matrix_ready_external_gates_closed")
            self.assertEqual(vendors["status"], "production_vendor_register_ready_approvals_required")
            self.assertEqual(backup["status"], "local_backup_restore_hash_drill_passed")
            self.assertIn("Production Security, Privacy, Reliability", doc)
            self.assertIn("Real file uploads allowed: `false`", doc)
            self.assertIn("Legal/privacy/security approved by evidence: `false`", doc)


if __name__ == "__main__":
    unittest.main()
