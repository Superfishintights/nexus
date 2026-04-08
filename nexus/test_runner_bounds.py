import sys
import textwrap
from pathlib import Path

import pytest

from nexus import tool_catalog
from nexus.runner import (
    RUN_CODE_MODE_ENV,
    RUN_CODE_MODE_ONESHOT,
    RUN_CODE_MODE_PERSISTENT,
    RUN_CODE_MODE_PERSISTENT_POOL,
    PERSISTENT_POOL_SIZE_ENV,
    RunnerExecutionError,
    RunnerLimits,
    execute_user_code_in_process,
    run_user_code,
    shutdown_persistent_worker,
)
from nexus.tool_policy import ToolPolicy
from nexus.tool_registry import clear_registry


@pytest.fixture(autouse=True)
def reset_persistent_worker() -> None:
    shutdown_persistent_worker()
    yield
    shutdown_persistent_worker()


def test_run_user_code_uses_subprocess() -> None:
    result = run_user_code("RESULT = 2 + 2")

    assert result.result == 4
    assert result.metadata["executionModel"] == "subprocess"
    assert result.metadata["toolExecutionModel"] == "host_bridge"
    assert result.metadata["workerLifecycle"] == RUN_CODE_MODE_PERSISTENT_POOL


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


@pytest.fixture
def dummy_runner_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    package_path = tmp_path / "dummy_runner_tools"
    package_path.mkdir()
    (package_path / "__init__.py").write_text("", encoding="utf-8")
    (package_path / "alpha.py").write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(name="alpha", aliases=["legacy_alpha"])
            def alpha(x: int = 1) -> int:
                return x + 1
            """
        ).lstrip(),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "dummy_runner_tools")
    clear_registry()
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    yield "dummy_runner_tools"

    for module_name in list(sys.modules):
        if module_name == "dummy_runner_tools" or module_name.startswith("dummy_runner_tools."):
            sys.modules.pop(module_name, None)


def test_run_user_code_restricted_mode_denies_imports() -> None:
    with pytest.raises(RunnerExecutionError) as exc_info:
        run_user_code(
            """
import os
RESULT = os.name
""",
            policy=ToolPolicy(mode="restricted", allowed_tools=frozenset({"alpha"})),
        )

    assert exc_info.value.details.error_type in {"ImportError", "KeyError"}
    assert "__import__" in exc_info.value.details.message


def test_run_user_code_restricted_mode_rejects_alias_loads(dummy_runner_tools: str) -> None:
    del dummy_runner_tools
    with pytest.raises(RunnerExecutionError) as exc_info:
        run_user_code(
            """
load_tool("legacy_alpha")
RESULT = "should not reach"
""",
            policy=ToolPolicy(mode="restricted", allowed_tools=frozenset({"alpha"})),
        )

    assert exc_info.value.details.error_type in {"ToolAccessError", "KeyError"}
    assert "legacy_alpha" in exc_info.value.details.message


def test_run_user_code_restricted_mode_allows_approved_tool_calls(dummy_runner_tools: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RUN_CODE_MODE_ENV, RUN_CODE_MODE_PERSISTENT_POOL)
    del dummy_runner_tools
    result = run_user_code(
        """
tool = load_tool("alpha")
RESULT = {
    "value": tool(4),
    "tool_type": type(tool).__name__,
}
""",
        policy=ToolPolicy(mode="restricted", allowed_tools=frozenset({"alpha"})),
    )

    assert result.result == {"value": 5, "tool_type": "RestrictedToolCallable"}
    assert result.metadata["executionModel"] == "subprocess"
    assert result.metadata["toolExecutionModel"] == "host_bridge"
    assert result.metadata["workerLifecycle"] == RUN_CODE_MODE_PERSISTENT_POOL


def test_run_user_code_restricted_mode_hides_tool_globals(dummy_runner_tools: str) -> None:
    del dummy_runner_tools
    with pytest.raises(RunnerExecutionError) as exc_info:
        run_user_code(
            """
tool = load_tool("alpha")
RESULT = tool.__globals__
""",
            policy=ToolPolicy(mode="restricted", allowed_tools=frozenset({"alpha"})),
        )

    assert exc_info.value.details.error_type == "AttributeError"
    assert "__globals__" in exc_info.value.details.message


@pytest.mark.parametrize(
    ("snippet", "error_type", "message_fragment"),
    [
        ("RESULT = open('blocked.txt', 'w')", "NameError", "open"),
        ("import socket\nRESULT = socket.gethostname()", "ImportError", "__import__"),
        ("import subprocess\nRESULT = subprocess.run(['echo', 'hi'])", "ImportError", "__import__"),
    ],
)
def test_run_user_code_restricted_mode_blocks_direct_local_capabilities(
    snippet: str,
    error_type: str,
    message_fragment: str,
) -> None:
    with pytest.raises(RunnerExecutionError) as exc_info:
        run_user_code(
            snippet,
            policy=ToolPolicy(mode="restricted", allowed_tools=frozenset({"alpha"})),
        )

    assert exc_info.value.details.error_type == error_type
    assert message_fragment in exc_info.value.details.message


def test_run_user_code_persistent_mode_reuses_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RUN_CODE_MODE_ENV, RUN_CODE_MODE_PERSISTENT)
    first = run_user_code('RESULT = 1')
    second = run_user_code('RESULT = 2')

    assert first.metadata['workerLifecycle'] == RUN_CODE_MODE_PERSISTENT
    assert second.metadata['workerLifecycle'] == RUN_CODE_MODE_PERSISTENT
    assert first.metadata['workerPid'] == second.metadata['workerPid']


def test_run_user_code_persistent_mode_does_not_leak_globals(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RUN_CODE_MODE_ENV, RUN_CODE_MODE_PERSISTENT)
    first = run_user_code('TEMP_VALUE = 123\nRESULT = "set"')
    second = run_user_code(
        'try:\n    TEMP_VALUE\n    RESULT = True\nexcept Exception:\n    RESULT = False'
    )

    assert first.result == 'set'
    assert second.result is False


def test_run_user_code_persistent_mode_recovers_after_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RUN_CODE_MODE_ENV, RUN_CODE_MODE_PERSISTENT)
    with pytest.raises(RunnerExecutionError):
        run_user_code(
            'while True:\n    pass',
            limits=RunnerLimits(timeout_seconds=0.2, max_stdout_chars=1024, max_result_chars=2048),
        )

    result = run_user_code('RESULT = 9')

    assert result.result == 9
    assert result.metadata['workerLifecycle'] == RUN_CODE_MODE_PERSISTENT


def test_run_user_code_oneshot_override_still_works(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RUN_CODE_MODE_ENV, RUN_CODE_MODE_ONESHOT)

    first = run_user_code('RESULT = 1')
    second = run_user_code('RESULT = 2')

    assert first.metadata['workerLifecycle'] == RUN_CODE_MODE_ONESHOT
    assert second.metadata['workerLifecycle'] == RUN_CODE_MODE_ONESHOT
    assert first.metadata['workerPid'] != second.metadata['workerPid']


def test_run_user_code_pool_mode_uses_multiple_workers_under_parallel_load(monkeypatch: pytest.MonkeyPatch) -> None:
    from concurrent.futures import ThreadPoolExecutor

    monkeypatch.setenv(RUN_CODE_MODE_ENV, RUN_CODE_MODE_PERSISTENT_POOL)
    monkeypatch.setenv(PERSISTENT_POOL_SIZE_ENV, '2')

    def task(_: int):
        return run_user_code('RESULT = 7').metadata['workerPid']

    with ThreadPoolExecutor(max_workers=2) as executor:
        pids = list(executor.map(task, range(4)))

    assert len(set(pids)) == 2


def test_get_run_code_mode_defaults_to_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    from nexus.runner import get_run_code_mode

    monkeypatch.delenv(RUN_CODE_MODE_ENV, raising=False)
    assert get_run_code_mode() == RUN_CODE_MODE_PERSISTENT_POOL
