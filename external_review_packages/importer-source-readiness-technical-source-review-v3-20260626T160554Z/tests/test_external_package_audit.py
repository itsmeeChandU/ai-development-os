from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "audit_external_package.py"
spec = importlib.util.spec_from_file_location("audit_external_package", SCRIPT)
assert spec and spec.loader
audit_external_package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_external_package)


class ExternalPackageAuditTests(unittest.TestCase):
    def test_repo_audit_passes_for_current_tree(self) -> None:
        errors = audit_external_package.audit_root(ROOT)

        self.assertEqual(errors, [])

    def test_zip_audit_blocks_traversal_and_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("../escape.txt", "bad")
                archive.writestr("docs/local.md", "see /" + "Users/chandu/private")

            errors = audit_external_package.audit_zip(zip_path)

        self.assertTrue(any("path traversal" in error for error in errors))
        self.assertTrue(any("local path reference" in error for error in errors))

    def test_zip_audit_blocks_secret_like_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "secret.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("config/example.md", "token " + "sk-" + "test_abcdefghijklmnopqrstuvwxyz")

            errors = audit_external_package.audit_zip(zip_path)

        self.assertTrue(any("secret-like token" in error for error in errors))

    def test_zip_audit_allows_local_path_examples_only_in_audit_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "examples.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("REDACTION_REPORT.md", "blocked example /" + "Users/chandu/private")
                archive.writestr("PACKAGE_AUDIT.md", "blocked example file:///" + "Users/chandu/private")
                archive.writestr("docs/process.md", "safe text")

            errors = audit_external_package.audit_zip(zip_path)

        self.assertFalse(any("local path reference" in error for error in errors))

    def test_zip_audit_blocks_local_paths_outside_audit_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "bad-example.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("docs/process.md", "blocked example /" + "Users/chandu/private")

            errors = audit_external_package.audit_zip(zip_path)

        self.assertTrue(any("local path reference" in error for error in errors))

    def test_root_audit_reports_missing_required_review_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            errors = audit_external_package.audit_root(Path(tmp))

        self.assertTrue(any("missing required review artifact" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
