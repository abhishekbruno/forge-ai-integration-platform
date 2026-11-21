# FORGE Packaging & Client Configuration

## Exporting a Connector

A connector build can be packaged into a standalone distribution archive using the GUI or CLI:

```bash
forge package <build-id> --workspace ./my_project
```

This creates a ZIP archive in `.forge/packages/` containing:
- `server.py`
- `launcher.py`
- `pyproject.toml`
- `README.md`
- `tools.json`
- `policy.json`
- `client_config.json`

## Configuring Claude Desktop / Cursor / Antigravity

Add the following to your MCP client configuration file:

```json
{
  "mcpServers": {
    "my-connector": {
      "command": "python",
      "args": ["/path/to/extracted/package/launcher.py"],
      "env": {
        "FORGE_WORKSPACE": "/path/to/authorized/workspace"
      }
    }
  }
}
```
