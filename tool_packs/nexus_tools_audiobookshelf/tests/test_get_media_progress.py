"""Tests for the Audiobookshelf media progress lookup tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import get_media_progress as get_media_progress_module


def test_get_media_progress_is_registered_as_read():
    module_path = Path(get_media_progress_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "get_media_progress"
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
    assert metadata["tool_class"] == "read"
    assert metadata["aliases"] == []


def test_get_media_progress_gets_encoded_item_progress(monkeypatch):
    client = Mock()
    expected = {"libraryItemId": "item/id", "currentTime": 42}
    client.segment.return_value = "item%2Fid"
    client.get.return_value = expected
    monkeypatch.setattr(get_media_progress_module, "get_client", Mock(return_value=client))

    assert get_media_progress_module.get_media_progress("item/id") == expected
    assert list(inspect.signature(get_media_progress_module.get_media_progress).parameters) == [
        "item_id",
        "episode_id",
    ]
    client.segment.assert_called_once_with("item/id", name="item_id")
    client.get.assert_called_once_with("me/progress/item%2Fid")


def test_get_media_progress_gets_encoded_episode_progress(monkeypatch):
    client = Mock()
    expected = {"episodeId": "episode/id", "currentTime": 84}
    client.segment.side_effect = ["podcast%2Fid", "episode%2Fid"]
    client.get.return_value = expected
    monkeypatch.setattr(get_media_progress_module, "get_client", Mock(return_value=client))

    assert (
        get_media_progress_module.get_media_progress("podcast/id", "episode/id")
        == expected
    )
    assert client.segment.call_args_list == [
        (("podcast/id",), {"name": "item_id"}),
        (("episode/id",), {"name": "episode_id"}),
    ]
    client.get.assert_called_once_with("me/progress/podcast%2Fid/episode%2Fid")


@pytest.mark.parametrize("item_id", ["", "   ", None])
def test_get_media_progress_rejects_blank_item_id(item_id):
    with pytest.raises(ValueError, match="item_id must be non-empty"):
        get_media_progress_module.get_media_progress(item_id)


@pytest.mark.parametrize("episode_id", [None, "", "   "])
def test_get_media_progress_omits_blank_episode_id(monkeypatch, episode_id):
    client = Mock()
    client.segment.return_value = "item-123"
    monkeypatch.setattr(get_media_progress_module, "get_client", Mock(return_value=client))

    get_media_progress_module.get_media_progress("item-123", episode_id)

    client.segment.assert_called_once_with("item-123", name="item_id")
    client.get.assert_called_once_with("me/progress/item-123")
