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

from importer_source_readiness.production_data_model import (
    STATUS,
    build_production_data_model,
    render_postgres_schema,
    write_production_data_model_artifacts,
)


class ProductionDataModelTests(unittest.TestCase):
    def test_manifest_covers_first_rebuild_package_entities(self) -> None:
        manifest = build_production_data_model()
        table_names = {row["table"] for row in manifest["tables"]}

        self.assertEqual(manifest["status"], STATUS)
        self.assertGreaterEqual(manifest["table_count"], 38)
        self.assertGreaterEqual(manifest["foreign_key_count"], 35)
        self.assertGreaterEqual(manifest["check_constraint_count"], 25)
        self.assertGreaterEqual(manifest["index_count"], 30)
        self.assertGreaterEqual(manifest["row_level_security_table_count"], 25)
        self.assertGreaterEqual(manifest["domain_event_count"], 14)
        self.assertGreaterEqual(manifest["json_migration_map_count"], 8)
        self.assertFalse(manifest["hosted_database_ready"])
        self.assertFalse(manifest["production_migration_applied"])
        self.assertFalse(manifest["external_claims_opened"])
        self.assertFalse(manifest["public_launch_ready"])

        for required_table in (
            "organizations",
            "users",
            "workspaces",
            "trade_readiness_packets",
            "packet_events",
            "trade_lanes",
            "product_profiles",
            "country_packs",
            "source_records",
            "source_snapshots",
            "research_intakes",
            "dataset_connectors",
            "country_pack_sources",
            "documents",
            "extracted_fields",
            "field_provenance",
            "evidence_items",
            "evidence_mappers",
            "market_signals",
            "market_signal_sources",
            "buyer_profiles",
            "buyer_evidence_events",
            "supplier_profiles",
            "supplier_evidence_events",
            "responsibility_paths",
            "blocked_claims",
            "claim_gate_mappers",
            "decision_scores",
            "reviewer_lanes",
            "review_requests",
            "review_findings",
            "reports",
            "audit_events",
            "billing_accounts",
            "subscriptions",
            "usage_records",
        ):
            self.assertIn(required_table, table_names)

    def test_postgres_schema_has_integrity_and_tenant_isolation_controls(self) -> None:
        sql = render_postgres_schema()

        self.assertIn("create table if not exists trade_readiness_packets", sql)
        self.assertIn("references workspaces(workspace_id)", sql)
        self.assertIn("references trade_lanes(trade_lane_id)", sql)
        self.assertIn("constraint packet_state_check", sql)
        self.assertIn("constraint decision_scores_name_check", sql)
        self.assertIn("refresh_attempted_not_verified", sql)
        self.assertIn("checked_current_reference_only", sql)
        self.assertIn("buyer_supplier_evidence_score", sql)
        self.assertIn("constraint buyer_profiles_evidence_level_check", sql)
        self.assertIn("po_or_paid_order_received", sql)
        self.assertIn("constraint supplier_profiles_evidence_level_check", sql)
        self.assertIn("reviewer_assessed", sql)
        self.assertIn("alter table trade_readiness_packets enable row level security", sql)
        self.assertIn("current_setting('app.current_organization_id', true)", sql)
        self.assertIn("create index if not exists evidence_items_packet_idx", sql)
        self.assertIn("external_charge_created boolean not null default false", sql)
        self.assertNotIn("ready_to_ship' default", sql)

    def test_json_migration_map_and_seed_preserve_claim_boundaries(self) -> None:
        manifest = build_production_data_model()
        artifacts = {row["artifact"] for row in manifest["json_artifact_migration_map"]}
        seed = manifest["seed_fixture"]

        for artifact in (
            "system_review_graph/customer_source_packets.json",
            "system_review_graph/evidence_ledger.json",
            "data/official_source_registry.json",
            "system_review_graph/business_logic_phase_report.json",
            "system_review_graph/report_exports.json",
        ):
            self.assertIn(artifact, artifacts)

        self.assertEqual(seed["status"], "production_data_model_seed_ready_no_external_effects")
        self.assertEqual(seed["packet"]["packet_id"], "packet-frozen-tuna-canada-001")
        self.assertEqual(seed["packet"]["claim_boundary_status"], "external_claims_closed")
        self.assertIn("buyer_supplier_evidence_score", seed["decision_scores"])
        self.assertIn("ready_to_ship", seed["blocked_claims"])

    def test_writer_creates_migration_manifest_seed_and_doc(self) -> None:
        manifest = build_production_data_model()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_data_model_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_seed = json.loads(paths["seed"].read_text(encoding="utf-8"))
            written_sql = paths["migration"].read_text(encoding="utf-8")
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_seed["status"], "production_data_model_seed_ready_no_external_effects")
            self.assertIn("begin;", written_sql)
            self.assertIn("commit;", written_sql)
            self.assertIn("Production Data Model", written_doc)
            self.assertIn("Proof Boundary", written_doc)


if __name__ == "__main__":
    unittest.main()
