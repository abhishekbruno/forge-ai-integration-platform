"""Integration tests for build service."""

from pathlib import Path

from forge.core.build_service import BuildService
from forge.core.manifest_service import ManifestService


def test_build_service_generation(temp_workspace, temp_db):
    ms = ManifestService()
    manifest = ms.load_and_validate(Path("manifests/fixturelab.yaml"))

    bs = BuildService(temp_db)
    build = bs.generate_build("proj-123", temp_workspace, manifest)

    assert build.project_id == "proj-123"
    assert build.version == manifest.integration.version
    assert Path(build.build_dir).is_dir()
    assert "server.py" in build.files

    retrieved = bs.get_build(build.id)
    assert retrieved is not None
    assert retrieved.id == build.id
