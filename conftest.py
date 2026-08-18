"""Pytest bootstrap for local monorepo tool packs."""
from __future__ import annotations

import sys
from pathlib import Path


TOOL_PACKS_ROOT = Path(__file__).resolve().parent / "tool_packs"

if TOOL_PACKS_ROOT.exists():
    for package_root in sorted(TOOL_PACKS_ROOT.iterdir()):
        if package_root.is_dir() and (package_root / "pyproject.toml").exists():
            package_root_s = str(package_root)
            if package_root_s not in sys.path:
                sys.path.insert(0, package_root_s)
