"""Local operator web app for Importer Source Readiness Copilot."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


API_ROUTES = {
    "/api/readiness": "system_review_graph/readiness_report.json",
    "/api/external-gates": "system_review_graph/external_gate_report.json",
    "/api/continuation": "system_review_graph/continuation_plan.json",
    "/api/vc-pitch": "system_review_graph/vc_pitch_readiness_report.json",
    "/api/board-go-live": "system_review_graph/board_go_live_readiness_report.json",
    "/api/operator-workflow": "system_review_graph/operator_workflow_report.json",
    "/api/operator-screenshots": "system_review_graph/operator_screenshot_manifest.json",
}

STATIC_ROUTES = {
    "/": "system_review_graph/operator_dashboard.html",
    "/dashboard": "system_review_graph/operator_dashboard.html",
    "/operator_dashboard.html": "system_review_graph/operator_dashboard.html",
}


def _safe_join(root: Path, relative_path: str) -> Path | None:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_payload(repo_root: Path) -> dict[str, Any]:
    workflow = _load_json(repo_root / "system_review_graph" / "operator_workflow_report.json")
    continuation = _load_json(repo_root / "system_review_graph" / "continuation_plan.json")
    board = _load_json(repo_root / "system_review_graph" / "board_go_live_readiness_report.json")
    return {
        "product": "Importer Source Readiness Copilot",
        "surface": "local_operator_application",
        "operator_status": workflow.get("status"),
        "operator_can_use_now": workflow.get("operator_can_use_now"),
        "work_queue_count": workflow.get("work_queue_count"),
        "startup_status": continuation.get("status"),
        "board_status": board.get("status"),
        "allowed_use": workflow.get("allowed_use"),
        "not_allowed_use": workflow.get("not_allowed_use", []),
        "routes": sorted([*API_ROUTES, *STATIC_ROUTES]),
        "proof_boundary": (
            "This local app is the internal operator surface. It is not a public "
            "customer app, customs/tariff advice, supplier recommendation, legal "
            "or financial advice, or launch approval."
        ),
    }


def build_operator_app_handler(repo_root: Path) -> type[BaseHTTPRequestHandler]:
    repo_root = repo_root.resolve()

    class OperatorAppHandler(BaseHTTPRequestHandler):
        server_version = "ImporterSourceReadinessOperatorApp/0.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = unquote(parsed.path)

            if path == "/api":
                self._send_json(_index_payload(repo_root))
                return
            if path in API_ROUTES:
                self._send_file(API_ROUTES[path], "application/json; charset=utf-8")
                return
            if path in STATIC_ROUTES:
                self._send_file(STATIC_ROUTES[path], "text/html; charset=utf-8")
                return
            if path.startswith("/operator_screenshots/"):
                self._send_file(f"system_review_graph{path}", None)
                return
            if path.startswith("/system_review_graph/"):
                self._send_file(path.lstrip("/"), None)
                return

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown operator app route")

        def _send_json(self, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_file(self, relative_path: str, content_type: str | None) -> None:
            path = _safe_join(repo_root, relative_path)
            if path is None or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Artifact not found")
                return
            data = path.read_bytes()
            guessed_type = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", guessed_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

    return OperatorAppHandler


def make_server(repo_root: Path, host: str, port: int) -> ThreadingHTTPServer:
    handler = build_operator_app_handler(repo_root)
    return ThreadingHTTPServer((host, port), handler)
