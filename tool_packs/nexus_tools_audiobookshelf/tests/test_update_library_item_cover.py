from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import update_library_item_cover as update_library_item_cover_module


def test_update_library_item_cover_delegates_to_patch(monkeypatch):
    client = Mock()
    client.segment.return_value = "item%2F1"
    expected = {"success": True}
    client.patch.return_value = expected
    monkeypatch.setattr(update_library_item_cover_module, "get_client", Mock(return_value=client))

    assert update_library_item_cover_module.update_library_item_cover("item/1", "/covers/item.jpg") == expected
    client.segment.assert_called_once_with("item/1", name="item_id")
    client.patch.assert_called_once_with(
        "items/item%2F1/cover",
        body={"cover": "/covers/item.jpg"},
    )


@pytest.mark.parametrize("item_id", ["", "   "])
def test_update_library_item_cover_rejects_blank_item_id(item_id):
    with pytest.raises(ValueError, match="item_id must be non-empty"):
        update_library_item_cover_module.update_library_item_cover(item_id, "/covers/item.jpg")


@pytest.mark.parametrize("server_cover_path", ["", "   "])
def test_update_library_item_cover_rejects_blank_server_cover_path(server_cover_path):
    with pytest.raises(ValueError, match="server_cover_path must be non-empty"):
        update_library_item_cover_module.update_library_item_cover("item-1", server_cover_path)
