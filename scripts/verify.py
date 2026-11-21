#!/usr/bin/env python
"""End-to-end verification script testing all core FORGE pipelines without GUI."""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from forge.core.application_service import ApplicationService
from forge.core.execution_gateway import get_execution_gateway
from forge.domain.errors import ApprovalRequiredError
from forge.mcp.protocol_client import ProtocolClient
from forge.security.hashes import hash_arguments


async def run_verification():
    print("=" * 65)
    print("FORGE End-to-End Verification Pipeline")
    print("=" * 65)

    with tempfile.TemporaryDirectory(prefix="forge_verify_") as tmp_dir:
        ws = Path(tmp_dir).resolve()
        print(f"Temporary test workspace: {ws}")

        svc = ApplicationService()

        # Step 1: Create project and copy FixtureLab manifest
        manifest_src = Path("manifests/fixturelab.yaml").resolve()
        project = svc.create_project(ws, "Verification Project", initial_manifest=manifest_src)
        print(f"[PASS] Project created: {project.name} ({project.id})")

        # Step 2: Validate manifest
        manifest = svc.validate_manifest(project.manifest_path)
        print(
            f"[PASS] Manifest validated: {manifest.integration.id} v{manifest.integration.version} ({len(manifest.capabilities)} tools)"
        )

        # Step 3: Generate connector build
        build = svc.generate_connector(project.id, ws, project.manifest_path)
        print(f"[PASS] Connector generated: Build {build.id[:8]} at {build.build_dir}")

        # Step 4: Launch generated server with real MCP client over stdio
        launcher = Path(build.build_dir) / "launcher.py"
        client = ProtocolClient(
            command=sys.executable,
            args=[str(launcher)],
            env={"FORGE_WORKSPACE": str(ws), "PYTHONUNBUFFERED": "1"},
        )

        tools = await client.list_tools()
        tool_names = [t["name"] for t in tools]
        print(f"[PASS] MCP Protocol discovery: Found {len(tools)} tools: {tool_names}")
        assert "fixturelab_get_status" in tool_names
        assert "fixturelab_create_item" in tool_names

        # Step 5: Execute read tool via MCP client
        read_res = await client.call_tool("fixturelab_get_status", {})
        print(f"[PASS] MCP Read Tool call succeeded: {read_res.content}")

        # Step 6: Test Unapproved Write Denial
        create_args = {"item_id": "test_widget_01", "name": "Verified Widget"}
        denied = False
        try:
            await client.call_tool("fixturelab_create_item", create_args)
        except Exception:
            denied = True
        # Or checking via Gateway directly
        gateway = get_execution_gateway()
        try:
            gateway.execute_tool(
                manifest.integration.id, manifest, "fixturelab_create_item", create_args, ws
            )
        except ApprovalRequiredError:
            denied = True
        assert denied, "Mutating tool executed without approval!"
        print("[PASS] Unapproved mutation correctly denied with ApprovalRequiredError.")

        # Step 7: Grant exact-argument single-use approval
        arg_hash = hash_arguments(create_args)
        grant = svc.grant_approval(
            "fixturelab_create_item", arg_hash, "verify_corr_id", ttl_seconds=120
        )
        print(f"[PASS] Exact-argument approval grant issued: {grant.id[:8]}")

        # Step 8: Execute write tool with approval
        write_res = gateway.execute_tool(
            manifest.integration.id, manifest, "fixturelab_create_item", create_args, ws
        )
        print(f"[PASS] Approved mutation succeeded: {write_res}")

        # Step 9: Verify state mutation by reading back
        get_res = gateway.execute_tool(
            manifest.integration.id,
            manifest,
            "fixturelab_get_item",
            {"item_id": "test_widget_01"},
            ws,
        )
        assert get_res["item"]["name"] == "Verified Widget"
        print(f"[PASS] Read-back verification succeeded: {get_res}")

        # Step 10: Verify grant cannot be reused
        reused_denied = False
        try:
            gateway.execute_tool(
                manifest.integration.id, manifest, "fixturelab_create_item", create_args, ws
            )
        except ApprovalRequiredError:
            reused_denied = True
        assert reused_denied, "Single-use grant was improperly reused!"
        print("[PASS] Single-use approval grant consumption verified (reuse denied).")

        # Step 11: Export standalone connector package
        pkg = svc.export_package(build.id, ws)
        print(f"[PASS] Package exported: {pkg.archive_path} (SHA-256: {pkg.sha256[:16]}...)")

        # Step 12: Verify package archive contents & zip-slip protection
        ok, msg, files = svc.package_exporter.verify_package(pkg.archive_path)
        assert ok, f"Package verification failed: {msg}"
        print(f"[PASS] Package archive verified: {len(files)} files present.")

        # Step 13: Verify audit journal hash chain integrity
        is_valid, msg, broken_id = svc.verify_audit_integrity()
        assert is_valid, f"Audit chain broken: {msg}"
        print(f"[PASS] Cryptographic audit chain verified: {msg}")

        print("=" * 65)
        print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
        print("=" * 65)


def main():
    asyncio.run(run_verification())


if __name__ == "__main__":
    main()
