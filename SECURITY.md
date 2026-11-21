# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

The FORGE project takes security seriously. If you discover a vulnerability, please do NOT file a public issue.

Instead, please report security issues via email to:
`security@forge-platform.local` or through private GitHub vulnerability reporting.

Please include:
1. Description of the vulnerability and attack vector.
2. Steps to reproduce the issue (proof of concept manifest or CLI command).
3. The affected component (e.g., path canonicalization, approval broker, subprocess runner).
4. Potential impact.

We will acknowledge receipt within 48 hours and provide updates until resolution.

## Security Architecture & Design Guarantees

FORGE enforces the following design principles:
1. **Default Deny**: All operations not explicitly permitted by manifest policy and active approvals are blocked.
2. **Copy-on-Write**: Modifying application tools (such as 3D scenes) operate on safe copies and write new destination files; original inputs are preserved.
3. **No Shell Execution**: All external binaries (such as Blender) are launched via argument vectors (`shell=False`) with sanitized environments and hard timeouts.
4. **Exact Scope Approvals**: Approvals for mutating operations are bound to the SHA-256 hash of the exact validated arguments and single-use.
5. **Tamper-Evident Audit Journal**: Every security-relevant event is recorded in an append-only hash chain. Note: this provides local tamper evidence against accidental or ordinary modification; it does not replace kernel-level audit logging against a root/admin compromised host.
