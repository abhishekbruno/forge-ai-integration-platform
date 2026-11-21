# FixtureLab Demo Project

This is a complete, self-contained FORGE integration project demonstrating:
1. Manifest declaration and schema validation.
2. Connector generation to an MCP server.
3. Read tool invocation without human intervention.
4. Mutating tool approval request, approval grant, and single-use consumption.
5. Tamper-evident audit trail recording.

## Quickstart

Run via FORGE CLI:
```bash
# Validate manifest
forge manifest validate manifest.yaml

# Generate connector
forge generate manifest.yaml --workspace .

# Run test suite
forge test <build-id> --workspace .
```
