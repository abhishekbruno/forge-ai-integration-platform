# FORGE Testing & Verification Guide

FORGE includes a multi-tiered automated test suite:

## Test Levels

1. **Unit Tests**: Domain models, path security, hash calculations, policy engine logic, approval broker single-use constraints.
2. **Integration Tests**: Project service, build service, SQLite migrations, and packaging.
3. **MCP Contract Tests**: Starts generated connector packages over stdio and executes commands with an actual MCP client session.
4. **Security Negative Tests**: Path traversal, zip-slip, grant reuse, unauthorized writes, invalid schemas.
5. **UI Smoke Tests**: Headless PySide6 window instantiation, navigation, and theme toggling.
6. **Blender Live Tests**: Conditional tests executed against real Blender binaries when available.

## Running Tests

```bash
# Run all offline tests
pytest -m "not blender_live"

# Run end-to-end verification script
python scripts/verify.py

# Run doctor check
forge doctor
```
