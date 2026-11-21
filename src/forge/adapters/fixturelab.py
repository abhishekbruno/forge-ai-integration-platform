"""FixtureLab reference application adapter.

Provides deterministic, offline-capable stateful operations for testing
read, write, destructive, and denial policies without external dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forge.adapters.base import BaseAdapter
from forge.domain.capability import CapabilityDefinition, RiskLevel
from forge.domain.errors import AdapterExecutionError
from forge.security.paths import ensure_within_workspace

STATE_FILENAME = ".fixturelab_state.json"


class FixtureLabAdapter(BaseAdapter):
    """Deterministic reference adapter implementation."""

    @property
    def id(self) -> str:
        return "forge.adapters.fixturelab"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def supported_app_id(self) -> str:
        return "fixturelab"

    @property
    def supported_versions(self) -> str:
        return ">=1.0.0"

    def detect_application(self, workspace: Path | None = None) -> dict[str, Any]:
        return {
            "available": True,
            "version": "1.0.0-embedded",
            "executable": "embedded:python",
            "status": "ready",
            "message": "FixtureLab deterministic reference engine is active and operational.",
        }

    def list_capabilities(self) -> list[CapabilityDefinition]:
        return [
            CapabilityDefinition(
                name="fixturelab_get_status",
                handler="fixturelab.get_status",
                description="Returns the current version, engine state, and item count of FixtureLab.",
                risk=RiskLevel.READ,
                timeout_seconds=15,
                input_schema={"type": "object", "properties": {}, "additionalProperties": False},
                output_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "version": {"type": "string"},
                        "item_count": {"type": "integer"},
                    },
                    "required": ["status", "version", "item_count"],
                },
            ),
            CapabilityDefinition(
                name="fixturelab_list_items",
                handler="fixturelab.list_items",
                description="Returns an ordered list of items and total count from the sandbox.",
                risk=RiskLevel.READ,
                timeout_seconds=15,
                input_schema={
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "default": 50}},
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "items": {"type": "array"},
                        "total": {"type": "integer"},
                    },
                    "required": ["items", "total"],
                },
            ),
            CapabilityDefinition(
                name="fixturelab_get_item",
                handler="fixturelab.get_item",
                description="Retrieves an identified item by exact key or returns a typed error.",
                risk=RiskLevel.READ,
                timeout_seconds=15,
                input_schema={
                    "type": "object",
                    "properties": {"item_id": {"type": "string", "minLength": 1}},
                    "required": ["item_id"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {"item": {"type": "object"}},
                    "required": ["item"],
                },
            ),
            CapabilityDefinition(
                name="fixturelab_create_item",
                handler="fixturelab.create_item",
                description="Creates a validated new item in the approved sandbox (requires explicit approval).",
                risk=RiskLevel.WRITE,
                timeout_seconds=20,
                input_schema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "minLength": 1},
                        "name": {"type": "string", "minLength": 1},
                        "category": {"type": "string", "default": "general"},
                        "payload": {"type": "object", "default": {}},
                    },
                    "required": ["item_id", "name"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "created_id": {"type": "string"},
                        "version": {"type": "integer"},
                    },
                    "required": ["success", "created_id", "version"],
                },
            ),
            CapabilityDefinition(
                name="fixturelab_update_item",
                handler="fixturelab.update_item",
                description="Updates an existing approved item with optimistic version conflict checking.",
                risk=RiskLevel.WRITE,
                timeout_seconds=20,
                input_schema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "minLength": 1},
                        "expected_version": {"type": "integer", "minimum": 1},
                        "name": {"type": "string"},
                        "payload": {"type": "object"},
                    },
                    "required": ["item_id", "expected_version"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "updated_id": {"type": "string"},
                        "new_version": {"type": "integer"},
                    },
                    "required": ["success", "updated_id", "new_version"],
                },
            ),
            CapabilityDefinition(
                name="fixturelab_delete_item",
                handler="fixturelab.delete_item",
                description="Deletes an approved item from the sandbox state (destructive operation).",
                risk=RiskLevel.DESTRUCTIVE,
                timeout_seconds=20,
                input_schema={
                    "type": "object",
                    "properties": {"item_id": {"type": "string", "minLength": 1}},
                    "required": ["item_id"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "deleted_id": {"type": "string"},
                    },
                    "required": ["success", "deleted_id"],
                },
            ),
        ]

    def _get_state_file(self, workspace: Path) -> Path:
        state_file = workspace / STATE_FILENAME
        ensure_within_workspace(state_file, workspace, allow_nonexistent=True)
        return state_file

    def _read_state(self, workspace: Path) -> dict[str, Any]:
        path = self._get_state_file(workspace)
        if not path.exists():
            return {"items": {}}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            raise AdapterExecutionError(f"Failed to read FixtureLab state file: {exc}") from exc

    def _write_state(self, workspace: Path, state: dict[str, Any]) -> None:
        path = self._get_state_file(workspace)
        try:
            temp_path = path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, sort_keys=True)
            temp_path.replace(path)
        except Exception as exc:
            raise AdapterExecutionError(f"Failed to persist FixtureLab state: {exc}") from exc

    def invoke_capability(
        self,
        handler: str,
        args: dict[str, Any],
        workspace: Path,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        workspace = Path(workspace).resolve()

        if handler == "fixturelab.get_status":
            state = self._read_state(workspace)
            return {
                "status": "ready",
                "version": "1.0.0",
                "item_count": len(state.get("items", {})),
            }

        elif handler == "fixturelab.list_items":
            state = self._read_state(workspace)
            limit = int(args.get("limit", 50))
            items_dict = state.get("items", {})
            sorted_items = sorted(items_dict.values(), key=lambda x: str(x.get("id")))
            limited = sorted_items[:limit]
            return {
                "items": limited,
                "total": len(items_dict),
            }

        elif handler == "fixturelab.get_item":
            item_id = str(args.get("item_id", "")).strip()
            state = self._read_state(workspace)
            item = state.get("items", {}).get(item_id)
            if not item:
                raise AdapterExecutionError(f"Item '{item_id}' not found in FixtureLab state.")
            return {"item": item}

        elif handler == "fixturelab.create_item":
            item_id = str(args.get("item_id", "")).strip()
            name = str(args.get("name", "")).strip()
            category = str(args.get("category", "general")).strip()
            payload = args.get("payload", {})

            state = self._read_state(workspace)
            if item_id in state.get("items", {}):
                raise AdapterExecutionError(f"Item '{item_id}' already exists in FixtureLab state.")

            new_item = {
                "id": item_id,
                "name": name,
                "category": category,
                "payload": payload,
                "version": 1,
            }
            state.setdefault("items", {})[item_id] = new_item
            self._write_state(workspace, state)
            return {
                "success": True,
                "created_id": item_id,
                "version": 1,
            }

        elif handler == "fixturelab.update_item":
            item_id = str(args.get("item_id", "")).strip()
            expected_version = int(args.get("expected_version", 1))

            state = self._read_state(workspace)
            items = state.get("items", {})
            if item_id not in items:
                raise AdapterExecutionError(f"Cannot update nonexistent item '{item_id}'.")

            current_item = items[item_id]
            current_ver = current_item.get("version", 1)
            if current_ver != expected_version:
                raise AdapterExecutionError(
                    f"Conflict: item '{item_id}' version is {current_ver}, expected {expected_version}."
                )

            if "name" in args and args["name"]:
                current_item["name"] = str(args["name"])
            if "payload" in args and isinstance(args["payload"], dict):
                current_item["payload"] = args["payload"]

            current_item["version"] = current_ver + 1
            items[item_id] = current_item
            self._write_state(workspace, state)
            return {
                "success": True,
                "updated_id": item_id,
                "new_version": current_item["version"],
            }

        elif handler == "fixturelab.delete_item":
            item_id = str(args.get("item_id", "")).strip()
            state = self._read_state(workspace)
            items = state.get("items", {})
            if item_id not in items:
                raise AdapterExecutionError(f"Cannot delete nonexistent item '{item_id}'.")

            del items[item_id]
            self._write_state(workspace, state)
            return {
                "success": True,
                "deleted_id": item_id,
            }

        else:
            raise AdapterExecutionError(f"Unknown FixtureLab handler: '{handler}'")
