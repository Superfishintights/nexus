from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import remove_library_item_cover as remove_library_item_cover_module


def test_remove_library_item_cover_encodes_id_and_delegates_delete(monkeypatch):
    client = Mock()
    expected = {"removed": True}
    client.segment.return_value = "item%2Fid"
    client.delete.return_value = expected
    monkeypatch.setattr(remove_library_item_cover_module, "get_client", Mock(return_value=client))

    assert remove_library_item_cover_module.remove_library_item_cover("item/id") == expected
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.delete.assert_called_once_with("items/item%2Fid/cover")
