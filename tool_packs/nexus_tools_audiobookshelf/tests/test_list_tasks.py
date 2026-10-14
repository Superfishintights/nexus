from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_tasks as list_tasks_module


def test_list_tasks_delegates_to_tasks_endpoint(monkeypatch):
    client = Mock()
    expected = {"tasks": [{"id": "task-1", "status": "running"}]}
    client.get.return_value = expected
    monkeypatch.setattr(list_tasks_module, "get_client", Mock(return_value=client))

    assert list_tasks_module.list_tasks() == expected
    client.get.assert_called_once_with("tasks")
