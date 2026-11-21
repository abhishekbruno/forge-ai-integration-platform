"""Persistence repositories for projects, builds, tool calls, and approvals."""

from __future__ import annotations

import json
from pathlib import Path

from forge.domain.execution import ApprovalGrant, ToolCall
from forge.domain.project import Build, PackageMetadata, Project
from forge.persistence.db import get_db_manager


class ProjectRepository:
    def __init__(self, db_path: Path | None = None):
        self.mgr = get_db_manager(db_path)

    def save(self, project: Project) -> None:
        with self.mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (id, name, workspace_path, manifest_path, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    workspace_path=excluded.workspace_path,
                    manifest_path=excluded.manifest_path,
                    status=excluded.status,
                    updated_at=excluded.updated_at;
                """,
                (
                    project.id,
                    project.name,
                    project.workspace_path,
                    project.manifest_path,
                    project.status.value,
                    project.created_at,
                    project.updated_at,
                ),
            )

    def get_by_id(self, project_id: str) -> Project | None:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?;", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Project(
                id=row["id"],
                name=row["name"],
                workspace_path=row["workspace_path"],
                manifest_path=row["manifest_path"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def get_by_workspace(self, workspace_path: str) -> Project | None:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE workspace_path = ?;", (workspace_path,))
            row = cursor.fetchone()
            if not row:
                return None
            return Project(
                id=row["id"],
                name=row["name"],
                workspace_path=row["workspace_path"],
                manifest_path=row["manifest_path"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_all(self) -> list[Project]:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC;")
            return [
                Project(
                    id=row["id"],
                    name=row["name"],
                    workspace_path=row["workspace_path"],
                    manifest_path=row["manifest_path"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in cursor.fetchall()
            ]


class BuildRepository:
    def __init__(self, db_path: Path | None = None):
        self.mgr = get_db_manager(db_path)

    def save(self, build: Build) -> None:
        with self.mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO builds (id, project_id, version, manifest_hash, generated_source_hash, build_dir, status, created_at, files_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    files_json=excluded.files_json;
                """,
                (
                    build.id,
                    build.project_id,
                    build.version,
                    build.manifest_hash,
                    build.generated_source_hash,
                    build.build_dir,
                    build.status.value,
                    build.created_at,
                    json.dumps(build.files),
                ),
            )

    def get_by_id(self, build_id: str) -> Build | None:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM builds WHERE id = ?;", (build_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Build(
                id=row["id"],
                project_id=row["project_id"],
                version=row["version"],
                manifest_hash=row["manifest_hash"],
                generated_source_hash=row["generated_source_hash"],
                build_dir=row["build_dir"],
                status=row["status"],
                created_at=row["created_at"],
                files=json.loads(row["files_json"]),
            )

    def list_by_project(self, project_id: str) -> list[Build]:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM builds WHERE project_id = ? ORDER BY created_at DESC;",
                (project_id,),
            )
            return [
                Build(
                    id=row["id"],
                    project_id=row["project_id"],
                    version=row["version"],
                    manifest_hash=row["manifest_hash"],
                    generated_source_hash=row["generated_source_hash"],
                    build_dir=row["build_dir"],
                    status=row["status"],
                    created_at=row["created_at"],
                    files=json.loads(row["files_json"]),
                )
                for row in cursor.fetchall()
            ]


class ApprovalRepository:
    def __init__(self, db_path: Path | None = None):
        self.mgr = get_db_manager(db_path)

    def save(self, grant: ApprovalGrant) -> None:
        with self.mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO approval_grants
                (id, correlation_id, tool_name, argument_hash, actor, reason, granted_at, expires_at, single_use, consumed, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    consumed=excluded.consumed;
                """,
                (
                    grant.id,
                    grant.correlation_id,
                    grant.tool_name,
                    grant.argument_hash,
                    grant.actor,
                    grant.reason,
                    grant.granted_at,
                    grant.expires_at,
                    1 if grant.single_use else 0,
                    1 if grant.consumed else 0,
                    json.dumps(grant.details),
                ),
            )

    def find_valid_grant(self, tool_name: str, argument_hash: str) -> ApprovalGrant | None:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM approval_grants
                WHERE tool_name = ? AND argument_hash = ? AND consumed = 0
                ORDER BY granted_at DESC LIMIT 1;
                """,
                (tool_name, argument_hash),
            )
            row = cursor.fetchone()
            if not row:
                return None
            grant = ApprovalGrant(
                id=row["id"],
                correlation_id=row["correlation_id"],
                tool_name=row["tool_name"],
                argument_hash=row["argument_hash"],
                actor=row["actor"],
                reason=row["reason"],
                granted_at=row["granted_at"],
                expires_at=row["expires_at"],
                single_use=bool(row["single_use"]),
                consumed=bool(row["consumed"]),
                details=json.loads(row["details_json"]),
            )
            if grant.is_valid_for(tool_name, argument_hash):
                return grant
            return None

    def mark_consumed(self, grant_id: str) -> None:
        with self.mgr.get_connection() as conn:
            conn.execute("UPDATE approval_grants SET consumed = 1 WHERE id = ?;", (grant_id,))

    def list_recent(self, limit: int = 50) -> list[ApprovalGrant]:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM approval_grants ORDER BY granted_at DESC LIMIT ?;", (limit,)
            )
            return [
                ApprovalGrant(
                    id=row["id"],
                    correlation_id=row["correlation_id"],
                    tool_name=row["tool_name"],
                    argument_hash=row["argument_hash"],
                    actor=row["actor"],
                    reason=row["reason"],
                    granted_at=row["granted_at"],
                    expires_at=row["expires_at"],
                    single_use=bool(row["single_use"]),
                    consumed=bool(row["consumed"]),
                    details=json.loads(row["details_json"]),
                )
                for row in cursor.fetchall()
            ]


class PackageRepository:
    def __init__(self, db_path: Path | None = None):
        self.mgr = get_db_manager(db_path)

    def save(self, pkg: PackageMetadata) -> None:
        with self.mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO packages (id, build_id, version, archive_path, sha256, size_bytes, created_at, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET verified=excluded.verified;
                """,
                (
                    pkg.id,
                    pkg.build_id,
                    pkg.version,
                    pkg.archive_path,
                    pkg.sha256,
                    pkg.size_bytes,
                    pkg.created_at,
                    1 if pkg.verified else 0,
                ),
            )

    def list_by_build(self, build_id: str) -> list[PackageMetadata]:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM packages WHERE build_id = ? ORDER BY created_at DESC;", (build_id,)
            )
            return [
                PackageMetadata(
                    id=row["id"],
                    build_id=row["build_id"],
                    version=row["version"],
                    archive_path=row["archive_path"],
                    sha256=row["sha256"],
                    size_bytes=row["size_bytes"],
                    created_at=row["created_at"],
                    verified=bool(row["verified"]),
                )
                for row in cursor.fetchall()
            ]


class ToolCallRepository:
    def __init__(self, db_path: Path | None = None):
        self.mgr = get_db_manager(db_path)

    def save(self, tc: ToolCall) -> None:
        with self.mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tool_calls
                (id, correlation_id, connector_id, tool_name, argument_hash, arguments_json, actor, outcome, timestamp, duration_seconds, result_json, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    tc.id,
                    tc.correlation_id,
                    tc.connector_id,
                    tc.tool_name,
                    tc.argument_hash,
                    json.dumps(tc.arguments),
                    tc.actor,
                    tc.outcome.value,
                    tc.timestamp,
                    tc.duration_seconds,
                    json.dumps(tc.result) if tc.result else None,
                    tc.error_message,
                ),
            )

    def list_recent(self, limit: int = 50) -> list[ToolCall]:
        with self.mgr.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tool_calls ORDER BY timestamp DESC LIMIT ?;", (limit,))
            return [
                ToolCall(
                    id=row["id"],
                    correlation_id=row["correlation_id"],
                    connector_id=row["connector_id"],
                    tool_name=row["tool_name"],
                    argument_hash=row["argument_hash"],
                    arguments=json.loads(row["arguments_json"]),
                    actor=row["actor"],
                    outcome=row["outcome"],
                    timestamp=row["timestamp"],
                    duration_seconds=row["duration_seconds"],
                    result=json.loads(row["result_json"]) if row["result_json"] else None,
                    error_message=row["error_message"],
                )
                for row in cursor.fetchall()
            ]
