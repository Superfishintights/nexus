"""Tests for the read-only Audiobookshelf batch item lookup tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import batch_get_items as batch_get_items_module


def test_batch_get_items_is_registered_as_read():
    module_path = Path(batch_get_items_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "batch_get_items"
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

    assert metadata["tool_class"] == "read"
    assert metadata["aliases"] == []


def test_batch_get_items_posts_exact_item_id_list(monkeypatch):
    client = Mock()
    expected = {"items": [{"id": "item-123"}, {"id": "item-456"}]}
    client.post.return_value = expected
    monkeypatch.setattr(batch_get_items_module, "get_client", Mock(return_value=client))

    assert batch_get_items_module.batch_get_items(("item-123", "item-456")) == expected
    assert list(inspect.signature(batch_get_items_module.batch_get_items).parameters) == [
        "item_ids"
    ]
    client.post.assert_called_once_with(
        "items/batch/get",
        body={"libraryItemIds": ["item-123", "item-456"]},
    )


@pytest.mark.parametrize("item_ids", [[], "item-123", [""], ["   "], ["item-123", " "]])
def test_batch_get_items_rejects_empty_or_blank_ids(item_ids):
    with pytest.raises(ValueError):
        batch_get_items_module.batch_get_items(item_ids)
