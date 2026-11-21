"""Domain-specific typed exceptions for FORGE."""

from __future__ import annotations


class ForgeError(Exception):
    """Base class for all FORGE domain and service errors."""


class ManifestValidationError(ForgeError):
    """Raised when an integration manifest fails schema or semantic validation."""


class PolicyDenialError(ForgeError):
    """Raised when an action is blocked by security policy."""


class ApprovalRequiredError(ForgeError):
    """Raised when an operation requires human authorization before executing."""

    def __init__(
        self, tool_name: str, argument_hash: str, reason: str = "Explicit approval required"
    ):
        super().__init__(
            f"Approval required for '{tool_name}' (args hash: {argument_hash[:12]}): {reason}"
        )
        self.tool_name = tool_name
        self.argument_hash = argument_hash
        self.reason = reason


class ApprovalExpiredError(ForgeError):
    """Raised when an approval grant has expired or was already consumed."""


class AdapterNotFoundError(ForgeError):
    """Raised when a requested adapter ID is not registered."""


class AdapterExecutionError(ForgeError):
    """Raised when an external application adapter encounters an execution failure."""


class SecurityError(ForgeError):
    """Raised when security boundary rules are violated."""


class ValidationSecurityError(SecurityError):
    """Raised when data structure or schema validation fails."""


class ProjectError(ForgeError):
    """Raised when project operations fail."""
