"""Application and adapter metadata models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ApplicationDefinition(BaseModel):
    """Metadata describing an integrated target application."""

    id: str
    display_name: str
    supported_versions: str
    website: str | None = None
    api_description: str | None = None


class AdapterDefinition(BaseModel):
    """Metadata describing an adapter implementing interaction with an application."""

    id: str
    version: str
    supported_app_id: str
    supported_versions: str
    discovery_method: str = "local_process"
    capabilities: list[str] = Field(default_factory=list)
