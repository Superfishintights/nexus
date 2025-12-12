"""Core entrypoint for executing model-authored Python snippets."""
from __future__ import annotations

import builtins
import contextlib
import io
import sys
import textwrap
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

from . import config
from .tool_catalog import get_catalog, spec_to_dict
from .tool_registry import ToolInfo, ensure_tool_loaded, is_tool_loaded


@dataclass(frozen=True)
class RunnerResult:
    """Structured response after executing a code snippet."""

    result: Any
    logs: str
    globals: Dict[str, Any]


class RunnerExecutionError(RuntimeError):
    """Raised when user code fails."""


SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "zip": zip,
    "print": print,
    "__import__": builtins.__import__,
}


def build_execution_globals(
    *,
    additional_globals: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct the globals dictionary used for `exec`.

    The resulting namespace exposes:
    * A curated set of Python builtins.
    * The `RESULT` placeholder which user code must assign.
    * The lazy tool catalog via the `TOOLS` global.
    * `load_tool(name)` helper for lazy imports.
    * Read-only configuration (e.g., Jira settings), if configured.
    """

    catalog = get_catalog()

    def load_tool(name: str) -> Callable[..., object]:
        return ensure_tool_loaded(name).function

    ns: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "RESULT": None,
        "RUNNER_SETTINGS": config.RunnerSettings.from_env(),
        "TOOLS": {
            spec.name: spec_to_dict(
                spec, detail_level="summary", loaded=is_tool_loaded(spec.name)
            )
            for spec in catalog.values()
        },
        "load_tool": load_tool,
    }

    if additional_globals:
        ns.update(additional_globals)

    return ns


def run_user_code(
    code: str,
    *,
    globals_override: Optional[Mapping[str, Any]] = None,
) -> RunnerResult:
    """Execute Python *code* and return the structured result.

    Parameters
    ----------
    code:
        The Python source code authored by the model or user.
    globals_override:
        Optional mapping merged into the execution globals, useful for testing.
    """

    prepared_code = textwrap.dedent(code)
    exec_globals = build_execution_globals(additional_globals=globals_override)
    stdout_buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(prepared_code, exec_globals, exec_globals)  # noqa: S102
    except Exception as exc:
        raise RunnerExecutionError(str(exc)) from exc

    result_value = exec_globals.get("RESULT")
    if isinstance(result_value, ToolInfo):
        result_value = result_value.function

    return RunnerResult(
        result=result_value,
        logs=stdout_buffer.getvalue(),
        globals={k: v for k, v in exec_globals.items() if not k.startswith("__")},
    )


__all__ = ["RunnerResult", "RunnerExecutionError", "run_user_code", "build_execution_globals"]
