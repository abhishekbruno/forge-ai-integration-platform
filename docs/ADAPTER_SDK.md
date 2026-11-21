# FORGE Adapter SDK Guide

Application Adapters in FORGE are verified Python classes implementing interaction with specific applications.

## Adapter Architecture

All adapters inherit from `forge.adapters.base.BaseAdapter`.

```python
from pathlib import Path
from typing import Any
from forge.adapters.base import BaseAdapter
from forge.domain.capability import CapabilityDefinition, RiskLevel
from forge.domain.errors import AdapterExecutionError


class MyCustomAdapter(BaseAdapter):
    @property
    def id(self) -> str:
        return "forge.adapters.my_app"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def supported_app_id(self) -> str:
        return "my_app"

    @property
    def supported_versions(self) -> str:
        return ">=1.0.0"

    def detect_application(self, workspace: Path | None = None) -> dict[str, Any]:
        return {
            "available": True,
            "version": "1.0.0",
            "executable": "/path/to/binary",
            "status": "ready",
            "message": "Operational",
        }

    def list_capabilities(self) -> list[CapabilityDefinition]:
        return [
            CapabilityDefinition(
                name="my_read_tool",
                handler="myapp.read_info",
                description="Read data",
                risk=RiskLevel.READ,
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {"data": {"type": "string"}}},
            )
        ]

    def invoke_capability(
        self,
        handler: str,
        args: dict[str, Any],
        workspace: Path,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if handler == "myapp.read_info":
            return {"data": "Hello world"}
        raise AdapterExecutionError(f"Unknown handler {handler}")
```

## Security Rules for Adapter Authors

1. **Never Import Non-Host Libraries in Host Python**: If an application provides an embedded Python (like Blender's `bpy`), execute it in a subprocess via a runner script.
2. **Copy-on-Write**: Always preserve user source files and write to new output paths.
3. **No Shell Invocations**: Execute binaries using lists of string arguments (`shell=False`).
4. **Boundary Checks**: Check that all file arguments reside strictly within the approved workspace.
