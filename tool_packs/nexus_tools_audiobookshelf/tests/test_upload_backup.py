from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import upload_backup as upload_backup_module


def test_upload_backup_delegates_to_client(monkeypatch):
    client = Mock()
    expected = {"success": True}
    client.upload_backup.return_value = expected
    monkeypatch.setattr(upload_backup_module, "get_client", Mock(return_value=client))

    assert (
        upload_backup_module.upload_backup("/backups/server-backup.audiobookshelf")
        == expected
    )
    client.upload_backup.assert_called_once_with("/backups/server-backup.audiobookshelf")


@pytest.mark.parametrize("file_path", ["", "   "])
def test_upload_backup_rejects_blank_file_path(file_path):
    with pytest.raises(ValueError, match="file_path must be non-empty"):
        upload_backup_module.upload_backup(file_path)
