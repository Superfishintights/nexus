"""Tests for the Audiobookshelf batch quick-match tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import (
    batch_quick_match_items as batch_quick_match_items_module,
)


def test_batch_quick_match_items_is_registered_as_admin():
    module_path = Path(batch_quick_match_items_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "batch_quick_match_items"
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


def test_batch_quick_match_items_posts_exact_body(monkeypatch):
    client = Mock()
    expected = {"matched": 2}
    client.post.return_value = expected
    monkeypatch.setattr(
        batch_quick_match_items_module,
        "get_client",
        Mock(return_value=client),
    )
    options = {"provider": "google", "overrideCover": True, "overrideDetails": False}

    assert (
        batch_quick_match_items_module.batch_quick_match_items(
            ["item-123", "item-456"], options
        )
        == expected
    )
    assert list(
        inspect.signature(
            batch_quick_match_items_module.batch_quick_match_items
        ).parameters
    ) == ["item_ids", "options"]
    client.post.assert_called_once_with(
        "items/batch/quickmatch",
        body={"libraryItemIds": ["item-123", "item-456"], "options": options},
    )


def test_batch_quick_match_items_posts_empty_options_by_default(monkeypatch):
    client = Mock()
    monkeypatch.setattr(
        batch_quick_match_items_module,
        "get_client",
        Mock(return_value=client),
    )

    batch_quick_match_items_module.batch_quick_match_items(["item-123"])

    client.post.assert_called_once_with(
        "items/batch/quickmatch",
        body={"libraryItemIds": ["item-123"], "options": {}},
    )


@pytest.mark.parametrize("item_ids", [[], [""], ["   "], ["item-123", " "]])
def test_batch_quick_match_items_rejects_empty_or_blank_ids(item_ids):
    with pytest.raises(ValueError):
        batch_quick_match_items_module.batch_quick_match_items(item_ids)
