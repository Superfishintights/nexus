from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_series as get_series_module


def test_get_series_encodes_id_and_forwards_params(monkeypatch):
    client = Mock()
    client.segment.return_value = "series%2Fid"
    expected = {"id": "series/id", "name": "Example Series"}
    client.get.return_value = expected
    monkeypatch.setattr(get_series_module, "get_client", Mock(return_value=client))

    params = {"include": "books"}

    assert get_series_module.get_series("series/id", params=params) == expected
    client.segment.assert_called_once_with("series/id", name="series_id")
    client.get.assert_called_once_with("series/series%2Fid", params=params)
