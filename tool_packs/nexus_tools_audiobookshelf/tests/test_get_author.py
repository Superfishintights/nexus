from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_author as get_author_module


def test_get_author_encodes_id_and_forwards_params(monkeypatch):
    client = Mock()
    client.segment.return_value = "author%2Fid"
    expected = {"id": "author/id", "name": "Example Author"}
    client.get.return_value = expected
    monkeypatch.setattr(get_author_module, "get_client", Mock(return_value=client))

    params = {"include": "items"}

    assert get_author_module.get_author("author/id", params=params) == expected
    client.segment.assert_called_once_with("author/id", name="author_id")
    client.get.assert_called_once_with("authors/author%2Fid", params=params)
