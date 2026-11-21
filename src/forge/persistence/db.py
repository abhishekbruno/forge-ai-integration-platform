"""SQLite database connection and lifecycle management."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from forge.config import get_config


class DatabaseManager:
    """Manages SQLite connections, pragmas, and migrations."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or get_config().db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_pragmas()

    def _init_pragmas(self) -> None:
        """Enable Write-Ahead Logging (WAL) and foreign keys."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA synchronous = NORMAL;")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a contextual thread-safe SQLite connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None,  # Autocommit mode, transactions via BEGIN/COMMIT
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


_DB_MANAGER: DatabaseManager | None = None


def get_db_manager(custom_path: Path | None = None) -> DatabaseManager:
    global _DB_MANAGER
    if custom_path or _DB_MANAGER is None:
        mgr = DatabaseManager(custom_path)
        if custom_path is None:
            _DB_MANAGER = mgr
        return mgr
    return _DB_MANAGER
