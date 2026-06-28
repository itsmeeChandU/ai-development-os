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

from importer_source_readiness.production_redevelopment import (
    build_production_redevelopment_plan,
    write_production_redevelopment_artifacts,
)


class ProductionRedevelopmentTests(unittest.TestCase):
    def test_redevelopment_plan_covers_all_phases_with_research_tracks(self) -> None:
        plan = build_production_redevelopment_plan()

        self.assertEqual(plan["status"], "production_redevelopment_contract_ready_with_external_build_gates")
        self.assertEqual(plan["production_layer_count"], 14)
        self.assertEqual(plan["phase_count"], 21)
        self.assertEqual(plan["research_anchor_count"], 18)
        self.assertGreaterEqual(plan["domain_entity_count"], 39)
        self.assertFalse(plan["external_claims_opened"])
        self.assertFalse(plan["public_launch_ready"])
        self.assertFalse(plan["hosted_production_ready"])
        self.assertFalse(plan["live_payment_ready"])

        phase_ids = {phase["phase"] for phase in plan["redevelopment_phases"]}
        self.assertEqual(phase_ids, set(range(21)))

        anchor_ids = {source["id"] for source in plan["research_anchors"]}
        official_source_ids = {
            row["id"]
            for row in json.loads((ROOT / "data" / "official_source_registry.json").read_text(encoding="utf-8"))
        }
        allowed_non_registry_ids = {
            "official_source_registry",
            "user_research_required",
            "enterprise_user_validation_required",
            "reviewer_findings",
            "user_validation_records",
        }
        allowed_source_ids = anchor_ids | official_source_ids | allowed_non_registry_ids

        for phase in plan["redevelopment_phases"]:
            for key in ("build_track", "research_track", "source_track", "evidence_track", "gate_track"):
                self.assertIn(key, phase)
                self.assertTrue(phase[key], f"phase {phase['phase']} missing {key}")
            self.assertTrue(all(1 <= layer_id <= 14 for layer_id in phase["layers"]))
            self.assertEqual(phase["claim_state"], "external_claims_closed")
            for source_id in phase["source_track"]:
                self.assertIn(source_id, allowed_source_ids)

    def test_research_layer_entities_and_sources_are_permanent_contracts(self) -> None:
        plan = build_production_redevelopment_plan()
        entity_names = {row["entity"] for row in plan["domain_entities"]}
        source_ids = {row["id"] for row in plan["research_anchors"]}
        registry_ids = {
            row["id"]
            for row in json.loads((ROOT / "data" / "official_source_registry.json").read_text(encoding="utf-8"))
        }

        for required_entity in (
            "ResearchIntake",
            "SourceRegistry",
            "SourceSnapshot",
            "DatasetConnector",
            "CountryPackSource",
            "MarketSignalSource",
            "LegalBoundarySource",
            "ExpertFindingSource",
            "EvidenceMapper",
            "ClaimGateMapper",
        ):
            self.assertIn(required_entity, entity_names)

        for required_source in (
            "cbsa-import-commercial-goods",
            "cbsa-customs-tariff-2026",
            "cbsa-licensed-customs-brokers",
            "cfia-airs",
            "gac-sanctions",
            "ised-trade-data-online",
            "canada-cid",
            "india-dgft-foreign-trade-policy",
            "world-bank-wits",
            "itc-trade-map",
            "itc-market-access-map",
            "wco-harmonized-system",
            "icc-incoterms-2020",
            "opc-pipeda-principles",
            "owasp-file-upload",
            "owasp-llm01-prompt-injection",
            "nist-ai-rmf",
            "stripe-go-live",
        ):
            self.assertIn(required_source, source_ids | registry_ids)

    def test_launch_control_plane_and_api_contracts_keep_external_effects_closed(self) -> None:
        plan = build_production_redevelopment_plan()
        control_plane = plan["launch_control_plane"]

        self.assertEqual(control_plane["status"], "launch_control_plane_contract_ready_public_launch_blocked")
        self.assertEqual(control_plane["gate_count"], 12)
        self.assertFalse(control_plane["public_launch_ready"])
        self.assertFalse(control_plane["hosted_production_ready"])
        self.assertFalse(control_plane["live_payment_ready"])
        self.assertTrue(all(gate["state"] == "blocked" for gate in control_plane["gates"]))

        self.assertTrue(plan["api_contracts"])
        for route in plan["api_contracts"]:
            self.assertFalse(route["external_effects_allowed"])
            self.assertIn("approval", route["forbidden"])
            self.assertIn("live_charge", route["forbidden"])

    def test_writer_creates_plan_research_and_review_doc(self) -> None:
        plan = build_production_redevelopment_plan()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_redevelopment_artifacts(plan, root)
            self.assertTrue(paths["plan"].exists())
            self.assertTrue(paths["research"].exists())
            self.assertTrue(paths["doc"].exists())

            written_plan = json.loads(paths["plan"].read_text(encoding="utf-8"))
            written_research = json.loads(paths["research"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")
            self.assertEqual(written_plan["phase_count"], 21)
            self.assertEqual(written_research["source_count"], 18)
            self.assertIn("Production Redevelopment Contract", written_doc)
            self.assertIn("External claims opened: false.", written_doc)


if __name__ == "__main__":
    unittest.main()
