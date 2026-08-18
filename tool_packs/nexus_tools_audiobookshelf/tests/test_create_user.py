"""Tests for the registered Audiobookshelf user-creation tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import create_user as create_user_module


def test_create_user_has_admin_metadata_and_redaction_notice():
    module_path = Path(create_user_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_user"
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

    assert metadata["tool_class"] == "admin"
    assert metadata["aliases"] == []
    assert all(
        term in metadata["description"].lower()
        for term in ("type", "permissions", "library", "tag", "token", "redacted")
    )


def test_create_user_posts_exact_user_definition(monkeypatch):
    client = Mock()
    expected = {"id": "user-123", "username": "reader"}
    client.post.return_value = expected
    monkeypatch.setattr(create_user_module, "get_client", Mock(return_value=client))
    user = {
        "username": "reader",
        "password": "not-a-real-secret",
        "type": "user",
        "permissions": {"download": True},
        "librariesAccessible": ["library-123"],
        "tagsAccessible": ["tag-123"],
    }

    assert create_user_module.create_user(user) == expected
    assert list(inspect.signature(create_user_module.create_user).parameters) == ["user"]
    client.post.assert_called_once_with("users", body=user)


@pytest.mark.parametrize(
    "user",
    [
        None,
        {},
        [],
        {"username": "reader"},
        {"username": "", "password": "password"},
        {"username": "   ", "password": "password"},
        {"username": "reader", "password": None},
        {"username": "reader", "password": 123},
        {"username": "reader", "password": ""},
        {"username": "reader", "password": "password", "permissions": []},
    ],
)
def test_create_user_rejects_invalid_definitions(user):
    with pytest.raises(ValueError):
        create_user_module.create_user(user)
