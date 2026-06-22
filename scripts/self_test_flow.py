"""Dry-run AI Development OS against simple and complex product prompts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FOR_FLOW = [
    "docs/COMPLEXITY_ROUTER.md",
    "docs/INSTRUCTION_NORMALIZATION.md",
    "docs/STATE_RECONSTRUCTION.md",
    "docs/AGENTIC_COMPANY_MODEL.md",
    "docs/DELIVERY_ESTIMATION.md",
    "docs/COMPLEX_PRODUCT_PLAYBOOK.md",
    "docs/TOOL_BREEDING_GROUND.md",
    "templates/COMPLEXITY_CLASSIFICATION.md",
    "templates/INSTRUCTION_CONTRACT.md",
    "templates/STATE_RECONSTRUCTION_REPORT.md",
    "templates/ARCHITECTURE_OVERVIEW.md",
    "templates/DELIVERY_ESTIMATE.md",
    "templates/WORK_PACKAGE.md",
    "templates/TOOL_DECISION_RECORD.md",
    "templates/HARDWARE_RESEARCH_RECORD.md",
    "templates/PROCUREMENT_AND_LAB_PLAN.md",
    "templates/ESTIMATE_VS_ACTUAL.md",
    "examples/calculator_app_prompt.txt",
    "examples/calculator_app_expected/COMPLEXITY_CLASSIFICATION.md",
    "examples/hardware_os_startup_prompt.txt",
    "examples/hardware_os_startup_expected/COMPLEXITY_CLASSIFICATION.md",
    "examples/hardware_os_startup_expected/INSTRUCTION_CONTRACT.md",
    "examples/hardware_os_startup_expected/ARCHITECTURE_OVERVIEW.md",
    "examples/hardware_os_startup_expected/DELIVERY_ESTIMATE.md",
    "examples/hardware_os_startup_expected/TOOL_DECISION_RECORD.md",
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

    print("AI Dev OS self-test: PASS")
    print(f"flow_files={len(REQUIRED_FOR_FLOW)}")
    print(f"tool_terms={len(REQUIRED_TOOL_TERMS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
