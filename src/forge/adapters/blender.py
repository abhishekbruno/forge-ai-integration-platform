"""Host-side Blender adapter implementation.

Orchestrates safe subprocess execution of Blender in background mode,
verifying input hashes, parameter schemas, and copy-on-write integrity.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from forge.adapters.base import BaseAdapter
from forge.config import get_config
from forge.domain.capability import CapabilityDefinition, RiskLevel
from forge.domain.errors import AdapterExecutionError
from forge.security.hashes import hash_file
from forge.security.paths import ensure_within_workspace
from forge.security.subprocesses import run_safe_subprocess


class BlenderAdapter(BaseAdapter):
    """Secure Blender integration adapter using background subprocess execution."""

    def __init__(self, executable_path: Path | None = None):
        self._custom_exe = executable_path

    @property
    def id(self) -> str:
        return "forge.adapters.blender"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def supported_app_id(self) -> str:
        return "blender"

    @property
    def supported_versions(self) -> str:
        return ">=4.0,<6.0"

    def get_executable(self) -> Path | None:
        if self._custom_exe and self._custom_exe.is_file():
            return self._custom_exe
        return get_config().blender_executable

    def detect_application(self, workspace: Path | None = None) -> dict[str, Any]:
        exe = self.get_executable()
        if not exe or not exe.is_file():
            return {
                "available": False,
                "version": None,
                "executable": None,
                "status": "missing",
                "message": "Blender executable not found in PATH or configured paths.",
            }

        # Query version
        result = run_safe_subprocess([str(exe), "--version"], timeout_seconds=10.0)
        if result.exit_code == 0:
            version_line = result.stdout.splitlines()[0] if result.stdout else "Blender (unknown)"
            return {
                "available": True,
                "version": version_line.strip(),
                "executable": str(exe),
                "status": "ready",
                "message": f"Blender detected: {version_line.strip()}",
            }
        else:
            return {
                "available": False,
                "version": None,
                "executable": str(exe),
                "status": "error",
                "message": f"Blender returned exit code {result.exit_code}: {result.stderr}",
            }

    def list_capabilities(self) -> list[CapabilityDefinition]:
        return [
            CapabilityDefinition(
                name="blender_scene_summary",
                handler="blender.scene_summary",
                description="Return a structured summary of a Blender scene.",
                risk=RiskLevel.READ,
                timeout_seconds=45,
                input_schema={
                    "type": "object",
                    "properties": {"blend_file": {"type": "string"}},
                    "required": ["blend_file"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "object_count": {"type": "integer"},
                        "object_types": {"type": "object"},
                        "blender_version": {"type": "string"},
                    },
                    "required": ["object_count", "object_types", "blender_version"],
                },
            ),
            CapabilityDefinition(
                name="blender_list_objects",
                handler="blender.list_objects",
                description="List objects in the scene with transforms and types.",
                risk=RiskLevel.READ,
                timeout_seconds=45,
                input_schema={
                    "type": "object",
                    "properties": {
                        "blend_file": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                    },
                    "required": ["blend_file"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {"objects": {"type": "array"}, "total": {"type": "integer"}},
                    "required": ["objects", "total"],
                },
            ),
            CapabilityDefinition(
                name="blender_inspect_object",
                handler="blender.inspect_object",
                description="Retrieve an object by exact name, returning dimensions and hierarchy.",
                risk=RiskLevel.READ,
                timeout_seconds=45,
                input_schema={
                    "type": "object",
                    "properties": {
                        "blend_file": {"type": "string"},
                        "object_name": {"type": "string", "minLength": 1},
                    },
                    "required": ["blend_file", "object_name"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "type": {"type": "string"}},
                    "required": ["name", "type"],
                },
            ),
            CapabilityDefinition(
                name="blender_list_materials",
                handler="blender.list_materials",
                description="List material names and metadata from the scene.",
                risk=RiskLevel.READ,
                timeout_seconds=45,
                input_schema={
                    "type": "object",
                    "properties": {"blend_file": {"type": "string"}},
                    "required": ["blend_file"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {"materials": {"type": "array"}, "total": {"type": "integer"}},
                    "required": ["materials", "total"],
                },
            ),
            CapabilityDefinition(
                name="blender_create_primitive",
                handler="blender.create_primitive",
                description="Create an allowed primitive in a NEW copy-on-write scene file.",
                risk=RiskLevel.WRITE,
                timeout_seconds=60,
                input_schema={
                    "type": "object",
                    "properties": {
                        "blend_file": {"type": "string"},
                        "output_file": {"type": "string"},
                        "primitive_type": {
                            "type": "string",
                            "enum": ["cube", "sphere", "cylinder", "plane"],
                        },
                        "name": {"type": "string", "minLength": 1},
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                        },
                        "size": {"type": "number", "minimum": 0.01},
                    },
                    "required": ["blend_file", "output_file", "primitive_type", "name"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "created_name": {"type": "string"},
                        "output_file": {"type": "string"},
                        "source_preserved": {"type": "boolean"},
                    },
                    "required": ["success", "created_name", "output_file", "source_preserved"],
                },
            ),
            CapabilityDefinition(
                name="blender_set_transform",
                handler="blender.set_transform",
                description="Change transform on a named object in a NEW copy-on-write scene file.",
                risk=RiskLevel.WRITE,
                timeout_seconds=60,
                input_schema={
                    "type": "object",
                    "properties": {
                        "blend_file": {"type": "string"},
                        "output_file": {"type": "string"},
                        "object_name": {"type": "string", "minLength": 1},
                        "location": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                        },
                        "rotation_euler": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                        },
                        "scale": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 3,
                            "maxItems": 3,
                        },
                    },
                    "required": ["blend_file", "output_file", "object_name"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "object_name": {"type": "string"},
                        "output_file": {"type": "string"},
                    },
                    "required": ["success", "object_name", "output_file"],
                },
            ),
            CapabilityDefinition(
                name="blender_rename_object",
                handler="blender.rename_object",
                description="Rename an object in a NEW copy-on-write scene file.",
                risk=RiskLevel.WRITE,
                timeout_seconds=60,
                input_schema={
                    "type": "object",
                    "properties": {
                        "blend_file": {"type": "string"},
                        "output_file": {"type": "string"},
                        "old_name": {"type": "string", "minLength": 1},
                        "new_name": {"type": "string", "minLength": 1},
                    },
                    "required": ["blend_file", "output_file", "old_name", "new_name"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "renamed_from": {"type": "string"},
                        "renamed_to": {"type": "string"},
                        "output_file": {"type": "string"},
                    },
                    "required": ["success", "renamed_from", "renamed_to", "output_file"],
                },
            ),
            CapabilityDefinition(
                name="blender_save_scene_copy",
                handler="blender.save_scene_copy",
                description="Safely copy the scene file to a new destination path.",
                risk=RiskLevel.WRITE,
                timeout_seconds=45,
                input_schema={
                    "type": "object",
                    "properties": {
                        "blend_file": {"type": "string"},
                        "output_file": {"type": "string"},
                    },
                    "required": ["blend_file", "output_file"],
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "output_file": {"type": "string"},
                    },
                    "required": ["success", "output_file"],
                },
            ),
        ]

    def invoke_capability(
        self,
        handler: str,
        args: dict[str, Any],
        workspace: Path,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        workspace = Path(workspace).resolve()
        exe = self.get_executable()
        if not exe or not exe.is_file():
            raise AdapterExecutionError(
                "Blender executable not found. Configure path in Settings or set FORGE_BLENDER_PATH."
            )

        # Validate input file path within workspace
        raw_blend_file = args.get("blend_file")
        if not raw_blend_file:
            raise AdapterExecutionError(
                "Missing required 'blend_file' argument for Blender operation."
            )

        input_path = ensure_within_workspace(raw_blend_file, workspace, allow_nonexistent=False)
        if not input_path.is_file() or input_path.suffix.lower() != ".blend":
            raise AdapterExecutionError(f"Input file is not a valid .blend file: {input_path}")

        # Compute pre-hash of original scene file
        initial_hash = hash_file(input_path)

        # Validate output file path if mutating
        is_mutating = "output_file" in args
        target_output_path: Path | None = None
        if is_mutating:
            raw_output = args["output_file"]
            target_output_path = ensure_within_workspace(
                raw_output, workspace, allow_nonexistent=True
            )
            if target_output_path.suffix.lower() != ".blend":
                raise AdapterExecutionError(
                    f"Target output file must have .blend extension: {target_output_path}"
                )
            if target_output_path == input_path:
                raise AdapterExecutionError(
                    f"Copy-on-write violation: output_file '{target_output_path}' cannot overwrite input_file."
                )

        runner_script = Path(__file__).parent / "blender_runner.py"
        if not runner_script.is_file():
            raise AdapterExecutionError(f"Blender runner script missing at {runner_script}")

        # Run inside a private temporary directory for IPC exchange
        with tempfile.TemporaryDirectory(prefix="forge_blender_") as temp_dir:
            temp_path = Path(temp_dir)
            req_file = temp_path / "request.json"
            res_file = temp_path / "result.json"

            # Prepare args with canonicalized absolute paths
            runner_args = dict(args)
            runner_args["blend_file"] = str(input_path)
            if target_output_path:
                runner_args["output_file"] = str(target_output_path)

            with open(req_file, "w", encoding="utf-8") as f:
                json.dump({"handler": handler, "args": runner_args}, f)

            # Construct safe CLI args
            cmd = [
                str(exe),
                "--background",
                str(input_path),
                "--python-exit-code",
                "1",
                "--python",
                str(runner_script),
                "--",
                str(req_file),
                str(res_file),
            ]

            result = run_safe_subprocess(cmd, cwd=workspace, timeout_seconds=60.0)

            # Verify input file was not modified (Copy-on-Write invariant)
            post_hash = hash_file(input_path)
            if post_hash != initial_hash:
                raise AdapterExecutionError(
                    f"CRITICAL SAFETY VIOLATION: Original .blend file '{input_path}' was mutated!"
                )

            if result.exit_code != 0:
                raise AdapterExecutionError(
                    f"Blender subprocess failed with exit code {result.exit_code}:\n{result.stderr or result.stdout}"
                )

            if not res_file.is_file():
                raise AdapterExecutionError(
                    f"Blender finished without producing result file. Logs:\n{result.stderr or result.stdout}"
                )

            try:
                with open(res_file, "r", encoding="utf-8") as f:
                    output_data = json.load(f)
            except Exception as exc:
                raise AdapterExecutionError(f"Failed to parse Blender result JSON: {exc}") from exc

            if not output_data.get("success", False):
                raise AdapterExecutionError(
                    f"Blender runner reported error: {output_data.get('error')}"
                )

            # If mutating, verify the output file exists and is non-empty
            if is_mutating and target_output_path:
                if not target_output_path.is_file() or target_output_path.stat().st_size == 0:
                    raise AdapterExecutionError(
                        f"Mutating operation completed but output file '{target_output_path}' was not created."
                    )

            return output_data.get("data", {})
