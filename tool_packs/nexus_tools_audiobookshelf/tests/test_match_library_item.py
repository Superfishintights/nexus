"""Tests for the Audiobookshelf library-item match tool."""

from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import match_library_item as match_library_item_module


def test_match_library_item_encodes_id_and_posts_options(monkeypatch):
    client = Mock()
    expected = {"matched": True}
    options = {"provider": "google", "title": "A Book"}
    client.segment.return_value = "item%2Fid"
    client.post.return_value = expected
    monkeypatch.setattr(
        match_library_item_module, "get_client", Mock(return_value=client)
    )

    assert match_library_item_module.match_library_item("item/id", options) == expected
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.post.assert_called_once_with("items/item%2Fid/match", body=options)


def test_match_library_item_posts_empty_options_by_default(monkeypatch):
    client = Mock()
    client.segment.return_value = "item-123"
    monkeypatch.setattr(
        match_library_item_module, "get_client", Mock(return_value=client)
    )

    match_library_item_module.match_library_item("item-123")

    client.post.assert_called_once_with("items/item-123/match", body={})
