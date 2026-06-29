#!/usr/bin/env python3
"""Regenerate all local proof artifacts before running tests.

This is the fresh-clone proof entrypoint. It intentionally skips packaging,
serving, and audits; those are downstream checks after the repo has recreated
its generated truth surfaces.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ARTIFACT_GENERATOR_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("scripts/build_external_review_packet.py",),
    ("scripts/run_external_review_intake.py",),
    ("scripts/build_reviewer_documents.py",),
    ("scripts/run_readiness.py",),
    ("scripts/run_external_gates.py",),
    ("scripts/plan_continuation.py",),
    ("scripts/build_vc_pitch_packet.py",),
    ("scripts/build_board_go_live_packet.py",),
    ("scripts/run_operator_workflow.py",),
    ("scripts/run_customer_workflow.py",),
    ("scripts/run_policy_intelligence.py",),
    ("scripts/run_completion_platform.py",),
    ("scripts/run_product_operations.py",),
    ("scripts/export_operator_dashboard.py",),
    ("scripts/run_final_go_live_review.py",),
    ("scripts/run_external_validation_requirements.py",),
    ("scripts/run_hosted_deployment_proof.py",),
    ("scripts/run_payment_activation_proof.py",),
    ("scripts/run_private_beta_outcomes.py",),
    ("scripts/run_production_redevelopment.py",),
    ("scripts/run_production_data_model.py",),
    ("scripts/run_production_packet_engine.py",),
    ("scripts/run_production_country_source_engine.py",),
    ("scripts/run_production_trade_discovery_engine.py",),
    ("scripts/run_production_trade_data_catalog_engine.py",),
    ("scripts/run_production_market_intelligence_engine.py",),
    ("scripts/run_production_document_intelligence_engine.py",),
    ("scripts/run_production_evidence_claim_gate_engine.py",),
    ("scripts/run_production_decision_scoring_engine.py",),
    ("scripts/run_production_ai_copilot_engine.py",),
    ("scripts/run_production_expert_review_network.py",),
    ("scripts/run_production_reports_engine.py",),
    ("scripts/run_production_persistence.py",),
    ("scripts/run_production_repository.py",),
    ("scripts/run_production_portal_workflow_engine.py",),
    ("scripts/run_production_enterprise_api_platform.py",),
    ("scripts/run_production_api_service.py",),
    ("scripts/run_production_payment_monetization_engine.py",),
    ("scripts/run_production_security_privacy_reliability_engine.py",),
    ("scripts/run_production_launch_control_plane.py",),
    ("scripts/run_production_market_readiness_evidence_room.py",),
)


def run_generator(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    completed: list[dict[str, str]] = []
    for command in ARTIFACT_GENERATOR_COMMANDS:
        result = run_generator(command)
        command_text = " ".join((sys.executable, *command))
        if result.returncode != 0:
            print("Artifact regeneration: FAIL")
            print(f"command: {command_text}")
            print(result.stdout)
            print(result.stderr)
            return result.returncode
        completed.append({"command": command_text, "status": "ok"})

    print(
        json.dumps(
            {
                "status": "all_artifacts_regenerated",
                "generator_count": len(completed),
                "commands": completed,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
