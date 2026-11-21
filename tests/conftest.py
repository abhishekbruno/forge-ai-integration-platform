"""Pytest shared fixtures and environment setup."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from forge.persistence.db import DatabaseManager
from forge.persistence.migrations import apply_migrations


@pytest.fixture
def temp_workspace():
    """Provides a temporary workspace folder for testing."""
    with tempfile.TemporaryDirectory(prefix="forge_test_ws_") as tmp_dir:
        yield Path(tmp_dir).resolve()


@pytest.fixture
def temp_db(temp_workspace):
    """Provides an isolated SQLite database manager with applied migrations."""
    db_file = temp_workspace / "test_forge.db"
    DatabaseManager(db_file)
    apply_migrations(db_file)
    return db_file
