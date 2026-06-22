"""Scaffold an AI-native project skeleton from this operating kit."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scaffold(name: str, idea: str, output_dir: Path) -> Path:
    slug = name.strip().lower().replace(" ", "-")
    project = output_dir / slug
    project.mkdir(parents=True, exist_ok=True)
    for folder in [
        "docs",
        "src",
        "tests",
        "scripts",
        "data",
        "system_review_graph",
        "handoffs",
        "research",
        "simulation",
        "hardware",
        "compliance",
        "operations",
    ]:
        (project / folder).mkdir(exist_ok=True)
    shutil.copy2(ROOT / "AGENTS.md", project / "AGENTS.md")
    shutil.copy2(ROOT / "templates" / "STARTUP_BRIEF.md", project / "docs" / "STARTUP_BRIEF.md")
    shutil.copy2(ROOT / "templates" / "INSTRUCTION_CONTRACT.md", project / "docs" / "INSTRUCTION_CONTRACT.md")
    shutil.copy2(ROOT / "templates" / "DELIVERY_ESTIMATE.md", project / "docs" / "DELIVERY_ESTIMATE.md")
    shutil.copy2(ROOT / "templates" / "ARCHITECTURE_OVERVIEW.md", project / "docs" / "ARCHITECTURE_OVERVIEW.md")
    shutil.copy2(ROOT / "templates" / "WORK_PACKAGE.md", project / "docs" / "WORK_PACKAGE.md")
    shutil.copy2(ROOT / "templates" / "ESTIMATE_VS_ACTUAL.md", project / "handoffs" / "ESTIMATE_VS_ACTUAL.md")
    shutil.copy2(ROOT / "templates" / "CURRENT_STATE_PROMPT.md", project / "docs" / "CURRENT_STATE_PROMPT.md")
    shutil.copy2(ROOT / "templates" / "STATE_RECONSTRUCTION_REPORT.md", project / "system_review_graph" / "STATE_RECONSTRUCTION_REPORT.md")
    shutil.copy2(ROOT / "templates" / "COMPLEX_PRODUCT_SPEC.md", project / "docs" / "COMPLEX_PRODUCT_SPEC.md")
    shutil.copy2(ROOT / "templates" / "HARDWARE_RESEARCH_RECORD.md", project / "research" / "HARDWARE_RESEARCH_RECORD.md")
    shutil.copy2(ROOT / "templates" / "TOOL_DECISION_RECORD.md", project / "research" / "TOOL_DECISION_RECORD.md")
    shutil.copy2(ROOT / "templates" / "PROCUREMENT_AND_LAB_PLAN.md", project / "hardware" / "PROCUREMENT_AND_LAB_PLAN.md")
    _write(
        project / "README.md",
        f"# {name}\n\nIdea: {idea}\n\nStart by filling `docs/STARTUP_BRIEF.md` and `system_review_graph/`.\n",
    )
    _write(
        project / "system_review_graph" / "README.md",
        "# System Review Graph\n\nCreate code, data, flow, proof, task, resource, hardware, simulation, compliance, and blocker maps here.\n",
    )
    _write(
        project / "handoffs" / "README.md",
        "# Handoffs\n\nEvery AI worker writes a handoff here before claiming completion.\n",
    )
    _write(
        project / "hardware" / "README.md",
        "# Hardware\n\nTrack hardware targets, datasheets, interfaces, procurement, and bench blockers here.\n",
    )
    _write(
        project / "simulation" / "README.md",
        "# Simulation\n\nTrack emulators, mocked hardware, fixtures, and simulation proof here.\n",
    )
    _write(
        project / "compliance" / "README.md",
        "# Compliance\n\nTrack standards, hazards, privacy/security, certification, and field blockers here.\n",
    )
    return project


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--idea", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = scaffold(args.name, args.idea, args.output_dir)
    print(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
