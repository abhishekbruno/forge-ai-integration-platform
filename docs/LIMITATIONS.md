# FORGE Scope & Known Limitations

## Scope & Design Boundaries

FORGE v1 is an integration development factory with two first-class reference adapters:
1. **FixtureLab**: Deterministic, self-contained reference adapter.
2. **Blender**: Background-mode headless DCC integration.

## Excluded Capabilities
- **Generic Reverse Engineering**: FORGE does not automatically reverse-engineer undocumented binaries.
- **Live GUI Blender Injection**: FORGE does not inject code into an active interactive Blender window session; it operates deterministically via headless background launches.
- **OS-Level Kernel Sandboxing**: Process execution uses strict argument-vector controls and sanitization, but does not provide hardware or hypervisor containerization.
- **Public Cloud Hosting**: Local-first design without mandatory cloud dependencies.
