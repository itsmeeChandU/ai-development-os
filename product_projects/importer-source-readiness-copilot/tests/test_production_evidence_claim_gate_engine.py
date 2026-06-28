from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.production_evidence_claim_gate_engine import (
    STATUS,
    build_production_evidence_claim_gate_engine,
    can_show_claim,
    write_production_evidence_claim_gate_engine_artifacts,
)


PACKET_ID = "packet-frozen-tuna-canada-001"


class ProductionEvidenceClaimGateEngineTests(unittest.TestCase):
    def test_claim_gate_manifest_keeps_external_claims_closed(self) -> None:
        manifest = build_production_evidence_claim_gate_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertGreaterEqual(manifest["packet_count"], 1)
        self.assertGreaterEqual(manifest["claim_type_count"], 17)
        self.assertEqual(manifest["claim_gate_decision_count"], manifest["packet_count"] * manifest["claim_type_count"])
        self.assertGreater(manifest["safe_research_claim_count"], 0)
        self.assertGreater(manifest["blocked_claim_count"], 0)
        self.assertGreaterEqual(manifest["forbidden_external_claim_count"], 6)
        self.assertGreater(manifest["evidence_mapper_count"], 0)
        self.assertEqual(manifest["claim_gate_mapper_count"], manifest["claim_type_count"])
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["live_payment_ready"])

    def test_can_show_claim_allows_source_backed_preparation_only(self) -> None:
        manifest = build_production_evidence_claim_gate_engine(ROOT)
        decision = can_show_claim("hs_candidate_research_route", PACKET_ID, manifest=manifest)

        self.assertTrue(decision["can_show_claim"])
        self.assertEqual(decision["display_level"], "safe_research_or_preparation_statement")
        self.assertIn("HS candidate", decision["allowed_wording"])
        self.assertGreaterEqual(decision["evidence_count"], 2)
        evidence_ids = {row["evidence_id"] for row in decision["evidence_trail"]}
        self.assertIn("source:wco-harmonized-system", evidence_ids)
        self.assertIn("source:cbsa-customs-tariff-2026", evidence_ids)
        self.assertFalse(decision["claims_opened"])
        self.assertFalse(decision["external_effects_created"])

    def test_document_gap_does_not_open_document_field_claim(self) -> None:
        manifest = build_production_evidence_claim_gate_engine(ROOT)
        decision = can_show_claim("document_field_extraction_draft", PACKET_ID, manifest=manifest)

        self.assertFalse(decision["can_show_claim"])
        self.assertEqual(decision["reason"], "missing_required_evidence")
        self.assertIn("missing customer document field extraction", decision["missing_evidence"])
        self.assertIn("missing required evidence type: document_field", decision["missing_evidence"])

    def test_forbidden_external_claims_fail_closed(self) -> None:
        manifest = build_production_evidence_claim_gate_engine(ROOT)
        for claim_type in (
            "tariff_confirmed",
            "cfia_approved",
            "buyer_validated",
            "supplier_verified",
            "customs_ready",
            "shipment_approved",
        ):
            decision = can_show_claim(claim_type, PACKET_ID, manifest=manifest)
            self.assertFalse(decision["can_show_claim"], claim_type)
            self.assertEqual(decision["display_level"], "blocked_external_or_unproven_claim")
            self.assertEqual(decision["allowed_wording"], "")
            self.assertFalse(decision["claims_opened"])
            self.assertIn(claim_type, manifest["blocked_external_claims"])

    def test_missing_origin_supplier_and_responsibility_proof_stays_blocked(self) -> None:
        manifest = build_production_evidence_claim_gate_engine(ROOT)
        expected_missing = {
            "origin_evidence_collected": "missing required evidence type: document or origin_document or reviewer_finding",
            "supplier_evidence_collected": "missing required evidence type: inspection_report or reviewer_finding or supplier_document or supplier_registration",
            "incoterms_responsibility_path": "missing packet field: importer_of_record",
        }
        for claim_type, missing_reason in expected_missing.items():
            decision = can_show_claim(claim_type, PACKET_ID, manifest=manifest)
            self.assertFalse(decision["can_show_claim"], claim_type)
            self.assertIn(missing_reason, decision["missing_evidence"])

    def test_mappers_store_claim_support_and_block_relationships(self) -> None:
        manifest = build_production_evidence_claim_gate_engine(ROOT)

        claim_gate_types = {row["claim_type"] for row in manifest["claim_gate_mappers"]}
        self.assertIn("hs_candidate_research_route", claim_gate_types)
        self.assertIn("tariff_confirmed", claim_gate_types)
        tariff_mapper = next(row for row in manifest["claim_gate_mappers"] if row["claim_type"] == "tariff_confirmed")
        self.assertTrue(tariff_mapper["forbidden_external_claim"])
        self.assertEqual(tariff_mapper["required_reviewer_lane"], "qualified_customs_review")

        source_mapper = next(
            row
            for row in manifest["evidence_mappers"]
            if row["evidence_id"] == "source:cbsa-customs-tariff-2026"
        )
        self.assertIn("hs_candidate_research_route", source_mapper["supports_claims"])
        self.assertIn("tariff_confirmed", source_mapper["blocks_claims"])

    def test_writer_creates_manifest_decisions_mappers_and_doc(self) -> None:
        manifest = build_production_evidence_claim_gate_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_evidence_claim_gate_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_decisions = json.loads(paths["decisions"].read_text(encoding="utf-8"))
            written_mappers = json.loads(paths["mappers"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_decisions["status"], "production_claim_gate_decisions_ready_fail_closed")
            self.assertEqual(written_mappers["status"], "production_evidence_claim_mappers_ready")
            self.assertIn("Production Evidence Claim-Gate Engine", written_doc)
            self.assertIn("Claims opened: false", written_doc)


if __name__ == "__main__":
    unittest.main()
