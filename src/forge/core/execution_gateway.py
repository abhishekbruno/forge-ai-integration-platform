"""Execution gateway enforcing schema validation, security policies, and audit logging."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from forge.adapters.registry import get_adapter_registry
from forge.core.approval_broker import get_approval_broker
from forge.core.policy_engine import PolicyDecision, get_policy_engine
from forge.domain.errors import (
    AdapterExecutionError,
    ApprovalRequiredError,
    PolicyDenialError,
    ValidationSecurityError,
)
from forge.domain.execution import ToolCall, ToolCallOutcome
from forge.domain.manifest import IntegrationManifest
from forge.events.bus import get_event_bus
from forge.events.models import (
    EVENT_TOOL_EXECUTION_FAILED,
    EVENT_TOOL_EXECUTION_REQUESTED,
    EVENT_TOOL_EXECUTION_STARTED,
    EVENT_TOOL_EXECUTION_SUCCEEDED,
    EventSeverity,
    ForgeEvent,
)
from forge.persistence.audit_journal import AuditJournal
from forge.persistence.repositories import ToolCallRepository
from forge.security.hashes import hash_arguments
from forge.security.validation import validate_data_against_schema


class ExecutionGateway:
    """The central security gateway through which ALL tool calls must flow."""

    def __init__(self, db_path: Path | None = None):
        self.policy_engine = get_policy_engine()
        self.approval_broker = get_approval_broker(db_path)
        self.audit_journal = AuditJournal(db_path)
        self.tool_call_repo = ToolCallRepository(db_path)

    def execute_tool(
        self,
        connector_id: str,
        manifest: IntegrationManifest,
        tool_name: str,
        args: dict[str, Any] | None,
        workspace: Path,
        actor: str = "mcp_client",
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute a tool call with strict verification, authorization, and audit trail."""
        if args is None:
            args = {}
        corr_id = correlation_id or str(uuid4())
        workspace = Path(workspace).resolve()
        start_time = time.monotonic()

        # 1. Lookup capability in manifest
        capability = manifest.get_capability(tool_name)
        if not capability:
            err_msg = f"Unknown tool '{tool_name}' for connector '{connector_id}'."
            self._record_denial(corr_id, connector_id, tool_name, args, actor, err_msg)
            raise PolicyDenialError(err_msg)

        # 2. Schema validation of input arguments
        try:
            if capability.input_schema:
                validate_data_against_schema(
                    args, capability.input_schema, context=f"tool '{tool_name}' arguments"
                )
        except ValidationSecurityError as exc:
            self._record_denial(corr_id, connector_id, tool_name, args, actor, str(exc))
            raise PolicyDenialError(f"Input validation failure: {exc}") from exc

        arg_hash = hash_arguments(args)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TOOL_EXECUTION_REQUESTED,
                correlation_id=corr_id,
                details={"tool": tool_name, "connector": connector_id, "arg_hash": arg_hash},
            )
        )

        # 3. Policy evaluation
        decision, reason = self.policy_engine.evaluate(manifest, capability, args, workspace)

        if decision == PolicyDecision.DENY:
            self._record_denial(corr_id, connector_id, tool_name, args, actor, reason)
            raise PolicyDenialError(f"Operation denied by policy: {reason}")

        elif decision == PolicyDecision.REQUIRE_APPROVAL:
            # Check for valid unconsumed approval
            has_approval = self.approval_broker.check_and_consume_grant(tool_name, arg_hash)
            if not has_approval:
                req_id = self.approval_broker.request_approval(
                    tool_name=tool_name,
                    argument_hash=arg_hash,
                    correlation_id=corr_id,
                    details={
                        "args": args,
                        "workspace": str(workspace),
                        "risk": capability.risk.value,
                    },
                    actor=actor,
                )
                self._record_denial(
                    corr_id,
                    connector_id,
                    tool_name,
                    args,
                    actor,
                    f"Approval required (request ID: {req_id})",
                )
                raise ApprovalRequiredError(tool_name, arg_hash, reason)

        # 4. Resolve adapter and invoke handler
        adapter = get_adapter_registry().get_adapter(manifest.adapter.id)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TOOL_EXECUTION_STARTED,
                correlation_id=corr_id,
                details={"tool": tool_name, "handler": capability.handler},
            )
        )

        try:
            raw_result = adapter.invoke_capability(
                handler=capability.handler,
                args=args,
                workspace=workspace,
                context={"correlation_id": corr_id, "actor": actor},
            )
        except Exception as exc:
            duration = time.monotonic() - start_time
            self._record_failure(corr_id, connector_id, tool_name, args, actor, str(exc), duration)
            raise AdapterExecutionError(f"Execution failed in adapter: {exc}") from exc

        # 5. Output schema validation
        try:
            if capability.output_schema:
                validate_data_against_schema(
                    raw_result, capability.output_schema, context=f"tool '{tool_name}' output"
                )
        except ValidationSecurityError as exc:
            duration = time.monotonic() - start_time
            err_msg = f"Output schema contract violation: {exc}"
            self._record_failure(corr_id, connector_id, tool_name, args, actor, err_msg, duration)
            raise AdapterExecutionError(err_msg) from exc

        duration = time.monotonic() - start_time

        # 6. Record success in audit journal and tool call repo
        self.audit_journal.record_event(
            action="tool.execute",
            target=f"{connector_id}:{tool_name}",
            outcome="success",
            correlation_id=corr_id,
            actor=actor,
            details={"arg_hash": arg_hash, "duration": round(duration, 3)},
        )

        tc = ToolCall(
            correlation_id=corr_id,
            connector_id=connector_id,
            tool_name=tool_name,
            argument_hash=arg_hash,
            arguments=args,
            actor=actor,
            outcome=ToolCallOutcome.SUCCESS,
            duration_seconds=round(duration, 3),
            result=raw_result,
        )
        self.tool_call_repo.save(tc)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TOOL_EXECUTION_SUCCEEDED,
                correlation_id=corr_id,
                details={"tool": tool_name, "duration": round(duration, 3)},
            )
        )

        return raw_result

    def _record_denial(
        self,
        corr_id: str,
        connector_id: str,
        tool_name: str,
        args: dict[str, Any],
        actor: str,
        reason: str,
    ) -> None:
        arg_hash = hash_arguments(args)
        self.audit_journal.record_event(
            action="tool.execute",
            target=f"{connector_id}:{tool_name}",
            outcome="denied",
            correlation_id=corr_id,
            actor=actor,
            details={"arg_hash": arg_hash, "reason": reason},
        )
        tc = ToolCall(
            correlation_id=corr_id,
            connector_id=connector_id,
            tool_name=tool_name,
            argument_hash=arg_hash,
            arguments=args,
            actor=actor,
            outcome=ToolCallOutcome.DENIED,
            duration_seconds=0.0,
            error_message=reason,
        )
        self.tool_call_repo.save(tc)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TOOL_EXECUTION_FAILED,
                correlation_id=corr_id,
                severity=EventSeverity.WARNING,
                details={"tool": tool_name, "reason": reason},
            )
        )

    def _record_failure(
        self,
        corr_id: str,
        connector_id: str,
        tool_name: str,
        args: dict[str, Any],
        actor: str,
        error_msg: str,
        duration: float,
    ) -> None:
        arg_hash = hash_arguments(args)
        self.audit_journal.record_event(
            action="tool.execute",
            target=f"{connector_id}:{tool_name}",
            outcome="failed",
            correlation_id=corr_id,
            actor=actor,
            details={"arg_hash": arg_hash, "error": error_msg},
        )
        tc = ToolCall(
            correlation_id=corr_id,
            connector_id=connector_id,
            tool_name=tool_name,
            argument_hash=arg_hash,
            arguments=args,
            actor=actor,
            outcome=ToolCallOutcome.FAILED,
            duration_seconds=round(duration, 3),
            error_message=error_msg,
        )
        self.tool_call_repo.save(tc)

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_TOOL_EXECUTION_FAILED,
                correlation_id=corr_id,
                severity=EventSeverity.ERROR,
                details={"tool": tool_name, "error": error_msg},
            )
        )


_GATEWAY: ExecutionGateway | None = None


def get_execution_gateway(db_path: Path | None = None) -> ExecutionGateway:
    global _GATEWAY
    if db_path is not None:
        return ExecutionGateway(db_path)
    if _GATEWAY is None:
        _GATEWAY = ExecutionGateway()
    return _GATEWAY
