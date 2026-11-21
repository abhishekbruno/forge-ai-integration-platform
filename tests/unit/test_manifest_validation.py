"""Unit tests for manifest validation service."""

from pathlib import Path

from forge.core.manifest_service import ManifestService


def test_validate_valid_fixturelab_manifest():
    svc = ManifestService()
    manifest_file = Path("manifests/fixturelab.yaml").resolve()
    manifest = svc.load_and_validate(manifest_file)
    assert manifest.integration.id == "forge.fixturelab"
    assert len(manifest.capabilities) == 6


def test_validate_valid_blender_manifest():
    svc = ManifestService()
    manifest_file = Path("manifests/blender.yaml").resolve()
    manifest = svc.load_and_validate(manifest_file)
    assert manifest.integration.id == "forge.blender.scene"
    assert len(manifest.capabilities) == 8


def test_reject_duplicate_capability_names(temp_workspace):
    svc = ManifestService()
    invalid_data = {
        "schema_version": "1.0",
        "integration": {"id": "test.dup", "name": "Dup Test", "version": "0.1.0"},
        "application": {
            "id": "fixturelab",
            "display_name": "FixtureLab",
            "supported_versions": ">=1.0.0",
        },
        "adapter": {"id": "forge.adapters.fixturelab", "version": "0.1.0"},
        "capabilities": [
            {
                "name": "same_name",
                "handler": "fixturelab.get_status",
                "description": "desc 1",
                "risk": "read",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            },
            {
                "name": "same_name",
                "handler": "fixturelab.list_items",
                "description": "desc 2",
                "risk": "read",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            },
        ],
        "policy": {
            "default": "deny",
            "read_operations": "allow_within_workspace",
            "write_operations": "explicit_approval",
            "network_operations": "deny",
        },
    }
    is_valid, errors, manifest = svc.validate_manifest_data(invalid_data)
    assert not is_valid
    assert any("Duplicate capability name" in e for e in errors)


def test_reject_unknown_adapter_handler():
    svc = ManifestService()
    invalid_data = {
        "schema_version": "1.0",
        "integration": {"id": "test.badhandler", "name": "Bad Handler", "version": "0.1.0"},
        "application": {
            "id": "fixturelab",
            "display_name": "FixtureLab",
            "supported_versions": ">=1.0.0",
        },
        "adapter": {"id": "forge.adapters.fixturelab", "version": "0.1.0"},
        "capabilities": [
            {
                "name": "bad_tool",
                "handler": "nonexistent.handler.id",
                "description": "tool with bogus handler",
                "risk": "read",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
        ],
        "policy": {
            "default": "deny",
            "read_operations": "allow_within_workspace",
            "write_operations": "explicit_approval",
            "network_operations": "deny",
        },
    }
    is_valid, errors, manifest = svc.validate_manifest_data(invalid_data)
    assert not is_valid
    assert any("not provided by adapter" in e for e in errors)
