"""Subprocess entrypoint for bounded code execution."""

from __future__ import annotations

import json
import sys

from .runner import RunnerExecutionError, RunnerLimits, execute_user_code_in_process


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        limits = RunnerLimits(
            timeout_seconds=float(payload["limits"]["timeoutSeconds"]),
            max_stdout_chars=int(payload["limits"]["maxStdoutChars"]),
            max_result_chars=int(payload["limits"]["maxResultChars"]),
        )
        result = execute_user_code_in_process(payload["code"], limits=limits)
        json.dump(
            {
                "success": True,
                "result": result.result,
                "logs": result.logs,
                "globals": result.globals,
                "metadata": {
                    **result.metadata,
                    "executionModel": "subprocess",
                },
            },
            sys.stdout,
            ensure_ascii=False,
        )
        return 0
    except RunnerExecutionError as exc:
        json.dump(
            {
                "success": False,
                "error": exc.details.to_dict(),
            },
            sys.stdout,
            ensure_ascii=False,
        )
        return 0
    except Exception as exc:  # pragma: no cover
        json.dump(
            {
                "success": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            },
            sys.stdout,
            ensure_ascii=False,
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
