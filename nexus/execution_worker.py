"""Subprocess entrypoint for bounded code execution."""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Mapping

from .tool_policy import ToolAccessError, ToolPolicy
from .runner import (
    RunnerExecutionError,
    RunnerErrorDetails,
    RunnerLimits,
    _catalog_from_payload,
    execute_user_code_in_process,
)


_REMOTE_EXCEPTION_TYPES = {
    "AttributeError": AttributeError,
    "KeyError": KeyError,
    "PermissionError": PermissionError,
    "RuntimeError": RuntimeError,
    "ToolAccessError": ToolAccessError,
    "TypeError": TypeError,
    "ValueError": ValueError,
}


def _read_message() -> dict[str, Any]:
    line = sys.stdin.readline()
    if not line:
        raise EOFError("worker stdin closed")
    return json.loads(line)


def _send_message(payload: Mapping[str, Any]) -> None:
    sys.__stdout__.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.__stdout__.flush()


def _raise_remote_tool_error(error: Mapping[str, Any]) -> None:
    error_type = str(error.get("type", "RuntimeError"))
    message = str(error.get("message", "Tool call failed"))
    if bool(error.get("timedOut")) or error_type == "ExecutionTimeout":
        raise RunnerExecutionError(
            RunnerErrorDetails(
                error_type=error_type,
                message=message,
                traceback_text=str(error.get("traceback", "")),
                timed_out=bool(error.get("timedOut", True)),
                exit_code=error.get("exitCode"),
                logs=str(error.get("logs", "")),
            )
        )
    exc_type = _REMOTE_EXCEPTION_TYPES.get(error_type, RuntimeError)
    raise exc_type(message)


class _HostToolInvoker:
    def __call__(self, tool_name: str, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
        request_id = str(uuid.uuid4())
        _send_message(
            {
                "type": "tool_call",
                "requestId": request_id,
                "name": tool_name,
                "args": list(args),
                "kwargs": kwargs,
            }
        )
        while True:
            message = _read_message()
            if message.get("type") != "tool_result":
                raise RuntimeError(f"Unexpected worker protocol message: {message.get('type')!r}")
            if message.get("requestId") != request_id:
                raise RuntimeError("Mismatched tool response from host")
            if message.get("ok"):
                return message.get("result")
            _raise_remote_tool_error(message.get("error") or {})


def _handle_start(payload: Mapping[str, Any]) -> dict[str, Any]:
    limits = RunnerLimits(
        timeout_seconds=float(payload["limits"]["timeoutSeconds"]),
        max_stdout_chars=int(payload["limits"]["maxStdoutChars"]),
        max_result_chars=int(payload["limits"]["maxResultChars"]),
    )
    policy = ToolPolicy.from_dict(payload.get("policy", {}))
    catalog = _catalog_from_payload(payload.get("catalog", []))
    result = execute_user_code_in_process(
        payload["code"],
        limits=limits,
        policy=policy,
        catalog=catalog,
        tool_invoker=_HostToolInvoker(),
    )
    return {
        "type": "result",
        "success": True,
        "result": result.result,
        "logs": result.logs,
        "globals": result.globals,
        "metadata": {
            **result.metadata,
            "executionModel": "subprocess",
            "toolExecutionModel": "host_bridge",
            "workerPid": os.getpid(),
        },
    }


def main() -> int:
    try:
        while True:
            try:
                payload = _read_message()
            except EOFError:
                return 0

            message_type = payload.get("type")
            if message_type == "shutdown":
                return 0
            if message_type != "start":
                _send_message(
                    {
                        "type": "result",
                        "success": False,
                        "error": {
                            "type": "RuntimeError",
                            "message": f"Unexpected startup payload: {message_type!r}",
                        },
                    }
                )
                continue

            try:
                _send_message(_handle_start(payload))
            except RunnerExecutionError as exc:
                _send_message(
                    {
                        "type": "result",
                        "success": False,
                        "error": exc.details.to_dict(),
                    }
                )
    except Exception as exc:  # pragma: no cover
        _send_message(
            {
                "type": "result",
                "success": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            }
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
