"""Tests for the Audiobookshelf author-match tool."""

from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import match_author as match_author_module


def test_match_author_encodes_id_and_posts_options(monkeypatch):
    client = Mock()
    expected = {"matched": True}
    options = {"provider": "audible", "name": "An Author"}
    client.segment.return_value = "author%2Fid"
    client.post.return_value = expected
    monkeypatch.setattr(match_author_module, "get_client", Mock(return_value=client))

    assert match_author_module.match_author("author/id", options) == expected
    client.segment.assert_called_once_with("author/id", name="author_id")
    client.post.assert_called_once_with("authors/author%2Fid/match", body=options)


def test_match_author_posts_empty_options_by_default(monkeypatch):
    client = Mock()
    client.segment.return_value = "author-123"
    monkeypatch.setattr(match_author_module, "get_client", Mock(return_value=client))

    match_author_module.match_author("author-123")

    client.post.assert_called_once_with("authors/author-123/match", body={})
