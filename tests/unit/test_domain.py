"""Unit tests for domain models."""

from forge.domain.capability import CapabilityDefinition, RiskLevel
from forge.domain.execution import ApprovalGrant


def test_capability_definition():
    cap = CapabilityDefinition(
        name="test_tool",
        handler="app.test_tool",
        description="A test tool",
        risk=RiskLevel.WRITE,
        timeout_seconds=30,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
    )
    assert cap.name == "test_tool"
    assert cap.risk == RiskLevel.WRITE
    assert cap.timeout_seconds == 30


def test_approval_grant_expiry():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    future = (now + timedelta(seconds=60)).isoformat()
    past = (now - timedelta(seconds=60)).isoformat()

    grant_valid = ApprovalGrant(
        tool_name="test_tool",
        argument_hash="abc123hash",
        expires_at=future,
        consumed=False,
    )
    assert grant_valid.is_valid_for("test_tool", "abc123hash") is True
    assert grant_valid.is_valid_for("other_tool", "abc123hash") is False
    assert grant_valid.is_valid_for("test_tool", "different_hash") is False

    grant_expired = ApprovalGrant(
        tool_name="test_tool",
        argument_hash="abc123hash",
        expires_at=past,
        consumed=False,
    )
    assert grant_expired.is_valid_for("test_tool", "abc123hash") is False

    grant_consumed = ApprovalGrant(
        tool_name="test_tool",
        argument_hash="abc123hash",
        expires_at=future,
        consumed=True,
    )
    assert grant_consumed.is_valid_for("test_tool", "abc123hash") is False
