"""MCP contract tests for FixtureLab generated server over stdio."""

import sys
from pathlib import Path

import pytest

from forge.core.build_service import BuildService
from forge.core.manifest_service import ManifestService
from forge.mcp.protocol_client import ProtocolClient


@pytest.mark.asyncio
async def test_fixturelab_mcp_contract(temp_workspace, temp_db):
    ms = ManifestService()
    manifest = ms.load_and_validate(Path("manifests/fixturelab.yaml"))

    bs = BuildService(temp_db)
    build = bs.generate_build("proj-fl-contract", temp_workspace, manifest)

    launcher = Path(build.build_dir) / "launcher.py"
    client = ProtocolClient(
        command=sys.executable,
        args=[str(launcher)],
        env={"FORGE_WORKSPACE": str(temp_workspace), "PYTHONUNBUFFERED": "1"},
    )

    # 1. Tool discovery
    tools = await client.list_tools()
    tool_names = [t["name"] for t in tools]
    assert len(tools) == 6
    assert "fixturelab_get_status" in tool_names
    assert "fixturelab_create_item" in tool_names

    # 2. Invoke read tool
    res = await client.call_tool("fixturelab_get_status", {})
    assert res is not None
    assert not getattr(res, "is_error", getattr(res, "isError", False))
    content_text = res.content[0].text
    assert '"status": "ready"' in content_text
