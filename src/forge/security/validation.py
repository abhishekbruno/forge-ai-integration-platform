"""Validation helpers for JSON schemas, identifier patterns, and payload boundaries."""

from __future__ import annotations

import re
from typing import Any

import jsonschema
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


class ValidationSecurityError(Exception):
    """Raised when data structure validation fails."""


IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,128}$")


def validate_identifier(name: str, field_name: str = "identifier") -> str:
    """Ensure an identifier conforms to safe alphanumeric characters with dot/underscore/hyphen."""
    if not name or not IDENTIFIER_PATTERN.match(name):
        raise ValidationSecurityError(
            f"Invalid {field_name}: '{name}'. Must be 1-128 characters matching [a-zA-Z0-9_.-]."
        )
    return name


def validate_json_schema_definition(schema: dict[str, Any], context: str = "schema") -> None:
    """Validate that a dict is a valid JSON Schema Draft 2020-12 / Draft 7 definition."""
    try:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
    except Exception as exc:
        raise ValidationSecurityError(f"Invalid JSON schema in {context}: {exc}") from exc


def validate_data_against_schema(
    data: Any, schema: dict[str, Any], context: str = "payload"
) -> None:
    """Validate data against a JSON schema and raise ValidationSecurityError on mismatch."""
    try:
        jsonschema.validate(instance=data, schema=schema)
    except JsonSchemaValidationError as exc:
        raise ValidationSecurityError(
            f"Validation failed for {context} at path '{'/'.join(str(p) for p in exc.path)}': {exc.message}"
        ) from exc
    except Exception as exc:
        raise ValidationSecurityError(
            f"Unexpected schema validation failure for {context}: {exc}"
        ) from exc
