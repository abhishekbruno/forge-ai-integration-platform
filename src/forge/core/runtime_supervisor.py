"""Runtime supervisor managing background connector server processes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Mapping

from forge.security.subprocesses import sanitize_environment, terminate_process_tree


class RuntimeSupervisor:
    """Manages starting, supervising, and stopping generated MCP servers."""

    def __init__(self) -> None:
        self._active_processes: dict[str, subprocess.Popen] = {}

    def start_connector_server(
        self,
        build_dir: Path | str,
        workspace_path: Path | str,
        extra_env: Mapping[str, str] | None = None,
    ) -> subprocess.Popen:
        """Start a connector server subprocess communicating over stdio."""
        b_dir = Path(build_dir).resolve()
        launcher = b_dir / "launcher.py"
        if not launcher.is_file():
            raise FileNotFoundError(f"Launcher script not found in build directory: {launcher}")

        env = sanitize_environment(
            extra_env={
                "FORGE_WORKSPACE": str(Path(workspace_path).resolve()),
                "PYTHONUNBUFFERED": "1",
                **(dict(extra_env) if extra_env else {}),
            }
        )

        proc = subprocess.Popen(
            [sys.executable, str(launcher)],
            cwd=str(b_dir),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

        self._active_processes[str(b_dir)] = proc
        return proc

    def stop_connector_server(self, build_dir: Path | str) -> None:
        """Terminate a running connector server cleanly."""
        key = str(Path(build_dir).resolve())
        proc = self._active_processes.pop(key, None)
        if proc and proc.poll() is None:
            terminate_process_tree(proc.pid)
            try:
                proc.wait(timeout=2.0)
            except Exception:
                pass

    def stop_all(self) -> None:
        """Stop all running servers upon application exit."""
        for key in list(self._active_processes.keys()):
            self.stop_connector_server(key)
