"""Integration manifest and policy specification models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from forge.domain.capability import CapabilityDefinition


class PolicySettings(BaseModel):
    """Security policy rules for an integration."""

    default: str = Field(default="deny", pattern="^(deny|allow)$")
    read_operations: str = Field(
        default="allow_within_workspace",
        pattern="^(allow_within_workspace|explicit_approval|deny)$",
    )
    write_operations: str = Field(
        default="explicit_approval",
        pattern="^(explicit_approval|deny|allow_within_workspace)$",
    )
    network_operations: str = Field(default="deny", pattern="^(deny|allow)$")


class IntegrationInfo(BaseModel):
    """Metadata identifying the integration."""

    id: str
    name: str
    version: str
    description: str | None = None


class ManifestApplication(BaseModel):
    id: str
    display_name: str
    supported_versions: str
    website: str | None = None


class ManifestAdapter(BaseModel):
    id: str
    version: str


class IntegrationManifest(BaseModel):
    """Complete validated integration manifest."""

    schema_version: str = "1.0"
    integration: IntegrationInfo
    application: ManifestApplication
    adapter: ManifestAdapter
    capabilities: list[CapabilityDefinition]
    policy: PolicySettings = Field(default_factory=PolicySettings)

    def get_capability(self, name: str) -> CapabilityDefinition | None:
        """Find capability by name."""
        for cap in self.capabilities:
            if cap.name == name:
                return cap
        return None
