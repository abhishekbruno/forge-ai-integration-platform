"""Automated test orchestrator running contract, e2e, and safety test suites."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from forge.adapters.registry import get_adapter_registry
from forge.core.approval_broker import get_approval_broker
from forge.core.build_service import BuildService
from forge.core.execution_gateway import get_execution_gateway
from forge.core.manifest_service import get_manifest_service
from forge.domain.execution import TestCaseResult, TestRun, TestRunStatus
from forge.domain.project import Build
from forge.events.bus import get_event_bus
from forge.events.models import (
    EVENT_TEST_RUN_FINISHED,
    EVENT_TEST_RUN_STARTED,
    ForgeEvent,
)
from forge.persistence.db import get_db_manager
from forge.security.hashes import hash_arguments, hash_file


class TestOrchestrator:
    """Executes automated verification suites against generated connector packages."""

    __test__ = False

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path
        self.mgr = get_db_manager(db_path)
        self.build_service = BuildService(db_path)
        self.manifest_service = get_manifest_service()

    async def run_mcp_contract_tests(self, build: Build, workspace: Path) -> TestRun:
        """Execute MCP stdio contract verification using official MCP client session."""
        run_id = str(uuid4())
        ws = Path(workspace).resolve()
        build_dir = Path(build.build_dir).resolve()
        launcher_file = build_dir / "launcher.py"

        test_run = TestRun(
            id=run_id,
            build_id=build.id,
            test_type="mcp_contract",
            command=f"{sys.executable} {launcher_file}",
            status=TestRunStatus.RUNNING,
            start_time=datetime.now(timezone.utc).isoformat(),
        )

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TEST_RUN_STARTED,
                correlation_id=run_id,
                details={"build_id": build.id, "type": "mcp_contract"},
            )
        )

        test_cases: list[TestCaseResult] = []
        stdout_buf: list[str] = []
        stderr_buf: list[str] = []

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(launcher_file)],
            env={"FORGE_WORKSPACE": str(ws), "PYTHONUNBUFFERED": "1"},
        )

        start_time = time.monotonic()

        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # 1. Initialize session
                    await session.initialize()
                    stdout_buf.append("Session initialized successfully over stdio.\n")

                    # 2. List tools
                    t0 = time.monotonic()
                    tools_result = await session.list_tools()
                    d0 = time.monotonic() - t0
                    tool_names = [t.name for t in tools_result.tools]
                    stdout_buf.append(f"Discovered tools: {tool_names}\n")

                    test_cases.append(
                        TestCaseResult(
                            name="contract_list_tools",
                            status=TestRunStatus.PASSED if tool_names else TestRunStatus.FAILED,
                            duration_seconds=round(d0, 3),
                            error_message=None if tool_names else "No tools returned by MCP server",
                        )
                    )

                    # 3. Call a read tool if present
                    read_tool = None
                    for name in tool_names:
                        if "status" in name or "summary" in name or "list" in name:
                            read_tool = name
                            break

                    if read_tool and "fixturelab" in read_tool:
                        t1 = time.monotonic()
                        call_res = await session.call_tool(read_tool, arguments={})
                        d1 = time.monotonic() - t1
                        is_ok = not getattr(
                            call_res, "is_error", getattr(call_res, "isError", False)
                        )
                        stdout_buf.append(f"Called {read_tool}: {call_res.content}\n")
                        test_cases.append(
                            TestCaseResult(
                                name=f"contract_call_{read_tool}",
                                status=TestRunStatus.PASSED if is_ok else TestRunStatus.FAILED,
                                duration_seconds=round(d1, 3),
                                error_message=None if is_ok else str(call_res.content),
                            )
                        )

            overall_status = (
                TestRunStatus.PASSED
                if all(tc.status == TestRunStatus.PASSED for tc in test_cases)
                else TestRunStatus.FAILED
            )

        except Exception as exc:
            overall_status = TestRunStatus.FAILED
            stderr_buf.append(f"MCP client contract test failed: {exc}\n")
            test_cases.append(
                TestCaseResult(
                    name="contract_client_session",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - start_time, 3),
                    error_message=str(exc),
                )
            )

        time.monotonic() - start_time
        test_run.status = overall_status
        test_run.finish_time = datetime.now(timezone.utc).isoformat()
        test_run.test_cases = test_cases
        test_run.stdout = "".join(stdout_buf)
        test_run.stderr = "".join(stderr_buf)

        self._save_test_run(test_run)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TEST_RUN_FINISHED,
                correlation_id=run_id,
                details={"status": overall_status.value, "case_count": len(test_cases)},
            )
        )

        return test_run

    def run_fixturelab_e2e(self, build: Build, workspace: Path) -> TestRun:
        """Run complete synchronous end-to-end read, write, approval, and reuse-denial checks."""
        run_id = str(uuid4())
        ws = Path(workspace).resolve()

        test_run = TestRun(
            id=run_id,
            build_id=build.id,
            test_type="fixturelab_e2e",
            command="forge test --type fixturelab_e2e",
            status=TestRunStatus.RUNNING,
            start_time=datetime.now(timezone.utc).isoformat(),
        )

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TEST_RUN_STARTED,
                correlation_id=run_id,
                details={"build_id": build.id, "type": "fixturelab_e2e"},
            )
        )

        test_cases: list[TestCaseResult] = []
        gateway = get_execution_gateway(self.db_path)
        approval_broker = get_approval_broker(self.db_path)

        manifest_file = ws / "manifest.yaml"
        manifest = self.manifest_service.load_and_validate(manifest_file)

        # Step 1: Read get_status
        t0 = time.monotonic()
        try:
            status_res = gateway.execute_tool(
                connector_id="forge.fixturelab",
                manifest=manifest,
                tool_name="fixturelab_get_status",
                args={},
                workspace=ws,
            )
            assert "status" in status_res and "item_count" in status_res
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_read_status",
                    status=TestRunStatus.PASSED,
                    duration_seconds=round(time.monotonic() - t0, 3),
                )
            )
        except Exception as exc:
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_read_status",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - t0, 3),
                    error_message=str(exc),
                )
            )

        # Step 2: Write attempt WITHOUT approval -> MUST fail with ApprovalRequiredError
        t1 = time.monotonic()
        test_item_id = f"item-{uuid4().hex[:6]}"
        create_args = {"item_id": test_item_id, "name": "Test Widget", "category": "benchmark"}
        try:
            gateway.execute_tool(
                connector_id="forge.fixturelab",
                manifest=manifest,
                tool_name="fixturelab_create_item",
                args=create_args,
                workspace=ws,
            )
            # Should not reach here
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_unapproved_write_denial",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - t1, 3),
                    error_message="Mutating tool executed without approval!",
                )
            )
        except Exception:
            # Expected to be denied
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_unapproved_write_denial",
                    status=TestRunStatus.PASSED,
                    duration_seconds=round(time.monotonic() - t1, 3),
                )
            )

        # Step 3: Grant approval once for exact arguments
        arg_hash = hash_arguments(create_args)
        approval_broker.grant_approval(
            tool_name="fixturelab_create_item",
            argument_hash=arg_hash,
            correlation_id=run_id,
            ttl_seconds=120,
            actor="test_runner",
        )

        # Step 4: Write attempt WITH approval -> MUST succeed
        t2 = time.monotonic()
        try:
            create_res = gateway.execute_tool(
                connector_id="forge.fixturelab",
                manifest=manifest,
                tool_name="fixturelab_create_item",
                args=create_args,
                workspace=ws,
            )
            assert (
                create_res.get("success") is True and create_res.get("created_id") == test_item_id
            )
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_approved_write",
                    status=TestRunStatus.PASSED,
                    duration_seconds=round(time.monotonic() - t2, 3),
                )
            )
        except Exception as exc:
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_approved_write",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - t2, 3),
                    error_message=str(exc),
                )
            )

        # Step 5: Read created item back -> MUST match
        t3 = time.monotonic()
        try:
            get_res = gateway.execute_tool(
                connector_id="forge.fixturelab",
                manifest=manifest,
                tool_name="fixturelab_get_item",
                args={"item_id": test_item_id},
                workspace=ws,
            )
            assert (
                get_res["item"]["id"] == test_item_id and get_res["item"]["name"] == "Test Widget"
            )
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_read_back_created_item",
                    status=TestRunStatus.PASSED,
                    duration_seconds=round(time.monotonic() - t3, 3),
                )
            )
        except Exception as exc:
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_read_back_created_item",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - t3, 3),
                    error_message=str(exc),
                )
            )

        # Step 6: Attempt reusing same grant -> MUST be denied (single-use constraint)
        t4 = time.monotonic()
        try:
            gateway.execute_tool(
                connector_id="forge.fixturelab",
                manifest=manifest,
                tool_name="fixturelab_create_item",
                args=create_args,
                workspace=ws,
            )
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_grant_reuse_denial",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - t4, 3),
                    error_message="Consumed grant was reused successfully!",
                )
            )
        except Exception:
            test_cases.append(
                TestCaseResult(
                    name="fixturelab_grant_reuse_denial",
                    status=TestRunStatus.PASSED,
                    duration_seconds=round(time.monotonic() - t4, 3),
                )
            )

        overall_status = (
            TestRunStatus.PASSED
            if all(tc.status == TestRunStatus.PASSED for tc in test_cases)
            else TestRunStatus.FAILED
        )

        test_run.status = overall_status
        test_run.finish_time = datetime.now(timezone.utc).isoformat()
        test_run.test_cases = test_cases

        self._save_test_run(test_run)
        return test_run

    def run_blender_live_test(self, build: Build, workspace: Path) -> TestRun:
        """Run real Blender operations if installed, or gracefully mark SKIPPED if not."""
        run_id = str(uuid4())
        ws = Path(workspace).resolve()

        test_run = TestRun(
            id=run_id,
            build_id=build.id,
            test_type="blender_live",
            command="blender --background scene.blend",
            status=TestRunStatus.RUNNING,
            start_time=datetime.now(timezone.utc).isoformat(),
        )

        blender_adapter = get_adapter_registry().get_adapter("forge.adapters.blender")
        detection = blender_adapter.detect_application()

        if not detection.get("available", False):
            # Blender not installed -> mark SKIPPED with explicit honest reason
            test_case = TestCaseResult(
                name="blender_live_integration",
                status=TestRunStatus.SKIPPED,
                duration_seconds=0.0,
                skip_reason=detection.get(
                    "message", "Blender executable not installed in environment."
                ),
            )
            test_run.status = TestRunStatus.SKIPPED
            test_run.finish_time = datetime.now(timezone.utc).isoformat()
            test_run.test_cases = [test_case]
            test_run.stdout = "Blender live tests skipped: " + test_case.skip_reason
            self._save_test_run(test_run)
            return test_run

        # If Blender IS installed, run genuine live scene verification
        test_cases: list[TestCaseResult] = []
        gateway = get_execution_gateway(self.db_path)
        approval_broker = get_approval_broker(self.db_path)

        # Manifest
        manifest_file = ws / "manifest.yaml"
        manifest = self.manifest_service.load_and_validate(manifest_file)

        # 1. Create a minimal .blend file via blender background command
        fixture_blend = ws / "test_scene.blend"
        # We can launch blender to save a factory startup file
        import subprocess

        try:
            subprocess.run(
                [
                    str(blender_adapter.get_executable()),
                    "--background",
                    "--factory-startup",
                    "--python-expr",
                    f"import bpy; bpy.ops.wm.save_as_mainfile(filepath=r'{fixture_blend}')",
                ],
                capture_output=True,
                check=True,
                timeout=30.0,
            )
        except Exception as exc:
            test_cases.append(
                TestCaseResult(
                    name="blender_fixture_creation",
                    status=TestRunStatus.FAILED,
                    error_message=f"Failed to create fixture .blend: {exc}",
                )
            )
            test_run.status = TestRunStatus.FAILED
            test_run.test_cases = test_cases
            self._save_test_run(test_run)
            return test_run

        initial_hash = hash_file(fixture_blend)

        # 2. Call blender_scene_summary
        t0 = time.monotonic()
        try:
            gateway.execute_tool(
                connector_id="forge.blender.scene",
                manifest=manifest,
                tool_name="blender_scene_summary",
                args={"blend_file": "test_scene.blend"},
                workspace=ws,
            )
            test_cases.append(
                TestCaseResult(
                    name="blender_scene_summary",
                    status=TestRunStatus.PASSED,
                    duration_seconds=round(time.monotonic() - t0, 3),
                )
            )
        except Exception as exc:
            test_cases.append(
                TestCaseResult(
                    name="blender_scene_summary",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - t0, 3),
                    error_message=str(exc),
                )
            )

        # 3. Create primitive in NEW file with approval
        output_blend = ws / "modified_scene.blend"
        prim_args = {
            "blend_file": "test_scene.blend",
            "output_file": "modified_scene.blend",
            "primitive_type": "cube",
            "name": "ForgeCube",
        }
        arg_hash = hash_arguments(prim_args)
        approval_broker.grant_approval(
            tool_name="blender_create_primitive",
            argument_hash=arg_hash,
            correlation_id=run_id,
            ttl_seconds=120,
            actor="test_runner",
        )

        t1 = time.monotonic()
        try:
            gateway.execute_tool(
                connector_id="forge.blender.scene",
                manifest=manifest,
                tool_name="blender_create_primitive",
                args=prim_args,
                workspace=ws,
            )
            # Verify original scene hash is unchanged
            post_hash = hash_file(fixture_blend)
            assert post_hash == initial_hash, "Original .blend was mutated!"
            assert output_blend.is_file() and output_blend.stat().st_size > 0

            test_cases.append(
                TestCaseResult(
                    name="blender_create_primitive_cow",
                    status=TestRunStatus.PASSED,
                    duration_seconds=round(time.monotonic() - t1, 3),
                )
            )
        except Exception as exc:
            test_cases.append(
                TestCaseResult(
                    name="blender_create_primitive_cow",
                    status=TestRunStatus.FAILED,
                    duration_seconds=round(time.monotonic() - t1, 3),
                    error_message=str(exc),
                )
            )

        overall_status = (
            TestRunStatus.PASSED
            if all(tc.status == TestRunStatus.PASSED for tc in test_cases)
            else TestRunStatus.FAILED
        )

        test_run.status = overall_status
        test_run.finish_time = datetime.now(timezone.utc).isoformat()
        test_run.test_cases = test_cases
        self._save_test_run(test_run)
        return test_run

    def _save_test_run(self, test_run: TestRun) -> None:
        import json

        with self.mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO test_runs
                (id, build_id, test_type, command, environment_fingerprint_json, status, start_time, finish_time, test_cases_json, stdout, stderr, artifacts_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    finish_time=excluded.finish_time,
                    test_cases_json=excluded.test_cases_json,
                    stdout=excluded.stdout,
                    stderr=excluded.stderr;
                """,
                (
                    test_run.id,
                    test_run.build_id,
                    test_run.test_type,
                    test_run.command,
                    json.dumps(test_run.environment_fingerprint),
                    test_run.status.value,
                    test_run.start_time,
                    test_run.finish_time,
                    json.dumps([tc.model_dump() for tc in test_run.test_cases]),
                    test_run.stdout,
                    test_run.stderr,
                    json.dumps(test_run.artifacts),
                ),
            )
