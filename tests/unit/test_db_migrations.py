"""Unit tests for database migrations."""

from forge.persistence.db import DatabaseManager
from forge.persistence.migrations import apply_migrations


def test_migrations_idempotent(temp_workspace):
    db_file = temp_workspace / "mig_test.db"
    v1 = apply_migrations(db_file)
    assert v1 == 1

    # Running migrations again on already migrated DB must be a no-op
    v2 = apply_migrations(db_file)
    assert v2 == 1

    mgr = DatabaseManager(db_file)
    with mgr.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert "projects" in tables
        assert "builds" in tables
        assert "audit_events" in tables
        assert "approval_grants" in tables
        assert "tool_calls" in tables
