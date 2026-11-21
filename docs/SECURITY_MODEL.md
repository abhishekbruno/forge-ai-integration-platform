# FORGE Security Model & Threat Boundaries

## Threat Model

FORGE is designed for developers building AI integrations locally. The security model addresses the risk of untrusted or hallucinating AI models attempting unauthorized access or data destruction.

## Security Principles

1. **Default Deny**: All capabilities, adapters, and policies fail closed.
2. **Workspace Confinement**: Operations targeting files outside the workspace are blocked. Relative paths containing `..` and external symlinks are rejected.
3. **Copy-on-Write Invariant**: Mutating operations on complex documents (e.g., 3D scene files) operate on temporary copies and emit new destination files.
4. **Exact-Argument Cryptographic Approvals**: Approvals are bound to `SHA-256(canonical_json(arguments))` and expire automatically.
5. **No Shell Invocations**: External binaries run via direct argument vectors.

## Residual Limitations

- A policy layer is not an OS-level sandbox. If a target application binary contains arbitrary code execution vulnerabilities, the operating system kernel must enforce user account limits.
- Local hash chains provide tamper evidence against ordinary edits, not against a local administrator with direct write access to disk and code.
