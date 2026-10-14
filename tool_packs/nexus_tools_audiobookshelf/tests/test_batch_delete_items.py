"""Tests for the registered Audiobookshelf batch item delete tool."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import batch_delete_items as batch_delete_items_module


@pytest.mark.parametrize(
    ("hard_delete", "hard_parameter"),
    [(False, 0), (True, 1)],
)
def test_batch_delete_items_posts_exact_item_id_list_and_hard_parameter(
    monkeypatch, hard_delete, hard_parameter
):
    client = Mock()
    expected = {"success": True}
    client.post.return_value = expected
    monkeypatch.setattr(batch_delete_items_module, "get_client", Mock(return_value=client))

    item_ids = ("item-123", "item-456")

    assert batch_delete_items_module.batch_delete_items(item_ids, hard_delete=hard_delete) == expected
    client.post.assert_called_once_with(
        "items/batch/delete",
        body={"libraryItemIds": ["item-123", "item-456"]},
        params={"hard": hard_parameter},
    )


@pytest.mark.parametrize(
    ("item_ids", "message"),
    [
        ([], "item_ids must contain at least one item ID"),
        (["item-123", ""], "item_ids must not contain blank item IDs"),
        (["item-123", "   "], "item_ids must not contain blank item IDs"),
    ],
)
def test_batch_delete_items_rejects_empty_or_blank_item_ids(item_ids, message):
    with pytest.raises(ValueError, match=message):
        batch_delete_items_module.batch_delete_items(item_ids)
