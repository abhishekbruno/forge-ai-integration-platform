"""Policy engine evaluating tool invocation requests against security rules."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from forge.domain.capability import CapabilityDefinition, RiskLevel
from forge.domain.manifest import IntegrationManifest
from forge.security.paths import ensure_within_workspace


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


class PolicyEngine:
    """Enforces default-deny access control and workspace boundary policies."""

    def evaluate(
        self,
        manifest: IntegrationManifest,
        capability: CapabilityDefinition,
        args: dict[str, Any],
        workspace: Path,
    ) -> tuple[PolicyDecision, str]:
        """Evaluate a capability execution against manifest policy rules."""
        # 1. Check workspace confinement for any path-like argument values
        for arg_name, arg_val in args.items():
            if isinstance(arg_val, str) and (
                "/" in arg_val or "\\" in arg_val or arg_name.endswith(("_path", "_file"))
            ):
                try:
                    # Allow nonexistent if it looks like an output target
                    is_output = "output" in arg_name or "target" in arg_name or "dest" in arg_name
                    ensure_within_workspace(arg_val, workspace, allow_nonexistent=is_output)
                except Exception as exc:
                    return (
                        PolicyDecision.DENY,
                        f"Path argument '{arg_name}' violates workspace confinement: {exc}",
                    )

        # 2. Risk classification checks
        policy = manifest.policy

        if capability.risk == RiskLevel.READ:
            rule = policy.read_operations
            if rule == "allow_within_workspace":
                return PolicyDecision.ALLOW, "Read operation permitted within workspace."
            elif rule == "explicit_approval":
                return (
                    PolicyDecision.REQUIRE_APPROVAL,
                    "Read operation requires explicit approval by policy.",
                )
            else:
                return PolicyDecision.DENY, "Read operations are denied by policy."

        elif capability.risk == RiskLevel.WRITE:
            rule = policy.write_operations
            if rule == "explicit_approval":
                return PolicyDecision.REQUIRE_APPROVAL, "Write operation requires human approval."
            elif rule == "allow_within_workspace":
                return PolicyDecision.ALLOW, "Write operation permitted within workspace."
            else:
                return PolicyDecision.DENY, "Write operations are denied by policy."

        elif capability.risk == RiskLevel.DESTRUCTIVE:
            # Destructive always requires explicit approval, regardless of write policy
            return (
                PolicyDecision.REQUIRE_APPROVAL,
                "Destructive operation requires explicit human approval.",
            )

        elif capability.risk == RiskLevel.EXTERNAL:
            if policy.network_operations == "allow":
                return (
                    PolicyDecision.REQUIRE_APPROVAL,
                    "External network operation requires explicit approval.",
                )
            return PolicyDecision.DENY, "External network operations are denied by policy."

        return PolicyDecision.DENY, "Default deny: unrecognized capability risk level."


_POLICY_ENGINE = PolicyEngine()


def get_policy_engine() -> PolicyEngine:
    return _POLICY_ENGINE
