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

from importer_source_readiness.production_payment_monetization_engine import (
    STATUS,
    build_production_payment_monetization_engine,
    write_production_payment_monetization_engine_artifacts,
)


class ProductionPaymentMonetizationEngineTests(unittest.TestCase):
    def test_manifest_defines_tiers_scope_and_closed_payment_gates(self) -> None:
        manifest = build_production_payment_monetization_engine(ROOT)

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["pricing_tier_count"], 7)
        self.assertEqual(manifest["research_reference_count"], 5)
        self.assertGreaterEqual(manifest["payment_gate_count"], 10)
        self.assertEqual(manifest["blocked_payment_gate_count"], manifest["payment_gate_count"])
        self.assertIn("prepared trade readiness packet", manifest["allowed_paid_scope"])
        self.assertIn("customs approval", manifest["forbidden_paid_scope"])
        self.assertFalse(manifest["external_charge_created"])
        self.assertFalse(manifest["live_checkout_enabled"])
        self.assertFalse(manifest["live_payment_ready"])
        self.assertFalse(manifest["checkout_url_created"])
        self.assertFalse(manifest["webhook_delivery_enabled"])
        self.assertFalse(manifest["claims_opened"])
        self.assertFalse(manifest["public_launch_ready"])

    def test_pricing_tiers_charge_for_preparation_not_approval(self) -> None:
        manifest = build_production_payment_monetization_engine(ROOT)

        paid_tiers = [row for row in manifest["pricing_tiers"] if row["paid"]]
        self.assertEqual(len(paid_tiers), 6)
        for tier in paid_tiers:
            self.assertFalse(tier["live_checkout_enabled"])
            self.assertFalse(tier["can_charge_for_approval"])
            self.assertTrue(tier["claim_language_review_required"])
            self.assertIn("tariff confirmation", tier["forbidden_scope"])
            self.assertIn("prepared trade readiness packet", tier["allowed_scope"])

    def test_checkout_and_webhook_controls_stay_closed(self) -> None:
        manifest = build_production_payment_monetization_engine(ROOT)

        for control in manifest["checkout_controls"]:
            if "live_mode_enabled" in control:
                self.assertFalse(control["live_mode_enabled"])
            if "external_charge_created" in control:
                self.assertFalse(control["external_charge_created"])
        for webhook in manifest["webhook_controls"]:
            self.assertFalse(webhook["delivery_enabled"])
            self.assertFalse(webhook["external_effects_created"])
            self.assertTrue(webhook["signature_verification_required"])
            self.assertTrue(webhook["idempotency_required"])
            self.assertTrue(webhook["duplicate_event_handling_required"])
            self.assertTrue(webhook["out_of_order_event_handling_required"])

    def test_writer_creates_payment_artifacts(self) -> None:
        manifest = build_production_payment_monetization_engine(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_production_payment_monetization_engine_artifacts(manifest, root)

            for path in paths.values():
                self.assertTrue(path.exists())

            written_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            pricing = json.loads(paths["pricing"].read_text(encoding="utf-8"))
            paid_scope = json.loads(paths["paid_scope"].read_text(encoding="utf-8"))
            webhooks = json.loads(paths["webhooks"].read_text(encoding="utf-8"))
            doc = paths["doc"].read_text(encoding="utf-8")

            self.assertEqual(written_manifest["status"], STATUS)
            self.assertEqual(pricing["status"], "production_pricing_tiers_ready_review_required")
            self.assertEqual(paid_scope["status"], "production_paid_scope_policy_ready")
            self.assertEqual(webhooks["status"], "production_payment_webhook_controls_ready_delivery_closed")
            self.assertIn("Production Payment Monetization Engine", doc)
            self.assertIn("Live checkout enabled: false", doc)


if __name__ == "__main__":
    unittest.main()
