"""Report quality checks for System Review Graph manifests."""

from __future__ import annotations

from typing import Any

from system_review_graph.validate import validate_manifest


def _count(manifest: dict[str, Any], key: str) -> int:
    value = manifest.get(key)
    return len(value) if isinstance(value, list) else 0


def doctor_manifest(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Return quality findings for a manifest."""

    findings: list[dict[str, str]] = []
    for error in validate_manifest(manifest):
        findings.append({"severity": "error", "message": error})
    if not manifest.get("bigger_picture"):
        findings.append(
            {
                "severity": "warning",
                "message": (
                    "missing bigger_picture; reviewers may not understand "
                    "why the system exists"
                ),
            }
        )
    if not manifest.get("current_truth"):
        findings.append(
            {
                "severity": "warning",
                "message": "missing current_truth; report lacks an honest status snapshot",
            }
        )
    if not manifest.get("source_links"):
        findings.append(
            {
                "severity": "warning",
                "message": "missing source_links; public reports are harder to verify",
            }
        )
    if _count(manifest, "systems") < 2:
        findings.append(
            {
                "severity": "warning",
                "message": "fewer than two systems; report may be too shallow for a system map",
            }
        )
    if _count(manifest, "systems") > 12 and _count(manifest, "child_maps") == 0:
        findings.append(
            {
                "severity": "info",
                "message": (
                    "large manifest has no child_maps; consider atlas mode so reviewers can "
                    "drill into subsystem maps"
                ),
            }
        )
    if _count(manifest, "systems") > 12 and _count(manifest, "blueprint_sections") == 0:
        findings.append(
            {
                "severity": "info",
                "message": (
                    "large manifest has no blueprint_sections; add source-evidence-backed "
                    "flows for blueprint-level review"
                ),
            }
        )
    if _count(manifest, "workflows") == 0:
        findings.append(
            {
                "severity": "warning",
                "message": "no workflows; report cannot show end-to-end movement",
            }
        )
    if _count(manifest, "decision_gates") == 0:
        findings.append(
            {
                "severity": "warning",
                "message": "no decision_gates; report cannot show what advances, waits, or blocks",
            }
        )
    if not manifest.get("review_questions"):
        findings.append(
            {
                "severity": "warning",
                "message": "missing review_questions; auditors do not know what to inspect next",
            }
        )
    if not manifest.get("known_boundaries"):
        findings.append(
            {
                "severity": "warning",
                "message": "missing known_boundaries; report may overclaim what is proven",
            }
        )
    for index, system in enumerate(manifest.get("systems") or []):
        if not isinstance(system, dict):
            continue
        name = system.get("name") or f"systems[{index}]"
        for field in ("truth_boundary", "ideal_target", "code_surfaces"):
            if not system.get(field):
                findings.append(
                    {
                        "severity": "info",
                        "message": f"{name} missing {field}; drill-down may be less useful",
                    }
                )
    return findings


def format_doctor_findings(findings: list[dict[str, str]]) -> str:
    """Format doctor findings for CLI output."""

    if not findings:
        return "doctor clean: no manifest quality findings"
    lines = ["doctor findings:"]
    for finding in findings:
        lines.append(f"- {finding['severity']}: {finding['message']}")
    return "\n".join(lines)
