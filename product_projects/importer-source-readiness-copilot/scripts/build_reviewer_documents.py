#!/usr/bin/env python3
"""Build the three reviewer-facing current-state documents."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs" / "reviewer"
PDF_DIR = ROOT / "output" / "pdf"
GRAPH = ROOT / "system_review_graph"


@dataclass(frozen=True)
class Section:
    title: str
    body: tuple[str, ...] = ()
    bullets: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewerDocument:
    title: str
    filename: str
    subtitle: str
    sections: tuple[Section, ...]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _plain(text: Any) -> str:
    return str(text or "").replace("_", " ")


def _clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def _write_markdown(doc: ReviewerDocument) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / doc.filename
    lines = [f"# {doc.title}", "", doc.subtitle, ""]
    for section in doc.sections:
        lines.extend([f"## {section.title}", ""])
        for paragraph in section.body:
            lines.extend([paragraph, ""])
        if section.bullets:
            for bullet in section.bullets:
                lines.append(f"- {bullet}")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    footer = f"Trade Readiness Copilot reviewer document - page {doc.page}"
    canvas.drawRightString(7.5 * inch, 0.45 * inch, footer)
    canvas.restoreState()


def _write_pdf(doc: ReviewerDocument) -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    path = PDF_DIR / doc.filename.replace(".md", ".pdf")
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReviewerTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=26,
        textColor=colors.HexColor("#111827"),
        spaceAfter=8,
    )
    subtitle = ParagraphStyle(
        "ReviewerSubtitle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#475467"),
        spaceAfter=16,
    )
    heading = ParagraphStyle(
        "ReviewerHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1D2939"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "ReviewerBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14.5,
        textColor=colors.HexColor("#344054"),
        spaceAfter=7,
    )
    bullet_style = ParagraphStyle(
        "ReviewerBullet",
        parent=body,
        leftIndent=0,
        firstLineIndent=0,
        spaceAfter=4,
    )

    story: list[Any] = [
        Paragraph(_clean_inline(doc.title), title),
        Paragraph(_clean_inline(doc.subtitle), subtitle),
    ]
    for index, section in enumerate(doc.sections):
        if index and section.title in {"Reviewer Decision Requested", "Current Boundaries"}:
            story.append(PageBreak())
        story.append(Paragraph(_clean_inline(section.title), heading))
        for paragraph in section.body:
            story.append(Paragraph(_clean_inline(paragraph), body))
        if section.bullets:
            story.append(
                ListFlowable(
                    [
                        ListItem(Paragraph(_clean_inline(item), bullet_style), leftIndent=14)
                        for item in section.bullets
                    ],
                    bulletType="bullet",
                    start="circle",
                    leftIndent=16,
                )
            )
            story.append(Spacer(1, 5))

    pdf = SimpleDocTemplate(
        str(path),
        pagesize=LETTER,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.65 * inch,
        title=doc.title,
        author="Trade Readiness Copilot",
    )
    pdf.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path


def _status_context() -> dict[str, Any]:
    business = _load_json(GRAPH / "business_logic_phase_report.json")
    product_ops = _load_json(GRAPH / "product_operations_report.json")
    final_go_live = _load_json(GRAPH / "final_go_live_decision_report.json")
    external_validation = _load_json(GRAPH / "external_validation_requirements_report.json")
    production_document = _load_json(GRAPH / "production_document_intelligence_manifest.json")
    production_claim_gate = _load_json(GRAPH / "production_evidence_claim_gate_manifest.json")
    production_scoring = _load_json(GRAPH / "production_decision_scoring_manifest.json")
    production_ai = _load_json(GRAPH / "production_ai_copilot_manifest.json")
    row = business["packet_rows"][0]
    return {
        "today": date.today().isoformat(),
        "business": business,
        "product_ops": product_ops,
        "final_go_live": final_go_live,
        "external_validation": external_validation,
        "production_document": production_document,
        "production_claim_gate": production_claim_gate,
        "production_scoring": production_scoring,
        "production_ai": production_ai,
        "packet": row,
    }


def _functional(ctx: dict[str, Any]) -> ReviewerDocument:
    packet = ctx["packet"]
    ops = ctx["product_ops"]
    document = ctx["production_document"]
    claim_gate = ctx["production_claim_gate"]
    scoring = ctx["production_scoring"]
    ai_copilot = ctx["production_ai"]
    return ReviewerDocument(
        title="Functional Requirements For External Review",
        filename="functional_requirements_for_review.md",
        subtitle=(
            f"Prepared on {ctx['today']} for Trade Readiness Copilot. "
            "This is a current-state review document for the locally implemented product, not a public-launch claim."
        ),
        sections=(
            Section(
                "2-Minute Summary",
                body=(
                    "Trade Readiness Copilot helps an exporter or trade operator prepare a Trade Readiness Packet before taking external action. The product accepts product, country, party, and evidence details; then it shows what is known, what is missing, what source routes should be checked, and what the next safe action is.",
                    "The current product is usable for local review and controlled preparation. It does not approve imports or exports, confirm tariff or CFIA status, verify suppliers, validate buyers, send messages, collect payments, or approve public launch.",
                ),
            ),
            Section(
                "Users",
                bullets=(
                    "Public visitor: can start a quick check and receive a safe result.",
                    "Exporter or customer operator: can create packets, add evidence, review missing inputs, and export safe reports.",
                    "Internal operator: can review queues, source routes, evidence, and generated next steps.",
                    "Expert reviewer: can review a scoped packet and return findings for that exact scope.",
                    "Admin or support: can inspect audit, gates, health, and operational state.",
                ),
            ),
            Section(
                "Core Functions Implemented Now",
                bullets=(
                    "Create or inspect a Trade Readiness Packet.",
                    "Support a beginner flow with little or no documentation.",
                    "Support a no-document quick check that creates a missing-evidence packet without showing upload-only actions.",
                    "Support uploaded PDF triage with quarantine metadata, draft field extraction, user confirmation, delete-file action, and blocked-claim boundaries.",
                    "Record product, origin, destination, buyer/importer, supplier, Incoterms, HS-code candidate, source, and evidence details.",
                    "Maintain an evidence ledger and mark evidence as missing, reference-only, stale, or needing review.",
                    "Route users to official-source references without treating those references as approval.",
                    "Generate missing-evidence, starter checklist, buyer packet draft, broker/expert packet, safe summary, and business decision outputs.",
                    "Show grouped unresolved items and the next safe move.",
                    "Record local operation proof with `external_effects_created: false` and `claims_opened: false`.",
                ),
            ),
            Section(
                "Main Workflows",
                bullets=(
                    "Quick check: user gives product and country details, optionally adds documents, then receives missing evidence and next safe action.",
                    "Packet workspace: user reviews the packet, evidence, official-source routes, unresolved items, and report outputs.",
                    "Document intelligence: product separates official samples, synthetic parser QA fixtures, no-document intake, and customer-uploaded evidence.",
                    "Business decision preparation: product runs the decision tree, scores, source freshness check, buyer/supplier evidence ladder, and allowed/blocked action matrix.",
                    "Expert routing: product prepares a scoped packet for a human reviewer; AI cannot approve the lane.",
                    "Local operations: product can refresh source records, generate reports, create work orders, reserve billing internally, and record audit events without external effects.",
                ),
            ),
            Section(
                "Document Intelligence Implemented",
                bullets=(
                    f"Pipeline status: `{document['status']}`.",
                    f"Expected document classes: `{len(document.get('required_trade_document_classes', []))}`.",
                    f"Official sample PDFs downloaded: `{document.get('official_sample_document_count')}`.",
                    f"Synthetic parser QA PDFs generated: `{document.get('synthetic_parser_fixture_count')}`.",
                    "Parser output is draft evidence only and requires user confirmation before sharing.",
                    "No document parser output opens customs, tariff, CFIA, buyer, supplier, shipment, payment, legal, or launch gates.",
                ),
            ),
            Section(
                "Claim Gate Implemented",
                bullets=(
                    f"Claim-gate status: `{claim_gate['status']}`.",
                    f"Packet statements evaluated: `{claim_gate.get('claim_gate_decision_count')}`.",
                    f"Safe preparation statements currently showable: `{claim_gate.get('safe_research_claim_count')}`.",
                    f"Blocked packet statements: `{claim_gate.get('blocked_claim_count')}`.",
                    "The product can show source-routing and preparation language with an evidence trail.",
                    "It still blocks tariff confirmed, CFIA approved, buyer validated, supplier verified, customs ready, and shipment approved.",
                ),
            ),
            Section(
                "Decision Scoring Implemented",
                bullets=(
                    f"Scoring status: `{scoring['status']}`.",
                    f"Separate score records: `{scoring.get('decision_score_record_count')}`.",
                    "Scores remain separate for market signal, evidence completeness, source freshness, buyer/supplier evidence, responsibility clarity, and decision safety.",
                    "The product does not create one combined readiness score or approval label.",
                    "Every score includes a reason, cap, blocker fields, claim-gate dependency, and next action.",
                ),
            ),
            Section(
                "AI Copilot Implemented",
                bullets=(
                    f"AI copilot status: `{ai_copilot['status']}`.",
                    f"AI roles: `{ai_copilot.get('ai_role_count')}`.",
                    "AI can help draft, extract, summarize, prepare reviewer work orders, and flag wording risks.",
                    "AI outputs are labeled as draft, source-backed, needs user confirmation, needs expert review, or blocked.",
                    "Live model calls are disabled and AI cannot open product gates.",
                ),
            ),
            Section(
                "Enterprise And Advisor Use Cases",
                bullets=(
                    "Broker or trade advisor can manage multiple client packets and export missing-evidence or broker-review packets.",
                    "Enterprise sourcing team can compare lanes while seeing which country/source paths are full, partial, reference-only, or generic.",
                    "Compliance or legal reviewer can inspect blocked claims, source routes, evidence provenance, and the exact scope of requested review.",
                    "Security or privacy reviewer can inspect upload, AI, deletion, audit, and retention controls before real-user data is accepted.",
                    "Finance or billing reviewer can confirm that paid scope is preparation only and live checkout remains disabled until payment gates pass.",
                ),
            ),
            Section(
                "Current Product Proof",
                bullets=(
                    f"Business logic status: `{ctx['business']['status']}`.",
                    f"Operation status: `{ops['status']}`.",
                    f"Operation count in latest product run: `{ops.get('operation_count')}`.",
                    f"Sample packet: `{packet['packet_id']}`.",
                    "Product proof commands currently pass: product tests, product check, root product check, completion integrity audit, and AI Dev OS check.",
                ),
            ),
            Section(
                "Current Boundaries",
                bullets=(
                    "No customs, tariff, CFIA, legal, buyer, supplier, shipment, payment, or launch approval claim is opened.",
                    "No automatic buyer/supplier outreach is sent.",
                    "Live checkout is disabled.",
                    "Hosted private beta and public launch remain blocked until real external review and platform proof exist.",
                    "Official-source references are source routes only; they are not current-law proof or professional advice.",
                ),
            ),
            Section(
                "Reviewer Decision Requested",
                body=(
                    "Please review whether the implemented workflows are understandable, useful, and safe for a controlled private-beta candidate. A useful response can be short.",
                ),
                bullets=(
                    "Decision: approve for your reviewed scope, needs changes, or blocked.",
                    "Top issues that must change before private beta.",
                    "Any wording that sounds like approval, legal advice, customs advice, supplier verification, buyer validation, or launch readiness.",
                    "Any workflow gap that would stop a real exporter or reviewer from using the product.",
                ),
            ),
        ),
    )


def _business_logic(ctx: dict[str, Any]) -> ReviewerDocument:
    business = ctx["business"]
    packet = ctx["packet"]
    document = ctx["production_document"]
    claim_gate = ctx["production_claim_gate"]
    scoring = ctx["production_scoring"]
    ai_copilot = ctx["production_ai"]
    buyer_supplier = packet["buyer_supplier_evidence"]
    gate = packet["business_gate_decision"]
    market = packet["market_intelligence"]["market_signal_evaluation"]
    return ReviewerDocument(
        title="Business Logic Document For External Review",
        filename="business_logic_for_review.md",
        subtitle=(
            f"Prepared on {ctx['today']} for Trade Readiness Copilot. "
            "This document explains how the product makes local preparation decisions while keeping real-world claims closed."
        ),
        sections=(
            Section(
                "2-Minute Summary",
                body=(
                    "The product's business logic is now implemented for the local repo-controlled scope. It can prepare a packet, compute safe statuses, score the packet, show evidence gaps, and decide which local actions are allowed.",
                    "The logic deliberately does not approve trade action. It blocks stronger claims until real source freshness, buyer/supplier evidence, qualified review, security/privacy review, payment review, and public go/no-go approval exist.",
                ),
            ),
            Section(
                "Business Position",
                bullets=(
                    "Product name: Trade Readiness Copilot.",
                    "First wedge: foreign exporters preparing to sell into Canada.",
                    "First categories: food, seafood, agri, and general goods.",
                    "First persona: beginner-to-intermediate exporter.",
                    "Country path: Canada destination, Vietnam demo origin, India strategic next origin, Generic fallback.",
                    "Core object: Trade Readiness Packet.",
                ),
            ),
            Section(
                "Implemented Business Rules",
                bullets=(
                    "12-question decision tree: trade direction, product, origin, destination, HS code, buyer/importer, importer of record, Incoterms, documents, regulated-product risk, official sources, and next safe move.",
                    "Starter flow: checks minimum inputs and allows a starter packet when product, country, direction, intended use, and source routes exist.",
                    "Market signal: computes a bounded local signal from source routes and evidence, capped before real demand proof.",
                    "Country packs: checks whether required import, tariff, regulated-product, restricted-party, and market/buyer source routes exist.",
                    "Source freshness: evaluates attached evidence for freshness, last verification, content hash, and review status.",
                    "Buyer/supplier evidence: uses evidence ladders and blocks buyer-validated and supplier-verified language.",
                    "Business gate decision: allows local drafts and reports while blocking outreach, payment, approvals, and shipment decisions.",
                    "Phase coverage: exposes 13 business phase surfaces, while phase 0 remains the business identity lock.",
                ),
            ),
            Section(
                "Document Logic Implemented Now",
                body=(
                    "Document logic is now part of the packet decision system. The product accepts no-document intake as a valid beginner path and accepts PDFs as draft evidence only when upload checks pass.",
                ),
                bullets=(
                    "No-document intake creates a missing-evidence packet and does not show extracted-field confirmation or delete-uploaded-files actions.",
                    "Uploaded-document intake creates quarantine metadata, draft extraction rows, user-confirmation status, and deletion actions.",
                    f"Expected document classes covered locally: `{len(document.get('required_trade_document_classes', []))}`.",
                    f"Official sample PDFs stored for parser orientation: `{document.get('official_sample_document_count')}`.",
                    f"Synthetic filled parser QA PDFs stored for local parser testing: `{document.get('synthetic_parser_fixture_count')}`.",
                    "Official samples and synthetic QA files do not count as customer proof.",
                    "Every extracted field has provenance, confidence, user-confirmation status, claim boundary, supported claims, and blocked claims.",
                ),
            ),
            Section(
                "Claim Gate Logic Implemented Now",
                body=(
                    "The product now checks packet statements through a claim gate before showing them. This prevents a source route, user input, parser draft, or missing-document placeholder from being presented as real approval.",
                ),
                bullets=(
                    f"Claim decisions generated: `{claim_gate.get('claim_gate_decision_count')}`.",
                    f"Safe preparation/source-routing statements: `{claim_gate.get('safe_research_claim_count')}`.",
                    f"Blocked statements: `{claim_gate.get('blocked_claim_count')}`.",
                    "HS candidate, tariff route, CFIA route, market signal, and buyer lead-route statements can be shown only as preparation language.",
                    "Origin evidence, supplier evidence, Incoterms responsibility, and document extraction stay blocked when the required proof is missing.",
                    "Tariff confirmed, CFIA approved, buyer validated, supplier verified, customs ready, and shipment approved remain forbidden external claims.",
                ),
            ),
            Section(
                "Decision Scoring Logic Implemented Now",
                body=(
                    "The product explains decisions with six separate capped scores. It does not collapse the packet into a single readiness score, because that would hide risk.",
                ),
                bullets=(
                    f"Score records generated: `{scoring.get('decision_score_record_count')}`.",
                    "Market signal score shows whether deeper validation is worth doing, not whether demand is proven.",
                    "Evidence completeness score shows what is missing, not whether the packet is approved.",
                    "Source freshness score is capped when official/reference evidence is stale, reference-only, or unreviewed.",
                    "Buyer/supplier evidence score cannot say buyer validated or supplier verified.",
                    "Decision safety score remains red while forbidden external claims are blocked.",
                ),
            ),
            Section(
                "AI Copilot Logic Implemented Now",
                body=(
                    "AI is treated as a drafting and organization helper, not as a decision maker. Deterministic rules decide what can be shown.",
                ),
                bullets=(
                    f"AI role contracts generated: `{ai_copilot.get('ai_role_count')}`.",
                    f"AI output contracts generated: `{ai_copilot.get('ai_output_contract_count')}`.",
                    f"Prompt-injection checks generated: `{ai_copilot.get('prompt_injection_test_count')}`.",
                    "AI can produce drafts, source summaries, confirmation tasks, reviewer work orders, redaction prompts, and QA findings.",
                    "AI cannot approve customs, tariff, CFIA, buyer, supplier, payment, shipment, legal, or launch claims.",
                ),
            ),
            Section(
                "Current Sample Packet Result",
                bullets=(
                    f"Packet reviewed: `{packet['packet_id']}`.",
                    f"Business logic status: `{business['status']}`.",
                    f"Business phase surfaces: `{business['phase_count']}`.",
                    f"Market signal score: `{market['score']}` out of `{market['score_cap']}` before external evidence.",
                    f"Buyer evidence level: `{buyer_supplier['buyer']['current_label']}`.",
                    f"Supplier evidence level: `{buyer_supplier['supplier']['current_label']}`.",
                    f"Source freshness: `{packet['source_freshness']['status']}`.",
                    f"Customer-visible decision: `{gate['customer_visible_decision']}`.",
                ),
            ),
            Section(
                "Actions Allowed Locally",
                bullets=tuple(
                    f"{_plain(name)}: {value}"
                    for name, value in gate["local_actions_allowed"].items()
                ),
            ),
            Section(
                "Claims Still Blocked",
                bullets=tuple(_plain(item) for item in gate["external_actions_blocked"]),
            ),
            Section(
                "Evidence Needed Before Stronger Claims",
                bullets=(
                    "Dated official-source refresh and qualified review.",
                    "Qualified customs/trade review for country, tariff, CFIA, import controls, and claim language.",
                    "Dated buyer reply, call note, LOI, PO, or paid-order evidence before buyer-demand claims.",
                    "Supplier registration, export ability, product documents, inspection/certificate, and prior-shipment evidence before supplier confidence claims.",
                    "Security, privacy, AI-safety, DevOps, billing/payment, report-language, and launch-owner approval before hosted/private/public rollout.",
                ),
            ),
            Section(
                "Reviewer Decision Requested",
                body=(
                    "Please review whether the business rules make sense for a safe trade-readiness preparation product.",
                ),
                bullets=(
                    "Are any rules too weak or too strict for a controlled private-beta candidate?",
                    "Do any labels overclaim approval, compliance, buyer validation, supplier verification, or market demand?",
                    "Are the buyer and supplier evidence ladders reasonable?",
                    "What must change before this can be shown to real users?",
                ),
            ),
        ),
    )


def _non_functional(ctx: dict[str, Any]) -> ReviewerDocument:
    document = ctx["production_document"]
    claim_gate = ctx["production_claim_gate"]
    scoring = ctx["production_scoring"]
    ai_copilot = ctx["production_ai"]
    return ReviewerDocument(
        title="Non-Functional Requirements For External Review",
        filename="non_functional_requirements_for_review.md",
        subtitle=(
            f"Prepared on {ctx['today']} for Trade Readiness Copilot. "
            "This document focuses on security, privacy, AI safety, reliability, auditability, payments, and launch controls."
        ),
        sections=(
            Section(
                "2-Minute Summary",
                body=(
                    "The product is a local private-beta candidate with external human gates still closed. It has local controls for roles, audit, deletion tracking, AI-use boundaries, redaction preview, no-AI/manual workflow, claim gates, billing gates, and launch gates.",
                    "The product is not ready for unrestricted real files, live payments, public launch, or production claims until external review and hosted-platform proof are complete.",
                ),
            ),
            Section(
                "Security And Access",
                bullets=(
                    "Implemented locally: role model, organization boundary model, scoped review links, admin/gate/health surfaces, and audit event records.",
                    "Implemented locally for uploads: generated filenames, PDF signature checks, page limits, quarantine metadata, direct-file-serving blocks, and delete-file actions for uploaded quick-check files.",
                    "Required before hosted beta: real authentication, secure sessions, CSRF where needed, rate limits, malware scanning, private object storage, secret management, and security review signoff.",
                ),
            ),
            Section(
                "Privacy And Data Governance",
                bullets=(
                    "Implemented locally: AI-use policy, per-evidence AI permission concept, redaction preview, no-AI/manual fallback, deletion request tracking, and public upload notice.",
                    "Official sample PDFs, synthetic parser QA files, and customer-uploaded evidence are separated so test fixtures are not mistaken for customer proof.",
                    "Required before real user data: privacy notice, terms, retention/deletion approval, breach process, provider inventory, and review of whether any file content may be sent to AI providers.",
                ),
            ),
            Section(
                "Document Handling Boundary",
                body=(
                    "The document engine is ready for local review and parser QA. It is not yet approved for unrestricted real customer files in production.",
                ),
                bullets=(
                    f"Document pipeline status: `{document['status']}`.",
                    f"Pipeline stages tracked: `{document.get('pipeline_stage_count')}`.",
                    f"Official sample PDFs: `{document.get('official_sample_document_count')}`.",
                    f"Synthetic parser QA PDFs: `{document.get('synthetic_parser_fixture_count')}`.",
                    "Real file uploads remain blocked until hosted auth, private storage, malware scanning, retention/deletion approval, privacy/legal review, security review, monitoring, and incident response are proven.",
                ),
            ),
            Section(
                "AI Safety",
                bullets=(
                    "AI can summarize, structure, and create findings only when permitted.",
                    "AI cannot approve customs, tariff, CFIA, legal, buyer, supplier, payment, launch, or shipment claims.",
                    "Required before real documents: prompt-injection review, provider routing decision, redaction tests on real examples, incident process, and customer-facing AI-language review.",
                ),
            ),
            Section(
                "AI Copilot Controls",
                bullets=(
                    f"AI copilot status: `{ai_copilot['status']}`.",
                    f"Output contracts: `{ai_copilot.get('ai_output_contract_count')}`.",
                    f"Prompt-injection checks: `{ai_copilot.get('prompt_injection_test_count')}`.",
                    "Live model calls remain disabled.",
                    "Provider terms review and qualified AI safety review remain incomplete.",
                    "AI output contracts cannot open product gates.",
                ),
            ),
            Section(
                "Claim Safety",
                bullets=(
                    f"Evidence claim-gate status: `{claim_gate['status']}`.",
                    f"Evidence mapper rows: `{claim_gate.get('evidence_mapper_count')}`.",
                    f"Claim mapper rows: `{claim_gate.get('claim_gate_mapper_count')}`.",
                    "Missing, stale, reference-only, parser-draft, or unreviewed evidence cannot open external claims.",
                    "AI, source routes, uploaded documents, and generated reports cannot approve customs, tariff, CFIA, buyer, supplier, payment, shipment, legal, or launch claims.",
                ),
            ),
            Section(
                "Scoring Safety",
                bullets=(
                    f"Decision scoring status: `{scoring['status']}`.",
                    f"Score policy count: `{scoring.get('score_count')}`.",
                    "No single global readiness score is created.",
                    "No combined readiness label is created.",
                    "Approval language remains blocked even when a score is yellow or blue.",
                ),
            ),
            Section(
                "Reliability And Operations",
                bullets=(
                    "Implemented locally: repeatable report generation, SQLite workflow store, generated state files, operation log, proof commands, and deployment-readiness artifacts.",
                    "Required before hosted beta: managed database, object storage, backup policy, restore test, monitoring, rollback, incident runbook, and owner assignment.",
                ),
            ),
            Section(
                "Payments And Billing",
                bullets=(
                    "Implemented locally: billing controls, usage ledger, payment gate matrix, and live checkout disabled.",
                    "Required before payment activation: pricing decision, refund/support policy, tax/account review, processor setup, webhook handling, payment security review, and approval to activate live checkout.",
                ),
            ),
            Section(
                "Launch And External Claims",
                bullets=(
                    f"Final go-live status: `{ctx['final_go_live']['status']}`.",
                    "Public launch ready remains false.",
                    "External validation gates remain open until real reviewers, users, hosted proof, payment proof, buyer/supplier evidence, and launch-owner approval exist.",
                    "The product must keep `external_effects_created: false` and `claims_opened: false` in local operation proofs.",
                ),
            ),
            Section(
                "Reviewer Decision Requested",
                body=(
                    "Please review whether the non-functional controls are enough for the next controlled private-beta step, and what must change before hosted use or real customer data.",
                ),
                bullets=(
                    "Decision: approve for your reviewed scope, needs changes, or blocked.",
                    "Security/privacy/AI issues that must be fixed first.",
                    "Any data-retention, deletion, upload, logging, or access-control concern.",
                    "Any reason live payment, real-file beta, hosted beta, or public launch should stay blocked.",
                ),
            ),
        ),
    )


def main() -> int:
    ctx = _status_context()
    docs = (_business_logic(ctx), _functional(ctx), _non_functional(ctx))
    outputs = []
    for doc in docs:
        md = _write_markdown(doc)
        pdf = _write_pdf(doc)
        outputs.append({"markdown": str(md.relative_to(ROOT)), "pdf": str(pdf.relative_to(ROOT))})
    print(json.dumps({"status": "reviewer_documents_ready", "outputs": outputs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
