"""Security utilities for path validation, canonicalization, and workspace boundary confinement."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from forge.domain.errors import PathSecurityError


def canonicalize_path(path: str | Path) -> Path:
    """Resolve a path to its strict canonical absolute representation.

    Resolves symlinks, normalizes drive letters on Windows, and eliminates relative segments.
    """
    raw_path = Path(path)
    try:
        # If path exists, resolve fully
        if raw_path.exists():
            return raw_path.resolve(strict=True)
        # If not, resolve parent and append name
        parent = raw_path.parent.resolve()
        return (parent / raw_path.name).resolve()
    except Exception as exc:
        raise PathSecurityError(f"Failed to canonicalize path '{path}': {exc}") from exc


def ensure_within_workspace(
    target_path: str | Path,
    workspace_root: str | Path,
    allow_nonexistent: bool = False,
    disallowed_extensions: Sequence[str] = (
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bat",
        ".cmd",
        ".sh",
        ".ps1",
    ),
) -> Path:
    """Assert that target_path resides strictly within the workspace_root.

    Prevents path traversal, external symlink escapes, drive switching on Windows,
    and unsafe executable extensions.
    """
    ws = canonicalize_path(workspace_root)
    if not ws.exists() or not ws.is_dir():
        raise PathSecurityError(f"Workspace root does not exist or is not a directory: {ws}")

    # Check for obvious traversal tokens in input representation
    str_target = str(target_path).replace("\\", "/")
    if (
        "/../" in str_target
        or str_target.startswith("../")
        or str_target.endswith("/..")
        or str_target == ".."
    ):
        # Resolve to check if escape happens
        pass

    target = Path(target_path)
    if not target.is_absolute():
        target = ws / target

    canonical_target = canonicalize_path(target)

    # Validate workspace containment
    try:
        canonical_target.relative_to(ws)
    except ValueError as exc:
        raise PathSecurityError(
            f"Access denied: Path '{target_path}' resolves to '{canonical_target}', which is outside workspace '{ws}'."
        ) from exc

    if not allow_nonexistent and not canonical_target.exists():
        raise PathSecurityError(f"Path does not exist within workspace: {canonical_target}")

    # If nonexistent is allowed, ensure nearest existing parent is within workspace
    if not canonical_target.exists():
        parent = canonical_target.parent
        while not parent.exists() and parent != parent.parent:
            parent = parent.parent
        try:
            parent.resolve().relative_to(ws)
        except ValueError as exc:
            raise PathSecurityError(
                f"Access denied: Parent of '{canonical_target}' resolves outside workspace: {parent}"
            ) from exc

    # Extension check
    suffix = canonical_target.suffix.lower()
    if suffix in [ext.lower() for ext in disallowed_extensions]:
        raise PathSecurityError(
            f"Access denied: Disallowed file extension '{suffix}' on path '{canonical_target}'"
        )

    return canonical_target


def validate_safe_filename(filename: str) -> str:
    """Validate that a filename is a plain single basename without directory components."""
    if not filename or filename in (".", ".."):
        raise PathSecurityError("Filename cannot be empty, '.', or '..'")
    if "/" in filename or "\\" in filename:
        raise PathSecurityError(f"Filename cannot contain directory separators: '{filename}'")
    invalid_chars = set('<>:"|?*\0')
    if any(c in invalid_chars for c in filename):
        raise PathSecurityError(f"Filename contains illegal characters: '{filename}'")
    return filename
