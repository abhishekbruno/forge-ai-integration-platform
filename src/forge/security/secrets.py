"""Secret redaction and sensitive parameter masking."""

from __future__ import annotations

import re
from typing import Any

SENSITIVE_PATTERNS = [
    re.compile(
        r"(?i)(api[_-]?key|secret|password|token|auth|credential|private[_-]?key)\s*[:=]\s*['\"]?([^'\" \n,]+)"
    ),
    re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}"),
]


def redact_sensitive_text(text: str) -> str:
    """Redact sensitive patterns (tokens, API keys, passwords) from a log string."""
    if not text:
        return text

    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(r"\1: [REDACTED]", sanitized)

    return sanitized


def sanitize_dict_for_logging(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask sensitive values in dictionary keys matching passwords/tokens."""
    sanitized: dict[str, Any] = {}
    sensitive_keys = {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "credential",
        "private_key",
    }

    for key, value in data.items():
        if any(sk in key.lower() for sk in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_for_logging(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict_for_logging(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str):
            sanitized[key] = redact_sensitive_text(value)
        else:
            sanitized[key] = value

    return sanitized
