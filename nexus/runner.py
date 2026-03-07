"""Core entrypoint for executing model-authored Python snippets."""
from __future__ import annotations

import builtins
import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import textwrap
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from . import config
from .lazy_tools import LazyTools
from .tool_catalog import get_catalog
from .tool_registry import ToolInfo, ensure_tool_loaded


@dataclass(frozen=True)
class RunnerResult:
    """Structured response after executing a code snippet."""

    result: Any
    logs: str
    globals: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class RunnerLimits:
    """Execution bounds applied to model-authored code."""

    timeout_seconds: float = 10.0
    max_stdout_chars: int = 32_000
    max_result_chars: int = 64_000

    @classmethod
    def from_env(cls) -> "RunnerLimits":
        return cls(
            timeout_seconds=_env_float("NEXUS_RUN_CODE_TIMEOUT_SECONDS", 10.0),
            max_stdout_chars=_env_int("NEXUS_RUN_CODE_MAX_STDOUT_CHARS", 32_000),
            max_result_chars=_env_int("NEXUS_RUN_CODE_MAX_RESULT_CHARS", 64_000),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeoutSeconds": self.timeout_seconds,
            "maxStdoutChars": self.max_stdout_chars,
            "maxResultChars": self.max_result_chars,
        }


@dataclass(frozen=True)
class RunnerErrorDetails:
    """Structured diagnostic information for execution failures."""

    error_type: str
    message: str
    traceback_text: str = ""
    timed_out: bool = False
    exit_code: Optional[int] = None
    logs: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": self.error_type,
            "message": self.message,
            "timedOut": self.timed_out,
        }
        if self.traceback_text:
            payload["traceback"] = self.traceback_text
        if self.exit_code is not None:
            payload["exitCode"] = self.exit_code
        if self.logs:
            payload["logs"] = self.logs
        return payload


class RunnerExecutionError(RuntimeError):
    """Raised when user code fails."""

    def __init__(self, details: RunnerErrorDetails):
        super().__init__(details.message)
        self.details = details


SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "Exception": Exception,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "isinstance": isinstance,
    "KeyError": KeyError,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "RuntimeError": RuntimeError,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "TypeError": TypeError,
    "type": type,
    "tuple": tuple,
    "ValueError": ValueError,
    "zip": zip,
    "print": print,
    "__import__": builtins.__import__,
}


class _BoundedStdout(io.StringIO):
    """Capture stdout up to a hard character limit."""

    def __init__(self, max_chars: int):
        super().__init__()
        self._max_chars = max_chars
        self._written = 0
        self.truncated = False

    def write(self, s: str) -> int:
        if not isinstance(s, str):
            s = str(s)

        remaining = self._max_chars - self._written
        if remaining <= 0:
            self.truncated = True
            return len(s)

        chunk = s[:remaining]
        self._written += len(chunk)
        super().write(chunk)
        if len(chunk) < len(s):
            self.truncated = True
        return len(s)

    def getvalue(self) -> str:
        value = super().getvalue()
        if self.truncated:
            return value + "\n[stdout truncated]\n"
        return value


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(1, value)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(0.1, value)


def _json_default(value: Any) -> Any:
    if isinstance(value, ToolInfo):
        return value.name
    return repr(value)


def _normalize_result(value: Any, *, max_result_chars: int) -> tuple[Any, bool]:
    serialized = json.dumps(value, default=_json_default, ensure_ascii=False)
    if len(serialized) <= max_result_chars:
        return json.loads(serialized), False

    preview_limit = max(32, max_result_chars - 32)
    return (
        {
            "truncated": True,
            "type": type(value).__name__,
            "preview": serialized[:preview_limit] + "...",
        },
        True,
    )


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

    catalog = get_catalog(refresh=True)

    def load_tool(name: str) -> Callable[..., object]:
        return ensure_tool_loaded(name).function

    ns: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        "RESULT": None,
        "RUNNER_SETTINGS": config.RunnerSettings.from_env(),
        "TOOLS": LazyTools(catalog),
        "load_tool": load_tool,
    }

    if additional_globals:
        ns.update(additional_globals)

    return ns


def execute_user_code_in_process(
    code: str,
    *,
    globals_override: Optional[Mapping[str, Any]] = None,
    limits: Optional[RunnerLimits] = None,
) -> RunnerResult:
    """Execute Python code directly in the current process."""

    limits = limits or RunnerLimits.from_env()
    prepared_code = textwrap.dedent(code)
    exec_globals = build_execution_globals(additional_globals=globals_override)
    stdout_buffer = _BoundedStdout(limits.max_stdout_chars)

    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(prepared_code, exec_globals, exec_globals)  # noqa: S102
    except Exception as exc:
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type=type(exc).__name__,
                message=str(exc),
                traceback_text=traceback.format_exc(),
                logs=stdout_buffer.getvalue(),
            )
        ) from exc

    result_value = exec_globals.get("RESULT")
    normalized_result, truncated_result = _normalize_result(
        result_value,
        max_result_chars=limits.max_result_chars,
    )

    return RunnerResult(
        result=normalized_result,
        logs=stdout_buffer.getvalue(),
        globals={"RESULT": normalized_result},
        metadata={
            "limits": limits.to_dict(),
            "truncatedLogs": stdout_buffer.truncated,
            "truncatedResult": truncated_result,
            "executionModel": "in_process",
        },
    )


def run_user_code(
    code: str,
    *,
    globals_override: Optional[Mapping[str, Any]] = None,
    limits: Optional[RunnerLimits] = None,
) -> RunnerResult:
    """Execute Python *code* and return the structured result.

    Parameters
    ----------
    code:
        The Python source code authored by the model or user.
    globals_override:
        Optional mapping merged into the execution globals, useful for testing.
    """

    limits = limits or RunnerLimits.from_env()
    if globals_override:
        return execute_user_code_in_process(
            code,
            globals_override=globals_override,
            limits=limits,
        )

    worker_payload = json.dumps(
        {
            "code": code,
            "limits": limits.to_dict(),
        },
        ensure_ascii=False,
    )
    worker_env = os.environ.copy()
    repo_root = str(Path(__file__).resolve().parent.parent)
    pythonpath = worker_env.get("PYTHONPATH")
    worker_env["PYTHONPATH"] = (
        repo_root if not pythonpath else f"{repo_root}{os.pathsep}{pythonpath}"
    )
    command = [sys.executable, "-m", "nexus.execution_worker"]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=repo_root,
        env=worker_env,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(
            worker_payload,
            timeout=limits.timeout_seconds + 1.0,
        )
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process)
        stdout, stderr = process.communicate()
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="ExecutionTimeout",
                message=(
                    f"Code execution exceeded {limits.timeout_seconds:.1f} seconds"
                ),
                timed_out=True,
                exit_code=process.returncode,
                logs=stderr or stdout,
            )
        ) from exc

    if process.returncode != 0:
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="WorkerProcessError",
                message="Execution worker exited unexpectedly",
                exit_code=process.returncode,
                logs=(stderr or stdout).strip(),
            )
        )

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="WorkerProtocolError",
                message="Execution worker returned invalid JSON",
                logs=(stderr or stdout).strip(),
            )
        ) from exc

    if not payload.get("success", False):
        details_raw = payload.get("error") or {}
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type=details_raw.get("type", "ExecutionError"),
                message=details_raw.get("message", "Code execution failed"),
                traceback_text=details_raw.get("traceback", ""),
                timed_out=bool(details_raw.get("timedOut", False)),
                exit_code=details_raw.get("exitCode"),
                logs=details_raw.get("logs", ""),
            )
        )

    return RunnerResult(
        result=payload.get("result"),
        logs=payload.get("logs", ""),
        globals=payload.get("globals", {}),
        metadata=payload.get("metadata", {}),
    )


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover
            process.kill()
    except ProcessLookupError:
        pass


__all__ = [
    "RunnerResult",
    "RunnerLimits",
    "RunnerErrorDetails",
    "RunnerExecutionError",
    "build_execution_globals",
    "execute_user_code_in_process",
    "run_user_code",
]
