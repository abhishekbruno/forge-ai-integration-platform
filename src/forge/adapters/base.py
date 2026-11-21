"""Abstract Base Adapter interface for FORGE integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from forge.domain.capability import CapabilityDefinition


class BaseAdapter(ABC):
    """Contract for application adapters exposing capabilities to FORGE."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique adapter identifier (e.g. 'forge.adapters.fixturelab')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of the adapter."""

    @property
    @abstractmethod
    def supported_app_id(self) -> str:
        """Application ID this adapter binds to (e.g. 'fixturelab', 'blender')."""

    @property
    @abstractmethod
    def supported_versions(self) -> str:
        """Version expression of supported target applications."""

    @abstractmethod
    def detect_application(self, workspace: Path | None = None) -> dict[str, Any]:
        """Detect presence, executable path, version, and operational health of target application."""

    @abstractmethod
    def list_capabilities(self) -> list[CapabilityDefinition]:
        """Enumerate all capabilities safely exposed and handled by this adapter."""

    @abstractmethod
    def invoke_capability(
        self,
        handler: str,
        args: dict[str, Any],
        workspace: Path,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a verified capability handler with validated arguments in the approved workspace."""
