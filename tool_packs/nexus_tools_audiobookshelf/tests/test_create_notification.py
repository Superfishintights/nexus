"""Tests for the registered Audiobookshelf notification-creation tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import create_notification as create_notification_module


def test_create_notification_has_exact_admin_metadata():
    module_path = Path(create_notification_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_notification"
    )
    decorator = next(
        decorator
        for decorator in function.decorator_list
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "register_tool"
    )
    metadata = {
        keyword.arg: ast.literal_eval(keyword.value) for keyword in decorator.keywords
    }

    assert metadata["namespace"] == "audiobookshelf"
    assert metadata["tool_class"] == "admin"
    assert metadata["aliases"] == []


def test_create_notification_posts_exact_definition(monkeypatch):
    client = Mock()
    expected = {"id": "notification-123", "eventName": "onItemAdded"}
    client.post.return_value = expected
    monkeypatch.setattr(
        create_notification_module, "get_client", Mock(return_value=client)
    )
    notification = {
        "eventName": "onItemAdded",
        "urls": ["https://notify.example.com/audiobookshelf"],
        "titleTemplate": "New audiobook added",
        "bodyTemplate": "{{title}} is now available.",
    }

    assert create_notification_module.create_notification(notification) == expected
    assert list(inspect.signature(create_notification_module.create_notification).parameters) == [
        "notification"
    ]
    client.post.assert_called_once_with("notifications", body=notification)


@pytest.mark.parametrize(
    "notification",
    [
        None,
        {},
        [],
        {"eventName": "onItemAdded"},
        {"eventName": "", "urls": ["https://notify.example.com"], "titleTemplate": "Title", "bodyTemplate": "Body"},
        {"eventName": "   ", "urls": ["https://notify.example.com"], "titleTemplate": "Title", "bodyTemplate": "Body"},
        {"eventName": "onItemAdded", "urls": [], "titleTemplate": "Title", "bodyTemplate": "Body"},
        {"eventName": "onItemAdded", "urls": [""], "titleTemplate": "Title", "bodyTemplate": "Body"},
        {"eventName": "onItemAdded", "urls": ["   "], "titleTemplate": "Title", "bodyTemplate": "Body"},
        {"eventName": "onItemAdded", "urls": [123], "titleTemplate": "Title", "bodyTemplate": "Body"},
        {"eventName": "onItemAdded", "urls": "https://notify.example.com", "titleTemplate": "Title", "bodyTemplate": "Body"},
        {"eventName": "onItemAdded", "urls": ["https://notify.example.com"], "titleTemplate": "", "bodyTemplate": "Body"},
        {"eventName": "onItemAdded", "urls": ["https://notify.example.com"], "titleTemplate": "Title", "bodyTemplate": "   "},
    ],
)
def test_create_notification_rejects_invalid_definitions(notification):
    with pytest.raises(ValueError):
        create_notification_module.create_notification(notification)
