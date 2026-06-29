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

from importer_source_readiness.production_api_service import (
    STATUS,
    build_production_api_service,
    dispatch_production_api_request,
    write_production_api_service_artifacts,
)
from importer_source_readiness.production_repository import DEFAULT_PACKET_ID


class ProductionApiServiceTests(unittest.TestCase):
    def test_customer_can_read_own_packet_from_repository(self) -> None:
        response = dispatch_production_api_request(
            ROOT,
            "GET",
            f"/api/packets/{DEFAULT_PACKET_ID}",
            session_token="customer-session",
        )

        self.assertEqual(response["status_code"], 200)
        self.assertEqual(response["status"], "ok_repository_packet_context")
        self.assertEqual(response["data"]["status"], "packet_context_ready_from_production_repository")
        self.assertEqual(response["data"]["safe_claim_count"], 7)
        self.assertFalse(response["external_effects_created"])
        self.assertFalse(response["claims_opened"])

    def test_tenant_auth_and_unknown_routes_fail_closed(self) -> None:
        wrong_org = dispatch_production_api_request(
            ROOT,
            "GET",
            f"/api/packets/{DEFAULT_PACKET_ID}",
            session_token="other-customer-session",
        )
        anonymous = dispatch_production_api_request(ROOT, "GET", f"/api/packets/{DEFAULT_PACKET_ID}")
        missing = dispatch_production_api_request(
            ROOT,
            "GET",
            f"/api/packets/{DEFAULT_PACKET_ID}/claims/tariff_confirmed",
            session_token="customer-session",
        )

        self.assertEqual(wrong_org["status_code"], 403)
        self.assertEqual(wrong_org["status"], "access_denied")
        self.assertEqual(anonymous["status_code"], 401)
        self.assertEqual(anonymous["status"], "authentication_required")
        self.assertEqual(missing["status_code"], 404)
        self.assertEqual(missing["status"], "route_not_registered")
        self.assertFalse(wrong_org["external_effects_created"])
        self.assertFalse(missing["claims_opened"])

    def test_safe_reports_scores_and_ai_summary_are_read_only(self) -> None:
        scores = dispatch_production_api_request(
            ROOT,
            "GET",
            f"/api/packets/{DEFAULT_PACKET_ID}/scores",
            session_token="customer-session",
        )
        blocked = dispatch_production_api_request(
            ROOT,
            "GET",
            f"/api/packets/{DEFAULT_PACKET_ID}/blocked-claims",
            session_token="customer-session",
        )
        report = dispatch_production_api_request(
            ROOT,
            "POST",
            "/api/reports",
            session_token="customer-session",
            body={"packet_id": DEFAULT_PACKET_ID},
        )
        summary = dispatch_production_api_request(
            ROOT,
            "POST",
            "/api/ai/safe-summary",
            session_token="customer-session",
            body={"packet_id": DEFAULT_PACKET_ID},
        )

        self.assertEqual(scores["status"], "ok_repository_scores")
        self.assertFalse(scores["data"]["single_global_score"])
        self.assertEqual(blocked["status"], "ok_repository_blocked_claims")
        self.assertGreaterEqual(len(blocked["data"]["blocked_claims"]), 10)
        self.assertEqual(report["status"], "ok_repository_report_context_no_write")
        self.assertFalse(report["report_written"])
        self.assertEqual(summary["status"], "ok_safe_summary_no_live_model_call")
        self.assertFalse(summary["data"]["live_model_call_made"])
        self.assertFalse(summary["claims_opened"])

    def test_effectful_routes_remain_closed(self) -> None:
        for method, path in (
            ("POST", "/api/packets"),
            ("POST", f"/api/packets/{DEFAULT_PACKET_ID}/evidence"),
            ("POST", "/api/documents/upload"),
            ("POST", "/api/sources/refresh"),
            ("POST", "/api/reviews"),
            ("POST", "/api/api-keys"),
            ("POST", "/api/webhooks"),
        ):
            with self.subTest(path=path):
                response = dispatch_production_api_request(
                    ROOT,
                    method,
                    path,
                    session_token="customer-session",
                    body={"packet_id": DEFAULT_PACKET_ID},
                )
                self.assertIn(response["status_code"], {403, 423})
                self.assertIn(response["status"], {"permission_denied", "effect_gate_closed"})
                self.assertFalse(response["external_effects_created"])
                self.assertFalse(response["claims_opened"])

    def test_manifest_and_writer_capture_service_proof(self) -> None:
        payload = build_production_api_service(ROOT)

        self.assertEqual(payload["status"], STATUS)
        self.assertGreaterEqual(payload["simulated_request_count"], 10)
        self.assertGreaterEqual(payload["safe_read_success_count"], 5)
        self.assertGreaterEqual(payload["tenant_denial_count"], 1)
        self.assertGreaterEqual(payload["unauthenticated_denial_count"], 1)
        self.assertGreaterEqual(payload["effect_gate_closed_count"], 3)
        self.assertFalse(payload["hosted_api_ready"])
        self.assertFalse(payload["claims_opened"])
        self.assertFalse(payload["external_effects_created"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_api_service_artifacts(payload, root)
            for path in paths.values():
                self.assertTrue(path.exists())

            manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            samples = json.loads(paths["sample_responses"].read_text(encoding="utf-8"))
            doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(manifest["status"], STATUS)
            self.assertEqual(samples["status"], "production_api_service_sample_responses_ready")
            self.assertIn("Production API Service", doc)
            self.assertIn("effectful routes", doc)


if __name__ == "__main__":
    unittest.main()
