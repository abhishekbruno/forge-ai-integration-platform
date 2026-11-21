"""Unit tests for path security checks and workspace confinement."""

import pytest

from forge.security.paths import (
    PathSecurityError,
    ensure_within_workspace,
    validate_safe_filename,
)


def test_valid_path_within_workspace(temp_workspace):
    test_file = temp_workspace / "subfolder" / "scene.blend"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("dummy", encoding="utf-8")

    canonical = ensure_within_workspace(test_file, temp_workspace)
    assert canonical == test_file.resolve()


def test_path_traversal_rejection(temp_workspace):
    temp_workspace.parent / "escape.txt"
    with pytest.raises(PathSecurityError, match="outside workspace"):
        ensure_within_workspace("../escape.txt", temp_workspace)


def test_disallowed_extension_rejection(temp_workspace):
    exe_file = temp_workspace / "malware.exe"
    with pytest.raises(PathSecurityError, match="Disallowed file extension"):
        ensure_within_workspace(exe_file, temp_workspace, allow_nonexistent=True)


def test_validate_safe_filename():
    assert validate_safe_filename("valid_name.blend") == "valid_name.blend"
    with pytest.raises(PathSecurityError):
        validate_safe_filename("../escape.blend")
    with pytest.raises(PathSecurityError):
        validate_safe_filename("sub/folder.blend")
