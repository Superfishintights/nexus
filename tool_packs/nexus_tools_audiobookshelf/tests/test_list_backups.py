from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_backups as list_backups_module


def test_list_backups_delegates_to_backups_endpoint(monkeypatch):
    client = Mock()
    expected = {"backups": [{"id": "backup-1", "filename": "server.audiobookshelf"}]}
    client.get.return_value = expected
    monkeypatch.setattr(list_backups_module, "get_client", Mock(return_value=client))

    assert list_backups_module.list_backups() == expected
    client.get.assert_called_once_with("backups")
