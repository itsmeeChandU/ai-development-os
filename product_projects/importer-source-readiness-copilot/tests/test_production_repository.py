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

from importer_source_readiness.production_repository import (
    DEFAULT_PACKET_ID,
    STATUS,
    ProductionRepository,
    build_production_repository_service,
    write_production_repository_artifacts,
)


class ProductionRepositoryTests(unittest.TestCase):
    def test_repository_reads_packet_context_from_domain_store(self) -> None:
        repository = ProductionRepository(ROOT / "system_review_graph" / "production_domain.sqlite")
        context = repository.packet_context(DEFAULT_PACKET_ID, organization_id="org-importer-demo")

        self.assertEqual(context["status"], "packet_context_ready_from_production_repository")
        self.assertEqual(context["packet"]["claim_boundary_status"], "external_claims_closed")
        self.assertEqual(context["trade_lane"]["destination_country"], "CA")
        self.assertGreaterEqual(len(context["evidence_items"]), 3)
        self.assertGreaterEqual(len(context["decision_scores"]), 6)
        self.assertGreaterEqual(len(context["reports"]), 12)
        self.assertGreaterEqual(context["safe_claim_count"], 7)
        self.assertGreaterEqual(context["blocked_claim_decision_count"], 10)
        self.assertFalse(context["external_claims_opened"])
        self.assertFalse(context["public_launch_ready"])

    def test_repository_enforces_tenant_scope_and_claims_fail_closed(self) -> None:
        repository = ProductionRepository(ROOT / "system_review_graph" / "production_domain.sqlite")

        denied = repository.packet_context(DEFAULT_PACKET_ID, organization_id="org-other")
        safe = repository.can_show_claim(DEFAULT_PACKET_ID, "product_context_recorded", organization_id="org-importer-demo")
        blocked = repository.can_show_claim(DEFAULT_PACKET_ID, "tariff_confirmed", organization_id="org-importer-demo")
        missing = repository.can_show_claim(DEFAULT_PACKET_ID, "not_registered_claim", organization_id="org-importer-demo")

        self.assertEqual(denied["status"], "access_denied")
        self.assertTrue(safe["can_show_claim"])
        self.assertFalse(blocked["can_show_claim"])
        self.assertFalse(missing["can_show_claim"])
        self.assertEqual(missing["reason"], "claim_gate_mapper_missing")
        self.assertFalse(blocked["external_claims_opened"])

    def test_report_context_is_database_backed_and_not_approval(self) -> None:
        repository = ProductionRepository(ROOT / "system_review_graph" / "production_domain.sqlite")
        report = repository.report_context(DEFAULT_PACKET_ID, organization_id="org-importer-demo")

        self.assertEqual(report["status"], "database_backed_report_context_ready")
        self.assertEqual(report["watermark"], "DRAFT - NOT APPROVAL")
        self.assertGreaterEqual(len(report["visible_claims"]), 7)
        self.assertGreaterEqual(len(report["blocked_claims"]), 10)
        self.assertGreaterEqual(len(report["score_summary"]), 6)
        self.assertFalse(report["external_claims_opened"])
        self.assertFalse(report["public_launch_ready"])

    def test_writer_creates_repository_manifest_context_report_and_doc(self) -> None:
        payload = build_production_repository_service(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph = root / "system_review_graph"
            graph.mkdir(parents=True)
            source_store = ROOT / "system_review_graph" / "production_domain.sqlite"
            target_store = graph / "production_domain.sqlite"
            target_store.write_bytes(source_store.read_bytes())
            paths = write_production_repository_artifacts(payload, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            context = json.loads(paths["packet_context"].read_text(encoding="utf-8"))
            report_context = json.loads(paths["report_context"].read_text(encoding="utf-8"))
            doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(manifest["status"], STATUS)
            self.assertEqual(context["status"], "packet_context_ready_from_production_repository")
            self.assertEqual(report_context["status"], "database_backed_report_context_ready")
            self.assertIn("Production Repository Service", doc)


if __name__ == "__main__":
    unittest.main()
