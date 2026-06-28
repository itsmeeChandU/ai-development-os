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
    "docs/STARTUP_LIFECYCLE_DEVELOPMENT.md",
    "docs/COMPLEX_PRODUCT_PLAYBOOK.md",
    "docs/TOOL_BREEDING_GROUND.md",
    "docs/PRODUCT_AUTOMATION_GUIDE.md",
    "docs/AGENTIC_WORKFLOW_INTEGRATION.md",
    "docs/STARTUP_CONTINUATION_RULE.md",
    "docs/VC_PITCH_READINESS.md",
    "docs/BOARD_GO_LIVE_READINESS.md",
    "docs/EXTERNAL_AGENT_HARNESS_INTEGRATION.md",
    "manifests/agentic_execution_manifest.json",
    "manifests/internal_repo_registry.json",
    "manifests/research_data_router.json",
    "manifests/development_strategy_router.json",
    "templates/COMPLEXITY_CLASSIFICATION.md",
    "templates/STARTUP_LIFECYCLE.md",
    "templates/INSTRUCTION_CONTRACT.md",
    "templates/STATE_RECONSTRUCTION_REPORT.md",
    "templates/ARCHITECTURE_OVERVIEW.md",
    "templates/DELIVERY_ESTIMATE.md",
    "templates/WORK_PACKAGE.md",
    "templates/TOOL_DECISION_RECORD.md",
    "templates/HARDWARE_RESEARCH_RECORD.md",
    "templates/PROCUREMENT_AND_LAB_PLAN.md",
    "templates/PRODUCT_AUTOMATION_RUNBOOK.md",
    "templates/EXTERNAL_HARNESS_ADOPTION.md",
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
    "product_projects/importer-source-readiness-copilot/PRODUCT_DOCTRINE.md",
    "product_projects/importer-source-readiness-copilot/CUSTOMER_SOURCE_PACKET_SPEC.md",
    "product_projects/importer-source-readiness-copilot/SOURCE_OF_TRUTH.md",
    "product_projects/importer-source-readiness-copilot/RUN_RESULTS.md",
    "product_projects/importer-source-readiness-copilot/REDACTION_REPORT.md",
    "product_projects/importer-source-readiness-copilot/REVIEW_USE_TERMS.md",
    "product_projects/importer-source-readiness-copilot/OFFLINE_REPRODUCTION.md",
    "product_projects/importer-source-readiness-copilot/PACKAGE_AUDIT.md",
    "product_projects/importer-source-readiness-copilot/docs/PRODUCT_AUTOMATION_RUNBOOK.md",
    "product_projects/importer-source-readiness-copilot/docs/PRODUCT_STATUS.md",
    "product_projects/importer-source-readiness-copilot/docs/REQUIREMENTS_ANALYSIS.md",
    "product_projects/importer-source-readiness-copilot/docs/PUBLIC_TRADE_READINESS.md",
    "product_projects/importer-source-readiness-copilot/docs/STARTUP_LIFECYCLE.md",
    "product_projects/importer-source-readiness-copilot/docs/OPERATOR_GUIDE.md",
    "product_projects/importer-source-readiness-copilot/data/sample_source_cards.json",
    "product_projects/importer-source-readiness-copilot/data/country_requirements_matrix.json",
    "product_projects/importer-source-readiness-copilot/data/evidence_packets.json",
    "product_projects/importer-source-readiness-copilot/data/official_source_registry.json",
    "product_projects/importer-source-readiness-copilot/data/investor_evidence.json",
    "product_projects/importer-source-readiness-copilot/data/canada_tool_registry.json",
    "product_projects/importer-source-readiness-copilot/data/expert_review_simulations.json",
    "product_projects/importer-source-readiness-copilot/data/launch_controls.json",
    "product_projects/importer-source-readiness-copilot/data/customer_source_packets.json",
    "product_projects/importer-source-readiness-copilot/data/evidence_ledger.json",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/readiness.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/external_gates.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/continuation.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/investor_readiness.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/board_readiness.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/operator_app.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/operator_workflow.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/operator_report.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/operator_screenshots.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/source_packet_workflow.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/customer_store.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/product_runtime.py",
    "product_projects/importer-source-readiness-copilot/src/importer_source_readiness/ai_review_validation.py",
    "product_projects/importer-source-readiness-copilot/scripts/run_readiness.py",
    "product_projects/importer-source-readiness-copilot/scripts/run_external_gates.py",
    "product_projects/importer-source-readiness-copilot/scripts/export_operator_dashboard.py",
    "product_projects/importer-source-readiness-copilot/scripts/plan_continuation.py",
    "product_projects/importer-source-readiness-copilot/scripts/build_vc_pitch_packet.py",
    "product_projects/importer-source-readiness-copilot/scripts/build_board_go_live_packet.py",
    "product_projects/importer-source-readiness-copilot/scripts/serve_operator_app.py",
    "product_projects/importer-source-readiness-copilot/scripts/run_operator_workflow.py",
    "product_projects/importer-source-readiness-copilot/scripts/run_customer_workflow.py",
    "product_projects/importer-source-readiness-copilot/scripts/audit_external_package.py",
    "product_projects/importer-source-readiness-copilot/scripts/check_product.py",
    "product_projects/importer-source-readiness-copilot/tests/test_readiness.py",
    "product_projects/importer-source-readiness-copilot/tests/test_external_gates.py",
    "product_projects/importer-source-readiness-copilot/tests/test_continuation.py",
    "product_projects/importer-source-readiness-copilot/tests/test_investor_readiness.py",
    "product_projects/importer-source-readiness-copilot/tests/test_board_go_live.py",
    "product_projects/importer-source-readiness-copilot/tests/test_operator_app.py",
    "product_projects/importer-source-readiness-copilot/tests/test_operator_workflow.py",
    "product_projects/importer-source-readiness-copilot/tests/test_operator_screenshots.py",
    "product_projects/importer-source-readiness-copilot/tests/test_source_packet_workflow.py",
    "product_projects/importer-source-readiness-copilot/tests/test_customer_store.py",
    "product_projects/importer-source-readiness-copilot/tests/test_product_runtime.py",
    "product_projects/importer-source-readiness-copilot/tests/test_external_package_audit.py",
    "product_projects/importer-source-readiness-copilot/system_review_graph/readiness_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/external_gate_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/continuation_plan.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/vc_pitch_readiness_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/board_go_live_readiness_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/operator_workflow_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/operator_dashboard.html",
    "product_projects/importer-source-readiness-copilot/system_review_graph/operator_screenshot_manifest.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/operator_screenshots/operator-dashboard.png",
    "product_projects/importer-source-readiness-copilot/system_review_graph/customer_readiness_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/customer_readiness_report.md",
    "product_projects/importer-source-readiness-copilot/system_review_graph/customer_source_packets.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/evidence_ledger.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/customer_ai_review_runs.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/customer_workflow.sqlite",
    "product_projects/importer-source-readiness-copilot/system_review_graph/product_runtime_state.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/auth_rbac_matrix.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/claims_gate_matrix.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/review_requests.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/human_review_findings.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/report_exports.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/audit_events.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/deletion_requests.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/deployment_readiness_report.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/private_beta_readiness_checklist.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/ai_data_policy.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/model_endpoints.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/ai_model_router.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/redaction_pipeline.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/manual_no_ai_workflow.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/requirements_traceability_matrix.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/public_trade_readiness_manifest.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/exporter_mode_requirements.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/public_report_types.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/public_upload_policy.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/source_refresh_runs.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/source_refresh_report_packet-frozen-tuna-canada-001.json",
    "product_projects/importer-source-readiness-copilot/system_review_graph/expert_review_packet_packet-frozen-tuna-canada-001.md",
    "product_projects/importer-source-readiness-copilot/system_review_graph/blockers.jsonl",
    "product_projects/importer-source-readiness-copilot/investor/vc_pitch_deck.md",
    "product_projects/importer-source-readiness-copilot/investor/one_pager.md",
    "product_projects/importer-source-readiness-copilot/investor/demo_script.md",
    "product_projects/importer-source-readiness-copilot/investor/diligence_room_index.md",
    "product_projects/importer-source-readiness-copilot/board/board_go_live_brief.md",
    "product_projects/importer-source-readiness-copilot/board/expert_review_packet.md",
    "product_projects/importer-source-readiness-copilot/board/launch_control_checklist.md",
    "product_projects/importer-source-readiness-copilot/board/financial_operating_model.md",
    "product_projects/importer-source-readiness-copilot/migrations/0001_product_runtime.sql",
    "product_projects/importer-source-readiness-copilot/Dockerfile",
    "product_projects/importer-source-readiness-copilot/compose.yaml",
    "product_projects/importer-source-readiness-copilot/.env.example",
    "product_projects/importer-source-readiness-copilot/docs/SECURITY_PRIVACY.md",
    "product_projects/importer-source-readiness-copilot/docs/DEPLOYMENT.md",
    "product_projects/importer-source-readiness-copilot/handoffs/product_completion_handoff.md",
    "system_review_graph/internal_repo_intake_packet.json",
    "system_review_graph/research_data_plan.json",
    "system_review_graph/development_strategy_plan.json",
    "system_review_graph/external_harness_integration_packet.json",
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
    "Everything Claude Code",
    "ECC AgentShield",
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
        if "vc_pitch_readiness_report.json" not in generated_agents:
            print("AI Dev OS self-test: FAIL")
            print("generated AGENTS.md missing VC pitch readiness rule")
            return 1
        if "board_go_live_readiness_report.json" not in generated_agents:
            print("AI Dev OS self-test: FAIL")
            print("generated AGENTS.md missing board go-live readiness rule")
            return 1
        if "STARTUP_LIFECYCLE.md" not in generated_agents:
            print("AI Dev OS self-test: FAIL")
            print("generated AGENTS.md missing startup lifecycle rule")
            return 1

    print("AI Dev OS self-test: PASS")
    print(f"flow_files={len(REQUIRED_FOR_FLOW)}")
    print(f"tool_terms={len(REQUIRED_TOOL_TERMS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
