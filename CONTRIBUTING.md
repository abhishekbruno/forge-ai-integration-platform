# Contributing to FORGE

Thank you for contributing to FORGE!

## Development Setup

1. **Prerequisites**:
   - Python >= 3.12
   - Git

2. **Clone and Install**:
   ```bash
   git clone https://github.com/abhishekbruno/forge-ai-integration-platform.git
   cd forge-ai-integration-platform
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate

   pip install -e ".[dev]"
   ```

3. **Verify Installation**:
   ```bash
   forge doctor
   pytest
   ```

## Coding Guidelines

- Format and lint code with `ruff check .` and `ruff format --check .`.
- Strict typing with Pydantic v2 domain models.
- No Qt imports inside core, domain, persistence, or adapter modules.
- No direct `bpy` imports in the host Python environment; Blender interactions must happen exclusively inside `blender_runner.py` launched by Blender's interpreter.
- Maintain test coverage for any new capability or security gate.

## Submitting Pull Requests

1. Create a feature branch: `git checkout -b feature/my-feature`.
2. Ensure all tests pass: `pytest`.
3. Verify doctor diagnostics: `forge doctor`.
4. Commit with descriptive messages.
5. Submit a pull request against `main`.
