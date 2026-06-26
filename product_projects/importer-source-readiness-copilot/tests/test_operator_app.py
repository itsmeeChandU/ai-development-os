from __future__ import annotations

import json
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.operator_app import make_server


MUTABLE_GENERATED_PATHS = [
    ROOT / "system_review_graph" / "customer_source_packets.json",
    ROOT / "system_review_graph" / "evidence_ledger.json",
    ROOT / "system_review_graph" / "customer_readiness_report.json",
    ROOT / "system_review_graph" / "customer_readiness_report.md",
    ROOT / "system_review_graph" / "customer_ai_review_runs.json",
    ROOT / "system_review_graph" / "customer_workflow.sqlite",
    ROOT / "system_review_graph" / "product_runtime_state.json",
    ROOT / "system_review_graph" / "auth_rbac_matrix.json",
    ROOT / "system_review_graph" / "claims_gate_matrix.json",
    ROOT / "system_review_graph" / "review_requests.json",
    ROOT / "system_review_graph" / "report_exports.json",
    ROOT / "system_review_graph" / "audit_events.json",
    ROOT / "system_review_graph" / "deletion_requests.json",
    ROOT / "system_review_graph" / "deployment_readiness_report.json",
    ROOT / "system_review_graph" / "private_beta_readiness_checklist.json",
    ROOT / "system_review_graph" / "ai_data_policy.json",
    ROOT / "system_review_graph" / "model_endpoints.json",
    ROOT / "system_review_graph" / "ai_model_router.json",
    ROOT / "system_review_graph" / "redaction_pipeline.json",
    ROOT / "system_review_graph" / "manual_no_ai_workflow.json",
    ROOT / "system_review_graph" / "requirements_traceability_matrix.json",
    ROOT / "system_review_graph" / "customer_action_log.json",
]


class OperatorAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(ROOT, "127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_home_serves_customer_landing(self) -> None:
        with urlopen(f"{self.base_url}/", timeout=5) as response:
            html = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn("Importer Source Readiness Copilot", html)
        self.assertIn("Know what is missing", html)
        self.assertIn("Create source packet", html)

    def test_operator_route_serves_operator_dashboard(self) -> None:
        with urlopen(f"{self.base_url}/operator", timeout=5) as response:
            html = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn("Operator Work Queue", html)

    def test_api_index_declares_operator_surface(self) -> None:
        with urlopen(f"{self.base_url}/api", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(payload["surface"], "local_customer_operator_expert_application")
        self.assertEqual(payload["runtime_status"], "private_beta_candidate_with_external_human_gates")
        self.assertEqual(payload["operator_status"], "operator_workflow_ready_internal")
        self.assertEqual(payload["operator_display_status"], "Operator workbench usable for internal review")
        self.assertEqual(payload["customer_workflow_status"], "customer_workflow_ready_internal")
        self.assertEqual(payload["customer_stage_status"], "Customer packet prototype active - real customer use not enabled")
        self.assertIn("local session auth", payload["auth_status"])
        self.assertIn("/review/:token", payload["routes"])
        self.assertGreaterEqual(payload["customer_packet_count"], 1)
        self.assertFalse("public_launch_claim" in payload["allowed_use"])

    def test_api_operator_workflow_returns_queue(self) -> None:
        with urlopen(f"{self.base_url}/api/operator-workflow", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(payload["status"], "operator_workflow_ready_internal")
        self.assertGreaterEqual(payload["work_queue_count"], 20)

    def test_unknown_route_404s(self) -> None:
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"{self.base_url}/../../pyproject.toml", timeout=5)

        self.assertEqual(ctx.exception.code, 404)

    def test_route_specific_artifact_roots_block_traversal(self) -> None:
        blocked_paths = [
            "/system_review_graph/../README.md",
            "/system_review_graph/%2e%2e/README.md",
            "/operator_screenshots/../readiness_report.json",
            "/operator_screenshots/%2e%2e/readiness_report.json",
        ]
        for path in blocked_paths:
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as ctx:
                    urlopen(f"{self.base_url}{path}", timeout=5)
                self.assertIn(ctx.exception.code, {403, 404})

    def test_customer_source_packet_routes_render_safe_report(self) -> None:
        with urlopen(f"{self.base_url}/packets", timeout=5) as response:
            listing = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("Customer Source Packet", listing)
        self.assertIn("Internal logic ready - external claims blocked", listing)
        self.assertIn("Blocked - source freshness missing", listing)

        packet_url = f"{self.base_url}/packets/packet-frozen-tuna-canada-001/readiness"
        with urlopen(packet_url, timeout=5) as response:
            report = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("Readiness Report", report)
        self.assertIn("Tariff/HS classification", report)
        self.assertIn("Missing Evidence", report)
        self.assertNotIn("safe_to_import", report)

    def test_customer_source_packet_guided_pages_exist(self) -> None:
        routes = {
            "/packets/packet-frozen-tuna-canada-001": "Refresh Official Sources",
            "/packets/packet-frozen-tuna-canada-001/evidence": "AI processing mode",
            "/packets/packet-frozen-tuna-canada-001/blockers": "Resolve",
            "/packets/packet-frozen-tuna-canada-001/ai-reviews": "AI simulated reviews",
            "/packets/packet-frozen-tuna-canada-001/reviews": "Scoped review link",
            "/packets/packet-frozen-tuna-canada-001/reports": "Reports",
            "/settings/ai-data-policy": "Requirement Traceability",
            "/privacy": "Privacy Notice",
            "/terms": "Terms",
            "/ai-use": "AI Use",
            "/data-retention": "Data Retention",
            "/review/review-token-packet-frozen-tuna-canada-001": "Out Of Scope",
            "/admin/sources": "Official Source Registry",
            "/admin/gates": "Private Beta Gates",
            "/admin/audit": "Audit",
            "/admin/system-health": "System Health",
        }
        for path, expected in routes.items():
            with self.subTest(path=path):
                with urlopen(f"{self.base_url}{path}", timeout=5) as response:
                    body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn(expected, body)

    def test_customer_source_packet_export_includes_gate_context(self) -> None:
        path = "/packets/packet-frozen-tuna-canada-001/export"
        with urlopen(f"{self.base_url}{path}", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["packet_id"], "packet-frozen-tuna-canada-001")
        self.assertEqual(
            payload["customer_stage_status"],
            "Customer packet prototype active - real customer use not enabled",
        )
        self.assertEqual(payload["private_beta_status"], "blocked")
        self.assertGreaterEqual(len(payload["blocker_groups"]), 4)
        self.assertEqual(payload["private_beta_readiness"]["status"], "blocked")
        self.assertGreaterEqual(len(payload["private_beta_readiness"]["blocked"]), 4)
        self.assertIn("Customer packet prototype", payload["private_beta_readiness"]["ready"])
        self.assertGreaterEqual(len(payload["ai_review_runs"]), 1)
        self.assertIn("Tariff/HS classification", payload["blocked_claims"])

    def test_customer_source_packet_post_creates_local_readiness_report(self) -> None:
        generated_paths = [
            *MUTABLE_GENERATED_PATHS,
            ROOT / "system_review_graph" / "expert_review_packet_packet-local-test-product.md",
        ]
        backups = {path: path.read_bytes() if path.exists() else None for path in generated_paths}
        body = urlencode(
            {
                "packet_name": "Local test packet",
                "product_name": "Local test product",
                "product_category": "food_import",
                "origin_country": "Mexico",
                "destination_country": "Canada",
                "supplier_name": "Local Supplier",
                "supplier_country": "Mexico",
                "source_url": "https://example.com/source",
                "intended_use": "Local source readiness review",
                "csrf_token": "local-dev-csrf-token",
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/packets",
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
                return None

        try:
            opener = build_opener(NoRedirect)
            with self.assertRaises(HTTPError) as ctx:
                opener.open(request, timeout=5)
            self.assertEqual(ctx.exception.code, 303)
            self.assertIn(
                "/packets/packet-local-test-product/readiness",
                ctx.exception.headers["Location"],
            )
        finally:
            for path, content in backups.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)

    def test_ai_policy_api_and_permission_patch_work(self) -> None:
        backups = {path: path.read_bytes() if path.exists() else None for path in MUTABLE_GENERATED_PATHS}
        try:
            with urlopen(f"{self.base_url}/api/orgs/current/ai-policy", timeout=5) as response:
                policy = json.loads(response.read().decode("utf-8"))
            self.assertEqual(policy["policy"]["default_mode"], "redacted")
            self.assertEqual(policy["router"]["status"], "ai_model_router_ready")

            endpoint_body = urlencode({"mode": "metadata_only"}).encode("utf-8")
            endpoint_request = Request(
                f"{self.base_url}/api/orgs/current/ai-policy/test-model-endpoint",
                data=endpoint_body,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urlopen(endpoint_request, timeout=5) as response:
                endpoint = json.loads(response.read().decode("utf-8"))
            self.assertEqual(endpoint["status"], "endpoint_contract_ready")
            self.assertFalse(endpoint["live_call_made"])

            patch_body = urlencode({"ai_processing_mode": "no_ai", "sensitivity_level": "confidential"}).encode("utf-8")
            patch_request = Request(
                f"{self.base_url}/api/evidence/evidence-frozen-tuna-cid-reference/ai-permission",
                data=patch_body,
                method="PATCH",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urlopen(patch_request, timeout=5) as response:
                patched = json.loads(response.read().decode("utf-8"))
            self.assertEqual(patched["status"], "ai_permission_updated")
            self.assertEqual(patched["evidence"]["ai_processing_mode"], "no_ai")
            self.assertFalse(patched["route_decision"]["allowed"])
            self.assertEqual(patched["route_decision"]["mode"], "no_ai")
        finally:
            for path, content in backups.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)

    def test_rbac_blocks_cross_org_packet_access(self) -> None:
        request = Request(
            f"{self.base_url}/api/packets/packet-frozen-tuna-canada-001",
            headers={"X-ISR-Session": "other-customer-session"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=5)
        self.assertEqual(ctx.exception.code, 403)

    def test_api_supports_auth_health_and_scoped_review(self) -> None:
        with urlopen(f"{self.base_url}/healthz", timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
        self.assertEqual(health["status"], "ok")

        login_body = urlencode({"email": "operator@example.local"}).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/auth/login",
            data=login_body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertTrue(payload["authenticated"])
        self.assertIn("isr_session=operator-session", response.headers["Set-Cookie"])

        with urlopen(f"{self.base_url}/api/external-review/review-token-packet-frozen-tuna-canada-001", timeout=5) as response:
            review = json.loads(response.read().decode("utf-8"))
        self.assertEqual(review["review_request"]["packet_id"], "packet-frozen-tuna-canada-001")


if __name__ == "__main__":
    unittest.main()
