import sys
import textwrap
from pathlib import Path

import pytest

from nexus import tool_catalog
from nexus.runner import RunnerExecutionError, RunnerLimits, execute_user_code_in_process, run_user_code
from nexus.tool_policy import ToolPolicy
from nexus.tool_registry import clear_registry


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
