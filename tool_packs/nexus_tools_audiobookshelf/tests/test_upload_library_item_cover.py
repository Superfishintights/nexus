from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import upload_library_item_cover as upload_cover_module


def test_upload_library_item_cover_delegates_to_client(monkeypatch):
    client = Mock()
    expected = {"success": True}
    client.upload_cover.return_value = expected
    monkeypatch.setattr(upload_cover_module, "get_client", Mock(return_value=client))

    assert (
        upload_cover_module.upload_library_item_cover(
            "item-123", "/media/covers/book.jpg"
        )
        == expected
    )
    client.upload_cover.assert_called_once_with("item-123", "/media/covers/book.jpg")


@pytest.mark.parametrize(
    ("item_id", "file_path", "message"),
    [
        ("", "/media/covers/book.jpg", "item_id must be non-empty"),
        ("   ", "/media/covers/book.jpg", "item_id must be non-empty"),
        ("item-123", "", "file_path must be non-empty"),
        ("item-123", "   ", "file_path must be non-empty"),
    ],
)
def test_upload_library_item_cover_rejects_blank_required_arguments(
    item_id, file_path, message
):
    with pytest.raises(ValueError, match=message):
        upload_cover_module.upload_library_item_cover(item_id, file_path)
