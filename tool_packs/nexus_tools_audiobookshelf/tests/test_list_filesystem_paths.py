from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_filesystem_paths as filesystem_module


def test_list_filesystem_paths_delegates_to_filesystem_endpoint(monkeypatch):
    client = Mock()
    expected = {"paths": ["/audiobooks", "/podcasts"]}
    client.get.return_value = expected
    monkeypatch.setattr(filesystem_module, "get_client", Mock(return_value=client))

    assert filesystem_module.list_filesystem_paths() == expected
    client.get.assert_called_once_with("filesystem")
