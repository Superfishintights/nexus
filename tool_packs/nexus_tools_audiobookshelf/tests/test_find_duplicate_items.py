"""Tests for the registered Audiobookshelf duplicate-candidate tool."""

from __future__ import annotations

import inspect
from unittest.mock import Mock

from nexus_tools_audiobookshelf import find_duplicate_items as find_duplicate_items_module


def test_find_duplicate_items_delegates_to_client(monkeypatch):
    client = Mock()
    expected = {"duplicateGroupCount": 1, "groups": []}
    client.find_duplicate_items.return_value = expected
    monkeypatch.setattr(
        find_duplicate_items_module,
        "get_client",
        Mock(return_value=client),
    )
    keys = ("asin", "isbn")

    assert (
        find_duplicate_items_module.find_duplicate_items(
            "library-123", keys=keys, max_items=200, page_size=25
        )
        == expected
    )
    assert list(inspect.signature(find_duplicate_items_module.find_duplicate_items).parameters) == [
        "library_id",
        "keys",
        "max_items",
        "page_size",
    ]
    client.find_duplicate_items.assert_called_once_with(
        "library-123", keys=keys, max_items=200, page_size=25
    )
