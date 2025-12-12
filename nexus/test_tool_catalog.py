import sys
import textwrap
from pathlib import Path

import pytest

from nexus import tool_catalog
from nexus.runner import build_execution_globals
from nexus.tool_registry import (
    clear_registry,
    ensure_tool_loaded,
    is_tool_loaded,
)


@pytest.fixture
def dummy_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    package_path = tmp_path / "dummy_tools"
    package_path.mkdir()
    (package_path / "__init__.py").write_text("", encoding="utf-8")

    (package_path / "alpha.py").write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(description="Alpha tool", examples=["alpha(1)"])
            def alpha(x: int, y: str = "hi") -> str:
                \"\"\"Alpha docstring.\"\"\"
                return f"{x}-{y}"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    (package_path / "beta.py").write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(name="beta_tool")
            def beta(*, flag: bool = True) -> bool:
                \"\"\"Beta doc.\"\"\"
                return flag
            """
        ).lstrip(),
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "dummy_tools")

    yield "dummy_tools"

    # Cleanup loaded dummy modules to avoid cross-test bleed.
    for module_name in list(sys.modules):
        if module_name == "dummy_tools" or module_name.startswith("dummy_tools."):
            sys.modules.pop(module_name, None)


def test_catalog_scans_without_import(dummy_tools: str) -> None:
    clear_registry()

    catalog = tool_catalog.get_catalog(refresh=True)

    assert "alpha" in catalog
    assert "beta_tool" in catalog
    assert not is_tool_loaded("alpha")
    assert catalog["alpha"].module.endswith("dummy_tools.alpha")
    assert catalog["alpha"].description == "Alpha tool"
    assert catalog["alpha"].examples == ("alpha(1)",)
    assert catalog["alpha"].signature.startswith("(x")


def test_ensure_tool_loaded_imports_module(dummy_tools: str) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    info = ensure_tool_loaded("alpha")

    assert is_tool_loaded("alpha")
    assert info.examples == ["alpha(1)"]
    assert info.function(3) == "3-hi"


def test_runner_globals_support_load_tool(dummy_tools: str) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    ns = build_execution_globals()

    assert "alpha" in ns["TOOLS"]
    alpha_fn = ns["load_tool"]("alpha")
    assert alpha_fn(2, "yo") == "2-yo"


def test_builtin_tools_are_discoverable() -> None:
    catalog = tool_catalog.get_catalog(refresh=True)

    assert "get_issue_status" in catalog
    assert "tautulli_get_activity" in catalog
