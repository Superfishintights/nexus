from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import search_library as search_library_module


def test_search_library_encodes_identifier_and_delegates_query(monkeypatch):
    client = Mock()
    client.segment.return_value = "library%2Ffiction"
    expected = {"book": [], "podcast": []}
    client.get.return_value = expected
    monkeypatch.setattr(search_library_module, "get_client", Mock(return_value=client))

    assert search_library_module.search_library("library/fiction", "The Sandman") == expected
    client.segment.assert_called_once_with("library/fiction", name="library_id")
    client.get.assert_called_once_with(
        "libraries/library%2Ffiction/search",
        params={"q": "The Sandman", "limit": None},
    )


@pytest.mark.parametrize("query", ["", "   "])
def test_search_library_rejects_empty_query(query):
    with pytest.raises(ValueError, match="query must be non-empty"):
        search_library_module.search_library("library-1", query)
