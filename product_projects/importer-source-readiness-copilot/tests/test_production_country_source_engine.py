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

from importer_source_readiness.production_country_source_engine import (
    CANADA_REQUIRED_SOURCE_AREAS,
    COUNTRY_PACK_ORDER,
    STATUS,
    build_production_country_source_engine,
    write_production_country_source_engine_artifacts,
)


class ProductionCountrySourceEngineTests(unittest.TestCase):
    def test_country_source_engine_builds_required_packs_from_registry(self) -> None:
        manifest = build_production_country_source_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["country_pack_count"], 4)
        self.assertEqual(manifest["country_pack_order"], list(COUNTRY_PACK_ORDER))
        self.assertGreaterEqual(manifest["source_lifecycle_count"], 20)
        self.assertGreaterEqual(manifest["researched_source_fact_count"], 18)
        self.assertGreaterEqual(manifest["packet_impact_count"], 1)
        self.assertFalse(manifest["external_effects_created"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["public_launch_ready"])
        self.assertFalse(manifest["hosted_private_beta_ready"])
        self.assertFalse(manifest["live_payment_ready"])

        packs = {row["country_pack_id"]: row for row in manifest["country_packs"]}
        self.assertEqual(set(packs), set(COUNTRY_PACK_ORDER))
        self.assertEqual(packs["CA-import"]["coverage_level"], "reference_only")
        self.assertEqual(packs["IN-export"]["coverage_level"], "reference_only")
        self.assertEqual(packs["VN-demo-origin"]["coverage_level"], "reference_only")
        self.assertEqual(packs["GENERIC-fallback"]["coverage_level"], "generic")
        self.assertTrue(set(CANADA_REQUIRED_SOURCE_AREAS).issubset(set(packs["CA-import"]["source_types_present"])))
        self.assertTrue(all(pack["external_claims_opened"] is False for pack in packs.values()))
        self.assertTrue(all(pack["reviewer_required"] for pack in packs.values()))

    def test_source_lifecycle_and_packet_impacts_fail_closed(self) -> None:
        manifest = build_production_country_source_engine(ROOT)
        sources = {row["source_id"]: row for row in manifest["source_lifecycle"]}
        impact = manifest["packet_source_impacts"][0]

        self.assertIn("refresh_attempted_not_verified", manifest["source_state_values"])
        self.assertIn("cbsa-import-commercial-goods", sources)
        self.assertIn("cfia-airs", sources)
        self.assertIn("canada-cid", sources)
        self.assertEqual(sources["cbsa-import-commercial-goods"]["source_state"], "checked_current_reference_only")
        self.assertEqual(sources["cfia-airs"]["source_state"], "checked_current_reference_only")
        self.assertIn(
            sources["canada-cid"]["source_state"],
            {"checked_current_reference_only", "refresh_attempted_not_verified", "source_unavailable"},
        )
        if sources["canada-cid"]["source_state"] != "checked_current_reference_only":
            self.assertFalse(sources["canada-cid"]["claims_opened"])
        self.assertEqual(sources["cbsa-customs-tariff-2026"]["source_state"], "not_checked")
        self.assertIn("tariff_confirmed", sources["cbsa-customs-tariff-2026"]["blocked_claims"])
        self.assertIn("cfia_approved", impact["blocked_claims"])
        self.assertIn("tariff_confirmed", impact["blocked_claims"])
        self.assertTrue(impact["packet_stale_if_material_change"])
        self.assertFalse(impact["external_claims_opened"])
        self.assertIn("regulated_goods", impact["needed_source_areas"])
        self.assertIn("broker_directory", impact["needed_source_areas"])

    def test_per_packet_refresh_report_can_replace_aggregate_and_failed_refresh_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "system_review_graph").mkdir()
            source_url = "https://www.cbsa-asfc.gc.ca/import/menu-eng.html"
            (root / "data" / "official_source_registry.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "cbsa-import-commercial-goods",
                            "name": "CBSA commercial import process",
                            "url": source_url,
                            "jurisdiction": "Canada",
                            "evidence_role": "Canada import process route",
                            "claim_boundary": "Reference route only.",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (root / "data" / "customer_source_packets.json").write_text(
                json.dumps(
                    [
                        {
                            "packet_id": "packet-test",
                            "origin_country": "India",
                            "destination_country": "Canada",
                            "product_name": "Frozen seafood",
                            "product_category": "food",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (root / "system_review_graph" / "source_refresh_report_packet-test.json").write_text(
                json.dumps(
                    {
                        "refresh_run_id": "source-refresh-packet-test-20260629T000000Z",
                        "packet_id": "packet-test",
                        "actor": "local_operator",
                        "generated_at": "2026-06-29T00:00:00+00:00",
                        "status": "source_refresh_recorded",
                        "row_count": 1,
                        "rows": [
                            {
                                "evidence_id": "evidence-cbsa",
                                "source_url": source_url,
                                "http_status": 0,
                                "content_hash": "abc",
                                "source_changed": False,
                                "freshness_status": "needs_current_refresh_before_claims",
                                "error": "DNS failure",
                            }
                        ],
                        "claim_boundary": "Refresh attempts are not approval evidence.",
                    }
                ),
                encoding="utf-8",
            )

            manifest = build_production_country_source_engine(root)

        source = manifest["source_lifecycle"][0]
        impact = manifest["packet_source_impacts"][0]
        self.assertEqual(manifest["source_refresh_run_count"], 1)
        self.assertEqual(manifest["source_refresh_record_count"], 1)
        self.assertEqual(source["source_state"], "refresh_attempted_not_verified")
        self.assertEqual(source["verification_status"], "network_or_dns_refresh_not_verified")
        self.assertFalse(source["claims_opened"])
        self.assertEqual(len(manifest["source_snapshot_history"]), 1)
        self.assertEqual(manifest["source_snapshot_history"][0]["source_state"], "refresh_attempted_not_verified")
        self.assertEqual(len(manifest["source_refresh_audit_events"]), 1)
        self.assertEqual(impact["packet_source_state"], "source_stale_or_review_required")
        self.assertEqual(impact["packet_stale_status"], "stale_until_source_refresh_and_review")
        self.assertIn("cbsa-import-commercial-goods:refresh_attempted_not_verified", impact["packet_stale_reasons"])

    def test_writer_creates_manifest_country_packs_lifecycle_and_doc(self) -> None:
        manifest = build_production_country_source_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_country_source_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            written_packs = json.loads(paths["country_packs"].read_text(encoding="utf-8"))
            written_lifecycle = json.loads(paths["source_lifecycle"].read_text(encoding="utf-8"))
            written_snapshot_history = json.loads(paths["source_snapshot_history"].read_text(encoding="utf-8"))
            written_refresh_audit = json.loads(paths["source_refresh_audit_events"].read_text(encoding="utf-8"))
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_packs["status"], "production_country_packs_ready_reference_only_claims_closed")
            self.assertEqual(written_lifecycle["status"], "production_source_lifecycle_ready_reference_only_claims_closed")
            self.assertEqual(written_snapshot_history["status"], "production_source_snapshot_history_recorded_claims_closed")
            self.assertEqual(written_refresh_audit["status"], "production_source_refresh_audit_events_recorded_claims_closed")
            self.assertIn("Production Country Source Engine", written_doc)
            self.assertIn("External claims opened: false", written_doc)


if __name__ == "__main__":
    unittest.main()
