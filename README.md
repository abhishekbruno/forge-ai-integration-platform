# FORGE

> **Build, verify, secure, and package AI integrations.**

[![CI](https://github.com/abhishekbruno/forge-ai-integration-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/abhishekbruno/forge-ai-integration-platform/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MCP v2](https://img.shields.io/badge/MCP-SDK%20v2-green.svg)](https://modelcontextprotocol.io/)

**FORGE** is a local-first, open-source AI integration development desktop platform and integration factory. It accepts a structured description of an application's safely exposed capabilities, generates a standards-compliant Model Context Protocol (MCP) server package, runs automated contract and safety tests, enforces fine-grained human approvals for mutating operations, records tamper-evident audit evidence, and exports ready-to-install connectors.

---

## Key Features

- **Integration Factory**: Generates deterministic, standards-compliant MCP servers using the official Model Context Protocol Python SDK v2.
- **Human-in-the-Loop Approvals**: Zero unapproved mutations. Mutating operations (`write`, `destructive`) require exact-argument, single-use approval grants bound by cryptographic SHA-256 digests.
- **Copy-on-Write 3D Pipeline**: Blender integration runs strictly in headless background mode (`--background --python-exit-code 1`). Scene modifications produce new `.blend` files; input files are verified unchanged before and after execution.
- **FixtureLab Deterministic Reference Suite**: Fully offline, zero-dependency reference adapter for unit, contract, and workflow verification on machines without external DCC software.
- **Tamper-Evident Audit Journal**: Every action, tool call, approval decision, and build is recorded in an append-only SHA-256 hash chain (`forge audit verify`).
- **Desktop UI (PySide6)**: Full-featured desktop application with 11 views: Dashboard, Projects, Manifest Studio, Adapter Library, Tool Explorer, Builds/Generator, Test Lab, Approvals, Audits, Packages, and Settings.
- **Full CLI Parity**: Complete command-line suite (`forge gui`, `forge doctor`, `forge project`, `forge manifest`, `forge generate`, `forge test`, `forge package`, `forge audit`).

---

## Supported Reference Adapters

1. **FixtureLab (`forge.adapters.fixturelab`)**: Deterministic reference application providing `get_status`, `list_items`, `get_item`, `create_item` (write; approval required), `update_item` (optimistic version lock), and `delete_item` (destructive).
2. **Blender (`forge.adapters.blender`)**: Safe background-mode integration providing read operations (`scene_summary`, `list_objects`, `inspect_object`, `list_materials`) and copy-on-write mutating operations (`create_primitive`, `set_transform`, `rename_object`, `save_scene_copy`).

---

## Installation & Setup

### Prerequisites
- Python >= 3.12
- Git
- (Optional) Blender 4.x for live Blender scene workflows

### Quickstart

```bash
# 1. Clone repository
git clone https://github.com/abhishekbruno/forge-ai-integration-platform.git
cd forge-ai-integration-platform

# 2. Create virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install FORGE and development dependencies
pip install -e ".[dev]"

# 4. Verify environment
forge doctor

# 5. Launch Desktop GUI
forge gui
```

---

## Command Line Interface (CLI)

```bash
# Inspect environment and detected binaries
forge doctor

# Validate an integration manifest
forge manifest validate manifests/fixturelab.yaml

# Generate an MCP connector from a manifest
forge generate manifests/fixturelab.yaml --workspace ./my_project

# Test the generated connector (contract tests + e2e)
forge test <build-id> --workspace ./my_project

# Package connector into a standalone distribution archive
forge package <build-id> --workspace ./my_project

# Verify audit trail cryptographic hash integrity
forge audit verify
```

---

## Security Guarantees

1. **Default Deny**: Any operation, handler, or path not explicitly granted by manifest policy and active approvals is blocked.
2. **Copy-on-Write**: Source project files are protected against silent mutation.
3. **No Dynamic Code Injection**: No arbitrary Python strings or unreviewed shell commands are executed from manifests.
4. **Isolated Process Boundaries**: External applications (like Blender) run as child processes via argument vectors (`shell=False`) with JSON parameter files in isolated temporary directories.
5. **Exact Scope Approvals**: Approvals cannot be reused, do not apply to altered arguments, and expire automatically after a configured TTL.

---

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Manifest Specification](docs/MANIFEST_SPEC.md)
- [Adapter SDK](docs/ADAPTER_SDK.md)
- [Security Model & Threat Boundaries](docs/SECURITY_MODEL.md)
- [Testing & Verification Guide](docs/TESTING.md)
- [Packaging & Distribution Guide](docs/PACKAGING.md)
- [Desktop User Guide](docs/USER_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Limitations & Scope](docs/LIMITATIONS.md)

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
