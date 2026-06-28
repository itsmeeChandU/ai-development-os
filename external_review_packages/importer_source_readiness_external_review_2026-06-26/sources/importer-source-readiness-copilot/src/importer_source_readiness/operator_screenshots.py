"""Build an operator screenshot manifest from generated image artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}

MANIFEST_VERSION = 1
PROOF_BOUNDARY = (
    "Operator screenshots are visual evidence artifacts. They help review the "
    "current operator experience, but generated reports, blocker ledgers, tests, "
    "and human approval gates remain canonical for readiness claims."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(path: Path, root: Path) -> str:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"screenshot path escapes repo root: {path}") from exc
    return relative.as_posix()


def _svg_dimensions(text: str) -> dict[str, int | None]:
    tag_match = re.search(r"<svg\b[^>]*>", text, flags=re.IGNORECASE)
    if not tag_match:
        return {"width": None, "height": None}
    tag = tag_match.group(0)
    width_match = re.search(r'\bwidth=["\']?([0-9.]+)', tag, flags=re.IGNORECASE)
    height_match = re.search(r'\bheight=["\']?([0-9.]+)', tag, flags=re.IGNORECASE)
    if width_match and height_match:
        return {"width": int(float(width_match.group(1))), "height": int(float(height_match.group(1)))}
    view_box_match = re.search(
        r'\bviewBox=["\']\s*[-0-9.]+\s+[-0-9.]+\s+([0-9.]+)\s+([0-9.]+)',
        tag,
        flags=re.IGNORECASE,
    )
    if view_box_match:
        return {
            "width": int(float(view_box_match.group(1))),
            "height": int(float(view_box_match.group(2))),
        }
    return {"width": None, "height": None}


def _png_dimensions(data: bytes) -> dict[str, int | None]:
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return {"width": int.from_bytes(data[16:20], "big"), "height": int.from_bytes(data[20:24], "big")}
    return {"width": None, "height": None}


def _image_dimensions(path: Path, media_type: str) -> dict[str, int | None]:
    if media_type == "image/svg+xml":
        return _svg_dimensions(path.read_text(encoding="utf-8", errors="ignore"))
    if media_type == "image/png":
        return _png_dimensions(path.read_bytes()[:32])
    return {"width": None, "height": None}


def _title_from_path(path: Path) -> str:
    words = re.split(r"[-_\s]+", path.stem.strip())
    return " ".join(word.capitalize() for word in words if word) or path.name


def _screenshot_row(path: Path, *, repo_root: Path, dashboard_dir: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    media_type = ALLOWED_IMAGE_EXTENSIONS[suffix]
    artifact_path = _safe_relative(path, repo_root)
    dashboard_src = path.resolve().relative_to(dashboard_dir.resolve()).as_posix()
    stat = path.stat()
    dimensions = _image_dimensions(path, media_type)
    return {
        "id": f"operator-screenshot:{artifact_path}",
        "title": _title_from_path(path),
        "artifact_path": artifact_path,
        "dashboard_src": dashboard_src,
        "file_name": path.name,
        "media_type": media_type,
        "size_bytes": stat.st_size,
        "sha256": _sha256(path),
        "width": dimensions["width"],
        "height": dimensions["height"],
        "captured_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "operator",
        "source": "operator_generated_screenshot",
        "claim_boundary": "Visual review aid only; generated JSON reports and blocker ledgers remain readiness truth.",
    }


def build_screenshot_manifest(
    *,
    repo_root: Path,
    screenshot_dir: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Create a manifest for operator-generated screenshots under ``screenshot_dir``."""

    repo_root = repo_root.resolve()
    screenshot_dir = screenshot_dir.resolve()
    _safe_relative(screenshot_dir, repo_root)
    dashboard_dir = repo_root / "system_review_graph"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    screenshots = [
        _screenshot_row(path, repo_root=repo_root, dashboard_dir=dashboard_dir)
        for path in sorted(screenshot_dir.iterdir())
        if path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS
    ]
    status = "screenshots_ready" if screenshots else "no_screenshots"
    return {
        "version": MANIFEST_VERSION,
        "generated_at": generated_at or _utc_now(),
        "status": status,
        "screenshot_count": len(screenshots),
        "screenshot_dir": _safe_relative(screenshot_dir, repo_root),
        "allowed_media_types": sorted(set(ALLOWED_IMAGE_EXTENSIONS.values())),
        "screenshots": screenshots,
        "proof_boundary": PROOF_BOUNDARY,
        "next_valid_move": (
            "Review the screenshot cards in system_review_graph/operator_dashboard.html."
            if screenshots
            else "Generate operator screenshots into system_review_graph/operator_screenshots and rerun the product check."
        ),
    }


def write_screenshot_manifest(manifest: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
