from __future__ import annotations

import ast
from pathlib import Path

import pytest

from . import tools


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def request(self, service, path, *, method="GET", params=None, payload=None):
        call = {
            "service": service,
            "path": path,
            "method": method,
            "params": params,
            "payload": payload,
        }
        self.calls.append(call)
        return {"call": call}


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    fake = FakeClient()
    monkeypatch.setattr(tools, "get_client", lambda: fake)
    return fake


def test_list_tasks_sends_pagination_and_date_filters(fake_client: FakeClient) -> None:
    tools.list_tasks(
        "my/list",
        page_token="next",
        show_completed=False,
        show_deleted=True,
        due_min="2026-07-29T00:00:00Z",
        updated_min="2026-07-28T00:00:00Z",
    )

    call = fake_client.calls[-1]
    assert call["service"] == "tasks"
    assert call["path"] == "lists/my%2Flist/tasks"
    assert call["method"] == "GET"
    assert call["params"]["pageToken"] == "next"
    assert call["params"]["showCompleted"] is False
    assert call["params"]["showDeleted"] is True
    assert call["params"]["dueMin"] == "2026-07-29T00:00:00Z"
    assert call["params"]["updatedMin"] == "2026-07-28T00:00:00Z"


def test_create_task_uses_parent_previous_as_query_params(fake_client: FakeClient) -> None:
    tools.create_task(
        "@default",
        title="Buy milk",
        notes="Semi-skimmed",
        parent="parent/1",
        previous="prev/1",
    )

    call = fake_client.calls[-1]
    assert call["path"] == "lists/%40default/tasks"
    assert call["method"] == "POST"
    assert call["params"] == {"parent": "parent/1", "previous": "prev/1"}
    assert call["payload"] == {"title": "Buy milk", "notes": "Semi-skimmed"}


def test_patch_task_merges_body_and_explicit_fields(fake_client: FakeClient) -> None:
    tools.patch_task(
        "@default",
        "task/1",
        body='{"notes":"old","status":"needsAction"}',
        notes="new",
        status="completed",
        deleted=False,
    )

    call = fake_client.calls[-1]
    assert call["path"] == "lists/%40default/tasks/task%2F1"
    assert call["method"] == "PATCH"
    assert call["payload"] == {
        "notes": "new",
        "status": "completed",
        "deleted": False,
    }


def test_move_task_supports_destination_tasklist(fake_client: FakeClient) -> None:
    tools.move_task(
        "@default",
        "task-1",
        parent="parent-1",
        destination_tasklist="other-list",
    )

    call = fake_client.calls[-1]
    assert call["path"] == "lists/%40default/tasks/task-1/move"
    assert call["method"] == "POST"
    assert call["params"] == {
        "parent": "parent-1",
        "destinationTasklist": "other-list",
    }


def test_update_tasklist_uses_put(fake_client: FakeClient) -> None:
    tools.update_tasklist("list-1", "Renamed")

    call = fake_client.calls[-1]
    assert call["path"] == "users/@me/lists/list-1"
    assert call["method"] == "PUT"
    assert call["payload"] == {"id": "list-1", "title": "Renamed"}


def test_registered_tool_classes_are_security_explicit() -> None:
    expected = {
        "google_tasks.list_tasklists": "read",
        "google_tasks.get_tasklist": "read",
        "google_tasks.create_tasklist": "write",
        "google_tasks.update_tasklist": "write",
        "google_tasks.patch_tasklist": "write",
        "google_tasks.delete_tasklist": "destructive",
        "google_tasks.list_tasks": "read",
        "google_tasks.get_task": "read",
        "google_tasks.create_task": "write",
        "google_tasks.update_task": "write",
        "google_tasks.patch_task": "write",
        "google_tasks.delete_task": "destructive",
        "google_tasks.move_task": "write",
        "google_tasks.clear_completed_tasks": "destructive",
    }

    tree = ast.parse(Path(tools.__file__).read_text(encoding="utf-8"))
    actual = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Name) or decorator.func.id != "register_tool":
                continue
            keywords = {keyword.arg: keyword.value for keyword in decorator.keywords}
            tool_class = keywords.get("tool_class")
            assert isinstance(tool_class, ast.Constant) and isinstance(tool_class.value, str)
            actual[f"google_tasks.{node.name}"] = tool_class.value

    assert actual == expected
