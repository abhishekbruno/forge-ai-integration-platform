#!/usr/bin/env python
"""Release packaging script building source distribution and wheel."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main():
    print("Building FORGE release distributions (wheel and sdist)...")
    result = subprocess.run([sys.executable, "-m", "build"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Build output:")
        print(result.stdout)
        dist_dir = Path("dist")
        if dist_dir.is_dir():
            print("\nGenerated distribution artifacts:")
            for item in dist_dir.iterdir():
                print(f" - {item.name} ({item.stat().st_size} bytes)")
    else:
        print(f"Build failed:\n{result.stderr}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
