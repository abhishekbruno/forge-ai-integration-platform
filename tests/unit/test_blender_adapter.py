"""Unit tests for Blender adapter logic and validation."""

import pytest

from forge.adapters.blender import BlenderAdapter
from forge.domain.errors import AdapterExecutionError


def test_blender_adapter_metadata():
    adapter = BlenderAdapter()
    assert adapter.id == "forge.adapters.blender"
    assert adapter.supported_app_id == "blender"
    caps = adapter.list_capabilities()
    assert len(caps) == 8


def test_blender_adapter_missing_blend_file(temp_workspace):
    adapter = BlenderAdapter()
    with pytest.raises(AdapterExecutionError):
        adapter.invoke_capability(
            "blender.scene_summary",
            {"blend_file": "nonexistent.blend"},
            temp_workspace,
        )


def test_blender_adapter_cow_violation_rejection(temp_workspace):
    adapter = BlenderAdapter()
    scene_file = temp_workspace / "scene.blend"
    scene_file.write_text("dummy blend content", encoding="utf-8")

    # Trying to overwrite input file with output file
    with pytest.raises(AdapterExecutionError):
        adapter.invoke_capability(
            "blender.create_primitive",
            {
                "blend_file": "scene.blend",
                "output_file": "scene.blend",
                "primitive_type": "cube",
                "name": "Box",
            },
            temp_workspace,
        )
