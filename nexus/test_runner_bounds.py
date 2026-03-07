import pytest

from nexus.runner import RunnerExecutionError, RunnerLimits, execute_user_code_in_process, run_user_code


def test_run_user_code_uses_subprocess() -> None:
    result = run_user_code("RESULT = 2 + 2")

    assert result.result == 4
    assert result.metadata["executionModel"] == "subprocess"


def test_run_user_code_times_out() -> None:
    with pytest.raises(RunnerExecutionError) as exc_info:
        run_user_code(
            """
while True:
    pass
""",
            limits=RunnerLimits(timeout_seconds=0.2, max_stdout_chars=1024, max_result_chars=2048),
        )

    assert exc_info.value.details.timed_out is True
    assert exc_info.value.details.error_type == "ExecutionTimeout"


def test_in_process_execution_truncates_stdout_and_result() -> None:
    result = execute_user_code_in_process(
        """
print("x" * 32)
RESULT = {"payload": "y" * 64}
""",
        limits=RunnerLimits(timeout_seconds=1.0, max_stdout_chars=12, max_result_chars=40),
    )

    assert result.metadata["truncatedLogs"] is True
    assert result.metadata["truncatedResult"] is True
    assert "[stdout truncated]" in result.logs
    assert result.result["truncated"] is True


def test_run_user_code_surfaces_traceback_details() -> None:
    with pytest.raises(RunnerExecutionError) as exc_info:
        run_user_code("raise ValueError('boom')")

    assert exc_info.value.details.error_type == "ValueError"
    assert "boom" in exc_info.value.details.message
    assert "ValueError" in exc_info.value.details.traceback_text


def test_run_user_code_exposes_basic_introspection_builtins() -> None:
    result = run_user_code(
        """
value = {"a": 1}
RESULT = {
    "is_dict": isinstance(value, dict),
    "type_name": type(value).__name__,
}
"""
    )

    assert result.result == {"is_dict": True, "type_name": "dict"}
