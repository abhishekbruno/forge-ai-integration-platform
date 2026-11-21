"""Deterministic connector generator rendering standards-compliant MCP packages."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from forge.domain.manifest import IntegrationManifest
from forge.security.hashes import canonical_json_dumps, hash_string

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ConnectorGenerator:
    """Generates runnable, standards-compliant MCP server packages from manifests."""

    def __init__(self, templates_dir: Path | None = None):
        t_dir = templates_dir or TEMPLATES_DIR
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(t_dir)),
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
        )

    def generate(
        self,
        manifest: IntegrationManifest,
        output_dir: Path,
        workspace_path: Path,
        build_id: str,
    ) -> dict[str, str]:
        """Render all connector files into output_dir. Returns dict of {filename: content_hash}."""
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        workspace_path = Path(workspace_path).resolve()

        now_iso = datetime.now(timezone.utc).isoformat()
        python_exe = sys.executable
        launcher_path = str(output_dir / "launcher.py")

        context = {
            "build_id": build_id,
            "generated_at": now_iso,
            "workspace_path": str(workspace_path),
            "workspace_path_repr": repr(str(workspace_path)),
            "python_executable": python_exe,
            "launcher_path": launcher_path,
            "integration": manifest.integration,
            "application": manifest.application,
            "adapter": manifest.adapter,
            "capabilities": manifest.capabilities,
            "policy": manifest.policy,
            "manifest_dict_repr": repr(manifest.model_dump(mode="json")),
        }

        files_to_render = [
            ("connector_pyproject.toml.j2", "pyproject.toml"),
            ("connector_server.py.j2", "server.py"),
            ("connector_readme.md.j2", "README.md"),
            ("connector_launcher.py.j2", "launcher.py"),
            ("connector_client_config.json.j2", "client_config.json"),
        ]

        rendered_files: dict[str, str] = {}

        for tmpl_name, out_filename in files_to_render:
            template = self.jinja_env.get_template(tmpl_name)
            rendered_content = template.render(**context)
            dest_file = output_dir / out_filename
            with open(dest_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(rendered_content)
            rendered_files[out_filename] = hash_string(rendered_content)

        # 6. Generate tools.json catalog
        tools_catalog = [
            {
                "name": cap.name,
                "handler": cap.handler,
                "description": cap.description,
                "risk": cap.risk.value,
                "timeout_seconds": cap.timeout_seconds,
                "input_schema": cap.input_schema,
                "output_schema": cap.output_schema,
            }
            for cap in manifest.capabilities
        ]
        tools_json_content = canonical_json_dumps(tools_catalog)
        with open(output_dir / "tools.json", "w", encoding="utf-8", newline="\n") as f:
            f.write(tools_json_content)
        rendered_files["tools.json"] = hash_string(tools_json_content)

        # 7. Generate policy.json
        policy_json_content = canonical_json_dumps(manifest.policy.model_dump())
        with open(output_dir / "policy.json", "w", encoding="utf-8", newline="\n") as f:
            f.write(policy_json_content)
        rendered_files["policy.json"] = hash_string(policy_json_content)

        return rendered_files
