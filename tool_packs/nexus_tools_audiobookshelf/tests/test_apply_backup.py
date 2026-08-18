from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import apply_backup as apply_backup_module


def test_apply_backup_encodes_id_and_calls_mutating_get(monkeypatch):
    client = Mock()
    expected = {"applied": True}
    client.segment.return_value = "backup%2Fbefore-upgrade"
    client.get.return_value = expected
    monkeypatch.setattr(apply_backup_module, "get_client", Mock(return_value=client))

    assert apply_backup_module.apply_backup("backup/before-upgrade") == expected
    client.segment.assert_called_once_with("backup/before-upgrade", name="backup_id")
    client.get.assert_called_once_with("backups/backup%2Fbefore-upgrade/apply")
