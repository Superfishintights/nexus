from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import update_library_item_media as update_library_item_media_module


def test_update_library_item_media_encodes_id_and_patches_payload(monkeypatch):
    client = Mock()
    media_payload = {"metadata": {"title": "The Sandman"}, "tags": ["fantasy"]}
    expected = {"id": "item/id", "media": media_payload}
    client.segment.return_value = "item%2Fid"
    client.patch.return_value = expected
    monkeypatch.setattr(update_library_item_media_module, "get_client", Mock(return_value=client))

    assert update_library_item_media_module.update_library_item_media("item/id", media_payload) == expected
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.patch.assert_called_once_with("items/item%2Fid/media", body=media_payload)


@pytest.mark.parametrize("media_payload", [{}, [], None])
def test_update_library_item_media_rejects_empty_or_non_dict_payload(media_payload):
    with pytest.raises(ValueError, match="media_payload must be a non-empty dictionary"):
        update_library_item_media_module.update_library_item_media("item-123", media_payload)
