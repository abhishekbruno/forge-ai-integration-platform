"""Unit tests for policy engine decisions."""

from forge.core.policy_engine import PolicyDecision, PolicyEngine
from forge.domain.capability import CapabilityDefinition, RiskLevel
from forge.domain.manifest import (
    IntegrationInfo,
    IntegrationManifest,
    ManifestAdapter,
    ManifestApplication,
    PolicySettings,
)


def test_policy_read_allow(temp_workspace):
    engine = PolicyEngine()
    manifest = IntegrationManifest(
        schema_version="1.0",
        integration=IntegrationInfo(id="test.i", name="Test", version="0.1.0"),
        application=ManifestApplication(id="app", display_name="App", supported_versions=">=1.0"),
        adapter=ManifestAdapter(id="ad", version="0.1.0"),
        capabilities=[],
        policy=PolicySettings(read_operations="allow_within_workspace"),
    )
    cap = CapabilityDefinition(
        name="read_tool",
        handler="h",
        description="d",
        risk=RiskLevel.READ,
        input_schema={},
        output_schema={},
    )
    decision, _ = engine.evaluate(manifest, cap, {}, temp_workspace)
    assert decision == PolicyDecision.ALLOW


def test_policy_write_requires_approval(temp_workspace):
    engine = PolicyEngine()
    manifest = IntegrationManifest(
        schema_version="1.0",
        integration=IntegrationInfo(id="test.i", name="Test", version="0.1.0"),
        application=ManifestApplication(id="app", display_name="App", supported_versions=">=1.0"),
        adapter=ManifestAdapter(id="ad", version="0.1.0"),
        capabilities=[],
        policy=PolicySettings(write_operations="explicit_approval"),
    )
    cap = CapabilityDefinition(
        name="write_tool",
        handler="h",
        description="d",
        risk=RiskLevel.WRITE,
        input_schema={},
        output_schema={},
    )
    decision, _ = engine.evaluate(manifest, cap, {}, temp_workspace)
    assert decision == PolicyDecision.REQUIRE_APPROVAL


def test_policy_path_traversal_denial(temp_workspace):
    engine = PolicyEngine()
    manifest = IntegrationManifest(
        schema_version="1.0",
        integration=IntegrationInfo(id="test.i", name="Test", version="0.1.0"),
        application=ManifestApplication(id="app", display_name="App", supported_versions=">=1.0"),
        adapter=ManifestAdapter(id="ad", version="0.1.0"),
        capabilities=[],
    )
    cap = CapabilityDefinition(
        name="read_tool",
        handler="h",
        description="d",
        risk=RiskLevel.READ,
        input_schema={},
        output_schema={},
    )
    decision, reason = engine.evaluate(
        manifest, cap, {"file_path": "../escape.txt"}, temp_workspace
    )
    assert decision == PolicyDecision.DENY
    assert "workspace confinement" in reason
