"""Capability and risk classification domain models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Security classification for tool capabilities."""

    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    EXTERNAL = "external"


class CapabilityDefinition(BaseModel):
    """A single safely exposed capability provided by an adapter and declared in a manifest."""

    name: str
    handler: str
    description: str
    risk: RiskLevel = RiskLevel.READ
    timeout_seconds: int = Field(default=45, ge=1, le=600)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
