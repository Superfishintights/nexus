from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_library_filter_data as get_library_filter_data_module


def test_get_library_filter_data_encodes_library_id_and_delegates(monkeypatch):
    client = Mock()
    client.segment.return_value = "library%2Fabc"
    expected = {"authors": [], "genres": []}
    client.get.return_value = expected
    monkeypatch.setattr(get_library_filter_data_module, "get_client", Mock(return_value=client))

    assert get_library_filter_data_module.get_library_filter_data("library/abc") == expected
    client.segment.assert_called_once_with("library/abc", name="library_id")
    client.get.assert_called_once_with("libraries/library%2Fabc/filterdata")
