"""Tests for the registered Audiobookshelf batch item scan tool."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import batch_scan_items as batch_scan_items_module


def test_batch_scan_items_posts_exact_item_id_list(monkeypatch):
    client = Mock()
    expected = {"success": True}
    client.post.return_value = expected
    monkeypatch.setattr(batch_scan_items_module, "get_client", Mock(return_value=client))

    item_ids = ("item-123", "item-456")

    assert batch_scan_items_module.batch_scan_items(item_ids) == expected
    client.post.assert_called_once_with(
        "items/batch/scan",
        body={"libraryItemIds": ["item-123", "item-456"]},
    )


@pytest.mark.parametrize(
    ("item_ids", "message"),
    [
        ([], "item_ids must contain at least one item ID"),
        (["item-123", ""], "item_ids must not contain blank item IDs"),
        (["item-123", "   "], "item_ids must not contain blank item IDs"),
    ],
)
def test_batch_scan_items_rejects_empty_or_blank_item_ids(item_ids, message):
    with pytest.raises(ValueError, match=message):
        batch_scan_items_module.batch_scan_items(item_ids)
