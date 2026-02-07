import sys
import textwrap
from pathlib import Path

import pytest

from nexus import tool_catalog


@pytest.fixture
def dummy_tools_incremental(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    package_path = tmp_path / "dummy_tools_inc"
    package_path.mkdir()
    (package_path / "__init__.py").write_text("", encoding="utf-8")

    alpha_path = package_path / "alpha.py"
    beta_path = package_path / "beta.py"

    alpha_path.write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(description="Alpha tool")
            def alpha() -> str:
                return "a"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    beta_path.write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(description="Beta tool")
            def beta() -> str:
                return "b"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "dummy_tools_inc")

    yield {"alpha": alpha_path, "beta": beta_path}

    for module_name in list(sys.modules):
        if module_name == "dummy_tools_inc" or module_name.startswith("dummy_tools_inc."):
            sys.modules.pop(module_name, None)


def test_refresh_skips_reparsing_unchanged_files(
    dummy_tools_incremental, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Clear global caches to avoid cross-test coupling.
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    calls = {"count": 0}
    original_parse = tool_catalog.ast.parse

    def wrapped_parse(*args, **kwargs):
        calls["count"] += 1
        return original_parse(*args, **kwargs)

    monkeypatch.setattr(tool_catalog.ast, "parse", wrapped_parse)

    tool_catalog.get_catalog(refresh=True)
    first = calls["count"]
    assert first >= 2  # alpha + beta

    calls["count"] = 0
    tool_catalog.get_catalog(refresh=True)
    assert calls["count"] == 0

    # Touch only alpha; beta should stay cached and not be re-parsed.
    dummy_tools_incremental["alpha"].write_text(
        dummy_tools_incremental["alpha"].read_text(encoding="utf-8") + "\n# changed\n",
        encoding="utf-8",
    )

    calls["count"] = 0
    tool_catalog.get_catalog(refresh=True)
    assert calls["count"] == 1

