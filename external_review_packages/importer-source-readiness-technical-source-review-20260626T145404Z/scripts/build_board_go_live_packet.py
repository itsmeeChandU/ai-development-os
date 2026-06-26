#!/usr/bin/env python3
"""Build the board-to-go-live readiness packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import build_board_go_live_readiness, load_json, write_json  # noqa: E402


def _bullet(rows: list[str]) -> str:
    return "\n".join(f"- {row}" for row in rows)


def _write_markdown(path: Path, title: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")
    return path


def _write_board_brief(report: dict[str, Any]) -> Path:
    body = f"""## Decision State

- status: `{report['status']}`
- primary market: `{report['primary_market']}`
- board decision scope: `{report['board_decision_scope']}`
- allowed next stage: `{report['allowed_next_stage']}`
- human approval gates: `{report['human_approval_gate_count']}`

## What Is Actually Built

- local source-card readiness engine
- external gate evaluator
- continuation plan for unresolved real-world evidence
- Canada official tool registry
- simulated expert review packet
- launch-control checklist
- operator dashboard
- VC/investor packet
- board go-live readiness report

## Board Ask

Approve or reject a controlled private beta path. Public launch, production
deployment, legal/financial/customs/tariff advice, CFIA compliance, buyer
validation, revenue, and PMF claims remain closed until the human approval
gates are satisfied.

## Human Approval Gates

{_bullet([f"{gate['id']}: {gate['gate']}" for gate in report['human_approval_gates']])}

## Proof Boundary

{report['proof_boundary']}
"""
    return _write_markdown(ROOT / "board" / "board_go_live_brief.md", "Board Go-Live Brief", body)


def _write_expert_packet(report: dict[str, Any]) -> Path:
    sections = []
    for review in report["simulated_expert_reviews"]:
        findings = _bullet(review["findings"])
        inputs = _bullet(review["implemented_inputs"])
        sections.append(
            f"## {review['role']}\n\n"
            f"- status: `{review['status']}`\n"
            f"- human gate: {review['human_approval_gate']}\n"
            f"- next: {review['next_valid_move']}\n\n"
            f"### Findings\n\n{findings}\n\n"
            f"### Implemented Inputs\n\n{inputs}"
        )
    return _write_markdown(ROOT / "board" / "expert_review_packet.md", "Expert Review Packet", "\n\n".join(sections))


def _write_launch_checklist(report: dict[str, Any]) -> Path:
    lines = []
    for control in report["launch_controls"]:
        lines.append(
            f"- `{control['id']}` [{control['status']}] owner={control['owner']}: "
            f"{control['control']} Next: {control['next_valid_move']}"
        )
    body = "## Controls\n\n" + "\n".join(lines)
    body += "\n\n## Closed Claims\n\n" + _bullet(report["closed_claims"])
    return _write_markdown(ROOT / "board" / "launch_control_checklist.md", "Launch Control Checklist", body)


def _write_financial_model(report: dict[str, Any]) -> Path:
    body = """## Canadian Finance Readiness

This is a planning model, not financial advice.

## Current Position

- funding ask remains a draft planning assumption
- no revenue claim is made
- no PMF claim is made
- no securities or financing document is approved
- budget, pricing, and runway need founder/accountant/finance review

## Board Review Inputs

- BDC financial plan template is registered in `data/canada_tool_registry.json`
- investor packet has a draft ask with explicit legal/financial boundary
- financial-advisor simulation is complete
- finance signoff remains a human approval gate

## Required Before Spend Commitments

- 12-month base/conservative/aggressive budget
- first 90-day operating plan
- pricing experiment with buyer feedback
- counsel/accountant review for financing terms
- board approval for spend authority
"""
    return _write_markdown(ROOT / "board" / "financial_operating_model.md", "Financial Operating Model", body)


def main() -> int:
    report = build_board_go_live_readiness(
        readiness=load_json(ROOT / "system_review_graph" / "readiness_report.json"),
        external=load_json(ROOT / "system_review_graph" / "external_gate_report.json"),
        continuation=load_json(ROOT / "system_review_graph" / "continuation_plan.json"),
        vc_pitch=load_json(ROOT / "system_review_graph" / "vc_pitch_readiness_report.json"),
        canada_tools=load_json(ROOT / "data" / "canada_tool_registry.json"),
        expert_reviews=load_json(ROOT / "data" / "expert_review_simulations.json"),
        launch_controls=load_json(ROOT / "data" / "launch_controls.json"),
    )
    out = write_json(report, ROOT / "system_review_graph" / "board_go_live_readiness_report.json")
    artifacts = [
        str(_write_board_brief(report)),
        str(_write_expert_packet(report)),
        str(_write_launch_checklist(report)),
        str(_write_financial_model(report)),
    ]
    print(
        json.dumps(
            {
                "out": str(out),
                "status": report["status"],
                "human_approval_gates": report["human_approval_gate_count"],
                "artifacts": artifacts,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
