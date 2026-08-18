from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import search_books as search_books_module


def test_search_books_delegates_optional_filters(monkeypatch):
    client = Mock()
    expected = {"books": [{"title": "The Sandman"}]}
    client.get.return_value = expected
    monkeypatch.setattr(search_books_module, "get_client", Mock(return_value=client))

    assert (
        search_books_module.search_books(
            "The Sandman",
            author="Neil Gaiman",
            provider="google",
        )
        == expected
    )
    client.get.assert_called_once_with(
        "search/books",
        params={"title": "The Sandman", "author": "Neil Gaiman", "provider": "google"},
    )


@pytest.mark.parametrize("title", ["", "   "])
def test_search_books_rejects_blank_title(title):
    with pytest.raises(ValueError, match="title must be non-empty"):
        search_books_module.search_books(title)
