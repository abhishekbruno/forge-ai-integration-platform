"""Build service orchestrating connector compilation and provenance tracking."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from forge.core.generator import ConnectorGenerator
from forge.core.manifest_service import get_manifest_service
from forge.domain.manifest import IntegrationManifest
from forge.domain.project import Build, BuildStatus
from forge.events.bus import get_event_bus
from forge.events.models import (
    EVENT_CONNECTOR_GENERATION_FINISHED,
    EVENT_CONNECTOR_GENERATION_STARTED,
    ForgeEvent,
)
from forge.persistence.audit_journal import AuditJournal
from forge.persistence.repositories import BuildRepository
from forge.security.hashes import canonical_json_dumps, hash_string


class BuildService:
    """Manages creation, immutability, and storage of connector package builds."""

    def __init__(self, db_path: Path | None = None):
        self.generator = ConnectorGenerator()
        self.manifest_service = get_manifest_service()
        self.build_repo = BuildRepository(db_path)
        self.audit_journal = AuditJournal(db_path)

    def generate_build(
        self,
        project_id: str,
        workspace_path: Path | str,
        manifest: IntegrationManifest,
    ) -> Build:
        """Deterministically compile a validated manifest into a runnable MCP build."""
        ws = Path(workspace_path).resolve()
        build_id = str(uuid4())
        build_dir = ws / ".forge" / "builds" / build_id
        build_dir.mkdir(parents=True, exist_ok=True)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_CONNECTOR_GENERATION_STARTED,
                correlation_id=build_id,
                project_id=project_id,
                details={"integration_id": manifest.integration.id, "build_id": build_id},
            )
        )

        manifest_hash = hash_string(canonical_json_dumps(manifest.model_dump()))

        # Generate files
        file_hashes = self.generator.generate(
            manifest=manifest,
            output_dir=build_dir,
            workspace_path=ws,
            build_id=build_id,
        )

        # Aggregate source hash
        source_hash = hash_string(canonical_json_dumps(file_hashes))

        build = Build(
            id=build_id,
            project_id=project_id,
            version=manifest.integration.version,
            manifest_hash=manifest_hash,
            generated_source_hash=source_hash,
            build_dir=str(build_dir),
            status=BuildStatus.GENERATED,
            files=list(file_hashes.keys()),
        )

        self.build_repo.save(build)

        self.audit_journal.record_event(
            action="connector.generate",
            target=f"{manifest.integration.id}:{build_id}",
            outcome="success",
            correlation_id=build_id,
            details={
                "version": build.version,
                "manifest_hash": manifest_hash,
                "source_hash": source_hash,
                "file_count": len(file_hashes),
            },
        )

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_CONNECTOR_GENERATION_FINISHED,
                correlation_id=build_id,
                project_id=project_id,
                details={
                    "build_id": build_id,
                    "source_hash": source_hash,
                    "build_dir": str(build_dir),
                },
            )
        )

        return build

    def get_build(self, build_id: str) -> Build | None:
        return self.build_repo.get_by_id(build_id)

    def list_builds(self, project_id: str) -> list[Build]:
        return self.build_repo.list_by_project(project_id)
