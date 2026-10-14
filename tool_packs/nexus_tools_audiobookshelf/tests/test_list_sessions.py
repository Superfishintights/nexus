from __future__ import annotations

import pytest
from unittest.mock import Mock

from nexus_tools_audiobookshelf import list_sessions as list_sessions_module


def test_list_sessions_delegates_to_sessions_endpoint_with_params(monkeypatch):
    client = Mock()
    expected = {"sessions": [{"id": "session-1", "userId": "user-1"}]}
    client.get.return_value = expected
    monkeypatch.setattr(list_sessions_module, "get_client", Mock(return_value=client))

    params = {"include": "user"}

    assert list_sessions_module.list_sessions(params=params) == expected
    client.get.assert_called_once_with("sessions", params=params)


def test_list_sessions_rejects_non_dictionary_params():
    with pytest.raises(ValueError, match="params must be a dictionary when supplied"):
        list_sessions_module.list_sessions(params=["include=user"])
