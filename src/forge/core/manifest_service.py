"""Manifest validation and parsing service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from forge.adapters.registry import get_adapter_registry
from forge.domain.errors import ManifestValidationError
from forge.domain.manifest import IntegrationManifest
from forge.events.bus import get_event_bus
from forge.events.models import (
    EVENT_MANIFEST_VALIDATION_FAILED,
    EVENT_MANIFEST_VALIDATION_STARTED,
    EVENT_MANIFEST_VALIDATION_SUCCEEDED,
    EventSeverity,
    ForgeEvent,
)
from forge.security.validation import (
    validate_data_against_schema,
    validate_json_schema_definition,
)

SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent / "schemas" / "forge_manifest_v1.schema.json"
)


class ManifestService:
    """Validates and parses Integration Manifests."""

    def __init__(self, schema_file: Path | None = None):
        self.schema_path = schema_file or SCHEMA_PATH
        self._schema_cache: dict[str, Any] | None = None

    def _load_schema(self) -> dict[str, Any]:
        if self._schema_cache is None:
            if not self.schema_path.is_file():
                # Fallback location check
                alt_path = Path("schemas/forge_manifest_v1.schema.json").resolve()
                if alt_path.is_file():
                    self.schema_path = alt_path
                else:
                    raise FileNotFoundError(f"Manifest schema not found at {self.schema_path}")

            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema_cache = json.load(f)
        return self._schema_cache

    def validate_manifest_data(
        self, data: dict[str, Any]
    ) -> tuple[bool, list[str], IntegrationManifest | None]:
        """Validate raw dictionary data against the schema and domain invariants."""
        errors: list[str] = []

        # 1. JSON Schema validation
        schema = self._load_schema()
        try:
            validate_data_against_schema(data, schema, context="Integration Manifest")
        except Exception as exc:
            errors.append(f"Schema validation error: {exc}")
            return False, errors, None

        # 2. Pydantic domain model validation
        try:
            manifest = IntegrationManifest.model_validate(data)
        except Exception as exc:
            errors.append(f"Model validation error: {exc}")
            return False, errors, None

        # 3. Adapter resolution check
        registry = get_adapter_registry()
        try:
            adapter = registry.get_adapter(manifest.adapter.id)
        except Exception:
            errors.append(f"Adapter '{manifest.adapter.id}' is not registered in the system.")
            return False, errors, None

        # 4. Capability verification against adapter
        adapter_caps = {cap.name: cap for cap in adapter.list_capabilities()}
        seen_names = set()

        for cap in manifest.capabilities:
            # Check duplicate tool names
            if cap.name in seen_names:
                errors.append(f"Duplicate capability name declared in manifest: '{cap.name}'")
            seen_names.add(cap.name)

            # Ensure capability handler is supported by the adapter
            matching_handler = any(ac.handler == cap.handler for ac in adapter_caps.values())
            if not matching_handler:
                errors.append(
                    f"Capability '{cap.name}' references handler '{cap.handler}' which is not provided by adapter '{adapter.id}'."
                )

            # Validate input and output schemas are valid JSON schemas
            try:
                validate_json_schema_definition(
                    cap.input_schema, context=f"capability '{cap.name}' input_schema"
                )
                validate_json_schema_definition(
                    cap.output_schema, context=f"capability '{cap.name}' output_schema"
                )
            except Exception as exc:
                errors.append(str(exc))

        if errors:
            return False, errors, None

        return True, [], manifest

    def load_and_validate(self, manifest_path: Path | str) -> IntegrationManifest:
        """Load manifest from file, validate thoroughly, and return parsed model or raise ManifestValidationError."""
        path = Path(manifest_path).resolve()
        if not path.is_file():
            raise ManifestValidationError(f"Manifest file not found: {path}")

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_MANIFEST_VALIDATION_STARTED,
                details={"path": str(path)},
            )
        )

        try:
            with open(path, "r", encoding="utf-8") as f:
                if path.suffix.lower() in (".yaml", ".yml"):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
        except Exception as exc:
            err = f"Failed to parse manifest file '{path}': {exc}"
            get_event_bus().publish(
                ForgeEvent(
                    name=EVENT_MANIFEST_VALIDATION_FAILED,
                    severity=EventSeverity.ERROR,
                    details={"path": str(path), "error": err},
                )
            )
            raise ManifestValidationError(err) from exc

        is_valid, errors, manifest = self.validate_manifest_data(data)
        if not is_valid or manifest is None:
            err_msg = "; ".join(errors)
            get_event_bus().publish(
                ForgeEvent(
                    name=EVENT_MANIFEST_VALIDATION_FAILED,
                    severity=EventSeverity.ERROR,
                    details={"path": str(path), "errors": errors},
                )
            )
            raise ManifestValidationError(f"Manifest validation failed for '{path}': {err_msg}")

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_MANIFEST_VALIDATION_SUCCEEDED,
                details={"path": str(path), "integration_id": manifest.integration.id},
            )
        )
        return manifest


_MANIFEST_SERVICE: ManifestService | None = None


def get_manifest_service() -> ManifestService:
    global _MANIFEST_SERVICE
    if _MANIFEST_SERVICE is None:
        _MANIFEST_SERVICE = ManifestService()
    return _MANIFEST_SERVICE
