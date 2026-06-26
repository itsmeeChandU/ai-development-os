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

    def test_home_serves_operator_dashboard(self) -> None:
        with urlopen(f"{self.base_url}/", timeout=5) as response:
            html = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn("Importer Source Readiness Copilot", html)
        self.assertIn("Operator Work Queue", html)

    def test_api_index_declares_operator_surface(self) -> None:
        with urlopen(f"{self.base_url}/api", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(payload["surface"], "local_operator_application")
        self.assertEqual(payload["operator_status"], "operator_workflow_ready_internal")
        self.assertEqual(payload["operator_display_status"], "Operator workbench usable for internal review")
        self.assertEqual(payload["customer_workflow_status"], "customer_workflow_ready_internal")
        self.assertEqual(payload["customer_stage_status"], "Customer packet prototype active - real customer use not enabled")
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
        with urlopen(f"{self.base_url}/source-packets", timeout=5) as response:
            listing = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("Customer Source Packet", listing)
        self.assertIn("Internal logic ready - external claims blocked", listing)
        self.assertIn("Blocked - source freshness missing", listing)

        packet_url = f"{self.base_url}/source-packets/packet-frozen-tuna-canada-001/readiness-report"
        with urlopen(packet_url, timeout=5) as response:
            report = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("Readiness Report", report)
        self.assertIn("Tariff/HS classification", report)
        self.assertIn("Missing Evidence", report)
        self.assertNotIn("safe_to_import", report)

    def test_customer_source_packet_guided_pages_exist(self) -> None:
        routes = {
            "/source-packets/packet-frozen-tuna-canada-001": "Refresh Official Sources",
            "/source-packets/packet-frozen-tuna-canada-001/evidence": "Upload Evidence",
            "/source-packets/packet-frozen-tuna-canada-001/blockers": "Resolve",
            "/source-packets/packet-frozen-tuna-canada-001/expert-review-packet": "Questions For Reviewer",
            "/admin/sources": "Official Source Registry",
            "/admin/gates": "Private Beta Gates",
        }
        for path, expected in routes.items():
            with self.subTest(path=path):
                with urlopen(f"{self.base_url}{path}", timeout=5) as response:
                    body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn(expected, body)

    def test_customer_source_packet_post_creates_local_readiness_report(self) -> None:
        generated_paths = [
            ROOT / "system_review_graph" / "customer_source_packets.json",
            ROOT / "system_review_graph" / "evidence_ledger.json",
            ROOT / "system_review_graph" / "customer_readiness_report.json",
            ROOT / "system_review_graph" / "customer_readiness_report.md",
            ROOT / "system_review_graph" / "customer_ai_review_runs.json",
            ROOT / "system_review_graph" / "customer_workflow.sqlite",
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
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/source-packets",
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
                "/source-packets/packet-local-test-product/readiness-report",
                ctx.exception.headers["Location"],
            )
        finally:
            for path, content in backups.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)


if __name__ == "__main__":
    unittest.main()
