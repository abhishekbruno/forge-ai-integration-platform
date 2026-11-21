"""Background Qt Worker threads for non-blocking UI execution."""

from __future__ import annotations

import asyncio
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from forge.core.application_service import ApplicationService
from forge.domain.execution import TestRun
from forge.domain.project import Build, PackageMetadata


class GenerateWorker(QThread):
    """Background worker for connector compilation."""

    finished = Signal(Build)
    failed = Signal(str)

    def __init__(self, project_id: str, workspace_path: Path, manifest_path: Path):
        super().__init__()
        self.project_id = project_id
        self.workspace_path = workspace_path
        self.manifest_path = manifest_path

    def run(self):
        svc = ApplicationService()
        try:
            build = svc.generate_connector(self.project_id, self.workspace_path, self.manifest_path)
            self.finished.emit(build)
        except Exception as exc:
            self.failed.emit(str(exc))


class TestRunnerWorker(QThread):
    """Background worker executing verification test suites."""

    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, build: Build, workspace: Path, live_blender: bool = False):
        super().__init__()
        self.build = build
        self.workspace = workspace
        self.live_blender = live_blender

    def run(self):
        svc = ApplicationService()
        try:
            runs: list[TestRun] = []
            # 1. MCP contract test
            contract_run = asyncio.run(
                svc.test_orchestrator.run_mcp_contract_tests(self.build, self.workspace)
            )
            runs.append(contract_run)

            # 2. FixtureLab e2e
            e2e_run = svc.test_orchestrator.run_fixturelab_e2e(self.build, self.workspace)
            runs.append(e2e_run)

            # 3. Blender live if requested
            if self.live_blender:
                blender_run = svc.test_orchestrator.run_blender_live_test(
                    self.build, self.workspace
                )
                runs.append(blender_run)

            self.finished.emit(runs)
        except Exception as exc:
            self.failed.emit(str(exc))


class PackageWorker(QThread):
    """Background worker exporting standalone archives."""

    finished = Signal(PackageMetadata)
    failed = Signal(str)

    def __init__(self, build_id: str, workspace: Path):
        super().__init__()
        self.build_id = build_id
        self.workspace = workspace

    def run(self):
        svc = ApplicationService()
        try:
            pkg = svc.export_package(self.build_id, self.workspace)
            self.finished.emit(pkg)
        except Exception as exc:
            self.failed.emit(str(exc))
