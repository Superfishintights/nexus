from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import delete_user as delete_user_module


def test_delete_user_encodes_id_and_deletes_exact_user(monkeypatch):
    client = Mock()
    expected = {"deleted": True}
    client.segment.return_value = "reader%2Fone"
    client.delete.return_value = expected
    monkeypatch.setattr(delete_user_module, "get_client", Mock(return_value=client))

    assert delete_user_module.delete_user("reader/one") == expected
    client.segment.assert_called_once_with("reader/one", name="user_id")
    client.delete.assert_called_once_with("users/reader%2Fone")
