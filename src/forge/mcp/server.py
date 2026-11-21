"""MCP server bootstrapping utilities using MCP Python SDK v2."""

from __future__ import annotations

from mcp.server import MCPServer

from forge.domain.manifest import IntegrationManifest


def create_mcp_server(manifest: IntegrationManifest) -> MCPServer:
    """Instantiate and configure an MCPServer instance from an IntegrationManifest."""
    return MCPServer(
        name=manifest.integration.id,
        version=manifest.integration.version,
        description=manifest.integration.description or manifest.integration.name,
    )
