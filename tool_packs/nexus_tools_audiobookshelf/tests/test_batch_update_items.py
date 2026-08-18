"""Tests for the registered Audiobookshelf batch item-update tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import batch_update_items as batch_update_items_module


def test_batch_update_items_is_registered_as_write_tool():
    module_path = Path(batch_update_items_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "batch_update_items"
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

    assert metadata["tool_class"] == "write"
    assert metadata["aliases"] == []
    assert metadata["examples"]


def test_batch_update_items_posts_exact_update_list(monkeypatch):
    client = Mock()
    expected = {"updated": 2}
    client.post.return_value = expected
    monkeypatch.setattr(
        batch_update_items_module, "get_client", Mock(return_value=client)
    )
    updates = (
        {"id": "item-123", "mediaPayload": {"metadata": {"title": "One"}}},
        {"id": "item-456", "mediaPayload": {"tags": ["fiction"]}},
    )

    assert batch_update_items_module.batch_update_items(updates) == expected
    assert list(inspect.signature(batch_update_items_module.batch_update_items).parameters) == [
        "updates"
    ]
    client.post.assert_called_once_with("items/batch/update", body=list(updates))


@pytest.mark.parametrize(
    "updates",
    [
        [],
        "item-123",
        [{}],
        [{"id": "", "mediaPayload": {}}],
        [{"id": "   ", "mediaPayload": {}}],
        [{"id": "item-123", "mediaPayload": []}],
    ],
)
def test_batch_update_items_rejects_invalid_updates(updates):
    with pytest.raises(ValueError):
        batch_update_items_module.batch_update_items(updates)


def test_batch_update_items_rejects_duplicate_item_ids():
    updates = [
        {"id": "item-123", "mediaPayload": {}},
        {"id": "item-123", "mediaPayload": {"metadata": {}}},
    ]

    with pytest.raises(ValueError, match="duplicate"):
        batch_update_items_module.batch_update_items(updates)
