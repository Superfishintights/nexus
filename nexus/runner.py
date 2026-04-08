"""Core entrypoint for executing model-authored Python snippets."""
from __future__ import annotations

import atexit
import builtins
import contextlib
import io
import json
import os
import queue
import selectors
import signal
import subprocess
import sys
import textwrap
import time
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from . import config
from .lazy_tools import LazyTools
from .tool_catalog import ToolSpec, get_catalog, resolve_tool_request
from .tool_policy import ToolPolicy, get_active_tool_policy
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


BASE_SAFE_BUILTINS = {
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
}

UNRESTRICTED_BUILTINS = {
    **BASE_SAFE_BUILTINS,
    "__import__": builtins.__import__,
}

RESTRICTED_BUILTINS = dict(BASE_SAFE_BUILTINS)

RUN_CODE_MODE_ENV = "NEXUS_RUN_CODE_MODE"
RUN_CODE_MODE_ONESHOT = "oneshot"
RUN_CODE_MODE_PERSISTENT = "persistent"
RUN_CODE_MODE_PERSISTENT_POOL = "persistent_pool"
PERSISTENT_MAX_REQUESTS_ENV = "NEXUS_PERSISTENT_WORKER_MAX_REQUESTS"
PERSISTENT_IDLE_SECONDS_ENV = "NEXUS_PERSISTENT_WORKER_IDLE_SECONDS"
PERSISTENT_POOL_SIZE_ENV = "NEXUS_PERSISTENT_WORKER_POOL_SIZE"


class HostedToolCallable:
    """Callable proxy that routes tool execution through a provided invoker."""

    __slots__ = ("_invoke", "_name", "_doc")

    def __init__(self, invoke: Callable[..., object], *, name: str, doc: str) -> None:
        object.__setattr__(self, "_invoke", invoke)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_doc", doc)

    def __call__(self, *args: object, **kwargs: object) -> object:
        return object.__getattribute__(self, "_invoke")(*args, **kwargs)

    def __getattribute__(self, name: str) -> object:
        if name in {"__call__", "__class__", "__doc__", "__name__", "name"}:
            if name == "__doc__":
                return object.__getattribute__(self, "_doc")
            if name == "__name__":
                return object.__getattribute__(self, "_name")
            if name == "name":
                return object.__getattribute__(self, "_name")
            return object.__getattribute__(self, name)
        raise AttributeError(f"{type(self).__name__!s} does not expose attribute {name!r}")

    def __repr__(self) -> str:
        return f"<HostedToolCallable {object.__getattribute__(self, '_name')}>"


class RestrictedToolCallable(HostedToolCallable):
    """Opaque callable wrapper that blocks direct access to function globals."""

    def __repr__(self) -> str:
        return f"<RestrictedToolCallable {object.__getattribute__(self, '_name')}>"


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


def _serialize_tool_result(value: Any) -> Any:
    serialized = json.dumps(value, default=_json_default, ensure_ascii=False)
    return json.loads(serialized)


def _catalog_to_payload(catalog: Mapping[str, ToolSpec]) -> list[Dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "module": spec.module,
            "description": spec.description,
            "signature": spec.signature,
            "examples": list(spec.examples),
            "toolClass": spec.tool_class,
            "aliasOf": spec.alias_of,
        }
        for spec in catalog.values()
    ]


def _catalog_from_payload(payload: list[Mapping[str, Any]]) -> Dict[str, ToolSpec]:
    return {
        str(item["name"]): ToolSpec(
            name=str(item["name"]),
            module=str(item["module"]),
            description=str(item.get("description", "")),
            signature=str(item.get("signature", "")),
            examples=tuple(str(v) for v in item.get("examples", [])),
            tool_class=str(item.get("toolClass", "read")),
            alias_of=str(item["aliasOf"]) if item.get("aliasOf") is not None else None,
        )
        for item in payload
    }


def build_execution_globals(
    *,
    additional_globals: Optional[Mapping[str, Any]] = None,
    policy: Optional[ToolPolicy] = None,
    catalog: Optional[Mapping[str, ToolSpec]] = None,
    tool_invoker: Optional[Callable[[str, tuple[object, ...], dict[str, object]], object]] = None,
) -> Dict[str, Any]:
    """Construct the globals dictionary used for `exec`.

    The resulting namespace exposes:
    * A curated set of Python builtins.
    * The `RESULT` placeholder which user code must assign.
    * The lazy tool catalog via the `TOOLS` global.
    * `load_tool(name)` helper for tool access.
    * Read-only configuration (e.g., Jira settings), if configured.
    """

    policy = policy or get_active_tool_policy()
    catalog_snapshot = dict(catalog) if catalog is not None else get_catalog(refresh=True)

    def load_tool(name: str) -> Callable[..., object]:
        spec = resolve_tool_request(
            name,
            catalog=catalog_snapshot,
            policy=policy,
            allow_aliases=not policy.is_restricted,
        )
        canonical_name = spec.alias_of or spec.name
        if tool_invoker is not None:
            proxy_type = RestrictedToolCallable if policy.is_restricted else HostedToolCallable
            return proxy_type(
                lambda *args, **kwargs: tool_invoker(canonical_name, args, kwargs),
                name=canonical_name,
                doc=spec.description,
            )

        info = ensure_tool_loaded(name, policy=policy)
        if policy.is_restricted:
            return RestrictedToolCallable(
                info.function,
                name=info.canonical_name,
                doc=info.description,
            )
        return info.function

    ns: Dict[str, Any] = {
        "__builtins__": RESTRICTED_BUILTINS if policy.is_restricted else UNRESTRICTED_BUILTINS,
        "RESULT": None,
        "RUNNER_SETTINGS": config.RunnerSettings.from_env(),
        "TOOLS": LazyTools(catalog_snapshot, policy=policy),
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
    policy: Optional[ToolPolicy] = None,
    catalog: Optional[Mapping[str, ToolSpec]] = None,
    tool_invoker: Optional[Callable[[str, tuple[object, ...], dict[str, object]], object]] = None,
) -> RunnerResult:
    """Execute Python code directly in the current process."""

    limits = limits or RunnerLimits.from_env()
    prepared_code = textwrap.dedent(code)
    policy = policy or get_active_tool_policy()
    exec_globals = build_execution_globals(
        additional_globals=globals_override,
        policy=policy,
        catalog=catalog,
        tool_invoker=tool_invoker,
    )
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
            "policy": policy.to_dict(),
            "truncatedLogs": stdout_buffer.truncated,
            "truncatedResult": truncated_result,
            "executionModel": "in_process",
            "toolExecutionModel": "host_bridge" if tool_invoker is not None else "direct",
        },
    )


def _send_worker_message(process: subprocess.Popen[str], payload: Mapping[str, Any]) -> None:
    if process.stdin is None:
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="WorkerProtocolError",
                message="Execution worker stdin is unavailable",
            )
        )
    process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    process.stdin.flush()


def _handle_worker_tool_call(message: Mapping[str, Any], *, policy: ToolPolicy) -> Dict[str, Any]:
    tool_name = str(message.get("name", ""))
    args = tuple(message.get("args", []))
    kwargs = dict(message.get("kwargs", {}))
    request_id = str(message.get("requestId", ""))
    try:
        info = ensure_tool_loaded(tool_name, policy=policy)
        result = info.function(*args, **kwargs)
        return {
            "type": "tool_result",
            "requestId": request_id,
            "ok": True,
            "result": _serialize_tool_result(result),
        }
    except Exception as exc:  # pragma: no cover - exercised via worker protocol tests
        return {
            "type": "tool_result",
            "requestId": request_id,
            "ok": False,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }


def _normalize_run_mode(raw: str | None) -> str:
    normalized = (raw or RUN_CODE_MODE_PERSISTENT_POOL).strip().lower()
    if normalized not in {RUN_CODE_MODE_ONESHOT, RUN_CODE_MODE_PERSISTENT, RUN_CODE_MODE_PERSISTENT_POOL}:
        return RUN_CODE_MODE_PERSISTENT_POOL
    return normalized


def get_run_code_mode() -> str:
    return _normalize_run_mode(os.getenv(RUN_CODE_MODE_ENV))


def _persistent_max_requests() -> int:
    return _env_int(PERSISTENT_MAX_REQUESTS_ENV, 100)


def _persistent_idle_seconds() -> float:
    return _env_float(PERSISTENT_IDLE_SECONDS_ENV, 300.0)


def _persistent_pool_size() -> int:
    return _env_int(PERSISTENT_POOL_SIZE_ENV, 4)


class PersistentWorkerSession:
    def __init__(self, *, repo_root: str) -> None:
        self._repo_root = repo_root
        self._process: subprocess.Popen[str] | None = None
        self._selector: selectors.BaseSelector | None = None
        self._request_count = 0
        self._last_used_monotonic = 0.0
        self._max_requests = _persistent_max_requests()
        self._idle_seconds = _persistent_idle_seconds()
        self._lock = threading.RLock()

    def close(self) -> None:
        with self._lock:
            self._close_locked()

    def execute(
        self,
        *,
        code: str,
        limits: RunnerLimits,
        policy: ToolPolicy,
        catalog: Mapping[str, ToolSpec],
    ) -> RunnerResult:
        with self._lock:
            self._ensure_process_locked()
            process = self._process
            selector = self._selector
            if process is None or selector is None:
                raise RunnerExecutionError(
                    RunnerErrorDetails(
                        error_type="WorkerProcessError",
                        message="Persistent worker failed to start",
                    )
                )
            worker_payload = {
                "type": "start",
                "code": code,
                "limits": limits.to_dict(),
                "policy": policy.to_dict(),
                "catalog": _catalog_to_payload(catalog),
            }
            try:
                _send_worker_message(process, worker_payload)
                final_payload = self._read_worker_result_locked(
                    process, selector, limits=limits, policy=policy
                )
            except subprocess.TimeoutExpired as exc:
                self._close_locked(kill=True)
                raise RunnerExecutionError(
                    RunnerErrorDetails(
                        error_type="ExecutionTimeout",
                        message=(
                            f"Code execution exceeded {limits.timeout_seconds:.1f} seconds"
                        ),
                        timed_out=True,
                        exit_code=process.returncode,
                    )
                ) from exc
            except RunnerExecutionError:
                self._close_locked(kill=True)
                raise

            self._request_count += 1
            self._last_used_monotonic = time.monotonic()
            result = _result_from_worker_payload(final_payload)
            result.metadata["workerLifecycle"] = RUN_CODE_MODE_PERSISTENT
            if self._request_count >= self._max_requests:
                self._close_locked()
            return result

    def _ensure_process_locked(self) -> None:
        idle_expired = (
            self._process is not None
            and self._last_used_monotonic > 0
            and (time.monotonic() - self._last_used_monotonic) > self._idle_seconds
        )
        process_dead = self._process is None or self._process.poll() is not None
        if idle_expired or process_dead:
            self._close_locked(kill=idle_expired)
            self._start_locked()

    def _start_locked(self) -> None:
        worker_env = os.environ.copy()
        pythonpath = worker_env.get("PYTHONPATH")
        worker_env["PYTHONPATH"] = (
            self._repo_root if not pythonpath else f"{self._repo_root}{os.pathsep}{pythonpath}"
        )
        command = [sys.executable, "-m", "nexus.execution_worker"]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self._repo_root,
            env=worker_env,
            start_new_session=True,
            bufsize=1,
        )
        if process.stdout is None:
            raise RunnerExecutionError(
                RunnerErrorDetails(
                    error_type="WorkerProcessError",
                    message="Persistent worker stdout is unavailable",
                )
            )
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        self._process = process
        self._selector = selector
        self._request_count = 0
        self._last_used_monotonic = time.monotonic()

    def _close_locked(self, *, kill: bool = False) -> None:
        selector = self._selector
        process = self._process
        self._selector = None
        self._process = None
        self._request_count = 0
        self._last_used_monotonic = 0.0
        if selector is not None:
            selector.close()
        if process is None:
            return
        try:
            if process.poll() is None:
                if not kill and process.stdin is not None:
                    try:
                        _send_worker_message(process, {"type": "shutdown"})
                    except Exception:
                        kill = True
                if kill:
                    _terminate_process_group(process)
        finally:
            try:
                if process.stdin is not None:
                    process.stdin.close()
            except Exception:
                pass
            try:
                process.wait(timeout=1.0)
            except Exception:
                _terminate_process_group(process)

    def _read_worker_result_locked(
        self,
        process: subprocess.Popen[str],
        selector: selectors.BaseSelector,
        *,
        limits: RunnerLimits,
        policy: ToolPolicy,
    ) -> Dict[str, Any]:
        deadline = time.monotonic() + limits.timeout_seconds + 1.0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired([sys.executable, "-m", "nexus.execution_worker"], timeout=limits.timeout_seconds + 1.0)
            events = selector.select(timeout=remaining)
            if not events:
                raise subprocess.TimeoutExpired([sys.executable, "-m", "nexus.execution_worker"], timeout=limits.timeout_seconds + 1.0)
            line = process.stdout.readline()
            if not line:
                stderr = process.stderr.read() if process.stderr is not None else ""
                raise RunnerExecutionError(
                    RunnerErrorDetails(
                        error_type="WorkerProtocolError",
                        message="Persistent worker exited without returning a result",
                        logs=stderr.strip(),
                    )
                )
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RunnerExecutionError(
                    RunnerErrorDetails(
                        error_type="WorkerProtocolError",
                        message="Execution worker returned invalid JSON",
                        logs=line.strip(),
                    )
                ) from exc
            message_type = message.get("type")
            if message_type == "tool_call":
                _send_worker_message(process, _handle_worker_tool_call(message, policy=policy))
                continue
            if message_type == "result":
                return dict(message)
            raise RunnerExecutionError(
                RunnerErrorDetails(
                    error_type="WorkerProtocolError",
                    message=f"Execution worker sent unsupported message type: {message_type!r}",
                )
            )


class PersistentWorkerPool:
    def __init__(self, *, repo_root: str, size: int) -> None:
        self._repo_root = repo_root
        self._size = max(1, size)
        self._sessions = [PersistentWorkerSession(repo_root=repo_root) for _ in range(self._size)]
        self._available: queue.LifoQueue[PersistentWorkerSession] = queue.LifoQueue()
        for session in self._sessions:
            self._available.put(session)
        self._lock = threading.Lock()

    def close(self) -> None:
        with self._lock:
            for session in self._sessions:
                session.close()

    def execute(
        self,
        *,
        code: str,
        limits: RunnerLimits,
        policy: ToolPolicy,
        catalog: Mapping[str, ToolSpec],
    ) -> RunnerResult:
        session = self._available.get()
        try:
            result = session.execute(code=code, limits=limits, policy=policy, catalog=catalog)
            result.metadata["workerLifecycle"] = RUN_CODE_MODE_PERSISTENT_POOL
            return result
        finally:
            self._available.put(session)



def _get_persistent_session(repo_root: str) -> PersistentWorkerSession:
    global _PERSISTENT_SESSION
    with _PERSISTENT_SESSION_LOCK:
        if _PERSISTENT_SESSION is None or _PERSISTENT_SESSION._repo_root != repo_root:
            if _PERSISTENT_SESSION is not None:
                _PERSISTENT_SESSION.close()
            _PERSISTENT_SESSION = PersistentWorkerSession(repo_root=repo_root)
        return _PERSISTENT_SESSION


def _get_persistent_pool(repo_root: str) -> PersistentWorkerPool:
    global _PERSISTENT_POOL
    size = _persistent_pool_size()
    with _PERSISTENT_SESSION_LOCK:
        if (
            _PERSISTENT_POOL is None
            or _PERSISTENT_POOL._repo_root != repo_root
            or _PERSISTENT_POOL._size != size
        ):
            if _PERSISTENT_POOL is not None:
                _PERSISTENT_POOL.close()
            _PERSISTENT_POOL = PersistentWorkerPool(repo_root=repo_root, size=size)
        return _PERSISTENT_POOL


def shutdown_persistent_worker() -> None:
    global _PERSISTENT_SESSION, _PERSISTENT_POOL
    with _PERSISTENT_SESSION_LOCK:
        if _PERSISTENT_SESSION is not None:
            _PERSISTENT_SESSION.close()
            _PERSISTENT_SESSION = None
        if _PERSISTENT_POOL is not None:
            _PERSISTENT_POOL.close()
            _PERSISTENT_POOL = None


atexit.register(shutdown_persistent_worker)


def _result_from_worker_payload(final_payload: Dict[str, Any]) -> RunnerResult:
    if not final_payload.get("success", False):
        details_raw = final_payload.get("error") or {}
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
        result=final_payload.get("result"),
        logs=final_payload.get("logs", ""),
        globals=final_payload.get("globals", {}),
        metadata=final_payload.get("metadata", {}),
    )


def _execute_user_code_oneshot(
    code: str,
    *,
    limits: RunnerLimits,
    policy: ToolPolicy,
) -> RunnerResult:
    catalog = get_catalog(refresh=True)
    worker_payload = {
        "type": "start",
        "code": code,
        "limits": limits.to_dict(),
        "policy": policy.to_dict(),
        "catalog": _catalog_to_payload(catalog),
    }
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
        bufsize=1,
    )
    selector = selectors.DefaultSelector()
    if process.stdout is None:
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="WorkerProtocolError",
                message="Execution worker stdout is unavailable",
            )
        )
    selector.register(process.stdout, selectors.EVENT_READ)

    try:
        _send_worker_message(process, worker_payload)
        deadline = time.monotonic() + limits.timeout_seconds + 1.0
        final_payload: Optional[Dict[str, Any]] = None

        while final_payload is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, timeout=limits.timeout_seconds + 1.0)
            events = selector.select(timeout=remaining)
            if not events:
                raise subprocess.TimeoutExpired(command, timeout=limits.timeout_seconds + 1.0)
            line = process.stdout.readline()
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RunnerExecutionError(
                    RunnerErrorDetails(
                        error_type="WorkerProtocolError",
                        message="Execution worker returned invalid JSON",
                        logs=line.strip(),
                    )
                ) from exc

            message_type = message.get("type")
            if message_type == "tool_call":
                _send_worker_message(process, _handle_worker_tool_call(message, policy=policy))
                continue
            if message_type == "result":
                final_payload = dict(message)
                break
            raise RunnerExecutionError(
                RunnerErrorDetails(
                    error_type="WorkerProtocolError",
                    message=f"Execution worker sent unsupported message type: {message_type!r}",
                )
            )
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process)
        stderr = process.stderr.read() if process.stderr is not None else ""
        stdout_tail = process.stdout.read() if process.stdout is not None else ""
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="ExecutionTimeout",
                message=(
                    f"Code execution exceeded {limits.timeout_seconds:.1f} seconds"
                ),
                timed_out=True,
                exit_code=process.returncode,
                logs=(stderr or stdout_tail).strip(),
            )
        ) from exc
    finally:
        selector.close()
        if process.stdin is not None:
            process.stdin.close()

    stderr = process.stderr.read() if process.stderr is not None else ""
    return_code = process.wait(timeout=1.0)

    if return_code != 0:
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="WorkerProcessError",
                message="Execution worker exited unexpectedly",
                exit_code=return_code,
                logs=stderr.strip(),
            )
        )

    if final_payload is None:
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type="WorkerProtocolError",
                message="Execution worker exited without returning a result",
                logs=stderr.strip(),
            )
        )

    result = _result_from_worker_payload(final_payload)
    result.metadata["workerLifecycle"] = RUN_CODE_MODE_ONESHOT
    return result


def _execute_user_code_persistent(
    code: str,
    *,
    limits: RunnerLimits,
    policy: ToolPolicy,
) -> RunnerResult:
    repo_root = str(Path(__file__).resolve().parent.parent)
    session = _get_persistent_session(repo_root)
    catalog = get_catalog(refresh=True)
    return session.execute(code=code, limits=limits, policy=policy, catalog=catalog)


def _execute_user_code_persistent_pool(
    code: str,
    *,
    limits: RunnerLimits,
    policy: ToolPolicy,
) -> RunnerResult:
    repo_root = str(Path(__file__).resolve().parent.parent)
    pool = _get_persistent_pool(repo_root)
    catalog = get_catalog(refresh=True)
    return pool.execute(code=code, limits=limits, policy=policy, catalog=catalog)


def run_user_code(
    code: str,
    *,
    globals_override: Optional[Mapping[str, Any]] = None,
    limits: Optional[RunnerLimits] = None,
    policy: Optional[ToolPolicy] = None,
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
    policy = policy or get_active_tool_policy()
    if globals_override:
        return execute_user_code_in_process(
            code,
            globals_override=globals_override,
            limits=limits,
            policy=policy,
        )

    mode = get_run_code_mode()
    if mode == RUN_CODE_MODE_ONESHOT:
        return _execute_user_code_oneshot(code, limits=limits, policy=policy)
    if mode == RUN_CODE_MODE_PERSISTENT:
        return _execute_user_code_persistent(code, limits=limits, policy=policy)
    return _execute_user_code_persistent_pool(code, limits=limits, policy=policy)

def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover
            process.kill()
    except ProcessLookupError:
        pass


__all__ = [
    "RUN_CODE_MODE_ENV",
    "RUN_CODE_MODE_ONESHOT",
    "RUN_CODE_MODE_PERSISTENT",
    "RUN_CODE_MODE_PERSISTENT_POOL",
    "RunnerResult",
    "RunnerLimits",
    "RunnerErrorDetails",
    "RunnerExecutionError",
    "HostedToolCallable",
    "PersistentWorkerSession",
    "PersistentWorkerPool",
    "RestrictedToolCallable",
    "build_execution_globals",
    "execute_user_code_in_process",
    "get_run_code_mode",
    "run_user_code",
    "shutdown_persistent_worker",
    "_catalog_from_payload",
]


_PERSISTENT_SESSION_LOCK = threading.Lock()
_PERSISTENT_SESSION: "PersistentWorkerSession | None" = None
_PERSISTENT_POOL: "PersistentWorkerPool | None" = None
