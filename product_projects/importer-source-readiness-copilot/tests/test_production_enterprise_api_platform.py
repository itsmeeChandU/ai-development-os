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

from importer_source_readiness.production_enterprise_api_platform import (
    STATUS,
    build_production_enterprise_api_platform,
    write_production_enterprise_api_platform_artifacts,
)


class ProductionEnterpriseApiPlatformTests(unittest.TestCase):
    def test_manifest_has_enterprise_contracts_and_closed_gates(self) -> None:
        manifest = build_production_enterprise_api_platform(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertGreaterEqual(manifest["api_contract_count"], 17)
        self.assertEqual(manifest["research_reference_count"], 5)
        self.assertEqual(manifest["capability_count"], 12)
        self.assertTrue(manifest["all_required_api_routes_present"])
        self.assertGreaterEqual(manifest["workspace_control_count"], 3)
        self.assertGreaterEqual(manifest["api_key_record_count"], 2)
        self.assertGreaterEqual(manifest["webhook_record_count"], 2)
        self.assertFalse(manifest["hosted_enterprise_ready"])
        self.assertFalse(manifest["live_api_keys_issued"])
        self.assertFalse(manifest["webhook_delivery_enabled"])
        self.assertFalse(manifest["unrestricted_uploads_enabled"])
        self.assertFalse(manifest["white_label_claims_approved"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["external_effects_created"])

    def test_api_contracts_require_auth_tenant_claim_gate_and_no_live_effects(self) -> None:
        manifest = build_production_enterprise_api_platform(ROOT)
        paths = {row["path"]: row for row in manifest["api_contracts"]}

        for path in (
            "/api/packets",
            "/api/packets/:id",
            "/api/packets/:id/evidence",
            "/api/documents/upload",
            "/api/sources/refresh",
            "/api/packets/:id/scores",
            "/api/packets/:id/blocked-claims",
            "/api/reviews",
            "/api/reports",
            "/api/ai/safe-summary",
            "/api/api-keys",
            "/api/webhooks",
        ):
            self.assertIn(path, paths)
            self.assertTrue(paths[path]["route_present"])
            self.assertTrue(paths[path]["auth_required"])
            self.assertTrue(paths[path]["tenant_filter_required"])
            self.assertTrue(paths[path]["object_level_authorization_required"])
            self.assertTrue(paths[path]["claim_gate_required"])
            self.assertFalse(paths[path]["external_effects_created"])
            self.assertFalse(paths[path]["claims_opened"])
            self.assertFalse(paths[path]["live_mode_enabled"])

    def test_rbac_keys_webhooks_and_white_label_fail_closed(self) -> None:
        manifest = build_production_enterprise_api_platform(ROOT)

        for row in manifest["permission_matrix"]:
            self.assertTrue(row["deny_by_default"])
            self.assertFalse(row["cross_org_access_allowed"])

        for key in manifest["api_key_records"]:
            self.assertFalse(key["raw_secret_returned"])
            self.assertFalse(key["live_key_issued"])
            self.assertTrue(key["secret_storage_required"])

        for webhook in manifest["webhook_records"]:
            self.assertFalse(webhook["delivery_enabled"])
            self.assertFalse(webhook["external_effects_created"])
            self.assertTrue(webhook["signature_required"])

        white_label = manifest["white_label_policy"]
        self.assertIn("remove blocked claims", white_label["forbidden_customization"])
        self.assertTrue(white_label["report_language_review_required"])
        self.assertFalse(white_label["claims_opened"])

    def test_writer_creates_enterprise_api_artifacts(self) -> None:
        manifest = build_production_enterprise_api_platform(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_enterprise_api_platform_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            contracts = json.loads(paths["api_contracts"].read_text(encoding="utf-8"))
            rbac = json.loads(paths["rbac_policy"].read_text(encoding="utf-8"))
            webhooks = json.loads(paths["webhook_policy"].read_text(encoding="utf-8"))
            doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(contracts["status"], "production_enterprise_api_contracts_ready")
            self.assertEqual(rbac["status"], "production_enterprise_rbac_policy_ready")
            self.assertEqual(webhooks["status"], "production_enterprise_webhook_policy_ready_delivery_closed")
            self.assertIn("Production Enterprise API Platform", doc)
            self.assertIn("/api/packets", doc)


if __name__ == "__main__":
    unittest.main()
