from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from importer_source_readiness.payment_activation_proof import (
    DISABLED_SCOPE_CATEGORIES,
    REQUIRED_PROOF_CATEGORIES,
    STATUS,
    build_payment_activation_contract,
    build_payment_activation_proof_intake,
    validate_payment_activation_record,
    write_payment_activation_proof_artifacts,
)


def _evidence_artifacts() -> dict[str, str]:
    return {
        row["category"]: f"https://evidence.example/payment/{row['category']}.pdf"
        for row in REQUIRED_PROOF_CATEGORIES
    }


def _complete_live_record() -> dict[str, object]:
    return {
        "payment_scope_id": "starter-packet-live-scope",
        "payment_provider": "stripe",
        "environment_mode": "stripe_live_mode",
        "owner_name": "Billing Owner",
        "checked_at": "2026-06-29",
        "build_or_commit_ref": "commit:1432f02",
        "decision": "activate_live_checkout_for_scope",
        "evidence_artifacts": _evidence_artifacts(),
    }


class PaymentActivationProofTests(unittest.TestCase):
    def test_contract_defines_payment_evidence_without_opening_claims(self) -> None:
        contract = build_payment_activation_contract("2026-06-29T00:00:00Z")

        self.assertEqual(contract["status"], "payment_activation_proof_contract_ready_claims_closed")
        self.assertEqual(contract["required_evidence_category_count"], len(REQUIRED_PROOF_CATEGORIES))
        self.assertGreaterEqual(contract["source_anchor_count"], 6)
        self.assertFalse(contract["claims_opened"])

    def test_complete_live_record_accepts_payment_evidence_without_enabling_checkout(self) -> None:
        validation = validate_payment_activation_record(_complete_live_record(), "2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "accepted_live_payment_activation_scope_evidence")
        self.assertTrue(validation["accepted_for_payment_activation_evidence"])
        self.assertTrue(validation["live_payment_ready_by_payment_evidence"])
        self.assertFalse(validation["live_checkout_enabled_by_intake"])
        self.assertFalse(validation["external_charge_created"])
        self.assertFalse(validation["public_launch_ready_by_payment_evidence"])
        self.assertFalse(validation["claims_opened_by_validation"])

    def test_stripe_test_mode_never_counts_as_live_activation(self) -> None:
        record = _complete_live_record()
        record["environment_mode"] = "stripe_test_mode"

        validation = validate_payment_activation_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "received_activation_without_live_mode")
        self.assertFalse(validation["accepted_for_payment_activation_evidence"])
        self.assertTrue(validation["test_mode_only"])

    def test_disabled_payment_scope_can_be_recorded_without_live_payment_claim(self) -> None:
        record = {
            "payment_scope_id": "public-preview-no-paid-checkout",
            "payment_provider": "stripe",
            "environment_mode": "disabled_for_launch",
            "owner_name": "Founder",
            "checked_at": "2026-06-29",
            "build_or_commit_ref": "commit:1432f02",
            "decision": "not_applicable_for_this_launch",
            "evidence_artifacts": {
                category: f"https://evidence.example/payment-disabled/{category}.pdf"
                for category in DISABLED_SCOPE_CATEGORIES
            },
        }

        validation = validate_payment_activation_record(record, "2026-06-29T00:00:00Z")

        self.assertEqual(validation["status"], "accepted_live_payment_disabled_scope_evidence")
        self.assertTrue(validation["accepted_for_payment_activation_evidence"])
        self.assertFalse(validation["live_payment_ready_by_payment_evidence"])
        self.assertFalse(validation["live_checkout_enabled_by_intake"])
        self.assertFalse(validation["external_charge_created"])

    def test_current_repo_has_no_payment_proof_and_stays_blocked(self) -> None:
        manifest = build_payment_activation_proof_intake(ROOT, "2026-06-29T00:00:00Z")

        self.assertEqual(manifest["status"], STATUS)
        self.assertEqual(manifest["payment_record_count"], 0)
        self.assertEqual(manifest["accepted_payment_record_count"], 0)
        self.assertEqual(manifest["missing_evidence_category_count"], len(REQUIRED_PROOF_CATEGORIES))
        self.assertEqual(manifest["blocker_export_count"], len(REQUIRED_PROOF_CATEGORIES))
        self.assertFalse(manifest["live_payment_ready_by_payment_evidence"])
        self.assertFalse(manifest["live_checkout_enabled_by_intake"])
        self.assertFalse(manifest["external_charge_created"])
        self.assertFalse(manifest["public_launch_ready_by_payment_evidence"])
        self.assertFalse(manifest["claims_opened_by_intake"])

    def test_writer_creates_payment_activation_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = write_payment_activation_proof_artifacts(root, "2026-06-29T00:00:00Z")

            self.assertEqual(result["status"], STATUS)
            self.assertTrue((root / "system_review_graph" / "payment_activation_proof_contract.json").exists())
            self.assertTrue((root / "system_review_graph" / "payment_activation_proof_manifest.json").exists())
            self.assertTrue((root / "system_review_graph" / "payment_activation_gate_matrix.json").exists())
            self.assertTrue((root / "system_review_graph" / "payment_activation_blocker_export.jsonl").exists())
            self.assertTrue((root / "docs" / "PAYMENT_ACTIVATION_PROOF.md").exists())

    def test_complete_record_loaded_from_external_input_counts_as_payment_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "external_inputs"
            input_dir.mkdir()
            (input_dir / "live_payment_activation_proof.json").write_text(
                json.dumps(_complete_live_record()),
                encoding="utf-8",
            )

            manifest = build_payment_activation_proof_intake(root, "2026-06-29T00:00:00Z")

        self.assertEqual(manifest["payment_record_count"], 1)
        self.assertEqual(manifest["accepted_payment_record_count"], 1)
        self.assertEqual(manifest["missing_evidence_category_count"], 0)
        self.assertEqual(manifest["blocked_gate_count"], 0)
        self.assertTrue(manifest["live_payment_ready_by_payment_evidence"])
        self.assertFalse(manifest["live_checkout_enabled_by_intake"])
        self.assertFalse(manifest["public_launch_ready_by_payment_evidence"])


if __name__ == "__main__":
    unittest.main()
