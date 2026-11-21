"""Environment and installation diagnostics (forge doctor)."""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from forge.adapters.registry import get_adapter_registry
from forge.config import get_config
from forge.persistence.migrations import apply_migrations


class DiagnosticStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class DiagnosticCheck:
    name: str
    status: DiagnosticStatus
    message: str
    details: dict[str, Any] | None = None


@dataclass
class DoctorReport:
    checks: list[DiagnosticCheck]
    overall_status: DiagnosticStatus

    @property
    def passed(self) -> bool:
        return self.overall_status != DiagnosticStatus.FAIL


class Doctor:
    """Performs deep environmental and functional capability diagnostics."""

    def run_diagnostics(self, workspace_path: Path | None = None) -> DoctorReport:
        checks: list[DiagnosticCheck] = []

        # 1. Python version check
        py_ver = sys.version_info
        if py_ver >= (3, 12):
            checks.append(
                DiagnosticCheck(
                    name="Python Runtime",
                    status=DiagnosticStatus.PASS,
                    message=f"Python {platform.python_version()} on {platform.system()} ({sys.executable})",
                )
            )
        else:
            checks.append(
                DiagnosticCheck(
                    name="Python Runtime",
                    status=DiagnosticStatus.FAIL,
                    message=f"Python version {platform.python_version()} is below required 3.12.",
                )
            )

        # 2. Critical dependency imports
        required_modules = [
            ("mcp", "MCP Python SDK v2"),
            ("PySide6", "Qt6 GUI Framework"),
            ("pydantic", "Pydantic Data Models"),
            ("yaml", "PyYAML Safe Parser"),
            ("jinja2", "Jinja2 Template Engine"),
            ("platformdirs", "Platform Directories"),
            ("jsonschema", "JSON Schema Validator"),
            ("rich", "Rich Terminal UI"),
            ("typer", "Typer CLI Framework"),
        ]
        missing_mods = []
        for mod, desc in required_modules:
            try:
                __import__(mod)
            except ImportError:
                missing_mods.append(f"{mod} ({desc})")

        if not missing_mods:
            checks.append(
                DiagnosticCheck(
                    name="Core Dependencies",
                    status=DiagnosticStatus.PASS,
                    message="All required core Python packages are installed and importable.",
                )
            )
        else:
            checks.append(
                DiagnosticCheck(
                    name="Core Dependencies",
                    status=DiagnosticStatus.FAIL,
                    message=f"Missing dependencies: {', '.join(missing_mods)}",
                )
            )

        # 3. User data directory check
        cfg = get_config()
        try:
            cfg.data_dir.mkdir(parents=True, exist_ok=True)
            test_file = cfg.data_dir / ".doctor_probe"
            test_file.write_text("probe", encoding="utf-8")
            test_file.unlink()
            checks.append(
                DiagnosticCheck(
                    name="Application Data Directory",
                    status=DiagnosticStatus.PASS,
                    message=f"Writable data directory: {cfg.data_dir}",
                )
            )
        except Exception as exc:
            checks.append(
                DiagnosticCheck(
                    name="Application Data Directory",
                    status=DiagnosticStatus.FAIL,
                    message=f"Cannot write to data dir '{cfg.data_dir}': {exc}",
                )
            )

        # 4. Database & migrations check
        try:
            version = apply_migrations()
            checks.append(
                DiagnosticCheck(
                    name="SQLite Database",
                    status=DiagnosticStatus.PASS,
                    message=f"Connected to {cfg.db_path} (migration v{version})",
                )
            )
        except Exception as exc:
            checks.append(
                DiagnosticCheck(
                    name="SQLite Database",
                    status=DiagnosticStatus.FAIL,
                    message=f"Database migration failure: {exc}",
                )
            )

        # 5. Registered adapters check
        reg = get_adapter_registry()
        adapter_ids = [a.id for a in reg.list_adapters()]
        if "forge.adapters.fixturelab" in adapter_ids:
            checks.append(
                DiagnosticCheck(
                    name="FixtureLab Reference Adapter",
                    status=DiagnosticStatus.PASS,
                    message="FixtureLab deterministic adapter is registered and ready.",
                )
            )
        else:
            checks.append(
                DiagnosticCheck(
                    name="FixtureLab Reference Adapter",
                    status=DiagnosticStatus.FAIL,
                    message="FixtureLab adapter is not registered.",
                )
            )

        # 6. Blender adapter and binary detection
        blender_adapter = reg.get_adapter("forge.adapters.blender")
        detect_result = blender_adapter.detect_application()
        if detect_result.get("available", False):
            checks.append(
                DiagnosticCheck(
                    name="Blender Integration",
                    status=DiagnosticStatus.PASS,
                    message=f"Blender binary available: {detect_result.get('version')} ({detect_result.get('executable')})",
                )
            )
        else:
            checks.append(
                DiagnosticCheck(
                    name="Blender Integration",
                    status=DiagnosticStatus.WARN,
                    message=detect_result.get(
                        "message", "Blender executable not found. Blender features will be skipped."
                    ),
                )
            )

        # 7. Environment variables safety inspection (names only, no secrets)
        forge_vars = [k for k in os.environ if k.startswith("FORGE_")]
        checks.append(
            DiagnosticCheck(
                name="Environment Variables",
                status=DiagnosticStatus.PASS,
                message=f"Active FORGE variables: {', '.join(forge_vars) if forge_vars else 'none (defaults in use)'}",
            )
        )

        # 8. Workspace safety check if provided
        if workspace_path:
            ws = Path(workspace_path).resolve()
            if ws.is_dir():
                checks.append(
                    DiagnosticCheck(
                        name="Project Workspace",
                        status=DiagnosticStatus.PASS,
                        message=f"Valid workspace path: {ws}",
                    )
                )
            else:
                checks.append(
                    DiagnosticCheck(
                        name="Project Workspace",
                        status=DiagnosticStatus.FAIL,
                        message=f"Workspace path does not exist or is not a directory: {ws}",
                    )
                )

        # Compute overall status
        if any(c.status == DiagnosticStatus.FAIL for c in checks):
            overall = DiagnosticStatus.FAIL
        elif any(c.status == DiagnosticStatus.WARN for c in checks):
            overall = DiagnosticStatus.WARN
        else:
            overall = DiagnosticStatus.PASS

        return DoctorReport(checks=checks, overall_status=overall)
