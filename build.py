"""
build.py

Convenience script to build the Windows executable locally using
PyInstaller and the project's .spec file. This is the same spec used
by the GitHub Actions workflow, so a local build should match CI.

Usage (Windows, from project root, with dependencies installed):
    python build.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC_FILE = ROOT / "ALMUS_PHONE_LAB.spec"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"


def main() -> int:
    print("=== ALMUS PHONE LAB - Local Build ===")

    for stale_dir in (DIST_DIR, BUILD_DIR):
        if stale_dir.exists():
            print(f"Cleaning {stale_dir} ...")
            shutil.rmtree(stale_dir, ignore_errors=True)

    cmd = [sys.executable, "-m", "PyInstaller", str(SPEC_FILE), "--noconfirm"]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print("Build FAILED.", file=sys.stderr)
        return result.returncode

    output_dir = DIST_DIR / "ALMUS_PHONE_LAB"
    print(f"\nBuild complete. Output directory: {output_dir}")
    print("You can zip this directory to distribute the application.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
