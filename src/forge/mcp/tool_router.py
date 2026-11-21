"""MCP tool routing and execution binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forge.core.execution_gateway import get_execution_gateway
from forge.domain.manifest import IntegrationManifest


class ToolRouter:
    """Routes incoming MCP protocol tool invocations through the FORGE execution gateway."""

    def __init__(self, manifest: IntegrationManifest, workspace: Path):
        self.manifest = manifest
        self.workspace = Path(workspace).resolve()
        self.gateway = get_execution_gateway()

    def route_call(
        self, tool_name: str, args: dict[str, Any], actor: str = "mcp_client"
    ) -> dict[str, Any]:
        """Dispatch a tool call to the gateway."""
        return self.gateway.execute_tool(
            connector_id=self.manifest.integration.id,
            manifest=self.manifest,
            tool_name=tool_name,
            args=args,
            workspace=self.workspace,
            actor=actor,
        )
