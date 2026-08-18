from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "nexus_tools_bazarr"


def test_all_generated_modules_have_literal_bazarr_metadata() -> None:
    generated = [p for p in PACKAGE_DIR.glob("*.py") if p.name not in {"__init__.py", "api.py", "client.py"}]
    assert len(generated) == 79
    for path in generated:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        assert len(functions) == 1, path
        fn = functions[0]
        decorators = [deco for deco in fn.decorator_list if isinstance(deco, ast.Call)]
        assert decorators, path
        keywords = {kw.arg: kw.value for kw in decorators[0].keywords}
        assert isinstance(keywords["namespace"], ast.Constant)
        assert keywords["namespace"].value == "bazarr"
        assert isinstance(keywords["description"], ast.Constant)
        assert isinstance(keywords["examples"], ast.List)
        assert isinstance(keywords["aliases"], ast.List)


def test_patch_operations_are_registered() -> None:
    names = {path.stem for path in PACKAGE_DIR.glob("update_*.py")}
    assert {
        "update_episodes_subtitles",
        "update_movies",
        "update_movies_subtitles",
        "update_series",
        "update_subtitles",
        "update_system_backups",
        "update_system_jobs",
    }.issubset(names)
