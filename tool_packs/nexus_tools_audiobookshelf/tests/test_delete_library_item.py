from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import delete_library_item as delete_library_item_module


def test_delete_library_item_defaults_to_database_only(monkeypatch):
    client = Mock()
    expected = {"deleted": True}
    client.segment.return_value = "item%2Fid"
    client.delete.return_value = expected
    monkeypatch.setattr(delete_library_item_module, "get_client", Mock(return_value=client))

    assert delete_library_item_module.delete_library_item("item/id") == expected
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.delete.assert_called_once_with("items/item%2Fid", params={"hard": 0})


def test_delete_library_item_hard_deletes_filesystem_media(monkeypatch):
    client = Mock()
    expected = {"deleted": True}
    client.segment.return_value = "item%2Fid"
    client.delete.return_value = expected
    monkeypatch.setattr(delete_library_item_module, "get_client", Mock(return_value=client))

    assert delete_library_item_module.delete_library_item("item/id", hard_delete=True) == expected
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.delete.assert_called_once_with("items/item%2Fid", params={"hard": 1})
