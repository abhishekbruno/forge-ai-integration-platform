"""Structured event model for real-time observability across services, CLI, and GUI."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ForgeEvent(BaseModel):
    """Immutable structured application event."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str | None = None
    severity: EventSeverity = EventSeverity.INFO
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


# Common Event Names
EVENT_PROJECT_OPENED = "project.opened"
EVENT_PROJECT_CREATED = "project.created"

EVENT_MANIFEST_VALIDATION_STARTED = "manifest.validation_started"
EVENT_MANIFEST_VALIDATION_SUCCEEDED = "manifest.validation_succeeded"
EVENT_MANIFEST_VALIDATION_FAILED = "manifest.validation_failed"

EVENT_CONNECTOR_GENERATION_STARTED = "connector.generation_started"
EVENT_CONNECTOR_GENERATION_FINISHED = "connector.generation_finished"

EVENT_TOOL_EXECUTION_REQUESTED = "tool.execution_requested"
EVENT_TOOL_APPROVAL_PENDING = "tool.approval_pending"
EVENT_TOOL_APPROVAL_GRANTED = "tool.approval_granted"
EVENT_TOOL_APPROVAL_DENIED = "tool.approval_denied"
EVENT_TOOL_EXECUTION_STARTED = "tool.execution_started"
EVENT_TOOL_EXECUTION_SUCCEEDED = "tool.execution_succeeded"
EVENT_TOOL_EXECUTION_FAILED = "tool.execution_failed"

EVENT_TEST_RUN_STARTED = "test.run_started"
EVENT_TEST_CASE_FINISHED = "test.case_finished"
EVENT_TEST_RUN_FINISHED = "test.run_finished"

EVENT_PACKAGE_EXPORTED = "package.exported"
