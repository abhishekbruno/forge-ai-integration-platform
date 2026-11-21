"""Approval broker managing human authorization grants for mutating operations."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from forge.domain.execution import ApprovalGrant
from forge.events.bus import get_event_bus
from forge.events.models import (
    EVENT_TOOL_APPROVAL_DENIED,
    EVENT_TOOL_APPROVAL_GRANTED,
    EVENT_TOOL_APPROVAL_PENDING,
    ForgeEvent,
)
from forge.persistence.repositories import ApprovalRepository


class ApprovalBroker:
    """Manages pending approval requests and validates cryptographic grants."""

    def __init__(self, db_path: Path | None = None):
        self.repo = ApprovalRepository(db_path)
        self._lock = threading.Lock()
        self._pending_requests: dict[str, dict[str, Any]] = {}

    def request_approval(
        self,
        tool_name: str,
        argument_hash: str,
        correlation_id: str,
        details: dict[str, Any],
        actor: str = "local_mcp_client",
    ) -> str:
        """Register a pending approval request."""
        request_id = str(uuid4())
        record = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "tool_name": tool_name,
            "argument_hash": argument_hash,
            "actor": actor,
            "details": details,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            self._pending_requests[request_id] = record

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TOOL_APPROVAL_PENDING,
                correlation_id=correlation_id,
                details=record,
            )
        )
        return request_id

    def list_pending_requests(self) -> list[dict[str, Any]]:
        """Return all active pending approval requests."""
        with self._lock:
            return list(self._pending_requests.values())

    def grant_approval(
        self,
        tool_name: str,
        argument_hash: str,
        correlation_id: str,
        ttl_seconds: int = 300,
        actor: str = "human_operator",
        reason: str = "Approved via FORGE",
        details: dict[str, Any] | None = None,
    ) -> ApprovalGrant:
        """Issue an exact-argument, single-use approval grant."""
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()

        grant = ApprovalGrant(
            correlation_id=correlation_id,
            tool_name=tool_name,
            argument_hash=argument_hash,
            actor=actor,
            reason=reason,
            granted_at=now.isoformat(),
            expires_at=expires_at,
            single_use=True,
            consumed=False,
            details=details or {},
        )

        self.repo.save(grant)

        # Clear any matching pending request
        with self._lock:
            matching = [
                req_id
                for req_id, req in self._pending_requests.items()
                if req["tool_name"] == tool_name and req["argument_hash"] == argument_hash
            ]
            for req_id in matching:
                del self._pending_requests[req_id]

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TOOL_APPROVAL_GRANTED,
                correlation_id=correlation_id,
                details=grant.model_dump(),
            )
        )
        return grant

    def deny_request(self, request_id: str, reason: str = "Denied by user") -> bool:
        """Explicitly deny and remove a pending approval request."""
        with self._lock:
            req = self._pending_requests.pop(request_id, None)

        if req:
            get_event_bus().publish(
                ForgeEvent(
                    name=EVENT_TOOL_APPROVAL_DENIED,
                    correlation_id=req["correlation_id"],
                    details={"request_id": request_id, "reason": reason},
                )
            )
            return True
        return False

    def check_and_consume_grant(self, tool_name: str, argument_hash: str) -> bool:
        """Verify if an unconsumed, unexpired approval exists for this exact tool and arguments.

        If found, marks it consumed immediately (single-use) and returns True.
        """
        with self._lock:
            grant = self.repo.find_valid_grant(tool_name, argument_hash)
            if not grant:
                return False

            # Mark as consumed immediately
            self.repo.mark_consumed(grant.id)
            return True


_APPROVAL_BROKER: ApprovalBroker | None = None


def get_approval_broker(db_path: Path | None = None) -> ApprovalBroker:
    global _APPROVAL_BROKER
    if db_path is not None:
        return ApprovalBroker(db_path)
    if _APPROVAL_BROKER is None:
        _APPROVAL_BROKER = ApprovalBroker()
    return _APPROVAL_BROKER
