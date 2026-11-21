# FORGE Troubleshooting

## Common Issues & Resolutions

### 1. Blender Not Detected (`WARN`)
- **Symptom**: `forge doctor` reports Blender binary missing.
- **Resolution**: Open **Settings** in the GUI and specify the path to `blender.exe` (or set `FORGE_BLENDER_PATH` in `.env`).

### 2. Approval Required Error
- **Symptom**: Tool call fails with `ApprovalRequiredError`.
- **Cause**: The tool is classified as `write` or `destructive` and requires human approval.
- **Resolution**: Approve the request in the GUI **Approvals** view or issue a grant via the CLI.

### 3. Path Traversal Blocked
- **Symptom**: `PathSecurityError: Access denied: Path resolves outside workspace`.
- **Cause**: An argument specified a path containing `..` or pointing outside the workspace.
- **Resolution**: Ensure all file paths are relative to or inside the approved workspace.
