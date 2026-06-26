from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from importer_source_readiness.operator_app import make_server


MUTABLE_GENERATED_PATHS = [
    ROOT / "system_review_graph" / "customer_source_packets.json",
    ROOT / "system_review_graph" / "evidence_ledger.json",
    ROOT / "system_review_graph" / "customer_readiness_report.json",
    ROOT / "system_review_graph" / "customer_readiness_report.md",
    ROOT / "system_review_graph" / "customer_ai_review_runs.json",
    ROOT / "system_review_graph" / "customer_workflow.sqlite",
    ROOT / "system_review_graph" / "product_runtime_state.json",
    ROOT / "system_review_graph" / "auth_rbac_matrix.json",
    ROOT / "system_review_graph" / "claims_gate_matrix.json",
    ROOT / "system_review_graph" / "review_requests.json",
    ROOT / "system_review_graph" / "report_exports.json",
    ROOT / "system_review_graph" / "audit_events.json",
    ROOT / "system_review_graph" / "deletion_requests.json",
    ROOT / "system_review_graph" / "deployment_readiness_report.json",
    ROOT / "system_review_graph" / "private_beta_readiness_checklist.json",
    ROOT / "system_review_graph" / "ai_data_policy.json",
    ROOT / "system_review_graph" / "model_endpoints.json",
    ROOT / "system_review_graph" / "ai_model_router.json",
    ROOT / "system_review_graph" / "redaction_pipeline.json",
    ROOT / "system_review_graph" / "manual_no_ai_workflow.json",
    ROOT / "system_review_graph" / "requirements_traceability_matrix.json",
    ROOT / "system_review_graph" / "customer_action_log.json",
    ROOT / "system_review_graph" / "public_trade_readiness_manifest.json",
    ROOT / "system_review_graph" / "exporter_mode_requirements.json",
    ROOT / "system_review_graph" / "public_report_types.json",
    ROOT / "system_review_graph" / "public_upload_policy.json",
    ROOT / "system_review_graph" / "public_upload_manifest.json",
    ROOT / "system_review_graph" / "completion_platform_manifest.json",
    ROOT / "system_review_graph" / "country_coverage_report.json",
    ROOT / "system_review_graph" / "opportunity_scanner_report.json",
    ROOT / "system_review_graph" / "transport_readiness_report.json",
    ROOT / "system_review_graph" / "billing_credit_controls.json",
    ROOT / "system_review_graph" / "agent_api_manifest.json",
    ROOT / "system_review_graph" / "traffic_pages_manifest.json",
    ROOT / "system_review_graph" / "research_execution_plan.json",
    ROOT / "system_review_graph" / "team_workspace_report.json",
    ROOT / "system_review_graph" / "expert_network_report.json",
    ROOT / "system_review_graph" / "billing_usage_ledger.json",
    ROOT / "system_review_graph" / "agent_api_gateway_contract.json",
    ROOT / "system_review_graph" / "launch_operations_report.json",
    ROOT / "system_review_graph" / "all_stage_readiness_report.json",
]


class OperatorAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(ROOT, "127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_home_serves_customer_landing(self) -> None:
        with urlopen(f"{self.base_url}/", timeout=5) as response:
            html = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn("Trade Readiness Copilot", html)
        self.assertIn("know what is missing", html)
        self.assertIn("Start without documents", html)
        self.assertIn("PDF Triage", html)

    def test_completion_stage_public_pages_and_api_exist(self) -> None:
        routes = {
            "/opportunities": "Opportunity Signals",
            "/country-coverage": "Country Coverage",
            "/transport-readiness": "Transport Readiness",
            "/pricing": "Billing And Credits",
            "/billing": "Billing And Credits",
            "/billing/usage": "Billing Usage",
            "/agent-api": "Agent API",
            "/stages": "All Product Stages",
            "/research-plan": "Research Execution",
            "/expert-network": "Expert Network",
            "/team-workspace": "Team Workspace",
            "/launch-operations": "Launch Operations",
            "/reports/sample": "Sample Reports",
            "/ai-data-policy": "AI Data Policy",
            "/security": "Security And Privacy",
            "/tools/document-check": "Quick Trade Readiness Check",
            "/tools/import-export-starter-checklist": "Import Export Starter Checklist",
            "/packets/packet-frozen-tuna-canada-001/source-monitoring": "Source Monitoring",
            "/packets/packet-frozen-tuna-canada-001/safe-summary": "ChatGPT-Safe Summary",
        }
        for path, expected in routes.items():
            with self.subTest(path=path):
                with urlopen(f"{self.base_url}{path}", timeout=5) as response:
                    body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn(expected, body)

        api_routes = {
            "/api/opportunities": "opportunity_scanner_ready_with_research_gates",
            "/api/country-coverage": "country_coverage_ready_with_claim_gates",
            "/api/billing/controls": "billing_credit_controls_ready_local_no_live_checkout",
            "/api/billing/usage": "billing_usage_ledger_ready_local_no_charges",
            "/api/agent-api": "agent_api_manifest_ready_scoped_and_metered",
            "/api/agent-api/gateway": "agent_api_gateway_ready_local_dry_run",
            "/api/traffic-pages": "traffic_pages_manifest_ready",
            "/api/transport-readiness": "transport_readiness_ready_with_forwarder_gates",
            "/api/stages": "all_local_stages_implemented_with_external_gates",
            "/api/research-plan": "research_execution_ready_with_evidence_gates",
            "/api/expert-network": "expert_network_ready_local_with_human_review_gates",
            "/api/team-workspace": "team_workspace_ready_local_with_approval_gates",
            "/api/launch-operations": "launch_operations_ready_for_private_beta_review",
        }
        for path, expected_status in api_routes.items():
            with self.subTest(path=path):
                with urlopen(f"{self.base_url}{path}", timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.status, 200)
                self.assertEqual(payload["status"], expected_status)

        with urlopen(f"{self.base_url}/api/agent-tools/generate_missing_evidence_report", timeout=5) as response:
            dry_run = json.loads(response.read().decode("utf-8"))
        self.assertEqual(dry_run["status"], "agent_tool_dry_run_ready")
        self.assertFalse(dry_run["external_effects_created"])

    def test_beginner_start_creates_starter_packet(self) -> None:
        generated_paths = [
            *MUTABLE_GENERATED_PATHS,
            ROOT / "system_review_graph" / "expert_review_packet_packet-beginner-cumin-starter.md",
        ]
        backups = {path: path.read_bytes() if path.exists() else None for path in generated_paths}
        body = urlencode(
            {
                "accept_notice": "accepted",
                "product_name": "Beginner cumin starter",
                "product_category": "food_import",
                "origin_country": "India",
                "destination_country": "Canada",
                "trade_direction": "export",
                "current_stage": "idea",
                "unknown_fields": "HS code, importer of record, certificates",
                "research_depth_requested": "starter checklist",
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/public/starter",
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
                return None

        try:
            opener = build_opener(NoRedirect)
            with self.assertRaises(HTTPError) as ctx:
                opener.open(request, timeout=5)
            self.assertEqual(ctx.exception.code, 303)
            self.assertEqual(ctx.exception.headers["Location"], "/public/packets/packet-beginner-cumin-starter/result")

            with urlopen(f"{self.base_url}/public/packets/packet-beginner-cumin-starter/result", timeout=5) as response:
                html = response.read().decode("utf-8")
            self.assertIn("Beginner cumin starter", html)
            self.assertIn("Starter Checklist", html)
            self.assertIn("Beginner mode", html)
        finally:
            for path, content in backups.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)

    def test_public_tool_selection_and_quick_check_upload_pdf_flow(self) -> None:
        generated_paths = [
            *MUTABLE_GENERATED_PATHS,
            ROOT / "system_review_graph" / "expert_review_packet_packet-india-turmeric-export.md",
            ROOT / "system_review_graph" / "source_refresh_report_packet-india-turmeric-export.json",
        ]
        backups = {path: path.read_bytes() if path.exists() else None for path in generated_paths}
        upload_root = ROOT / "system_review_graph" / "public_uploads"
        with tempfile.TemporaryDirectory() as tmp:
            upload_backup = Path(tmp) / "public_uploads"
            if upload_root.exists():
                shutil.copytree(upload_root, upload_backup)
            try:
                with urlopen(f"{self.base_url}/tools", timeout=5) as response:
                    tools = response.read().decode("utf-8")
                self.assertIn("Export Readiness Checker", tools)

                with urlopen(f"{self.base_url}/tools/export-readiness", timeout=5) as response:
                    form = response.read().decode("utf-8")
                self.assertIn("Quick Trade Readiness Check", form)
                self.assertIn("Importer of record", form)

                boundary = "----ISRBoundary"
                fields = {
                    "accept_notice": "accepted",
                    "trade_direction": "export",
                    "product_name": "India turmeric export",
                    "product_category": "food_import",
                    "origin_country": "India",
                    "destination_country": "Canada",
                    "exporter_name": "Example Exporter Pvt Ltd",
                    "buyer_name": "",
                    "importer_of_record": "unknown",
                    "incoterms_if_known": "unknown",
                    "product_documents": "product spec PDF",
                }
                parts: list[bytes] = []
                for key, value in fields.items():
                    parts.append(
                        (
                            f"--{boundary}\r\n"
                            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                            f"{value}\r\n"
                        ).encode("utf-8")
                    )
                parts.append(
                    (
                        f"--{boundary}\r\n"
                        'Content-Disposition: form-data; name="documents"; filename="turmeric-product-spec.pdf"\r\n'
                        "Content-Type: application/pdf\r\n\r\n"
                    ).encode("utf-8")
                    + b"%PDF-1.4\n1 0 obj <<>> endobj\n%%EOF\n"
                    + b"\r\n"
                )
                parts.append(f"--{boundary}--\r\n".encode("utf-8"))
                request = Request(
                    f"{self.base_url}/api/public/quick-check",
                    data=b"".join(parts),
                    method="POST",
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                )

                class NoRedirect(HTTPRedirectHandler):
                    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
                        return None

                opener = build_opener(NoRedirect)
                with self.assertRaises(HTTPError) as ctx:
                    opener.open(request, timeout=5)
                self.assertEqual(ctx.exception.code, 303)
                location = ctx.exception.headers["Location"]
                self.assertEqual(location, "/public/packets/packet-india-turmeric-export/result")

                with urlopen(f"{self.base_url}{location}", timeout=5) as response:
                    result_html = response.read().decode("utf-8")
                self.assertIn("Export-to-Canada Packet", result_html)
                self.assertIn("Blocked - not ready for shipment decision", result_html)
                self.assertIn("Generate Buyer Packet", result_html)
                self.assertIn("Confirm Extracted Fields", result_html)
                self.assertIn("Missing Evidence PDF", result_html)
                self.assertIn("Delete Uploaded Files", result_html)
                self.assertNotIn("system_review_graph", result_html)

                with urlopen(f"{self.base_url}/public/packets/packet-india-turmeric-export/confirm", timeout=5) as response:
                    confirm_html = response.read().decode("utf-8")
                self.assertIn("Confirm Extracted Fields", confirm_html)
                self.assertIn("turmeric-product-spec.pdf", confirm_html)

                manifest = json.loads((ROOT / "system_review_graph" / "public_upload_manifest.json").read_text(encoding="utf-8"))
                packet_manifest = next(row for row in manifest["packets"] if row["packet_id"] == "packet-india-turmeric-export")
                self.assertEqual(packet_manifest["files"][0]["filename"], "document-001.pdf")
                self.assertEqual(packet_manifest["files"][0]["original_filename"], "turmeric-product-spec.pdf")
                self.assertTrue(packet_manifest["files"][0]["user_confirmation_required"])
                self.assertIn("extraction_status", packet_manifest["files"][0])

                with self.assertRaises(HTTPError) as blocked_ctx:
                    urlopen(f"{self.base_url}/system_review_graph/{packet_manifest['files'][0]['relative_path'].removeprefix('system_review_graph/')}", timeout=5)
                self.assertEqual(blocked_ctx.exception.code, 403)

                confirm_body = urlencode(
                    {
                        "fields_confirmed": "accepted",
                        "product_name": "India turmeric export",
                        "origin_country": "India",
                        "destination_country": "Canada",
                        "importer_of_record": "unknown",
                        "incoterms_if_known": "unknown",
                    }
                ).encode("utf-8")
                confirm_request = Request(
                    f"{self.base_url}/api/public/packets/packet-india-turmeric-export/confirm",
                    data=confirm_body,
                    method="POST",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                with urlopen(confirm_request, timeout=5) as response:
                    confirmed = json.loads(response.read().decode("utf-8"))
                self.assertEqual(confirmed["status"], "public_packet_fields_confirmed")
                self.assertEqual(confirmed["packet"]["confirmation_status"], "user_confirmed_draft_fields")

                with urlopen(f"{self.base_url}/api/public/packets/packet-india-turmeric-export/chatgpt-safe-summary", timeout=5) as response:
                    safe_summary = json.loads(response.read().decode("utf-8"))
                self.assertEqual(safe_summary["status"], "chatgpt_safe_summary_ready")
                self.assertIn("Do not provide legal", safe_summary["copy_paste_summary"])

                with urlopen(f"{self.base_url}/api/public/packets/packet-india-turmeric-export/reports/broker.pdf", timeout=5) as response:
                    pdf = response.read()
                self.assertEqual(response.status, 200)
                self.assertTrue(pdf.startswith(b"%PDF"))

                with urlopen(f"{self.base_url}/api/public/packets/packet-india-turmeric-export/reports/starter.pdf", timeout=5) as response:
                    starter_pdf = response.read()
                self.assertTrue(starter_pdf.startswith(b"%PDF"))

                delete_request = Request(
                    f"{self.base_url}/api/public/packets/packet-india-turmeric-export/delete-files",
                    data=b"",
                    method="POST",
                )
                with urlopen(delete_request, timeout=5) as response:
                    deletion = json.loads(response.read().decode("utf-8"))
                self.assertEqual(deletion["status"], "public_upload_files_deleted")
            finally:
                shutil.rmtree(upload_root, ignore_errors=True)
                if upload_backup.exists():
                    shutil.copytree(upload_backup, upload_root)
                for path, content in backups.items():
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_bytes(content)

    def test_operator_route_serves_operator_dashboard(self) -> None:
        with urlopen(f"{self.base_url}/operator", timeout=5) as response:
            html = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn("Operator Work Queue", html)

    def test_api_index_declares_operator_surface(self) -> None:
        with urlopen(f"{self.base_url}/api", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(payload["surface"], "local_customer_operator_expert_application")
        self.assertEqual(payload["runtime_status"], "private_beta_candidate_with_external_human_gates")
        self.assertEqual(payload["operator_status"], "operator_workflow_ready_internal")
        self.assertEqual(payload["operator_display_status"], "Operator workbench usable for internal review")
        self.assertEqual(payload["customer_workflow_status"], "customer_workflow_ready_internal")
        self.assertEqual(payload["customer_stage_status"], "Customer packet prototype active - real customer use not enabled")
        self.assertIn("local session auth", payload["auth_status"])
        self.assertIn("/review/:token", payload["routes"])
        self.assertGreaterEqual(payload["customer_packet_count"], 1)
        self.assertFalse("public_launch_claim" in payload["allowed_use"])

    def test_api_operator_workflow_returns_queue(self) -> None:
        with urlopen(f"{self.base_url}/api/operator-workflow", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(payload["status"], "operator_workflow_ready_internal")
        self.assertGreaterEqual(payload["work_queue_count"], 20)

    def test_unknown_route_404s(self) -> None:
        with self.assertRaises(HTTPError) as ctx:
            urlopen(f"{self.base_url}/../../pyproject.toml", timeout=5)

        self.assertEqual(ctx.exception.code, 404)

    def test_route_specific_artifact_roots_block_traversal(self) -> None:
        blocked_paths = [
            "/system_review_graph/../README.md",
            "/system_review_graph/%2e%2e/README.md",
            "/operator_screenshots/../readiness_report.json",
            "/operator_screenshots/%2e%2e/readiness_report.json",
        ]
        for path in blocked_paths:
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as ctx:
                    urlopen(f"{self.base_url}{path}", timeout=5)
                self.assertIn(ctx.exception.code, {403, 404})

    def test_customer_source_packet_routes_render_safe_report(self) -> None:
        with urlopen(f"{self.base_url}/packets", timeout=5) as response:
            listing = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("Customer Source Packet", listing)
        self.assertIn("Internal logic ready - external claims blocked", listing)
        self.assertIn("Blocked - source freshness missing", listing)

        packet_url = f"{self.base_url}/packets/packet-frozen-tuna-canada-001/readiness"
        with urlopen(packet_url, timeout=5) as response:
            report = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("Readiness Report", report)
        self.assertIn("Tariff/HS classification", report)
        self.assertIn("Missing Evidence", report)
        self.assertNotIn("safe_to_import", report)

    def test_customer_source_packet_guided_pages_exist(self) -> None:
        routes = {
            "/packets/packet-frozen-tuna-canada-001": "Refresh Official Sources",
            "/packets/packet-frozen-tuna-canada-001/evidence": "AI processing mode",
            "/packets/packet-frozen-tuna-canada-001/blockers": "Resolve",
            "/packets/packet-frozen-tuna-canada-001/ai-reviews": "AI simulated reviews",
            "/packets/packet-frozen-tuna-canada-001/reviews": "Scoped review link",
            "/packets/packet-frozen-tuna-canada-001/reports": "Reports",
            "/packets/packet-frozen-tuna-canada-001/source-monitoring": "Source Monitoring",
            "/packets/packet-frozen-tuna-canada-001/safe-summary": "ChatGPT-Safe Summary",
            "/settings/ai-data-policy": "Requirement Traceability",
            "/privacy": "Privacy Notice",
            "/terms": "Terms",
            "/ai-use": "AI Use",
            "/data-retention": "Data Retention",
            "/review/review-token-packet-frozen-tuna-canada-001": "Out Of Scope",
            "/admin/sources": "Official Source Registry",
            "/admin/gates": "Private Beta Gates",
            "/admin/audit": "Audit",
            "/admin/system-health": "System Health",
        }
        for path, expected in routes.items():
            with self.subTest(path=path):
                with urlopen(f"{self.base_url}{path}", timeout=5) as response:
                    body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn(expected, body)

    def test_customer_source_packet_export_includes_gate_context(self) -> None:
        path = "/packets/packet-frozen-tuna-canada-001/export"
        with urlopen(f"{self.base_url}{path}", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["packet_id"], "packet-frozen-tuna-canada-001")
        self.assertEqual(
            payload["customer_stage_status"],
            "Customer packet prototype active - real customer use not enabled",
        )
        self.assertEqual(payload["private_beta_status"], "blocked")
        self.assertGreaterEqual(len(payload["blocker_groups"]), 4)
        self.assertEqual(payload["private_beta_readiness"]["status"], "blocked")
        self.assertGreaterEqual(len(payload["private_beta_readiness"]["blocked"]), 4)
        self.assertIn("Customer packet prototype", payload["private_beta_readiness"]["ready"])
        self.assertGreaterEqual(len(payload["ai_review_runs"]), 1)
        self.assertIn("Tariff/HS classification", payload["blocked_claims"])

    def test_customer_source_packet_post_creates_local_readiness_report(self) -> None:
        generated_paths = [
            *MUTABLE_GENERATED_PATHS,
            ROOT / "system_review_graph" / "expert_review_packet_packet-local-test-product.md",
        ]
        backups = {path: path.read_bytes() if path.exists() else None for path in generated_paths}
        body = urlencode(
            {
                "packet_name": "Local test packet",
                "product_name": "Local test product",
                "product_category": "food_import",
                "origin_country": "Mexico",
                "destination_country": "Canada",
                "supplier_name": "Local Supplier",
                "supplier_country": "Mexico",
                "source_url": "https://example.com/source",
                "intended_use": "Local source readiness review",
                "csrf_token": "local-dev-csrf-token",
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/packets",
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
                return None

        try:
            opener = build_opener(NoRedirect)
            with self.assertRaises(HTTPError) as ctx:
                opener.open(request, timeout=5)
            self.assertEqual(ctx.exception.code, 303)
            self.assertIn(
                "/packets/packet-local-test-product/readiness",
                ctx.exception.headers["Location"],
            )
        finally:
            for path, content in backups.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)

    def test_ai_policy_api_and_permission_patch_work(self) -> None:
        backups = {path: path.read_bytes() if path.exists() else None for path in MUTABLE_GENERATED_PATHS}
        try:
            with urlopen(f"{self.base_url}/api/orgs/current/ai-policy", timeout=5) as response:
                policy = json.loads(response.read().decode("utf-8"))
            self.assertEqual(policy["policy"]["default_mode"], "redacted")
            self.assertEqual(policy["router"]["status"], "ai_model_router_ready")

            endpoint_body = urlencode({"mode": "metadata_only"}).encode("utf-8")
            endpoint_request = Request(
                f"{self.base_url}/api/orgs/current/ai-policy/test-model-endpoint",
                data=endpoint_body,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urlopen(endpoint_request, timeout=5) as response:
                endpoint = json.loads(response.read().decode("utf-8"))
            self.assertEqual(endpoint["status"], "endpoint_contract_ready")
            self.assertFalse(endpoint["live_call_made"])

            patch_body = urlencode({"ai_processing_mode": "no_ai", "sensitivity_level": "confidential"}).encode("utf-8")
            patch_request = Request(
                f"{self.base_url}/api/evidence/evidence-frozen-tuna-cid-reference/ai-permission",
                data=patch_body,
                method="PATCH",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urlopen(patch_request, timeout=5) as response:
                patched = json.loads(response.read().decode("utf-8"))
            self.assertEqual(patched["status"], "ai_permission_updated")
            self.assertEqual(patched["evidence"]["ai_processing_mode"], "no_ai")
            self.assertFalse(patched["route_decision"]["allowed"])
            self.assertEqual(patched["route_decision"]["mode"], "no_ai")
        finally:
            for path, content in backups.items():
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)

    def test_rbac_blocks_cross_org_packet_access(self) -> None:
        request = Request(
            f"{self.base_url}/api/packets/packet-frozen-tuna-canada-001",
            headers={"X-ISR-Session": "other-customer-session"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=5)
        self.assertEqual(ctx.exception.code, 403)

    def test_api_supports_auth_health_and_scoped_review(self) -> None:
        with urlopen(f"{self.base_url}/healthz", timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
        self.assertEqual(health["status"], "ok")

        login_body = urlencode({"email": "operator@example.local"}).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/auth/login",
            data=login_body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertTrue(payload["authenticated"])
        self.assertIn("isr_session=operator-session", response.headers["Set-Cookie"])

        with urlopen(f"{self.base_url}/api/external-review/review-token-packet-frozen-tuna-canada-001", timeout=5) as response:
            review = json.loads(response.read().decode("utf-8"))
        self.assertEqual(review["review_request"]["packet_id"], "packet-frozen-tuna-canada-001")


if __name__ == "__main__":
    unittest.main()
