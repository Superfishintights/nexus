import sys
import textwrap
from pathlib import Path

import pytest

from nexus import tool_catalog
from nexus.runner import build_execution_globals
from nexus.test_helpers import builtin_tool_packages, configure_tool_packages
from nexus.tool_policy import ToolPolicy
from nexus.tool_registry import clear_registry, ensure_tool_loaded, is_tool_loaded


@pytest.fixture
def dummy_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    package_path = tmp_path / "dummy_tools"
    package_path.mkdir()
    (package_path / "__init__.py").write_text("", encoding="utf-8")

    (package_path / "alpha.py").write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(description="Alpha tool", examples=["alpha(1)"], aliases=["legacy_alpha"])
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

    (package_path / "gamma.py").write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(namespace="demo", description="Gamma tool")
            async def gamma() -> str:
                return "ok"
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


@pytest.fixture
def builtin_packs(monkeypatch: pytest.MonkeyPatch) -> tuple[str, ...]:
    return configure_tool_packages(monkeypatch, builtin_tool_packages())


def test_catalog_empty_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    env_file = tmp_path / "empty.env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.delenv(tool_catalog.TOOL_PACKAGES_ENV, raising=False)
    monkeypatch.setenv("NEXUS_ENV_FILE", str(env_file))
    clear_registry()
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    catalog = tool_catalog.get_catalog(refresh=True)
    diagnostics = tool_catalog.get_catalog_diagnostics()

    assert tool_catalog.get_tool_package_names() == ()
    assert catalog == {}
    assert diagnostics["warnings"] == []


def test_legacy_tools_alias_expands_to_local_tool_packs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "tools")

    package_names = tool_catalog.get_tool_package_names()

    assert package_names == builtin_tool_packages(include_starling=True)


def test_catalog_scans_without_import(dummy_tools: str) -> None:
    clear_registry()

    catalog = tool_catalog.get_catalog(refresh=True)

    assert "alpha" in catalog
    assert "beta_tool" in catalog
    assert "demo.gamma" in catalog
    assert not is_tool_loaded("alpha")
    assert catalog["alpha"].module.endswith("dummy_tools.alpha")
    assert catalog["alpha"].description == "Alpha tool"
    assert catalog["alpha"].examples == ("alpha(1)",)
    assert catalog["alpha"].tool_class == "read"
    assert catalog["alpha"].signature.startswith("(x")


def test_ensure_tool_loaded_imports_module(dummy_tools: str) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    info = ensure_tool_loaded("alpha")

    assert is_tool_loaded("alpha")
    assert info.examples == ["alpha(1)"]
    assert info.function(3) == "3-hi"

    gamma_info = ensure_tool_loaded("demo.gamma")
    assert gamma_info.name == "demo.gamma"


def test_runner_globals_support_load_tool(dummy_tools: str) -> None:
    clear_registry()
    tool_catalog.get_catalog(refresh=True)

    ns = build_execution_globals()

    assert "alpha" in ns["TOOLS"]
    assert "demo.gamma" in ns["TOOLS"]
    alpha_fn = ns["load_tool"]("alpha")
    assert alpha_fn(2, "yo") == "2-yo"


def test_policy_filters_search_and_resolution(dummy_tools: str) -> None:
    clear_registry()
    catalog = tool_catalog.get_catalog(refresh=True)
    policy = ToolPolicy(
        mode="restricted",
        allowed_tools=frozenset({"alpha"}),
    )

    visible = tool_catalog.search_catalog("", limit=20, policy=policy)
    visible_names = [spec.name for spec in visible]

    assert visible_names == ["alpha"]
    assert tool_catalog.resolve_tool_request(
        "alpha",
        catalog=catalog,
        policy=policy,
        allow_aliases=False,
    ).name == "alpha"

    with pytest.raises(KeyError):
        tool_catalog.resolve_tool_request(
            "legacy_alpha",
            catalog=catalog,
            policy=policy,
            allow_aliases=False,
        )

    with pytest.raises(KeyError):
        tool_catalog.resolve_tool_request(
            "beta_tool",
            catalog=catalog,
            policy=policy,
            allow_aliases=False,
        )


def test_catalog_reports_nonfatal_problems(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package_path = tmp_path / "broken_tools"
    package_path.mkdir()
    (package_path / "__init__.py").write_text("", encoding="utf-8")
    (package_path / "broken.py").write_text("def nope(:\n", encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "broken_tools,missing_tools")

    catalog = tool_catalog.get_catalog(refresh=True)
    problems = tool_catalog.get_catalog_problems()

    assert catalog == {}
    assert any(problem.code == "syntax_error" for problem in problems)
    assert any(problem.code == "missing_package" for problem in problems)


def test_duplicate_names_in_same_module_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package_path = tmp_path / "duplicate_tools"
    package_path.mkdir()
    (package_path / "__init__.py").write_text("", encoding="utf-8")
    (package_path / "dupe.py").write_text(
        textwrap.dedent(
            """
            from nexus.tool_registry import register_tool

            @register_tool(namespace="demo", aliases=["alpha"])
            def alpha() -> str:
                return "a"

            @register_tool(name="alpha")
            def beta() -> str:
                return "b"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "duplicate_tools")

    with pytest.raises(ValueError, match="Duplicate tool names found"):
        tool_catalog.get_catalog(refresh=True)


def test_builtin_tools_are_discoverable(builtin_packs: tuple[str, ...]) -> None:
    del builtin_packs
    catalog = tool_catalog.get_catalog(refresh=True)

    assert "jira.get_issue_status" in catalog
    assert "get_issue_status" in catalog  # alias
    assert "tautulli.get_activity" in catalog
    assert "tautulli_get_activity" in catalog  # alias
    assert "n8n.create_workflow" in catalog
    assert "sonarr.get_series" in catalog


def test_catalog_bootstraps_local_tool_pack_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_name = "nexus_tools_tautulli"
    package_root = str((Path(__file__).resolve().parents[1] / "tool_packs" / package_name))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, package_name)
    monkeypatch.setattr(
        sys,
        "path",
        [entry for entry in sys.path if entry != package_root],
    )
    clear_registry()
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    catalog = tool_catalog.get_catalog(refresh=True)

    assert "tautulli.get_activity" in catalog
    assert package_root in sys.path


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("tautulli recently watched items", "tautulli.get_history"),
        ("show me the latest plays from tautulli", "tautulli.get_history"),
        ("who is currently watching on plex", "tautulli.get_activity"),
        ("list tautulli users", "tautulli.get_users"),
        ("create a workflow in n8n", "n8n.create_workflow"),
        ("add a node to an n8n workflow", "n8n.add_node"),
        ("retry a failed n8n execution", "n8n.retry_execution"),
        ("what is the status of jira issue PROJ-123", "jira.get_issue_status"),
        ("show jira issue transitions", "jira.get_issue_status"),
        ("show missing episodes in sonarr", "sonarr.get_wanted_missing"),
        ("list sonarr series", "sonarr.get_series"),
        ("show sonarr queue status", "sonarr.get_queue_status"),
        ("show missing movies in radarr", "radarr.get_wanted_missing"),
        ("lookup a movie in radarr", "radarr.get_movie_lookup"),
        ("show radarr queue status", "radarr.get_queue_status"),
    ],
)
def test_builtin_catalog_matches_natural_language_tasks(
    query: str,
    expected: str,
    builtin_packs: tuple[str, ...],
) -> None:
    del builtin_packs
    matches = tool_catalog.search_catalog(query, limit=5)

    assert matches, f"Expected matches for query: {query}"
    assert matches[0].name == expected
