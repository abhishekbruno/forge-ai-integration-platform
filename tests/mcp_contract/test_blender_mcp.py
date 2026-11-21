"""MCP contract tests for Blender generated server over stdio."""

import sys
from pathlib import Path

import pytest

from forge.core.build_service import BuildService
from forge.core.manifest_service import ManifestService
from forge.mcp.protocol_client import ProtocolClient


@pytest.mark.asyncio
async def test_blender_mcp_tool_discovery(temp_workspace, temp_db):
    ms = ManifestService()
    manifest = ms.load_and_validate(Path("manifests/blender.yaml"))

    bs = BuildService(temp_db)
    build = bs.generate_build("proj-bl-contract", temp_workspace, manifest)

    launcher = Path(build.build_dir) / "launcher.py"
    client = ProtocolClient(
        command=sys.executable,
        args=[str(launcher)],
        env={"FORGE_WORKSPACE": str(temp_workspace), "PYTHONUNBUFFERED": "1"},
    )

    # 1. Discover all 8 Blender tools via official MCP protocol
    tools = await client.list_tools()
    tool_names = [t["name"] for t in tools]
    assert len(tools) == 8
    assert "blender_scene_summary" in tool_names
    assert "blender_create_primitive" in tool_names
    assert "blender_inspect_object" in tool_names
    assert "blender_set_transform" in tool_names
