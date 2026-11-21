"""Cryptographic and deterministic hashing utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def hash_bytes(data: bytes) -> str:
    """Compute SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def hash_string(text: str) -> str:
    """Compute SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_file(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hex digest of a file safely in chunks."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def canonical_json_dumps(obj: Any) -> str:
    """Serialize an arbitrary JSON-compatible data structure deterministically.

    Keys are sorted, whitespace is minimized, and floats are formatted predictably.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def hash_arguments(args: dict[str, Any] | None) -> str:
    """Compute deterministic SHA-256 digest of tool invocation arguments for exact approval binding."""
    if args is None:
        args = {}
    return hash_string(canonical_json_dumps(args))


def compute_audit_hash(previous_hash: str, event_payload: dict[str, Any]) -> str:
    """Compute the tamper-evident hash chain element.

    Combines the previous event hash with canonical JSON serialization of current event data.
    """
    combined = f"{previous_hash}:{canonical_json_dumps(event_payload)}"
    return hash_string(combined)
