"""MCP stdio protocol client wrapper for automated testing and inspection."""

from __future__ import annotations

from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class ProtocolClient:
    """High-level client communicating with an MCP server subprocess over stdio."""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None):
        self.parameters = StdioServerParameters(
            command=command,
            args=args,
            env=env or {},
        )

    async def list_tools(self) -> list[dict[str, Any]]:
        """Connect over stdio, initialize, and query list of registered tools."""
        async with stdio_client(self.parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": getattr(tool, "inputSchema", {}),
                    }
                    for tool in tools_result.tools
                ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Connect over stdio, call an identified tool, and return result."""
        async with stdio_client(self.parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments or {})
                return result
