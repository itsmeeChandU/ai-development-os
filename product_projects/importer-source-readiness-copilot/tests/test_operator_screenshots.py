from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from importer_source_readiness import (
    build_screenshot_manifest,
    render_dashboard,
    write_screenshot_manifest,
)


SVG_SCREENSHOT = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#111820"/>
  <text x="32" y="64" fill="#f6faf9" font-size="28">Operator dashboard screenshot</text>
</svg>
"""


class OperatorScreenshotTests(unittest.TestCase):
    def test_manifest_discovers_operator_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            screenshot_dir = root / "system_review_graph" / "operator_screenshots"
            screenshot_dir.mkdir(parents=True)
            (screenshot_dir / "readiness-overview.svg").write_text(SVG_SCREENSHOT, encoding="utf-8")
            (screenshot_dir / "notes.txt").write_text("ignored", encoding="utf-8")

            manifest = build_screenshot_manifest(
                repo_root=root,
                screenshot_dir=screenshot_dir,
                generated_at="2026-06-25T00:00:00+00:00",
            )

            self.assertEqual(manifest["status"], "screenshots_ready")
            self.assertEqual(manifest["screenshot_count"], 1)
            row = manifest["screenshots"][0]
            self.assertEqual(row["artifact_path"], "system_review_graph/operator_screenshots/readiness-overview.svg")
            self.assertEqual(row["dashboard_src"], "operator_screenshots/readiness-overview.svg")
            self.assertEqual(row["media_type"], "image/svg+xml")
            self.assertEqual(row["width"], 640)
            self.assertEqual(row["height"], 400)
            self.assertIn("sha256", row)

    def test_manifest_writer_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            screenshot_dir = root / "system_review_graph" / "operator_screenshots"
            manifest = build_screenshot_manifest(repo_root=root, screenshot_dir=screenshot_dir)
            output = write_screenshot_manifest(
                manifest,
                root / "system_review_graph" / "operator_screenshot_manifest.json",
            )

            loaded = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(loaded["status"], "no_screenshots")
            self.assertEqual(loaded["screenshot_count"], 0)
            self.assertIn("proof_boundary", loaded)

    def test_dashboard_renders_screenshot_gallery(self) -> None:
        manifest = {
            "status": "screenshots_ready",
            "screenshot_count": 1,
            "proof_boundary": "Visual proof boundary.",
            "screenshots": [
                {
                    "title": "Readiness Overview",
                    "dashboard_src": "operator_screenshots/readiness-overview.svg",
                    "artifact_path": "system_review_graph/operator_screenshots/readiness-overview.svg",
                    "media_type": "image/svg+xml",
                    "size_bytes": 200,
                    "sha256": "abcdef1234567890",
                    "captured_at": "2026-06-25T00:00:00+00:00",
                    "claim_boundary": "Visual review aid only.",
                }
            ],
        }
        html = render_dashboard(
            {"status": "ready_with_external_gates", "row_count": 2, "blockers": []},
            {"status": "ready_with_external_gates", "blockers": [], "official_sources": []},
            screenshot_manifest=manifest,
        )

        self.assertIn("Operator Screenshots", html)
        self.assertIn("operator_screenshots/readiness-overview.svg", html)
        self.assertIn("Visual proof boundary.", html)


if __name__ == "__main__":
    unittest.main()
