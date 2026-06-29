#!/usr/bin/env python3
"""Build executive and technical external-review packages."""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.final_go_live import write_final_go_live_artifacts
from importer_source_readiness.external_validation_research import write_external_validation_requirements
from importer_source_readiness.production_market_readiness_evidence_room import (
    build_production_market_readiness_evidence_room,
    write_production_market_readiness_evidence_room_artifacts,
)

EXECUTIVE_FILES = [
    "START_HERE.md",
    "WHAT_WE_ARE_BUILDING.md",
    "CURRENT_SLICE_VS_TARGET_PRODUCT.md",
    "FINAL_GO_LIVE_HANDOFF.md",
    "README.md",
    "SOURCE_OF_TRUTH.md",
    "SOURCE_OF_TRUTH_CURRENT.md",
    "RUN_RESULTS.md",
    "REVIEW_USE_TERMS.md",
    "REDACTION_REPORT.md",
    "PACKAGE_AUDIT.md",
    "OFFLINE_REPRODUCTION.md",
    "EXTERNAL_REVIEW_SUMMARY.md",
    "docs/GO_LIVE_READINESS.md",
    "docs/PRODUCT_STATUS.md",
    "docs/PUBLIC_TRADE_READINESS.md",
    "docs/SECURITY_PRIVACY.md",
    "docs/AI_DATA_POLICY.md",
    "docs/DOCUMENT_PROCESSING.md",
    "docs/DEPLOYMENT.md",
    "docs/EXTERNAL_REVIEW_PROCESS.md",
    "docs/EXTERNAL_VALIDATION_REQUIREMENTS.md",
    "docs/EXTERNAL_VALIDATION_REVIEWER_BRIEF.md",
    "docs/GO_LIVE_INPUT_REQUESTS.md",
    "docs/GO_LIVE_RETURNED_INPUT_EVIDENCE.md",
    "system_review_graph/final_go_live_decision_report.json",
    "system_review_graph/current_external_gate_research.json",
    "system_review_graph/external_validation_requirements_report.json",
    "system_review_graph/external_validation_evidence_requirements.json",
    "system_review_graph/go_live_input_templates.json",
    "system_review_graph/go_live_input_readiness_report.json",
    "system_review_graph/go_live_returned_input_evidence_manifest.json",
    "system_review_graph/go_live_returned_input_validation_matrix.json",
    "system_review_graph/production_market_readiness_evidence_room_manifest.json",
    "system_review_graph/production_market_readiness_input_ledger.json",
    "system_review_graph/production_market_readiness_input_history.json",
    "system_review_graph/reviewer_wave_execution_plan.json",
    "system_review_graph/private_beta_smoke_test_plan.json",
    "system_review_graph/all_stage_readiness_report.json",
    "system_review_graph/private_beta_readiness_checklist.json",
    "system_review_graph/deployment_readiness_report.json",
    "system_review_graph/external_review_findings_report.json",
    "system_review_graph/external_review_blocker_ledger.jsonl",
    "system_review_graph/ai_assisted_external_review_plan.json",
    "system_review_graph/ai_assisted_external_review_findings_report.json",
    "system_review_graph/public_trade_readiness_manifest.json",
    "system_review_graph/public_upload_policy.json",
    "system_review_graph/claims_gate_matrix.json",
    "system_review_graph/customer_readiness_report.json",
    "system_review_graph/evidence_ledger.json",
    "system_review_graph/operator_workflow_report.json",
    "system_review_graph/product_runtime_state.json",
    "system_review_graph/expert_review_packet_packet-frozen-tuna-canada-001.md",
    "system_review_graph/ui_ux_audit_report.json",
    "system_review_graph/ui_ux_audit_report.md",
    "external_review_findings/EXTERNAL_REVIEW_SUMMARY.json",
    "external_review_findings/README.md",
    "reviewer_packets/README.md",
    "ai_assisted_review/README.md",
    "ai_assisted_review/AI_ASSISTED_REVIEW_SUMMARY.md",
    "ai_assisted_review/WEB_RESEARCH_SOURCE_LOG.md",
    "board/expert_review_packet.md",
    "board/launch_control_checklist.md",
    "board/board_go_live_brief.md",
    "output/pdf/external_validation_requirements.pdf",
    "output/pdf/external_validation_reviewer_brief.pdf",
    "output/pdf/go_live_input_requests.pdf",
]

TECHNICAL_DIRS = [
    "src",
    "tests",
    "scripts",
    "docs",
    "data",
    "external_review_findings",
    "reviewer_packets",
    "ai_assisted_review",
    "system_review_graph/generated_reports",
]

TECHNICAL_FILES = [
    *EXECUTIVE_FILES,
    "AGENTS.md",
    "pyproject.toml",
    "Dockerfile",
    "compose.yaml",
    ".env.example",
    "CUSTOMER_SOURCE_PACKET_SPEC.md",
    "SOURCE_OF_TRUTH.md",
    "SOURCE_OF_TRUTH_CURRENT.md",
    "RUN_RESULTS.md",
    "PACKAGE_AUDIT.md",
    "OFFLINE_REPRODUCTION.md",
    "REVIEW_USE_TERMS.md",
    "system_review_graph/readiness_report.json",
    "system_review_graph/external_gate_report.json",
    "system_review_graph/continuation_plan.json",
    "system_review_graph/board_go_live_readiness_report.json",
    "system_review_graph/vc_pitch_readiness_report.json",
    "system_review_graph/requirements_traceability_matrix.json",
    "system_review_graph/public_report_types.json",
    "system_review_graph/billing_credit_controls.json",
    "system_review_graph/billing_usage_ledger.json",
    "system_review_graph/agent_api_manifest.json",
    "system_review_graph/agent_api_gateway_contract.json",
    "system_review_graph/transport_readiness_report.json",
    "system_review_graph/country_coverage_report.json",
    "system_review_graph/opportunity_scanner_report.json",
    "system_review_graph/production_data_model_manifest.json",
    "system_review_graph/production_packet_engine_manifest.json",
    "system_review_graph/production_persistence_snapshot.json",
    "system_review_graph/production_persistence_row_counts.json",
    "system_review_graph/production_repository_service_manifest.json",
    "system_review_graph/production_repository_packet_context_packet-frozen-tuna-canada-001.json",
    "system_review_graph/production_repository_report_context_packet-frozen-tuna-canada-001.json",
    "system_review_graph/production_api_service_manifest.json",
    "system_review_graph/production_api_service_sample_responses.json",
    "system_review_graph/production_country_source_engine_manifest.json",
    "system_review_graph/production_source_lifecycle.json",
    "system_review_graph/production_source_snapshot_history.json",
    "system_review_graph/production_source_refresh_audit_events.json",
    "system_review_graph/production_claim_gate_decisions.json",
    "system_review_graph/production_decision_score_records.json",
    "system_review_graph/production_report_exports.json",
]

EXCLUDE_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "public_uploads",
}

EXCLUDE_SUFFIXES = {".pyc", ".sqlite", ".zip"}


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_existing(paths: list[str], root: Path) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for item in paths:
        path = root / item
        if path.is_file() and path not in seen:
            files.append(path)
            seen.add(path)
    return files


def _iter_dir_files(dirs: list[str], root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for dirname in dirs:
        base = root / dirname
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            if any(part in EXCLUDE_PARTS for part in rel.parts):
                continue
            if path.suffix in EXCLUDE_SUFFIXES:
                continue
            if path not in seen:
                files.append(path)
                seen.add(path)
    return files


def write_package(zip_path: Path, files: list[Path], root: Path, package_root: str) -> dict[str, str]:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            rel = path.relative_to(root).as_posix()
            archive.write(path, f"{package_root}/{rel}")
    digest = sha256(zip_path)
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    return {
        "path": str(zip_path),
        "sha256": digest,
        "sha256_path": str(checksum_path),
        "file_count": str(len(files)),
    }


def package_review_bundles(root: Path, output_dir: Path, *, stamp: str | None = None) -> dict[str, dict[str, str]]:
    stamp = stamp or utc_stamp()
    write_final_go_live_artifacts(root, generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    write_external_validation_requirements(
        root,
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    market_readiness = build_production_market_readiness_evidence_room(root)
    write_production_market_readiness_evidence_room_artifacts(market_readiness, root)
    executive_files = _iter_existing(EXECUTIVE_FILES, root)
    technical_files = _iter_existing(TECHNICAL_FILES, root) + _iter_dir_files(TECHNICAL_DIRS, root)
    unique_technical = []
    seen: set[Path] = set()
    for path in technical_files:
        if path not in seen:
            unique_technical.append(path)
            seen.add(path)
    return {
        "executive": write_package(
            output_dir / f"importer-source-readiness-executive-review-{stamp}.zip",
            executive_files,
            root,
            f"importer-source-readiness-executive-review-{stamp}",
        ),
        "technical": write_package(
            output_dir / f"importer-source-readiness-technical-source-review-{stamp}.zip",
            unique_technical,
            root,
            f"importer-source-readiness-technical-source-review-{stamp}",
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build external review package zips.")
    parser.add_argument("--output-dir", default="external_review_packages")
    parser.add_argument("--stamp", default="")
    args = parser.parse_args()
    result = package_review_bundles(ROOT, ROOT / args.output_dir, stamp=args.stamp or None)
    for name, data in result.items():
        print(f"{name}_package={data['path']}")
        print(f"{name}_sha256={data['sha256']}")
        print(f"{name}_sha256_path={data['sha256_path']}")
        print(f"{name}_file_count={data['file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
