from __future__ import annotations

import ast
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PACK_ROOT / "nexus_tools_nzbget"


DOCUMENTED_METHODS = {
    "version",
    "shutdown",
    "reload",
    "listgroups",
    "listfiles",
    "history",
    "append",
    "editqueue",
    "scan",
    "status",
    "sysinfo",
    "systemhealth",
    "log",
    "writelog",
    "loadlog",
    "logscript",
    "logupdate",
    "servervolumes",
    "resetservervolume",
    "rate",
    "pausedownload",
    "resumedownload",
    "pausepost",
    "resumepost",
    "pausescan",
    "resumescan",
    "scheduleresume",
    "config",
    "loadconfig",
    "saveconfig",
    "configtemplates",
    "loadextensions",
    "downloadextension",
    "updateextension",
    "deleteextension",
    "testextension",
    "testserver",
    "testserverspeed",
    "testdiskspeed",
    "testnetworkspeed",
}


def _register_tool_decorators() -> dict[str, ast.Call]:
    decorators: dict[str, ast.Call] = {}
    for path in PACKAGE_ROOT.glob("*.py"):
        if path.name in {"__init__.py", "client.py"}:
            continue
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in module.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and getattr(decorator.func, "id", "") == "register_tool":
                    decorators[node.name] = decorator
    return decorators


def test_all_documented_methods_have_registered_tools() -> None:
    decorators = _register_tool_decorators()

    assert DOCUMENTED_METHODS <= decorators.keys()


def test_register_tool_metadata_is_literal_and_namespaced() -> None:
    decorators = _register_tool_decorators()
    assert decorators

    for function_name, decorator in decorators.items():
        keywords = {keyword.arg: keyword.value for keyword in decorator.keywords}
        assert isinstance(keywords["namespace"], ast.Constant), function_name
        assert keywords["namespace"].value == "nzbget", function_name
        assert isinstance(keywords["description"], ast.Constant), function_name
        assert isinstance(keywords["description"].value, str), function_name
        assert isinstance(keywords["examples"], ast.List), function_name
        for example in keywords["examples"].elts:
            assert isinstance(example, ast.Constant), function_name
            assert isinstance(example.value, str), function_name
