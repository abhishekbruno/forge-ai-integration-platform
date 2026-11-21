# FORGE Architecture Specification

## 1. System Overview

FORGE is a desktop-first integration factory designed to build, verify, secure, and package Model Context Protocol (MCP) integrations for desktop applications and local APIs.

```
+-------------------------------------------------------------------+
| FORGE Desktop UI (PySide6)                                         |
| Dashboard | Projects | Manifest Studio | Tool Explorer | Test Lab  |
| Runs | Approvals | Audit Viewer | Packages | Settings             |
+-------------------------------+-----------------------------------+
                                |
                        typed application services
                                |
+-------------------------------v-----------------------------------+
| FORGE Core                                                        |
| Project Service | Manifest Validation | Capability Registry        |
| Generator | Build Manager | Policy Engine | Approval Broker        |
| Runtime Supervisor | Test Orchestrator | Package Exporter          |
| Audit Journal | Artifact Store | Dependency Doctor               |
+-------------+--------------------------+--------------------------+
              |                          |
      +-------v-----------+      +-------v--------------------+
      | Local persistence |      | Generated MCP connector    |
      | SQLite (WAL)      |      | MCPServer v2 + tool router  |
      +-------------------+      +-------------+--------------+
                                               |
                                       policy enforcement
                                               |
                             +-----------------v---------------+
                             | Adapter SDK / verified handlers |
                             +--------------+------------------+
                                            |
                    +-----------------------+------------------+
                    |                                          |
          +---------v---------+                      +---------v--------+
          | Blender adapter   |                      | FixtureLab       |
          | safe subprocess   |                      | deterministic    |
          | bpy IN Blender    |                      | test application |
          +-------------------+                      +------------------+
```

## 2. Core Subsystems

### 2.1 Manifest Validation (`forge.core.manifest_service`)
- Validates YAML/JSON manifests against `forge_manifest_v1.schema.json` (Draft 2020-12).
- Validates Pydantic domain models.
- Resolves target adapters from `forge.adapters.registry.AdapterRegistry`.
- Verifies that every capability handler exists in the target adapter.
- Validates embedded `input_schema` and `output_schema` definitions.

### 2.2 Execution Gateway (`forge.core.execution_gateway`)
- The mandatory gatekeeper for ALL tool invocations.
- Enforces JSON Schema validation on input arguments.
- Computes canonical SHA-256 argument digests (`hash_arguments`).
- Evaluates access policy via `forge.core.policy_engine.PolicyEngine`.
- Checks and consumes single-use approval grants via `forge.core.approval_broker.ApprovalBroker`.
- Invokes adapter handlers inside the designated workspace.
- Validates result against output schema.
- Records every outcome to the append-only audit journal.

### 2.3 Deterministic Connector Generator (`forge.core.generator`)
- Renders Jinja2 templates into runnable MCP connector packages.
- Targets official MCP Python SDK v2 (`mcp.server.MCPServer`).
- Generates `server.py`, `launcher.py`, `pyproject.toml`, `README.md`, `client_config.json`, `tools.json`, and `policy.json`.
- Computes manifest hash and source bundle hash.

### 2.4 Cryptographic Audit Journal (`forge.persistence.audit_journal`)
- SQLite table `audit_events` with monotonically increasing ID.
- Hash chaining: `event_hash = SHA-256(previous_hash + ":" + canonical_json(event_payload))`.
- Genesis hash: 64 zeros.
- `verify_integrity()` verifies every link in the chain.

### 2.5 Adapter Layer
- **FixtureLab**: Embedded reference adapter with atomic state persistence (`.fixturelab_state.json`).
- **Blender**: Background subprocess runner (`blender_runner.py`) with IPC JSON files. Enforces copy-on-write by asserting input `.blend` SHA-256 before and after execution.
