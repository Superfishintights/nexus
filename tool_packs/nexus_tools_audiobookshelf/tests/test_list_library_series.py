"""Tests for the registered Audiobookshelf library-series tool."""

from __future__ import annotations

import inspect
from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_library_series as list_library_series_module


def test_list_library_series_encodes_library_id_and_passes_params(monkeypatch):
    client = Mock()
    client.segment.return_value = "library%2Fwith%20space"
    expected = {"results": [], "total": 0}
    client.get.return_value = expected
    monkeypatch.setattr(list_library_series_module, "get_client", Mock(return_value=client))
    params = {
        "page": 0,
        "limit": 50,
        "filter": "name%3DDiscworld",
        "sort": "name",
        "include": "books",
    }

    assert list_library_series_module.list_library_series("library/with space", params) == expected
    assert list(inspect.signature(list_library_series_module.list_library_series).parameters) == [
        "library_id",
        "params",
    ]
    client.segment.assert_called_once_with("library/with space", name="library_id")
    client.get.assert_called_once_with("libraries/library%2Fwith%20space/series", params=params)
