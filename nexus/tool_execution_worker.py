"""Subprocess entrypoint for bounded host-side tool execution."""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import sys
import traceback
from typing import Any, Mapping

from .runner import RunnerErrorDetails, _serialize_tool_result
from .tool_registry import get_tool


def _read_request() -> dict[str, Any]:
    line = sys.stdin.readline()
    if not line:
        raise EOFError("tool worker stdin closed")
    return json.loads(line)


def _write_response(payload: Mapping[str, Any]) -> None:
    sys.__stdout__.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.__stdout__.flush()


def _run(payload: Mapping[str, Any]) -> dict[str, Any]:
    tool_name = str(payload["toolName"])
    module_name = str(payload["module"])
    args = tuple(payload.get("args", []))
    kwargs = dict(payload.get("kwargs", {}))

    with contextlib.redirect_stdout(io.StringIO()):
        importlib.import_module(module_name)
        info = get_tool(tool_name)
        result = info.function(*args, **kwargs)
    return {"success": True, "result": _serialize_tool_result(result)}


def main() -> int:
    try:
        payload = _read_request()
        _write_response(_run(payload))
    except Exception as exc:
        details = RunnerErrorDetails(
            error_type=type(exc).__name__,
            message=str(exc),
            traceback_text=traceback.format_exc(),
        )
        _write_response({"success": False, "error": details.to_dict()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
