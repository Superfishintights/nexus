from __future__ import annotations

import ast
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1] / "nexus_tools_prowlarr"


def _decorated_tools() -> list[tuple[Path, ast.FunctionDef, ast.Call]]:
    tools: list[tuple[Path, ast.FunctionDef, ast.Call]] = []
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        if path.name in {"__init__.py", "api.py", "client.py"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Name) and func.id == "register_tool":
                        tools.append((path, node, decorator))
    return tools


def test_generated_tools_have_literal_prowlarr_metadata() -> None:
    tools = _decorated_tools()

    assert len(tools) == 129
    for path, node, decorator in tools:
        keywords = {keyword.arg: keyword.value for keyword in decorator.keywords}
        assert isinstance(keywords["namespace"], ast.Constant), path.name
        assert keywords["namespace"].value == "prowlarr", path.name
        assert isinstance(keywords["description"], ast.Constant), path.name
        assert isinstance(keywords["examples"], ast.List), path.name
        assert isinstance(keywords["aliases"], ast.List), path.name
        assert not path.name.endswith("_test.py")
        assert node.name in path.stem


def test_representative_tools_are_present() -> None:
    tool_names = {node.name for _, node, _ in _decorated_tools()}

    assert "get_ping" in tool_names
    assert "head_ping" in tool_names
    assert "create_indexer" in tool_names
    assert "delete_indexer_by_id" in tool_names
    assert "create_applications" in tool_names
    assert "get_history" in tool_names
    assert "get_system_status" in tool_names
