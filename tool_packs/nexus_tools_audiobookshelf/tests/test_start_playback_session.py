"""Tests for the registered Audiobookshelf playback-session tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import start_playback_session as start_playback_session_module


def test_start_playback_session_has_write_metadata_and_session_guidance():
    module_path = Path(start_playback_session_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "start_playback_session"
    )
    decorator = next(
        decorator
        for decorator in function.decorator_list
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and decorator.func.id == "register_tool"
    )
    metadata = {
        keyword.arg: ast.literal_eval(keyword.value) for keyword in decorator.keywords
    }

    assert metadata["namespace"] == "audiobookshelf"
    assert metadata["tool_class"] == "write"
    assert metadata["aliases"] == []
    description = metadata["description"].lower()
    assert "deviceinfo" in description
    assert "supportedmimetypes" in description
    assert "does not output audio" in description


def test_start_playback_session_posts_item_session_request(monkeypatch):
    client = Mock()
    expected = {"id": "session-123"}
    session_request = {
        "deviceInfo": {"clientName": "Nexus", "deviceId": "nexus-1"},
        "supportedMimeTypes": ["audio/mpeg"],
    }
    client.segment.return_value = "item%2Fid"
    client.post.return_value = expected
    monkeypatch.setattr(
        start_playback_session_module, "get_client", Mock(return_value=client)
    )

    assert start_playback_session_module.start_playback_session("item/id", session_request) == expected
    assert list(inspect.signature(start_playback_session_module.start_playback_session).parameters) == [
        "item_id",
        "session_request",
        "episode_id",
    ]
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.post.assert_called_once_with("items/item%2Fid/play", body=session_request)


def test_start_playback_session_posts_episode_session_request(monkeypatch):
    client = Mock()
    session_request = {"deviceInfo": {"deviceId": "nexus-1"}}
    client.segment.side_effect = ["item%2Fid", "episode%2Fid"]
    monkeypatch.setattr(
        start_playback_session_module, "get_client", Mock(return_value=client)
    )

    start_playback_session_module.start_playback_session(
        "item/id", session_request, episode_id="episode/id"
    )

    assert client.segment.call_args_list == [
        (("item/id",), {"name": "item_id"}),
        (("episode/id",), {"name": "episode_id"}),
    ]
    client.post.assert_called_once_with(
        "items/item%2Fid/play/episode%2Fid", body=session_request
    )


@pytest.mark.parametrize("item_id", [None, "", "   "])
def test_start_playback_session_rejects_blank_item_id(item_id):
    with pytest.raises(ValueError, match="item_id must be a non-blank string"):
        start_playback_session_module.start_playback_session(item_id, {"deviceInfo": {}})


@pytest.mark.parametrize("session_request", [None, {}, []])
def test_start_playback_session_rejects_empty_or_non_dict_session_request(session_request):
    with pytest.raises(ValueError, match="session_request must be a non-empty dictionary"):
        start_playback_session_module.start_playback_session("item-123", session_request)
