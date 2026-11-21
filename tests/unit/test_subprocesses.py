"""Unit tests for subprocess security wrapper."""

import sys

from forge.security.subprocesses import (
    run_safe_subprocess,
    sanitize_environment,
)


def test_run_safe_subprocess_echo():
    cmd = [sys.executable, "-c", "import sys; print('FORGE_ECHO'); sys.exit(0)"]
    result = run_safe_subprocess(cmd, timeout_seconds=5.0)
    assert result.exit_code == 0
    assert "FORGE_ECHO" in result.stdout
    assert result.timed_out is False


def test_subprocess_timeout_termination():
    cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
    result = run_safe_subprocess(cmd, timeout_seconds=1.0)
    assert result.timed_out is True
    assert result.exit_code == -999


def test_subprocess_environment_sanitization():
    env = sanitize_environment(
        base_env={"UNTRUSTED_KEY": "secret_val", "PATH": "safe_path"},
        extra_env={"CUSTOM_KEY": "allowed_val"},
    )
    assert "UNTRUSTED_KEY" not in env
    assert "PATH" in env
    assert env["CUSTOM_KEY"] == "allowed_val"
