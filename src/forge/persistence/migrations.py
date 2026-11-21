"""Idempotent database migrations for FORGE."""

from __future__ import annotations

from pathlib import Path

from forge.persistence.db import get_db_manager

MIGRATION_V1 = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    workspace_path TEXT NOT NULL UNIQUE,
    manifest_path TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS builds (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    generated_source_hash TEXT NOT NULL,
    build_dir TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    files_json TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS approval_grants (
    id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    argument_hash TEXT NOT NULL,
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    single_use INTEGER NOT NULL DEFAULT 1,
    consumed INTEGER NOT NULL DEFAULT 0,
    details_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    connector_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    argument_hash TEXT NOT NULL,
    arguments_json TEXT NOT NULL,
    actor TEXT NOT NULL,
    outcome TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    result_json TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS test_runs (
    id TEXT PRIMARY KEY,
    build_id TEXT NOT NULL,
    test_type TEXT NOT NULL,
    command TEXT NOT NULL,
    environment_fingerprint_json TEXT NOT NULL,
    status TEXT NOT NULL,
    start_time TEXT NOT NULL,
    finish_time TEXT,
    test_cases_json TEXT NOT NULL,
    stdout TEXT NOT NULL,
    stderr TEXT NOT NULL,
    artifacts_json TEXT NOT NULL,
    FOREIGN KEY(build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS packages (
    id TEXT PRIMARY KEY,
    build_id TEXT NOT NULL,
    version TEXT NOT NULL,
    archive_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    outcome TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    details_json TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action);
CREATE INDEX IF NOT EXISTS idx_tool_calls_connector ON tool_calls(connector_id);
CREATE INDEX IF NOT EXISTS idx_builds_project ON builds(project_id);
"""


def apply_migrations(db_path: Path | None = None) -> int:
    """Apply all pending migrations to the database idempotently. Returns latest version."""
    mgr = get_db_manager(db_path)
    with mgr.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);"
        )
        cursor.execute("SELECT MAX(version) FROM schema_migrations;")
        current_version = cursor.fetchone()[0] or 0

        if current_version < 1:
            from datetime import datetime, timezone

            cursor.executescript(MIGRATION_V1)
            cursor.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (1, ?);",
                (datetime.now(timezone.utc).isoformat(),),
            )
            current_version = 1

    return current_version
