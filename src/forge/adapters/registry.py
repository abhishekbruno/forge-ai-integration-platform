"""Adapter registry holding registered, allowlisted application adapters."""

from __future__ import annotations

from forge.adapters.base import BaseAdapter
from forge.adapters.blender import BlenderAdapter
from forge.adapters.fixturelab import FixtureLabAdapter
from forge.domain.errors import AdapterNotFoundError


class AdapterRegistry:
    """Manages verified application adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, BaseAdapter] = {}
        # Register standard built-in adapters
        self.register(FixtureLabAdapter())
        self.register(BlenderAdapter())

    def register(self, adapter: BaseAdapter) -> None:
        """Register an adapter instance."""
        self._adapters[adapter.id] = adapter

    def get_adapter(self, adapter_id: str) -> BaseAdapter:
        """Retrieve an adapter by id or raise AdapterNotFoundError."""
        if adapter_id not in self._adapters:
            raise AdapterNotFoundError(
                f"Adapter '{adapter_id}' is not registered. Available: {list(self._adapters.keys())}"
            )
        return self._adapters[adapter_id]

    def list_adapters(self) -> list[BaseAdapter]:
        """List all registered adapters."""
        return list(self._adapters.values())


# Global singleton registry
_REGISTRY = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    return _REGISTRY
