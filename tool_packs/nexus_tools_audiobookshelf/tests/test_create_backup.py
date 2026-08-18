"""Tests for the registered Audiobookshelf backup-creation tool."""

from __future__ import annotations

import inspect
from unittest.mock import Mock

from nexus_tools_audiobookshelf import create_backup as create_backup_module


def test_create_backup_posts_to_backups_without_a_body(monkeypatch):
    client = Mock()
    expected = {"filename": "backup.audiobookshelf"}
    client.post.return_value = expected
    monkeypatch.setattr(create_backup_module, "get_client", Mock(return_value=client))

    assert create_backup_module.create_backup() == expected
    assert list(inspect.signature(create_backup_module.create_backup).parameters) == []
    client.post.assert_called_once_with("backups")
