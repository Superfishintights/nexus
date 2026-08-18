from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import get_me as get_me_module


def test_get_me_delegates_to_authenticated_me_endpoint(monkeypatch):
    client = Mock()
    expected = {"id": "user-1", "username": "listener"}
    client.get.return_value = expected
    monkeypatch.setattr(get_me_module, "get_client", Mock(return_value=client))

    assert get_me_module.get_me() == expected
    client.get.assert_called_once_with("me")
