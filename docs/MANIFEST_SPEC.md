# FORGE Manifest Specification (v1.0)

Integration manifests define the contract between an external application, an adapter, and the generated Model Context Protocol (MCP) server.

## Schema Declaration

```yaml
schema_version: "1.0"
integration:
  id: "string (lowercase, alphanumeric with dots/hyphens)"
  name: "Human Readable Integration Name"
  version: "semver string (e.g. 0.1.0)"
  description: "Optional summary"

application:
  id: "application identifier (e.g. blender, fixturelab)"
  display_name: "Display Name"
  supported_versions: "Version constraint (e.g. >=4.0,<6.0)"
  website: "https://example.com"

adapter:
  id: "registered adapter id (e.g. forge.adapters.blender)"
  version: "adapter version"

capabilities:
  - name: "tool_identifier"
    handler: "adapter_handler_id"
    description: "Detailed description of tool action"
    risk: "read | write | destructive | external"
    timeout_seconds: 45
    input_schema:
      type: object
      properties:
        arg_name: { type: string }
      required: [arg_name]
      additionalProperties: false
    output_schema:
      type: object
      properties:
        success: { type: boolean }
      required: [success]

policy:
  default: "deny | allow"
  read_operations: "allow_within_workspace | explicit_approval | deny"
  write_operations: "explicit_approval | deny | allow_within_workspace"
  network_operations: "deny | allow"
```

## Risk Classifications

- `read`: Query-only operations that do not modify state or disk files.
- `write`: Modifying operations that create files, update records, or alter configurations.
- `destructive`: Deleting items or removing data. Always requires explicit approval.
- `external`: Network or remote API communication. Denied by default.
