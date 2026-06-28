#!/usr/bin/env python3
"""Audit review-package hygiene for local paths, traversal, and required docs."""

from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_PATH_PATTERNS = [
    re.compile("/" + "Users" + r"/[^\s'\"<>\x60]+"),
    re.compile("file:///" + "Users" + r"/[^\s'\"<>\x60]+"),
]
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE),
]
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}
SKIP_FILES = {
    "handoffs/product_completion_handoff.md",
    "system_review_graph/internal_repo_intake_packet.json",
    "system_review_graph/internal_repo_intake_packet.md",
    "system_review_graph/lane_packet_workflow-coordinator.json",
    "system_review_graph/lane_packet_workflow-coordinator.md",
    "system_review_graph/prompt_to_product_packet.json",
    "system_review_graph/prompt_to_product_packet.md",
}
TEXT_SUFFIXES = {
    ".csv",
    ".html",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
REQUIRED_FILES = [
    "SOURCE_OF_TRUTH.md",
    "RUN_RESULTS.md",
    "REDACTION_REPORT.md",
    "REVIEW_USE_TERMS.md",
    "OFFLINE_REPRODUCTION.md",
    "PACKAGE_AUDIT.md",
    "system_review_graph/readiness_report.json",
    "system_review_graph/customer_readiness_report.json",
    "system_review_graph/evidence_ledger.json",
    "system_review_graph/operator_workflow_report.json",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def _check_text(name: str, text: str) -> list[str]:
    errors = []
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            errors.append(f"{name}: local path reference found")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"{name}: obvious secret-like token found")
    return errors


def audit_root(root: Path) -> list[str]:
    errors: list[str] = []
    for required in REQUIRED_FILES:
        if not (root / required).exists():
            errors.append(f"missing required review artifact: {required}")
    for path in _iter_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in SKIP_FILES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        errors.extend(_check_text(str(path.relative_to(root)), text))
    return errors


def audit_zip(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.filename
            parts = Path(name).parts
            if name.startswith("/") or ".." in parts:
                errors.append(f"{name}: path traversal entry")
            if Path(name).suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                text = archive.read(info).decode("utf-8")
            except UnicodeDecodeError:
                continue
            errors.extend(_check_text(name, text))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit external review package hygiene.")
    parser.add_argument("--root", default="", help="Directory to audit")
    parser.add_argument("--zip", default="", help="Zip file to audit")
    args = parser.parse_args()

    errors: list[str] = []
    audited = []
    if args.root:
        root = Path(args.root).resolve()
        errors.extend(audit_root(root))
        audited.append(str(root))
    if args.zip:
        zip_path = Path(args.zip).resolve()
        errors.extend(audit_zip(zip_path))
        audited.append(f"{zip_path} sha256={_sha256(zip_path)}")
    if not args.root and not args.zip:
        errors.extend(audit_root(ROOT))
        audited.append(str(ROOT))

    if errors:
        print("External package audit: FAIL")
        for error in errors:
            print(error)
        return 1
    print("External package audit: PASS")
    for item in audited:
        print(f"audited={item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
