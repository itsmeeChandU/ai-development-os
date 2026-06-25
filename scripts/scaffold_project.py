"""Scaffold an AI-native project skeleton from this operating kit."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project_agents(name: str, idea: str, proj_type: str) -> str:
    return f"""# Agent Instructions

This is a scaffolded AI Development OS product project.

## Product

- name: {name}
- type: {proj_type}
- idea: {idea}

## First Read

Before meaningful work, read:

1. `README.md`
2. `docs/STARTUP_BRIEF.md`
3. `docs/INSTRUCTION_CONTRACT.md`
4. `docs/DELIVERY_ESTIMATE.md`
5. `docs/ARCHITECTURE_OVERVIEW.md`
6. `docs/WORK_PACKAGE.md`
7. `docs/PRODUCT_AUTOMATION_RUNBOOK.md`
8. `system_review_graph/README.md`
9. `system_review_graph/STATE_RECONSTRUCTION_REPORT.md`

## Operating Rules

- Treat this repo as truth; treat prompts and generated packets as claims until verified.
- Fill the startup brief and instruction contract before broad implementation.
- Keep the first useful product loop small enough to test locally.
- Use fixture data until real data rights, credentials, freshness, and source lineage are proven.
- Keep external effects closed by default: no paid calls, live sends, legal claims, production deploys, or public launch claims without explicit approval and proof.
- Treat `ready_with_external_gates` as `startup_in_progress`, not done. Generate and follow `system_review_graph/continuation_plan.json` before any fully operational, launch, commercial, supplier, customs, tariff, buyer, or legal readiness claim.
- Write missing data, API, expert, legal, procurement, or compliance inputs as blocker rows with `next_valid_move`.
- Every implementation lane needs allowed files, forbidden files, proof commands, generated artifacts, and a handoff.
- Do not claim completion without code/data changes where required, tests or smoke checks, generated artifacts, blockers, and next valid move.

## Proof Defaults

Start with local checks:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_product.py
```

Add stronger proof commands as the project grows.
"""


def scaffold(name: str, idea: str, output_dir: Path, proj_type: str = "default") -> Path:
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
    _write(project / "AGENTS.md", _project_agents(name, idea, proj_type))
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
    shutil.copy2(ROOT / "templates" / "PRODUCT_AUTOMATION_RUNBOOK.md", project / "docs" / "PRODUCT_AUTOMATION_RUNBOOK.md")
    _write(
        project / "README.md",
        f"# {name}\n\nIdea: {idea}\nType: {proj_type}\n\nStart by filling `docs/STARTUP_BRIEF.md` and `system_review_graph/`.\n",
    )
    if proj_type in ["webapp", "dataapp", "agentservice"]:
        template_dir = ROOT / "templates" / proj_type
        try:
            shutil.copy2(template_dir / "README.md", project / f"{proj_type}_scaffold.md")
        except FileNotFoundError:
            print(f"Warning: Template README.md not found in {template_dir}")
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
    parser.add_argument("--type", dest="proj_type", choices=["default", "webapp", "dataapp", "agentservice"], default="default")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = scaffold(args.name, args.idea, args.output_dir, args.proj_type)
    print(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
