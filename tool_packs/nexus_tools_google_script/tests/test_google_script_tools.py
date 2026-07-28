from __future__ import annotations

import ast
from pathlib import Path

import pytest

from nexus_tools_google_script import api


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def request(self, service, path, *, method="GET", params=None, payload=None):
        self.calls.append((service, path, method, params, payload))
        return {"service": service, "path": path, "method": method, "params": params, "payload": payload}


@pytest.fixture()
def fake_client(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr("nexus_tools_google_script.client.get_client", lambda: client)
    return client


def test_create_project_uses_script_service(fake_client):
    result = api.create_project("Automation", parent_id="drive file")
    assert result["service"] == "script"
    assert result["path"] == "projects"
    assert result["method"] == "POST"
    assert result["payload"] == {"title": "Automation", "parentId": "drive file"}


def test_update_content_requires_file_array(fake_client):
    with pytest.raises(ValueError):
        api.update_content("script", {"not": "a list"})


def test_run_function_requires_parameter_array(fake_client):
    with pytest.raises(ValueError):
        api.run_function("script", "main", parameters={"bad": True})


def test_get_metrics_passes_filter(fake_client):
    result = api.get_metrics("script/with space", metrics_filter="activeUsers", granularity="daily")
    assert result["path"] == "projects/script%2Fwith%20space/metrics"
    assert result["params"]["metricsFilter"] == "activeUsers"
    assert result["params"]["metricsGranularity"] == "daily"


def test_all_tools_have_explicit_literal_tool_class():
    source = Path(api.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    tools = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (isinstance(func, ast.Name) and func.id == "register_tool"):
                continue
            metadata = {keyword.arg: keyword.value for keyword in decorator.keywords}
            tools[node.name] = metadata

    assert tools
    assert all("tool_class" in metadata for metadata in tools.values())
    assert all(isinstance(metadata["tool_class"], ast.Constant) for metadata in tools.values())
    assert all(isinstance(metadata["tool_class"].value, str) for metadata in tools.values())


def test_tool_classifications_are_security_accurate():
    source = Path(api.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    actual = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (isinstance(func, ast.Name) and func.id == "register_tool"):
                continue
            for keyword in decorator.keywords:
                if keyword.arg == "tool_class":
                    actual[node.name] = keyword.value.value

    expected = {
        "create_project": "write",
        "get_project": "read",
        "get_content": "read",
        "update_content": "write",
        "create_version": "write",
        "list_versions": "read",
        "create_deployment": "write",
        "list_deployments": "read",
        "get_deployment": "read",
        "update_deployment": "write",
        "delete_deployment": "destructive",
        "run_function": "admin",
        "list_processes": "read",
        "list_script_processes": "read",
        "get_metrics": "read",
    }
    assert actual == expected
