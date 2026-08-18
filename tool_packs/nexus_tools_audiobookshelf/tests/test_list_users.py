from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_users as list_users_module


def test_list_users_delegates_to_users_endpoint(monkeypatch):
    client = Mock()
    expected = {"users": [{"id": "user-1", "username": "reader"}]}
    client.get.return_value = expected
    monkeypatch.setattr(list_users_module, "get_client", Mock(return_value=client))

    assert list_users_module.list_users() == expected
    client.get.assert_called_once_with("users")
