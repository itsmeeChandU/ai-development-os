"""Validation for simulated AI review output."""

from __future__ import annotations

from typing import Any

VALID_SEVERITIES = {
    "P0_unsafe",
    "P1_blocks_external_claim",
    "P2_blocks_private_beta",
    "P3_blocks_public_launch",
    "P4_improvement",
}

VALID_CLAIM_TYPES = {
    "source_freshness_claim",
    "source_rights_claim",
    "buyer_validation_claim",
    "commercial_contract_claim",
    "import_rules_claim",
    "export_rules_claim",
    "tariff_classification_claim",
    "food_safety_claim",
    "restricted_party_screening_claim",
    "expert_review_claim",
    "launch_readiness_claim",
}


def validate_ai_review_output(
    output: dict[str, Any],
    *,
    evidence_ids: set[str],
    source_ids: set[str],
) -> dict[str, Any]:
    """Validate a simulated AI review against fail-closed product rules."""

    errors: list[str] = []
    if output.get("can_open_gate") is not False:
        errors.append("can_open_gate must be false for AI simulated reviews")
    if output.get("human_review_required") is not True:
        errors.append("human_review_required must be true for AI simulated reviews")

    blocked_claims = output.get("blocked_claims")
    if not isinstance(blocked_claims, list) or not blocked_claims:
        errors.append("blocked_claims must be a non-empty list")
    else:
        for claim in blocked_claims:
            if claim not in VALID_CLAIM_TYPES:
                errors.append(f"unknown blocked claim type: {claim}")

    findings = output.get("findings")
    if not isinstance(findings, list) or not findings:
        errors.append("findings must be a non-empty list")
    else:
        for index, finding in enumerate(findings, start=1):
            if finding.get("severity") not in VALID_SEVERITIES:
                errors.append(f"finding {index} has unknown severity")
            used_evidence = finding.get("evidence_used")
            used_sources = finding.get("sources_used")
            if not isinstance(used_evidence, list) or not used_evidence:
                errors.append(f"finding {index} must cite packet evidence IDs")
            else:
                for evidence_id in used_evidence:
                    if evidence_id not in evidence_ids:
                        errors.append(f"finding {index} references unknown evidence ID: {evidence_id}")
            if not isinstance(used_sources, list) or not used_sources:
                errors.append(f"finding {index} must cite official source IDs")
            else:
                for source_id in used_sources:
                    if source_id not in source_ids:
                        errors.append(f"finding {index} references unknown source ID: {source_id}")
            for claim in finding.get("blocked_claims", []):
                if claim not in VALID_CLAIM_TYPES:
                    errors.append(f"finding {index} references unknown claim type: {claim}")

    return {
        "valid": not errors,
        "errors": errors,
        "can_open_gate": False,
        "decision": "accepted_simulated_review" if not errors else "rejected_fail_closed",
    }
