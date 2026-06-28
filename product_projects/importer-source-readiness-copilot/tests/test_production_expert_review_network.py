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

from importer_source_readiness.production_expert_review_network import (
    FORBIDDEN_EXTERNAL_CLAIMS,
    REVIEW_DECISIONS,
    SEVERITY_LEVELS,
    STATUS,
    build_production_expert_review_network,
    write_production_expert_review_network_artifacts,
)


class ProductionExpertReviewNetworkTests(unittest.TestCase):
    def test_manifest_registers_reviewer_lanes_and_keeps_gates_closed(self) -> None:
        manifest = build_production_expert_review_network(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["reviewer_lane_count"], 10)
        self.assertEqual(manifest["profile_requirement_count"], 10)
        self.assertEqual(manifest["finding_template_count"], 10)
        self.assertGreaterEqual(manifest["review_request_count"], 10)
        self.assertGreaterEqual(manifest["source_registry_coverage_count"], 9)
        self.assertFalse(manifest["real_reviewer_signoff_recorded"])
        self.assertFalse(manifest["qualified_credentials_verified"])
        self.assertFalse(manifest["scope_limited_approval_recorded"])
        self.assertFalse(manifest["can_open_customs_tariff_cfia_buyer_supplier_security_privacy_payment_launch_gate"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["external_effects_created"])

    def test_profiles_require_credentials_and_source_backed_scope(self) -> None:
        manifest = build_production_expert_review_network(ROOT)
        profiles = {row["reviewer_lane_id"]: row for row in manifest["reviewer_profiles"]}

        for lane_id in (
            "customs_trade_reviewer",
            "regulated_food_product_reviewer",
            "freight_logistics_reviewer",
            "market_trade_consultant_reviewer",
            "supplier_evidence_reviewer",
            "privacy_legal_reviewer",
            "security_upload_reviewer",
            "ai_safety_reviewer",
            "report_language_reviewer",
            "payment_billing_reviewer",
        ):
            self.assertIn(lane_id, profiles)
            profile = profiles[lane_id]
            self.assertEqual(profile["profile_status"], "missing_real_reviewer")
            self.assertEqual(profile["credential_status"], "missing")
            self.assertTrue(profile["required_credential_evidence"])
            self.assertTrue(profile["source_requirements"])
            self.assertFalse(profile["can_open_external_claim_gate"])
            self.assertFalse(profile["can_replace_customs_broker_legal_security_payment_approval"])

        self.assertIn("cbsa-licensed-customs-brokers", {row["source_id"] for row in profiles["customs_trade_reviewer"]["source_requirements"]})
        self.assertIn("owasp-file-upload", {row["source_id"] for row in profiles["security_upload_reviewer"]["source_requirements"]})
        self.assertIn("stripe-go-live", {row["source_id"] for row in profiles["payment_billing_reviewer"]["source_requirements"]})

    def test_review_requests_and_gate_impacts_do_not_open_claims(self) -> None:
        manifest = build_production_expert_review_network(ROOT)

        for request in manifest["review_requests"]:
            self.assertEqual(request["status"], "draft_ready_to_send_no_external_effect")
            self.assertEqual(request["scoped_review_link_status"], "token_required_not_sent")
            self.assertFalse(request["external_effects_created"])
            self.assertFalse(request["claims_opened"])
            self.assertTrue(request["questions"])
            self.assertTrue(request["claim_dependencies"])
            self.assertIn("tariff_confirmed", request["out_of_scope_claims"])

        for impact in manifest["gate_impacts"]:
            self.assertEqual(impact["impact_without_real_finding"], "claim_remains_blocked_or_reference_only")
            self.assertFalse(impact["can_show_after_local_request_only"])
            self.assertFalse(impact["can_open_external_claim_gate"])
            self.assertTrue(set(FORBIDDEN_EXTERNAL_CLAIMS).issubset(set(impact["forbidden_claims_remain_blocked"])))

    def test_finding_templates_are_scope_limited_and_require_attachments(self) -> None:
        manifest = build_production_expert_review_network(ROOT)

        for template in manifest["finding_templates"]:
            self.assertEqual(template["allowed_decisions"], list(REVIEW_DECISIONS))
            self.assertEqual(template["severity_levels"], list(SEVERITY_LEVELS))
            self.assertTrue(template["evidence_attachments_required"])
            self.assertIn("reviewer_credential_basis", template["required_fields"])
            self.assertIn("approved_scope", template["required_fields"])
            self.assertFalse(template["can_open_external_claim_gate"])
            self.assertTrue(template["can_update_only_scope_limited_wording"])

        for finding in manifest["pending_findings"]:
            self.assertEqual(finding["status"], "awaiting_real_reviewer_finding")
            self.assertEqual(finding["decision"], "not_submitted")
            self.assertFalse(finding["claims_opened"])
            self.assertFalse(finding["external_effects_created"])

    def test_writer_creates_manifest_profiles_requests_findings_and_doc(self) -> None:
        manifest = build_production_expert_review_network(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_expert_review_network_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_profiles = json.loads(paths["profiles"].read_text(encoding="utf-8"))
            written_requests = json.loads(paths["requests"].read_text(encoding="utf-8"))
            written_findings = json.loads(paths["findings"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_profiles["status"], "production_reviewer_profiles_credentials_required")
            self.assertEqual(written_requests["status"], "production_review_requests_ready_no_external_effects")
            self.assertEqual(written_findings["status"], "production_review_finding_contracts_ready_scope_limited")
            self.assertIn("Production Expert Review Network", written_doc)
            self.assertIn("Claims opened: false", written_doc)


if __name__ == "__main__":
    unittest.main()
