from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_library_stats as get_library_stats_module


def test_get_library_stats_gets_encoded_library_stats_endpoint(monkeypatch):
    client = Mock()
    expected = {"numItems": 42, "totalDuration": 12345}
    client.segment.return_value = "library%2Fwith%20spaces"
    client.get.return_value = expected
    monkeypatch.setattr(get_library_stats_module, "get_client", Mock(return_value=client))

    assert get_library_stats_module.get_library_stats("library/with spaces") == expected
    client.segment.assert_called_once_with("library/with spaces", name="library_id")
    client.get.assert_called_once_with("libraries/library%2Fwith%20spaces/stats")
