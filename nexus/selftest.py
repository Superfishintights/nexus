#!/usr/bin/env python3
"""Stdlib-only self-test for copy/paste deployments.

Runs a quick health check without requiring pytest:
- Compile core modules plus any local tool pack modules (py_compile).
- Build the configured tool catalog (AST scan).
- Verify empty-catalog core behavior when no tool packs are configured.
- Execute a minimal run_user_code snippet that sets RESULT.
"""

from __future__ import annotations

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
    for rel in ("nexus", "tool_packs"):
        base = root / rel
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
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


def _build_catalog_and_assert_behavior() -> None:
    from nexus.tool_catalog import (
        get_catalog,
        get_catalog_diagnostics,
        get_tool_package_names,
    )

    catalog = get_catalog(refresh=True)
    diagnostics = get_catalog_diagnostics()
    if diagnostics["warnings"]:
        raise RuntimeError(
            "Catalog warnings detected during selftest: "
            + "; ".join(diagnostics["warnings"])
        )

    configured = tuple(get_tool_package_names())
    if configured and not catalog:
        raise RuntimeError(
            "NEXUS_TOOL_PACKAGES is configured but the tool catalog is empty: "
            + ", ".join(configured)
        )
    if not configured and catalog:
        raise RuntimeError(
            "Core selftest expected an empty catalog with no configured tool packs, "
            f"but discovered: {', '.join(sorted(catalog)[:20])}"
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
    if rr.metadata.get("executionModel") != "subprocess":
        raise RuntimeError(f"run_user_code did not use subprocess execution: {rr.metadata!r}")
    if rr.metadata.get("limits", {}).get("timeoutSeconds", 0) <= 0:
        raise RuntimeError(f"run_user_code returned invalid limits metadata: {rr.metadata!r}")


def main() -> int:
    try:
        root = _repo_root()
        _ensure_repo_on_syspath(root)

        py_files = _iter_py_files(root)
        if not py_files:
            raise RuntimeError("No Python files found under nexus/ or tool_packs/.")

        _compile_all(py_files)
        _build_catalog_and_assert_behavior()
        _runner_smoke()
    except Exception as exc:
        print(f"nexus selftest failed: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    print("nexus selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
