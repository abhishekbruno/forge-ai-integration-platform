#!/usr/bin/env python
"""FORGE Bootstrap script for environment verification and setup."""

from __future__ import annotations

import subprocess
import sys


def main():
    print("=" * 60)
    print("FORGE — System Bootstrap & Verification")
    print("=" * 60)

    # Check python version
    if sys.version_info < (3, 12):
        print(f"Error: Python >= 3.12 is required. Found: {sys.version}")
        sys.exit(1)

    print(
        f"Python Runtime: {sys.executable} (v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})"
    )

    # Install in editable mode if needed
    print("Installing FORGE in editable mode...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)

    # Run doctor diagnostics
    print("\nRunning FORGE Doctor diagnostics...")
    result = subprocess.run([sys.executable, "-m", "forge", "doctor"])

    if result.returncode == 0:
        print("\nBootstrap complete! Run 'forge gui' to launch the desktop application.")
    else:
        print("\nBootstrap finished with warnings or issues. Review the doctor report above.")


if __name__ == "__main__":
    main()
