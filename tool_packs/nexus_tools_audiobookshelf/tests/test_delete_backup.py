from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import delete_backup as delete_backup_module


def test_delete_backup_encodes_id_and_deletes_exact_backup(monkeypatch):
    client = Mock()
    expected = {"deleted": True}
    client.segment.return_value = "backup%2Fbefore-upgrade"
    client.delete.return_value = expected
    monkeypatch.setattr(delete_backup_module, "get_client", Mock(return_value=client))

    assert delete_backup_module.delete_backup("backup/before-upgrade") == expected
    client.segment.assert_called_once_with("backup/before-upgrade", name="backup_id")
    client.delete.assert_called_once_with("backups/backup%2Fbefore-upgrade")
