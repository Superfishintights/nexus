import sys
import textwrap
from pathlib import Path

import pytest

from nexus import tool_catalog
from nexus.runner import build_execution_globals
from nexus.tool_registry import clear_registry, ensure_tool_loaded, get_tool, is_tool_loaded


@pytest.fixture
def dummy_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    package_path = tmp_path / "dummy_tools_lazy"
    package_path.mkdir()
    (package_path / "__init__.py").write_text("", encoding="utf-8")

    (package_path / "alpha.py").write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(description="Alpha tool", examples=["alpha(1)"], aliases=["legacy_alpha"])
            def alpha(x: int, y: str = "hi") -> str:
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
                return flag
            """
        ).lstrip(),
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "dummy_tools_lazy")

    yield "dummy_tools_lazy"

    for module_name in list(sys.modules):
        if module_name == "dummy_tools_lazy" or module_name.startswith("dummy_tools_lazy."):
            sys.modules.pop(module_name, None)


def test_tools_mapping_is_lazy(dummy_tools: str, monkeypatch: pytest.MonkeyPatch) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    import nexus.lazy_tools as lazy_tools_mod

    calls = {"count": 0}
    original = lazy_tools_mod.spec_to_dict

    def wrapped(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(lazy_tools_mod, "spec_to_dict", wrapped)

    ns = build_execution_globals()
    tools = ns["TOOLS"]

    # Building globals should not convert every tool to a dict.
    assert calls["count"] == 0

    items_view = tools.items()
    assert calls["count"] == 0

    first_name, _ = next(iter(items_view))
    assert calls["count"] == 1

    keys = list(tools.keys())
    assert first_name in keys
    assert "legacy_alpha" not in keys
    assert calls["count"] == 1

    other_name = next(name for name in keys if name != first_name)
    _ = tools[other_name]
    assert calls["count"] == 2

    # Cache: repeated access should not rebuild.
    _ = tools[other_name]
    assert calls["count"] == 2


def test_tools_search_matches_catalog_order(dummy_tools: str) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    ns = build_execution_globals()
    tools = ns["TOOLS"]

    expected = [spec.name for spec in tool_catalog.search_catalog("a", limit=20)]
    actual = [tool_dict["name"] for tool_dict in tools.search("a", limit=20)]

    assert actual == expected


def test_tools_search_supports_multiword_queries(dummy_tools: str) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    ns = build_execution_globals()
    results = ns["TOOLS"].search("alpha tool", limit=5)

    assert results
    assert results[0]["name"] == "alpha"


def test_tools_get_tool_and_loaded_overrides(dummy_tools: str) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    ns = build_execution_globals()
    tools = ns["TOOLS"]

    alpha_full = tools.get_tool("alpha", detail_level="full")
    assert alpha_full["name"] == "alpha"
    assert alpha_full["loaded"] is False
    assert alpha_full["description"] == "Alpha tool"
    assert alpha_full["examples"] == ["alpha(1)"]

    assert not is_tool_loaded("alpha")
    info = ensure_tool_loaded("alpha")
    assert is_tool_loaded("alpha")

    alpha_summary = tools.get_tool("alpha", detail_level="summary")
    assert alpha_summary["loaded"] is True
    assert alpha_summary["signature"] == info.signature

    # Alias lookups still work directly even though aliases are hidden from iteration.
    alias_summary = tools["legacy_alpha"]
    assert alias_summary["aliasOf"] == "alpha"

    # Loaded-only fallback: tool exists in registry, even if absent from catalog.
    loaded_info = get_tool("alpha")
    assert loaded_info.name == "alpha"

    with pytest.raises(KeyError):
        tools.get_tool("does_not_exist", detail_level="full")
