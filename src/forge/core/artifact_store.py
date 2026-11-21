"""Artifact store for organizing test outputs, scene files, and diagnostics."""

from __future__ import annotations

from pathlib import Path

from forge.security.paths import ensure_within_workspace


class ArtifactStore:
    """Manages the lifecycle of project-specific build artifacts and test reports."""

    def __init__(self, workspace_path: Path):
        self.workspace = Path(workspace_path).resolve()
        self.artifacts_dir = self.workspace / ".forge" / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def get_run_artifact_dir(self, run_id: str) -> Path:
        run_dir = self.artifacts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def store_file(self, run_id: str, filename: str, content: str | bytes) -> Path:
        run_dir = self.get_run_artifact_dir(run_id)
        target = run_dir / filename
        ensure_within_workspace(target, self.workspace, allow_nonexistent=True)

        if isinstance(content, str):
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(target, "wb") as f:
                f.write(content)

        return target
