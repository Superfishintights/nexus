"""Tests for the Audiobookshelf current-user media progress tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import update_media_progress as update_media_progress_module


def test_update_media_progress_is_registered_as_write_tool():
    module = ast.parse(Path(update_media_progress_module.__file__).read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "update_media_progress"
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


def test_update_media_progress_encodes_item_and_patches_exact_progress(monkeypatch):
    client = Mock()
    progress = {"currentTime": 120, "isFinished": False}
    expected = {"success": True}
    client.segment.return_value = "item%2F123"
    client.patch.return_value = expected
    monkeypatch.setattr(
        update_media_progress_module, "get_client", Mock(return_value=client)
    )

    assert update_media_progress_module.update_media_progress("item/123", progress) == expected
    assert list(inspect.signature(update_media_progress_module.update_media_progress).parameters) == [
        "item_id",
        "progress",
        "episode_id",
    ]
    client.segment.assert_called_once_with("item/123", name="item_id")
    client.patch.assert_called_once_with("me/progress/item%2F123", body=progress)


def test_update_media_progress_encodes_optional_episode_and_patches_exact_progress(monkeypatch):
    client = Mock()
    progress = {"currentTime": 60}
    client.segment.side_effect = ["item%2F123", "episode%2F456"]
    monkeypatch.setattr(
        update_media_progress_module, "get_client", Mock(return_value=client)
    )

    update_media_progress_module.update_media_progress(
        "item/123", progress, episode_id="episode/456"
    )

    assert client.segment.call_args_list == [
        (("item/123",), {"name": "item_id"}),
        (("episode/456",), {"name": "episode_id"}),
    ]
    client.patch.assert_called_once_with(
        "me/progress/item%2F123/episode%2F456", body=progress
    )


@pytest.mark.parametrize("item_id", ["", "   ", None])
def test_update_media_progress_rejects_blank_item_id_without_request(item_id):
    with pytest.raises(ValueError, match="item_id must be a non-blank string"):
        update_media_progress_module.update_media_progress(item_id, {"currentTime": 1})


@pytest.mark.parametrize("progress", [{}, [], None])
def test_update_media_progress_rejects_empty_or_non_dict_progress_without_request(progress):
    with pytest.raises(ValueError, match="progress must be a non-empty dictionary"):
        update_media_progress_module.update_media_progress("item-123", progress)
