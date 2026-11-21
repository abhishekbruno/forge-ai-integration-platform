"""Project management service."""

from __future__ import annotations

import shutil
from pathlib import Path

from forge.core.manifest_service import get_manifest_service
from forge.domain.errors import ProjectError
from forge.domain.project import Project, ProjectStatus
from forge.events.bus import get_event_bus
from forge.events.models import EVENT_PROJECT_CREATED, EVENT_PROJECT_OPENED, ForgeEvent
from forge.persistence.repositories import ProjectRepository
from forge.security.paths import canonicalize_path


class ProjectService:
    """Manages FORGE workspace projects and their manifest attachments."""

    def __init__(self, db_path: Path | None = None):
        self.repo = ProjectRepository(db_path)
        self.manifest_service = get_manifest_service()

    def create_project(
        self,
        workspace_path: Path | str,
        name: str,
        initial_manifest: Path | str | None = None,
    ) -> Project:
        """Create a new FORGE project in the given workspace directory."""
        ws = canonicalize_path(workspace_path)
        ws.mkdir(parents=True, exist_ok=True)

        forge_dir = ws / ".forge"
        forge_dir.mkdir(parents=True, exist_ok=True)

        manifest_file = ws / "manifest.yaml"
        if initial_manifest:
            init_path = Path(initial_manifest).resolve()
            if not init_path.is_file():
                raise ProjectError(f"Initial manifest file does not exist: {init_path}")
            shutil.copyfile(init_path, manifest_file)
        elif not manifest_file.exists():
            # Copy default fixturelab manifest as starter template
            sample_manifest = (
                Path(__file__).parent.parent.parent.parent / "manifests" / "fixturelab.yaml"
            )
            if sample_manifest.is_file():
                shutil.copyfile(sample_manifest, manifest_file)
            else:
                # Write minimal starter manifest
                manifest_file.write_text(
                    'schema_version: "1.0"\nintegration:\n  id: "my.integration"\n  name: "My Integration"\n  version: "0.1.0"\n'
                    'application:\n  id: "fixturelab"\n  display_name: "FixtureLab"\n  supported_versions: ">=1.0.0"\n'
                    'adapter:\n  id: "forge.adapters.fixturelab"\n  version: "0.1.0"\n'
                    'capabilities:\n  - name: "get_status"\n    handler: "fixturelab.get_status"\n    description: "Get status"\n    risk: "read"\n    input_schema: {type: object}\n    output_schema: {type: object}\n'
                    'policy:\n  default: "deny"\n  read_operations: "allow_within_workspace"\n  write_operations: "explicit_approval"\n  network_operations: "deny"\n',
                    encoding="utf-8",
                )

        project = Project(
            name=name,
            workspace_path=str(ws),
            manifest_path=str(manifest_file),
            status=ProjectStatus.ACTIVE,
        )

        self.repo.save(project)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_PROJECT_CREATED,
                project_id=project.id,
                details={"name": name, "workspace": str(ws)},
            )
        )
        return project

    def open_project(self, workspace_path: Path | str) -> Project:
        """Open or register an existing project directory."""
        ws = canonicalize_path(workspace_path)
        if not ws.is_dir():
            raise ProjectError(f"Workspace path does not exist: {ws}")

        project = self.repo.get_by_workspace(str(ws))
        if not project:
            manifest_file = ws / "manifest.yaml"
            if not manifest_file.exists():
                # Check for any .yaml in root
                yamls = list(ws.glob("*.yaml"))
                manifest_file = yamls[0] if yamls else ws / "manifest.yaml"

            project = Project(
                name=ws.name,
                workspace_path=str(ws),
                manifest_path=str(manifest_file),
                status=ProjectStatus.ACTIVE,
            )
            self.repo.save(project)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_PROJECT_OPENED,
                project_id=project.id,
                details={"name": project.name, "workspace": str(ws)},
            )
        )
        return project

    def list_projects(self) -> list[Project]:
        return self.repo.list_all()
