"""MCP client configuration formatting helpers."""

from __future__ import annotations

import sys
from pathlib import Path


def generate_claude_desktop_config(
    integration_id: str,
    launcher_path: Path | str,
    workspace_path: Path | str,
    python_exe: str | None = None,
) -> dict:
    """Generate configuration JSON block for Claude Desktop or other MCP client settings."""
    exe = python_exe or sys.executable
    return {
        "mcpServers": {
            integration_id: {
                "command": exe,
                "args": [str(Path(launcher_path).resolve())],
                "env": {
                    "FORGE_WORKSPACE": str(Path(workspace_path).resolve()),
                },
            }
        }
    }
