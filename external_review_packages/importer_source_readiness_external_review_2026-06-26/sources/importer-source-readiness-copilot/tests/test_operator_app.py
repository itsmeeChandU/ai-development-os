from __future__ import annotations

import json
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

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


if __name__ == "__main__":
    unittest.main()
