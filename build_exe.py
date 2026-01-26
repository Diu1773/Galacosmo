#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _format_elapsed(seconds: float) -> str:
    total = int(round(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build GalaCosmo with PyInstaller.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean PyInstaller cache and remove temporary files before build.",
    )
    parser.add_argument(
        "--noconfirm",
        action="store_true",
        help="Replace output directory without asking.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    spec_path = repo_root / "GalaCosmo.spec"
    if not spec_path.exists():
        print(f"Spec file not found: {spec_path}", file=sys.stderr)
        return 1

    pyinstaller = shutil.which("pyinstaller")
    if not pyinstaller:
        print("PyInstaller not found. Install it with:", file=sys.stderr)
        print("  pip install pyinstaller", file=sys.stderr)
        return 1

    cmd = [pyinstaller, str(spec_path)]
    if args.clean:
        cmd.append("--clean")
    if args.noconfirm:
        cmd.append("--noconfirm")

    print("Starting build...")
    start = time.perf_counter()
    try:
        result = subprocess.run(cmd, cwd=repo_root)
    except KeyboardInterrupt:
        print("\nBuild cancelled.")
        return 1
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print(f"Build failed after {_format_elapsed(elapsed)}.")
        return result.returncode

    out_dir = repo_root / "dist" / "GalaCosmo"
    print(f"Build finished in {_format_elapsed(elapsed)}.")
    print(f"Output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
