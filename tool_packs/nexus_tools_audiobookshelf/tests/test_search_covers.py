from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import search_covers as search_covers_module


def test_search_covers_delegates_all_query_parameters(monkeypatch):
    client = Mock()
    expected = [{"url": "https://covers.example/the-left-hand-of-darkness.jpg"}]
    client.get.return_value = expected
    monkeypatch.setattr(search_covers_module, "get_client", Mock(return_value=client))

    assert (
        search_covers_module.search_covers(
            "The Left Hand of Darkness",
            author="Ursula K. Le Guin",
            provider="google",
            podcast=True,
        )
        == expected
    )
    client.get.assert_called_once_with(
        "search/covers",
        params={
            "title": "The Left Hand of Darkness",
            "author": "Ursula K. Le Guin",
            "provider": "google",
            "podcast": True,
        },
    )


@pytest.mark.parametrize("title", ["", "   "])
def test_search_covers_rejects_blank_title(title):
    with pytest.raises(ValueError, match="title must be non-empty"):
        search_covers_module.search_covers(title)
