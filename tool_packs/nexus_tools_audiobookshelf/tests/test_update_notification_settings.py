"""Tests for the Audiobookshelf notification-settings update tool."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import (
    update_notification_settings as update_notification_settings_module,
)


def test_update_notification_settings_has_required_metadata_and_warning():
    module_path = Path(update_notification_settings_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "update_notification_settings"
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
    assert "admin-wide" in metadata["description"]
    assert "connector URL" in metadata["description"]


def test_update_notification_settings_patches_exact_body(monkeypatch):
    client = Mock()
    settings = {
        "apprise": {"enabled": True, "urls": ["ntfy://alerts"]},
        "webhooks": {"enabled": False},
    }
    expected = {"settings": settings}
    client.patch.return_value = expected
    monkeypatch.setattr(
        update_notification_settings_module, "get_client", Mock(return_value=client)
    )

    assert update_notification_settings_module.update_notification_settings(settings) == expected
    client.patch.assert_called_once_with("notifications", body=settings)


@pytest.mark.parametrize("settings", [{}, [], None])
def test_update_notification_settings_rejects_empty_or_non_dict_settings(settings):
    with pytest.raises(ValueError, match="settings must be a non-empty dictionary"):
        update_notification_settings_module.update_notification_settings(settings)
