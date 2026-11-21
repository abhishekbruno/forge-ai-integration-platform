"""Application service facade coordinating core domain capabilities for UI and CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forge.core.approval_broker import get_approval_broker
from forge.core.build_service import BuildService
from forge.core.doctor import Doctor, DoctorReport
from forge.core.execution_gateway import get_execution_gateway
from forge.core.manifest_service import get_manifest_service
from forge.core.packaging import PackageExporter
from forge.core.project_service import ProjectService
from forge.core.test_orchestrator import TestOrchestrator
from forge.domain.execution import ApprovalGrant
from forge.domain.manifest import IntegrationManifest
from forge.domain.project import Build, PackageMetadata, Project
from forge.persistence.audit_journal import AuditJournal
from forge.persistence.repositories import (
    ApprovalRepository,
    BuildRepository,
    PackageRepository,
    ProjectRepository,
    ToolCallRepository,
)


class ApplicationService:
    """Unified application coordinator."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path
        self.project_service = ProjectService(db_path)
        self.manifest_service = get_manifest_service()
        self.build_service = BuildService(db_path)
        self.approval_broker = get_approval_broker(db_path)
        self.execution_gateway = get_execution_gateway(db_path)
        self.package_exporter = PackageExporter(db_path)
        self.test_orchestrator = TestOrchestrator(db_path)
        self.doctor = Doctor()
        self.audit_journal = AuditJournal(db_path)

        self.project_repo = ProjectRepository(db_path)
        self.build_repo = BuildRepository(db_path)
        self.approval_repo = ApprovalRepository(db_path)
        self.package_repo = PackageRepository(db_path)
        self.tool_call_repo = ToolCallRepository(db_path)

    def create_project(
        self,
        workspace_path: str | Path,
        name: str,
        manifest: str | Path | None = None,
        initial_manifest: str | Path | None = None,
    ) -> Project:
        init_m = initial_manifest or manifest
        return self.project_service.create_project(workspace_path, name, init_m)

    def open_project(self, workspace_path: str | Path) -> Project:
        return self.project_service.open_project(workspace_path)

    def list_projects(self) -> list[Project]:
        return self.project_service.list_projects()

    def validate_manifest(self, manifest_path: str | Path) -> IntegrationManifest:
        return self.manifest_service.load_and_validate(manifest_path)

    def generate_connector(
        self, project_id: str, workspace_path: str | Path, manifest_path: str | Path
    ) -> Build:
        manifest = self.validate_manifest(manifest_path)
        return self.build_service.generate_build(project_id, workspace_path, manifest)

    def export_package(self, build_id: str, workspace_path: str | Path) -> PackageMetadata:
        build = self.build_repo.get_by_id(build_id)
        if not build:
            raise ValueError(f"Build ID '{build_id}' not found.")
        return self.package_exporter.export_package(build, workspace_path)

    def run_diagnostics(self, workspace_path: str | Path | None = None) -> DoctorReport:
        return self.doctor.run_diagnostics(Path(workspace_path) if workspace_path else None)

    def grant_approval(
        self,
        tool_name: str,
        argument_hash: str,
        correlation_id: str,
        ttl_seconds: int = 300,
        actor: str = "human_operator",
    ) -> ApprovalGrant:
        return self.approval_broker.grant_approval(
            tool_name=tool_name,
            argument_hash=argument_hash,
            correlation_id=correlation_id,
            ttl_seconds=ttl_seconds,
            actor=actor,
        )

    def list_pending_approvals(self) -> list[dict[str, Any]]:
        return self.approval_broker.list_pending_requests()

    def verify_audit_integrity(self) -> tuple[bool, str, int | None]:
        return self.audit_journal.verify_integrity()
