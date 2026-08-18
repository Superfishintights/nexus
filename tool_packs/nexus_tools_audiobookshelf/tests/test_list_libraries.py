from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_libraries as list_libraries_module


def test_list_libraries_delegates_optional_query_params(monkeypatch):
    client = Mock()
    expected = {"libraries": [{"id": "library-1", "name": "Audiobooks"}]}
    params = {"include": "stats"}
    client.get.return_value = expected
    monkeypatch.setattr(list_libraries_module, "get_client", Mock(return_value=client))

    assert list_libraries_module.list_libraries(params) == expected
    client.get.assert_called_once_with("libraries", params=params)
