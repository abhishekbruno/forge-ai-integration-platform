# Custom Adapter SDK Template

This folder provides a complete template for adding new first-class adapters to FORGE
(such as FreeCAD, Godot Engine, Unreal Engine, or external REST services).

## How to Author an Adapter

1. Inherit from `forge.adapters.base.BaseAdapter`.
2. Implement required properties:
   - `id`: Unique namespace string (e.g. `forge.adapters.freecad`).
   - `version`: Semver string.
   - `supported_app_id`: Canonical application name.
   - `supported_versions`: Version constraints.
3. Implement `detect_application(workspace)` to report binary health and location.
4. Implement `list_capabilities()` defining typed JSON Schemas for inputs and outputs.
5. Implement `invoke_capability(handler, args, workspace, context)` executing safe operations.
6. Register the adapter in `forge.adapters.registry.AdapterRegistry`.
