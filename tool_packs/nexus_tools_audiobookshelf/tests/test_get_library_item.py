from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_library_item as get_library_item_module


def test_get_library_item_encodes_id_and_delegates_optional_query_params(monkeypatch):
    client = Mock()
    expected = {"id": "item/id", "media": {"expanded": True}}
    params = {"include": "progress", "expanded": True}
    client.segment.return_value = "item%2Fid"
    client.get.return_value = expected
    monkeypatch.setattr(get_library_item_module, "get_client", Mock(return_value=client))

    assert get_library_item_module.get_library_item("item/id", params) == expected
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.get.assert_called_once_with("items/item%2Fid", params=params)
