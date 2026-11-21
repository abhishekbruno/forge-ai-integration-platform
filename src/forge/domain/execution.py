"""Tool execution, approvals, and test run domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolCallOutcome(str, Enum):
    SUCCESS = "success"
    DENIED = "denied"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ToolCall(BaseModel):
    """Record of a tool invocation through the policy gateway."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    connector_id: str
    tool_name: str
    argument_hash: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    actor: str = "local_mcp_client"
    outcome: ToolCallOutcome
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float = 0.0
    result: dict[str, Any] | None = None
    error_message: str | None = None


class ApprovalGrant(BaseModel):
    """A cryptographic, exact-argument scoped authorization grant."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    argument_hash: str
    actor: str = "human_operator"
    reason: str = "Approved via FORGE Approval Broker"
    granted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str
    single_use: bool = True
    consumed: bool = False
    details: dict[str, Any] = Field(default_factory=dict)

    def is_valid_for(self, tool_name: str, argument_hash: str) -> bool:
        """Check if grant is unconsumed, matches tool and argument hash, and has not expired."""
        if self.consumed:
            return False
        if self.tool_name != tool_name or self.argument_hash != argument_hash:
            return False

        now = datetime.now(timezone.utc)
        exp = datetime.fromisoformat(self.expires_at)
        return now <= exp


class TestRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TestCaseResult(BaseModel):
    name: str
    status: TestRunStatus
    duration_seconds: float = 0.0
    error_message: str | None = None
    skip_reason: str | None = None


class TestRun(BaseModel):
    """Record of an automated test execution against a build."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    build_id: str
    test_type: str  # unit, contract, fixturelab_e2e, blender_live, security
    command: str
    environment_fingerprint: dict[str, Any] = Field(default_factory=dict)
    status: TestRunStatus = TestRunStatus.QUEUED
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finish_time: str | None = None
    test_cases: list[TestCaseResult] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = Field(default_factory=list)
