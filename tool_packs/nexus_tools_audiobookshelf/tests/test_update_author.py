from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import update_author as update_author_module


def test_update_author_encodes_id_and_patches_updates(monkeypatch):
    client = Mock()
    updates = {"name": "Ursula K. Le Guin", "description": "Author"}
    expected = {"id": "author/id", **updates}
    client.segment.return_value = "author%2Fid"
    client.patch.return_value = expected
    monkeypatch.setattr(update_author_module, "get_client", Mock(return_value=client))

    assert update_author_module.update_author("author/id", updates) == expected
    client.segment.assert_called_once_with("author/id", name="author_id")
    client.patch.assert_called_once_with("authors/author%2Fid", body=updates)


@pytest.mark.parametrize("updates", [{}, [], None])
def test_update_author_rejects_empty_or_non_dict_updates(updates):
    with pytest.raises(ValueError, match="updates must be a non-empty dictionary"):
        update_author_module.update_author("author-123", updates)
