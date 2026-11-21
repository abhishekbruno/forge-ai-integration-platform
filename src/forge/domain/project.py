"""Project, build, and package domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(BaseModel):
    """A local FORGE workspace project."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    workspace_path: str
    manifest_path: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: ProjectStatus = ProjectStatus.ACTIVE


class BuildStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"


class Build(BaseModel):
    """Record of a generated MCP connector package build."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    version: str
    manifest_hash: str
    generated_source_hash: str
    build_dir: str
    status: BuildStatus = BuildStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    files: list[str] = Field(default_factory=list)


class PackageMetadata(BaseModel):
    """Record of an exported installable connector archive."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    build_id: str
    version: str
    archive_path: str
    sha256: str
    size_bytes: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified: bool = False
