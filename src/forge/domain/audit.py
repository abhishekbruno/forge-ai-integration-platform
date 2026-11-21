"""Audit event domain model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Tamper-evident audit event recorded in the append-only journal."""

    id: int  # Monotonically increasing database primary key
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str = "system"
    action: str
    target: str
    outcome: str  # "success", "denied", "failed", "pending"
    correlation_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    previous_hash: str
    event_hash: str

    model_config = {"frozen": True}
