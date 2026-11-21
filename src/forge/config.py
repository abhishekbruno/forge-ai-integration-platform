"""Configuration management for FORGE with prioritized fallback."""

from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_dir

DEFAULT_DATA_DIR = Path(user_data_dir("forge", "forge"))


class ForgeConfig:
    """System-wide configuration settings."""

    def __init__(
        self,
        data_dir: Path | None = None,
        blender_executable: Path | None = None,
        log_level: str = "INFO",
        theme: str = "dark",
        default_timeout: float = 45.0,
    ):
        self.data_dir = data_dir or self._resolve_data_dir()
        self.blender_executable = blender_executable or self._resolve_blender()
        self.log_level = os.environ.get("FORGE_LOG_LEVEL", log_level).upper()
        self.theme = os.environ.get("FORGE_UI_THEME", theme).lower()
        self.default_timeout = float(os.environ.get("FORGE_DEFAULT_TIMEOUT", default_timeout))

        # Ensure base data dir exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "forge.db"

    @classmethod
    def _resolve_data_dir(cls) -> Path:
        env_val = os.environ.get("FORGE_DATA_DIR")
        if env_val:
            return Path(env_val).resolve()
        return DEFAULT_DATA_DIR

    @classmethod
    def _resolve_blender(cls) -> Path | None:
        # Check environment variable
        env_path = os.environ.get("FORGE_BLENDER_PATH")
        if env_path and Path(env_path).is_file():
            return Path(env_path).resolve()

        # Check PATH
        import shutil

        which_path = shutil.which("blender")
        if which_path:
            return Path(which_path).resolve()

        # Check standard Windows paths
        standard_windows_paths = [
            Path("C:/Program Files/Blender Foundation/Blender 4.3/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.2/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.1/blender.exe"),
            Path("C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"),
        ]
        for p in standard_windows_paths:
            if p.is_file():
                return p.resolve()

        return None


# Global config instance
_CONFIG = ForgeConfig()


def get_config() -> ForgeConfig:
    return _CONFIG
