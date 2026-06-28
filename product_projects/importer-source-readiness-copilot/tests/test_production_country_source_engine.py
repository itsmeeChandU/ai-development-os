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

        self.assertIn("cbsa-import-commercial-goods", sources)
        self.assertIn("cfia-airs", sources)
        self.assertIn("canada-cid", sources)
        self.assertEqual(sources["cbsa-import-commercial-goods"]["source_state"], "checked_current_reference_only")
        self.assertEqual(sources["cfia-airs"]["source_state"], "checked_current_reference_only")
        self.assertEqual(sources["canada-cid"]["source_state"], "checked_current_reference_only")
        self.assertEqual(sources["cbsa-customs-tariff-2026"]["source_state"], "not_checked")
        self.assertIn("tariff_confirmed", sources["cbsa-customs-tariff-2026"]["blocked_claims"])
        self.assertIn("cfia_approved", impact["blocked_claims"])
        self.assertIn("tariff_confirmed", impact["blocked_claims"])
        self.assertTrue(impact["packet_stale_if_material_change"])
        self.assertFalse(impact["external_claims_opened"])
        self.assertIn("regulated_goods", impact["needed_source_areas"])
        self.assertIn("broker_directory", impact["needed_source_areas"])

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
            written_doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(written_packs["status"], "production_country_packs_ready_reference_only_claims_closed")
            self.assertEqual(written_lifecycle["status"], "production_source_lifecycle_ready_reference_only_claims_closed")
            self.assertIn("Production Country Source Engine", written_doc)
            self.assertIn("External claims opened: false", written_doc)


if __name__ == "__main__":
    unittest.main()
