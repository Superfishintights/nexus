"""Notification configuration checks without sending network requests."""

from unittest.mock import Mock

import pytest

from nexus.test_helpers import add_tool_pack_paths

add_tool_pack_paths(("nexus_tools_playtomic",))

from nexus_tools_playtomic import client


def test_unconfigured_topic_rejects_without_sending(monkeypatch):
    monkeypatch.delenv("PLAYTOMIC_NTFY_TOPIC", raising=False)
    send = Mock()
    monkeypatch.setattr(client.requests, "post", send)

    with pytest.raises(ValueError, match="PLAYTOMIC_NTFY_TOPIC is required"):
        client.notify("Available court")

    send.assert_not_called()


def test_configured_topic_receives_message_and_title(monkeypatch):
    monkeypatch.setenv("PLAYTOMIC_NTFY_TOPIC", " https://notify.example.invalid/padel ")
    response = Mock(status_code=200, ok=True, text="accepted")
    send = Mock(return_value=response)
    monkeypatch.setattr(client.requests, "post", send)

    result = client.notify("Court costs £24", title="Court availability")

    send.assert_called_once_with(
        "https://notify.example.invalid/padel",
        data="Court costs £24".encode(),
        headers={"Title": "Court availability"},
        timeout=15,
    )
    assert result == {"status_code": 200, "ok": True, "text": "accepted"}
