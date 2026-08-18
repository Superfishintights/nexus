from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import update_series as update_series_module


def test_update_series_encodes_id_and_patches_updates(monkeypatch):
    client = Mock()
    updates = {"name": "The Sandman", "description": "A dark fantasy series."}
    expected = {"id": "series/id", **updates}
    client.segment.return_value = "series%2Fid"
    client.patch.return_value = expected
    monkeypatch.setattr(update_series_module, "get_client", Mock(return_value=client))

    assert update_series_module.update_series("series/id", updates) == expected
    client.segment.assert_called_once_with("series/id", name="series_id")
    client.patch.assert_called_once_with("series/series%2Fid", body=updates)


@pytest.mark.parametrize("updates", [{}, [], None])
def test_update_series_rejects_empty_or_non_dict_updates(updates):
    with pytest.raises(ValueError, match="updates must be a non-empty dictionary"):
        update_series_module.update_series("series-123", updates)
