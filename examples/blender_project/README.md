# Blender 3D Scene Project

This example project integrates Blender with FORGE.

## Requirements
- Blender 4.x installed on your computer.
- Set `FORGE_BLENDER_PATH` if Blender is not in your system `PATH`.

## Copy-on-Write Invariant
When calling `blender_create_primitive`, FORGE guarantees:
- `blend_file` (input) is NEVER modified. Its SHA-256 is checked before and after.
- A NEW file specified by `output_file` is created inside the workspace.
