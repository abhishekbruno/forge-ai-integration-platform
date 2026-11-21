"""MCP package initialization."""

from forge.mcp.client_config import generate_claude_desktop_config
from forge.mcp.protocol_client import ProtocolClient
from forge.mcp.server import create_mcp_server
from forge.mcp.tool_router import ToolRouter

__all__ = [
    "create_mcp_server",
    "ToolRouter",
    "ProtocolClient",
    "generate_claude_desktop_config",
]
