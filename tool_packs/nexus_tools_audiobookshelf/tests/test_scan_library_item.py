from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import scan_library_item as scan_library_item_module


def test_scan_library_item_encodes_id_and_delegates_post(monkeypatch):
    client = Mock()
    expected = {"scanned": True}
    client.segment.return_value = "item%2Fid"
    client.post.return_value = expected
    monkeypatch.setattr(scan_library_item_module, "get_client", Mock(return_value=client))

    assert scan_library_item_module.scan_library_item("item/id") == expected
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.post.assert_called_once_with("items/item%2Fid/scan")
