#!/usr/bin/env python3
"""Generate a lightweight system review graph from the current repository."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def _tracked_files() -> list[str]:
    return [line for line in _run_git(["ls-files"]).splitlines() if line]


def _count_by_prefix(files: Iterable[str]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for path in files:
        if path.startswith("product_projects/importer-source-readiness-copilot/src/"):
            counter["product_source"] += 1
        elif path.startswith("product_projects/importer-source-readiness-copilot/tests/"):
            counter["product_tests"] += 1
        elif path.startswith("product_projects/importer-source-readiness-copilot/system_review_graph/"):
            counter["product_generated_artifacts"] += 1
        elif path.startswith("product_projects/importer-source-readiness-copilot/data/"):
            counter["product_data"] += 1
        elif path.startswith("scripts/"):
            counter["root_scripts"] += 1
        elif path.startswith("docs/"):
            counter["root_docs"] += 1
        elif path.startswith("manifests/"):
            counter["manifests"] += 1
        elif path.startswith("templates/"):
            counter["templates"] += 1
        else:
            counter["other"] += 1
    return counter


def _write(path: Path, title: str, lines: list[str]) -> None:
    path.write_text("# " + title + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def build_graph() -> dict[str, object]:
    files = _tracked_files()
    counts = _count_by_prefix(files)
    head = _run_git(["rev-parse", "HEAD"]).strip()
    product_root = "product_projects/importer-source-readiness-copilot"
    proof_commands = [
        "python3 scripts/ai_dev_os_check.py",
        "python3 scripts/workflow_manifest_check.py",
        "python3 scripts/product_project_check.py",
        "python3 scripts/no_scaffold_audit.py --check",
    ]
    generated_artifacts = [
        "system_review_graph/no_scaffold_audit_report.json",
        f"{product_root}/system_review_graph/external_validation_requirements_report.json",
        f"{product_root}/system_review_graph/go_live_input_readiness_report.json",
        f"{product_root}/output/pdf/external_validation_reviewer_brief.pdf",
        f"{product_root}/output/pdf/go_live_input_requests.pdf",
    ]
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "head": head,
        "file_count": len(files),
        "counts": dict(sorted(counts.items())),
        "code_layers": [
            "root scripts",
            "product source",
            "product tests",
            "manifests",
            "generated system_review_graph artifacts",
        ],
        "data_layers": [
            f"{product_root}/data",
            f"{product_root}/system_review_graph/*.json",
            f"{product_root}/system_review_graph/*.sqlite",
        ],
        "flow_layers": [
            "prompt-to-product orchestration",
            "product project proof checks",
            "external validation intake and evaluator",
            "no-scaffold audit",
        ],
        "proof_commands": proof_commands,
        "generated_artifacts": generated_artifacts,
        "task_boundaries": [
            "templates and scaffolds cannot satisfy completion",
            "fixture placeholders must remain blocker evidence",
            "simulated reviews cannot open launch or approval",
            "go-live inputs must be real returned records before readiness flips",
        ],
    }


def emit_graph(out_dir: Path) -> dict[str, object]:
    graph = build_graph()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "system_review_graph_summary.json").write_text(
        json.dumps(graph, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write(
        out_dir / "code_graph.md",
        "Code Graph",
        [
            f"- head: `{graph['head']}`",
            f"- tracked files: `{graph['file_count']}`",
            "- root scripts, product source, tests, manifests, and generated artifacts are separate code layers.",
            f"- counts: `{json.dumps(graph['counts'], sort_keys=True)}`",
        ],
    )
    _write(
        out_dir / "data_graph.md",
        "Data Graph",
        [f"- {item}" for item in graph["data_layers"]],
    )
    _write(
        out_dir / "flow_graph.md",
        "Flow Graph",
        [f"- {item}" for item in graph["flow_layers"]],
    )
    _write(
        out_dir / "proof_graph.md",
        "Proof Graph",
        [f"- `{item}`" for item in graph["proof_commands"]],
    )
    _write(
        out_dir / "task_graph.md",
        "Task Graph",
        [f"- {item}" for item in graph["task_boundaries"]],
    )
    _write(
        out_dir / "resource_graph.md",
        "Resource Graph",
        [f"- `{item}`" for item in graph["generated_artifacts"]],
    )
    return graph


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "system_review_graph")
    args = parser.parse_args()
    graph = emit_graph(args.out_dir)
    print("System review graph: PASS")
    print(f"head={graph['head']}")
    print(f"file_count={graph['file_count']}")
    print(f"out_dir={args.out_dir.relative_to(ROOT) if args.out_dir.is_relative_to(ROOT) else args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
