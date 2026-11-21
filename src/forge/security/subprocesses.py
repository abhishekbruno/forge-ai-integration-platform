"""Secure subprocess execution wrapper with timeout, argument validation, and resource limits."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class SubprocessResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


class SubprocessSecurityError(Exception):
    """Raised when command execution fails security checks or policies."""


SAFE_ENV_ALLOWLIST = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PYTHONUTF8",
    "PYTHONIOENCODING",
    "PYTHONUNBUFFERED",
    "PYTHONPATH",
    "VIRTUAL_ENV",
    "LD_LIBRARY_PATH",
    "FORGE_DB_PATH",
    "FORGE_WORKSPACE",
    "BLENDER_SYSTEM_SCRIPTS",
    "BLENDER_USER_SCRIPTS",
    "QT_QPA_PLATFORM",
}


def sanitize_environment(
    base_env: Mapping[str, str] | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Produce a sanitized environment dict containing only safe system variables plus explicit extras."""
    source = os.environ if base_env is None else base_env
    cleaned: dict[str, str] = {}

    for key, value in source.items():
        if key.upper() in SAFE_ENV_ALLOWLIST:
            cleaned[key] = value

    # Always ensure UTF-8 for python subprocesses
    cleaned["PYTHONUTF8"] = "1"
    cleaned["PYTHONIOENCODING"] = "utf-8"

    if extra_env:
        for k, v in extra_env.items():
            cleaned[k] = str(v)

    return cleaned


def terminate_process_tree(pid: int) -> None:
    """Terminate a process and all its children cleanly."""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass
    else:
        try:
            import signal

            # Only killpg if pid is its own process group leader to prevent killing the parent test runner
            if os.getpgid(pid) == pid:
                os.killpg(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGKILL)
        except Exception:
            try:
                import signal

                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass


def run_safe_subprocess(
    command: Sequence[str],
    cwd: str | Path | None = None,
    timeout_seconds: float = 45.0,
    extra_env: Mapping[str, str] | None = None,
    max_output_bytes: int = 10 * 1024 * 1024,  # 10 MB limit
) -> SubprocessResult:
    """Execute a command securely: no shell, explicit args list, strict timeout, bounded output."""
    if not command or not isinstance(command, (list, tuple)):
        raise SubprocessSecurityError("Command must be a non-empty sequence of arguments.")

    cmd_list = [str(arg) for arg in command]

    # Verify executable exists if specified as path
    exe_path = Path(cmd_list[0])
    if exe_path.is_absolute() and not exe_path.is_file():
        raise FileNotFoundError(f"Executable not found at path: {exe_path}")

    env = sanitize_environment(extra_env=extra_env)

    import time

    start_time = time.monotonic()
    timed_out = False
    proc = None

    try:
        proc = subprocess.Popen(
            cmd_list,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=(sys.platform != "win32"),
        )

        stdout_data, stderr_data = proc.communicate(timeout=timeout_seconds)
        exit_code = proc.returncode

    except subprocess.TimeoutExpired:
        timed_out = True
        if proc:
            terminate_process_tree(proc.pid)
            try:
                stdout_data, stderr_data = proc.communicate(timeout=2.0)
            except Exception:
                stdout_data, stderr_data = "", ""
        exit_code = -999

    except Exception as exc:
        if proc:
            terminate_process_tree(proc.pid)
        raise SubprocessSecurityError(
            f"Subprocess execution error for {cmd_list[0]}: {exc}"
        ) from exc

    duration = time.monotonic() - start_time

    # Truncate if unbounded
    if len(stdout_data.encode("utf-8")) > max_output_bytes:
        stdout_data = (
            stdout_data[:max_output_bytes] + "\n[OUTPUT TRUNCATED BY FORGE SECURITY LIMIT]"
        )
    if len(stderr_data.encode("utf-8")) > max_output_bytes:
        stderr_data = (
            stderr_data[:max_output_bytes] + "\n[STDERR TRUNCATED BY FORGE SECURITY LIMIT]"
        )

    return SubprocessResult(
        command=cmd_list,
        exit_code=exit_code,
        stdout=stdout_data,
        stderr=stderr_data,
        duration_seconds=duration,
        timed_out=timed_out,
    )
