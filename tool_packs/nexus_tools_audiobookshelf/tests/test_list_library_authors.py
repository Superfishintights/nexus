"""Tests for the registered Audiobookshelf library-authors tool."""

from __future__ import annotations

import inspect
from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_library_authors as list_library_authors_module


def test_list_library_authors_encodes_library_id_and_passes_params(monkeypatch):
    client = Mock()
    client.segment.return_value = "library%2Fwith%20space"
    expected = {"results": [], "total": 0}
    client.get.return_value = expected
    monkeypatch.setattr(list_library_authors_module, "get_client", Mock(return_value=client))
    params = {
        "page": 0,
        "limit": 50,
        "sort": "name",
        "filter": "name%3DNeil%20Gaiman",
    }

    assert list_library_authors_module.list_library_authors("library/with space", params) == expected
    assert list(inspect.signature(list_library_authors_module.list_library_authors).parameters) == [
        "library_id",
        "params",
    ]
    client.segment.assert_called_once_with("library/with space", name="library_id")
    client.get.assert_called_once_with("libraries/library%2Fwith%20space/authors", params=params)
