"""Dry-run AI Development OS against simple and complex product prompts."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from scaffold_project import scaffold

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FOR_FLOW = [
    "docs/COMPLEXITY_ROUTER.md",
    "docs/INSTRUCTION_NORMALIZATION.md",
    "docs/STATE_RECONSTRUCTION.md",
    "docs/AGENTIC_COMPANY_MODEL.md",
    "docs/DELIVERY_ESTIMATION.md",
    "docs/COMPLEX_PRODUCT_PLAYBOOK.md",
    "docs/TOOL_BREEDING_GROUND.md",
    "docs/PRODUCT_AUTOMATION_GUIDE.md",
    "docs/AGENTIC_WORKFLOW_INTEGRATION.md",
    "docs/STARTUP_CONTINUATION_RULE.md",
    "manifests/agentic_execution_manifest.json",
    "manifests/internal_repo_registry.json",
    "manifests/research_data_router.json",
    "manifests/development_strategy_router.json",
    "templates/COMPLEXITY_CLASSIFICATION.md",
    "templates/INSTRUCTION_CONTRACT.md",
    "templates/STATE_RECONSTRUCTION_REPORT.md",
    "templates/ARCHITECTURE_OVERVIEW.md",
    "templates/DELIVERY_ESTIMATE.md",
    "templates/WORK_PACKAGE.md",
    "templates/TOOL_DECISION_RECORD.md",
    "templates/HARDWARE_RESEARCH_RECORD.md",
    "templates/PROCUREMENT_AND_LAB_PLAN.md",
    "templates/PRODUCT_AUTOMATION_RUNBOOK.md",
    "templates/ESTIMATE_VS_ACTUAL.md",
    "examples/calculator_app_prompt.txt",
    "examples/calculator_app_expected/COMPLEXITY_CLASSIFICATION.md",
    "examples/hardware_os_startup_prompt.txt",
    "examples/hardware_os_startup_expected/COMPLEXITY_CLASSIFICATION.md",
    "examples/hardware_os_startup_expected/INSTRUCTION_CONTRACT.md",
    "examples/hardware_os_startup_expected/ARCHITECTURE_OVERVIEW.md",
    "examples/hardware_os_startup_expected/DELIVERY_ESTIMATE.md",
    "examples/hardware_os_startup_expected/TOOL_DECISION_RECORD.md",
    "examples/prompt-to-product-case-study.md",
    "product_projects/README.md",
    "product_projects/importer-source-readiness-copilot/README.md",
    "product_projects/importer-source-readiness-copilot/AGENTS.md",
    "product_projects/importer-source-readiness-copilot/docs/PRODUCT_AUTOMATION_RUNBOOK.md",
    "product_projects/importer-source-readiness-copilot/docs/PRODUCT_STATUS.md",
    "product_projects/importer-source-readiness-copilot/docs/OPERATOR_GUIDE.md",
    "product_projects/importer-source-readiness-copilot/data/sample_source_cards.json",
    "product_projects/importer-source-readiness-copilot/data/country_requirements_matrix.json",
    "product_projects/importer-source-readiness-copilot/data/evidence_packets.json",
    "product_projects/importer-source-readiness-copilot/data/official_source_registry.json",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/readiness.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/external_gates.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/continuation.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/operator_report.py",
    "product_projects/importer-source-readiness-copilot/scripts/run_readiness.py",
    "product_projects/importer-source-readiness-copilot/scripts/run_external_gates.py",
    "product_projects/importer-source-readiness-copilot/scripts/export_operator_dashboard.py",
    "product_projects/importer-source-readiness-copilot/scripts/plan_continuation.py",
    "product_projects/importer-source-readiness-copilot/scripts/check_product.py",
    "product_projects/importer-source-readiness-copilot/tests/test_readiness.py",
    "product_projects/importer-source-readiness-copilot/tests/test_external_gates.py",
    "product_projects/importer-source-readiness-copilot/tests/test_continuation.py",
    "product_projects/importer-source-readiness-copilot/system_review_graph/readiness_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/external_gate_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/continuation_plan.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/operator_dashboard.html",
    "product_projects/importer-source-readiness-copilot/system_review_graph/blockers.jsonl",
    "product_projects/importer-source-readiness-copilot/handoffs/product_completion_handoff.md",
    "system_review_graph/internal_repo_intake_packet.json",
    "system_review_graph/research_data_plan.json",
    "system_review_graph/development_strategy_plan.json",
]

REQUIRED_TOOL_TERMS = [
    "QEMU",
    "Renode",
    "Zephyr",
    "Yocto",
    "Buildroot",
    "OpenOCD",
    "KiCad",
    "FreeCAD",
    "ngspice",
    "Yosys",
    "Verilator",
    "cocotb",
]


def main() -> int:
    missing = [path for path in REQUIRED_FOR_FLOW if not (ROOT / path).exists()]
    if missing:
        print("AI Dev OS self-test: FAIL")
        for path in missing:
            print(f"missing: {path}")
        return 1

    registry = (ROOT / "manifests" / "tool_registry.yaml").read_text(encoding="utf-8")
    missing_tools = [term for term in REQUIRED_TOOL_TERMS if term not in registry]
    if missing_tools:
        print("AI Dev OS self-test: FAIL")
        for term in missing_tools:
            print(f"missing_tool: {term}")
        return 1

    calculator = (ROOT / "examples/calculator_app_expected/COMPLEXITY_CLASSIFICATION.md").read_text(
        encoding="utf-8"
    )
    hardware = (ROOT / "examples/hardware_os_startup_expected/COMPLEXITY_CLASSIFICATION.md").read_text(
        encoding="utf-8"
    )
    if "S0/S1" not in calculator or "S4" not in hardware:
        print("AI Dev OS self-test: FAIL")
        print("complexity routing examples are not distinct")
        return 1

    research_router = json.loads((ROOT / "manifests/research_data_router.json").read_text(encoding="utf-8"))
    strategy_router = json.loads(
        (ROOT / "manifests/development_strategy_router.json").read_text(encoding="utf-8")
    )
    research_ids = {row.get("id") for row in research_router.get("research_depths", [])}
    data_ids = {row.get("id") for row in research_router.get("data_routes", [])}
    mode_ids = {row.get("id") for row in strategy_router.get("development_modes", [])}
    required_research = {"R0_MODEL_PRIOR", "R1_NORMAL_WEB_SCAN", "R4_DEEP_RESEARCH", "R5_EXPERT_OR_USER_VALIDATION"}
    required_data = {"D1_NORMAL_WEB_SEARCH", "D2_PRIMARY_OFFICIAL_SOURCE", "D3_DATASET_OR_API", "D4_HUMAN_EXPERT_OR_USER"}
    required_modes = {"M0_SOFTWARE_LOCAL", "M4_HARDWARE_MANUFACTURING", "M5_CROSS_BORDER_SUPPLY_CHAIN"}
    if not required_research.issubset(research_ids):
        print("AI Dev OS self-test: FAIL")
        print("research router missing required depths")
        return 1
    if not required_data.issubset(data_ids):
        print("AI Dev OS self-test: FAIL")
        print("research router missing required data routes")
        return 1
    if not required_modes.issubset(mode_ids):
        print("AI Dev OS self-test: FAIL")
        print("strategy router missing required modes")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        project = scaffold(
            "self-test-data-app",
            "Build a fixture-only data app for scaffold verification.",
            Path(tmp),
            "dataapp",
        )
        generated_agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        if "scaffolded AI Development OS product project" not in generated_agents:
            print("AI Dev OS self-test: FAIL")
            print("generated AGENTS.md is not project-local")
            return 1
        if not (project / "docs" / "PRODUCT_AUTOMATION_RUNBOOK.md").exists():
            print("AI Dev OS self-test: FAIL")
            print("generated project missing product automation runbook")
            return 1
        if "continuation_plan.json" not in generated_agents:
            print("AI Dev OS self-test: FAIL")
            print("generated AGENTS.md missing startup continuation rule")
            return 1

    print("AI Dev OS self-test: PASS")
    print(f"flow_files={len(REQUIRED_FOR_FLOW)}")
    print(f"tool_terms={len(REQUIRED_TOOL_TERMS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
