from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_library as get_library_module


def test_get_library_encodes_id_and_forwards_params(monkeypatch):
    client = Mock()
    client.segment.return_value = "fiction%2Fnew"
    expected = {"id": "fiction/new", "name": "Fiction"}
    client.get.return_value = expected
    monkeypatch.setattr(get_library_module, "get_client", Mock(return_value=client))

    params = {"include": "items"}

    assert get_library_module.get_library("fiction/new", params=params) == expected
    client.segment.assert_called_once_with("fiction/new", name="library_id")
    client.get.assert_called_once_with("libraries/fiction%2Fnew", params=params)
