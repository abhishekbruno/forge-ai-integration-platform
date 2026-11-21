"""Template for authoring new FORGE application adapters (e.g. FreeCAD, Godot, Unreal, REST)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forge.adapters.base import BaseAdapter
from forge.domain.capability import CapabilityDefinition, RiskLevel
from forge.domain.errors import AdapterExecutionError


class CustomApplicationAdapter(BaseAdapter):
    """Example custom adapter template."""

    @property
    def id(self) -> str:
        return "forge.adapters.custom_example"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def supported_app_id(self) -> str:
        return "custom_app"

    @property
    def supported_versions(self) -> str:
        return ">=1.0.0"

    def detect_application(self, workspace: Path | None = None) -> dict[str, Any]:
        # Implement detection logic: check PATH, environment variable, or executable path
        return {
            "available": True,
            "version": "1.0.0",
            "executable": "/usr/local/bin/custom_app",
            "status": "ready",
            "message": "Custom application detected successfully.",
        }

    def list_capabilities(self) -> list[CapabilityDefinition]:
        return [
            CapabilityDefinition(
                name="custom_app_read_info",
                handler="custom.read_info",
                description="Read system info from custom application.",
                risk=RiskLevel.READ,
                timeout_seconds=30,
                input_schema={"type": "object", "properties": {}, "additionalProperties": False},
                output_schema={
                    "type": "object",
                    "properties": {"info": {"type": "string"}},
                    "required": ["info"],
                },
            ),
            CapabilityDefinition(
                name="custom_app_write_action",
                handler="custom.write_action",
                description="Perform a mutating action (requires approval).",
                risk=RiskLevel.WRITE,
                timeout_seconds=45,
                input_schema={
                    "type": "object",
                    "properties": {"action_name": {"type": "string"}},
                    "required": ["action_name"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {"success": {"type": "boolean"}},
                    "required": ["success"],
                },
            ),
        ]

    def invoke_capability(
        self,
        handler: str,
        args: dict[str, Any],
        workspace: Path,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if handler == "custom.read_info":
            return {"info": "Custom application operational."}
        elif handler == "custom.write_action":
            action = args.get("action_name")
            return {"success": True, "action": action}
        else:
            raise AdapterExecutionError(f"Unsupported handler: {handler}")
