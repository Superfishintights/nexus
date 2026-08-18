from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import search_authors as search_authors_module


def test_search_authors_delegates_query(monkeypatch):
    client = Mock()
    expected = {"authors": [{"name": "Octavia E. Butler"}]}
    client.get.return_value = expected
    monkeypatch.setattr(search_authors_module, "get_client", Mock(return_value=client))

    assert search_authors_module.search_authors("Octavia E. Butler") == expected
    client.get.assert_called_once_with("search/authors", params={"q": "Octavia E. Butler"})


@pytest.mark.parametrize("query", ["", "   "])
def test_search_authors_rejects_blank_query(query):
    with pytest.raises(ValueError, match="query must be non-empty"):
        search_authors_module.search_authors(query)
