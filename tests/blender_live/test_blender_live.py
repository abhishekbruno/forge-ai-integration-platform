"""Blender live integration tests (executed if Blender is installed, gracefully skipped if absent)."""

from pathlib import Path

import pytest

from forge.adapters.registry import get_adapter_registry
from forge.core.build_service import BuildService
from forge.core.manifest_service import ManifestService
from forge.core.test_orchestrator import TestOrchestrator


@pytest.mark.blender_live
def test_blender_live_or_skip(temp_workspace, temp_db):
    adapter = get_adapter_registry().get_adapter("forge.adapters.blender")
    detection = adapter.detect_application()

    ms = ManifestService()
    manifest = ms.load_and_validate(Path("manifests/blender.yaml"))

    bs = BuildService(temp_db)
    build = bs.generate_build("proj-bl-live", temp_workspace, manifest)

    orch = TestOrchestrator(temp_db)
    run = orch.run_blender_live_test(build, temp_workspace)

    if not detection.get("available", False):
        assert run.status.value == "skipped"
        assert len(run.test_cases) == 1
        assert run.test_cases[0].status.value == "skipped"
        assert (
            "not found" in run.test_cases[0].skip_reason.lower()
            or "not installed" in run.test_cases[0].skip_reason.lower()
        )
    else:
        assert run.status.value == "passed"
