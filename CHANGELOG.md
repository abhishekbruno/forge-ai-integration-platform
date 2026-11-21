# Changelog

All notable changes to the FORGE platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-21

### Added
- **Core Integration Engine**:
  - Deterministic manifest validation against `forge_manifest_v1.schema.json`.
  - Integration specification compilation and capability resolution.
  - Template-based generator producing standards-compliant MCP server packages (MCP Python SDK v2).
  - Copy-on-write execution gateway enforcing security classifications (`read`, `write`, `destructive`, `external`).
- **Security & Approvals**:
  - Default-deny policy engine with workspace boundary confinement and path traversal prevention.
  - Exact-argument cryptographic approval broker with expiry countdown and single-use consumption.
  - Subprocess execution wrapper with argument-vector invocation, strict timeout handling, and environment sanitization.
  - Cryptographic audit journal with SHA-256 hash chaining and tamper verification (`forge audit verify`).
- **Reference Adapters**:
  - **FixtureLab**: Deterministic, self-contained reference application for offline testing of read, write, and destructive tools.
  - **Blender**: Safe background-mode integration using trusted runner scripts (`blender_runner.py`), JSON parameter exchange, bounded scene introspection, and copy-on-write `.blend` preservation.
- **Desktop Application (PySide6)**:
  - 10 distinct functional views: Dashboard, Projects, Manifest Studio, Adapter Library, Tool Explorer, Test Lab, Runs, Approvals, Audit Viewer, Packages, Settings.
  - Asynchronous background workers for non-blocking UI execution.
  - Code/YAML editor, JSON tree inspector, diff viewer, and execution log widgets.
- **CLI Suite**:
  - Full parity CLI with `forge gui`, `forge doctor`, `forge project`, `forge manifest`, `forge adapter`, `forge generate`, `forge build`, `forge inspect`, `forge test`, `forge serve`, `forge package`, `forge audit`, `forge approvals`.
- **Packaging & Testing**:
  - Standalone connector archive export with manifest, entrypoint, client configuration, and README.
  - Comprehensive test suite covering domain logic, generator determinism, MCP protocol contract (via real stdio client), security boundaries, and UI smoke tests.
