#!/usr/bin/env python3
"""Stdlib-only self-test for copy/paste deployments.

Runs a quick health check without requiring pytest:
- Compile core modules + tool modules (py_compile).
- Build the tool catalog (AST scan).
- Assert a few canonical built-in tool names exist.
- Execute a minimal run_user_code snippet that sets RESULT.
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from py_compile import PyCompileError, compile as py_compile_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_repo_on_syspath(root: Path) -> None:
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)


def _iter_py_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in ("nexus", "tools"):
        base = root / rel
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            # Keep the selftest strict: compile everything under these roots.
            files.append(p)
    return sorted(set(files))


def _compile_all(py_files: list[Path]) -> None:
    failures: list[tuple[Path, str]] = []
    for p in py_files:
        try:
            py_compile_file(str(p), doraise=True)
        except PyCompileError as exc:
            failures.append((p, str(exc)))
        except Exception as exc:  # pragma: no cover
            failures.append((p, f"{type(exc).__name__}: {exc}"))

    if failures:
        lines = ["py_compile failures:"]
        for path, msg in failures[:20]:
            lines.append(f"  - {path}: {msg}")
        if len(failures) > 20:
            lines.append(f"  ... and {len(failures) - 20} more")
        raise RuntimeError("\n".join(lines))


def _ensure_tools_in_env() -> None:
    # Health-check should validate the built-in `tools/` package even if a user
    # has configured additional packages.
    current = (os.environ.get("NEXUS_TOOL_PACKAGES") or "").strip()
    if not current:
        os.environ["NEXUS_TOOL_PACKAGES"] = "tools"
        return

    names = [n.strip() for n in current.split(",") if n.strip()]
    if "tools" not in names:
        names.append("tools")
        os.environ["NEXUS_TOOL_PACKAGES"] = ",".join(names)


def _build_catalog_and_assert_tools() -> None:
    from nexus.tool_catalog import get_catalog

    catalog = get_catalog(refresh=True)

    expected = {
        "get_issue_status",  # Jira (unnamespaced legacy)
        "sonarr.get_series",
        "n8n.create_workflow",
        "tautulli_get_activity",  # Tautulli (prefixed legacy)
    }
    missing = sorted(name for name in expected if name not in catalog)
    if missing:
        available = ", ".join(sorted(catalog.keys())[:50])
        raise RuntimeError(
            "Tool catalog missing expected tools: "
            + ", ".join(missing)
            + f"\nFirst 50 discovered tools: {available}"
        )


def _runner_smoke() -> None:
    from nexus.runner import run_user_code

    rr = run_user_code(
        """
        x = 40 + 2
        RESULT = x
        """
    )
    if rr.result != 42:
        raise RuntimeError(f"run_user_code returned unexpected RESULT: {rr.result!r}")


def main() -> int:
    try:
        root = _repo_root()
        _ensure_repo_on_syspath(root)
        _ensure_tools_in_env()

        py_files = _iter_py_files(root)
        if not py_files:
            raise RuntimeError("No Python files found under nexus/ and tools/.")

        _compile_all(py_files)
        _build_catalog_and_assert_tools()
        _runner_smoke()
    except Exception as exc:
        print(f"nexus selftest failed: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    print("nexus selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

