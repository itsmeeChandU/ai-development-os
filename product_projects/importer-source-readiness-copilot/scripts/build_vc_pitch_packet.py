#!/usr/bin/env python3
"""Build the VC pitch readiness packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness import build_vc_pitch_readiness, load_json, write_json  # noqa: E402


def _bullet(rows: list[str]) -> str:
    return "\n".join(f"- {row}" for row in rows)


def _source_lines(rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {row['source_name']}: {row['source_url']} ({row['claim_boundary']})"
        for row in rows
    )


def _write_markdown(path: Path, title: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")
    return path


def _write_pitch_deck(report: dict[str, Any]) -> Path:
    slides = [
        ("1. Company", report["one_line"]),
        (
            "2. Problem",
            "Import/export source work crosses official sources, country requirements, "
            "buyer validation, contracts, data rights, and qualified compliance review. "
            "Teams need a proof surface before they make claims.",
        ),
        (
            "3. Product",
            "The copilot turns source cards into readiness reports, blocker ledgers, "
            "operator dashboards, continuation lanes, and investor-safe proof boundaries.",
        ),
        (
            "4. Why Now",
            "Global and U.S. trade remain large, current rules shift, and AI-native "
            "operators can move faster only when evidence gates are explicit.",
        ),
        (
            "5. Wedge",
            "Start with internal source-readiness review for import/export operators "
            "before public supplier, tariff, buyer, or compliance claims.",
        ),
        (
            "6. Demo",
            "\n".join(report["demo_script"]),
        ),
        (
            "7. Moat",
            "Repo-native proof gates, continuation lanes, SRG/code-review graph context, "
            "and generated blocker truth make the workflow auditable instead of chat-only.",
        ),
        (
            "8. Business Model Hypothesis",
            "Design-partner pilots first, then paid operator workflows for sourcing, "
            "trade compliance prep, and source-readiness evidence rooms.",
        ),
        (
            "9. Ask",
            f"Draft ask: ${report['draft_funding_ask']['amount_usd']:,} for "
            f"{report['draft_funding_ask']['runway_months']} months. Use of funds:\n"
            + _bullet(report["draft_funding_ask"]["use_of_funds"]),
        ),
        (
            "10. Diligence",
            "Open lanes remain visible and are part of the pitch, not hidden. "
            "They are buyer discovery, design partner, compliance, data rights, "
            "business model, and legal/financing review.",
        ),
    ]
    body = "\n\n".join(f"## {title}\n\n{text}" for title, text in slides)
    body += "\n\n## Closed Claims\n\n" + _bullet(report["closed_claims"])
    body += "\n\n## Sources\n\n" + _source_lines(report["investor_sources"])
    return _write_markdown(ROOT / "investor" / "vc_pitch_deck.md", "VC Pitch Deck", body)


def _write_one_pager(report: dict[str, Any]) -> Path:
    body = f"""## Status

- pitch status: `{report['status']}`
- demo ready: `{report['demo_ready']}`
- continuation status: `{report['startup_continuation_status']}`
- continuation lanes: `{report['continuation_lane_count']}`
- open external blockers: `{report['open_external_blockers']}`

## One Line

{report['one_line']}

## Investor Thesis

AI can build the software loop quickly, but import/export source claims still
need official sources, dated evidence, buyer validation, contracts, and
qualified review. This product makes that boundary operational.

## Draft Ask

- amount: `${report['draft_funding_ask']['amount_usd']:,}`
- runway: `{report['draft_funding_ask']['runway_months']}` months
- boundary: {report['draft_funding_ask']['boundary']}

## Sources

{_source_lines(report['investor_sources'])}
"""
    return _write_markdown(ROOT / "investor" / "one_pager.md", "Investor One Pager", body)


def _write_demo_script(report: dict[str, Any]) -> Path:
    body = "## Demo Steps\n\n" + _bullet(report["demo_script"])
    body += "\n\n## Talk Track\n\n"
    body += (
        "The demo proves local operator readiness and proof boundaries. It does not "
        "claim external operational readiness. The strongest point is that the system "
        "knows what it cannot yet claim and creates the next evidence lanes."
    )
    return _write_markdown(ROOT / "investor" / "demo_script.md", "Investor Demo Script", body)


def _write_diligence_index(report: dict[str, Any]) -> Path:
    lines = []
    for lane in report["diligence_lanes"]:
        lines.append(
            f"- `{lane['id']}` ({lane['owner']}): {lane['required_evidence']} "
            f"Next: {lane['next_valid_move']}"
        )
    body = "## Open Diligence Lanes\n\n" + "\n".join(lines)
    body += "\n\n## Closed Claims\n\n" + _bullet(report["closed_claims"])
    body += "\n\n## Proof Boundary\n\n" + report["proof_boundary"]
    return _write_markdown(ROOT / "investor" / "diligence_room_index.md", "Diligence Room Index", body)


def main() -> int:
    report = build_vc_pitch_readiness(
        readiness=load_json(ROOT / "system_review_graph" / "readiness_report.json"),
        external=load_json(ROOT / "system_review_graph" / "external_gate_report.json"),
        continuation=load_json(ROOT / "system_review_graph" / "continuation_plan.json"),
        investor_evidence=load_json(ROOT / "data" / "investor_evidence.json"),
    )
    out = write_json(report, ROOT / "system_review_graph" / "vc_pitch_readiness_report.json")
    artifacts = [
        str(_write_pitch_deck(report)),
        str(_write_one_pager(report)),
        str(_write_demo_script(report)),
        str(_write_diligence_index(report)),
    ]
    print(
        json.dumps(
            {
                "out": str(out),
                "status": report["status"],
                "diligence_lanes": len(report["diligence_lanes"]),
                "artifacts": artifacts,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
