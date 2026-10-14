"""Tests for the registered Audiobookshelf library-update tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import update_library as update_library_module


def test_update_library_has_required_metadata_and_warning():
    module_path = Path(update_library_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "update_library"
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

    assert metadata["tool_class"] == "admin"
    assert metadata["aliases"] == []
    assert "folders" in metadata["description"]
    assert "full replacement" in metadata["description"]
    assert "omitted folders are removed" in metadata["description"]


def test_update_library_encodes_id_and_patches_exact_updates(monkeypatch):
    client = Mock()
    client.segment.return_value = "library%2F123"
    expected = {"id": "library/123", "name": "Renamed Audiobooks"}
    client.patch.return_value = expected
    monkeypatch.setattr(update_library_module, "get_client", Mock(return_value=client))
    updates = {"name": "Renamed Audiobooks", "settings": {"coverAspectRatio": 1.6}}

    assert update_library_module.update_library("library/123", updates) == expected
    assert list(inspect.signature(update_library_module.update_library).parameters) == [
        "library_id",
        "updates",
    ]
    client.segment.assert_called_once_with("library/123", name="library_id")
    client.patch.assert_called_once_with("libraries/library%2F123", body=updates)


def test_update_library_accepts_valid_folder_replacement(monkeypatch):
    client = Mock()
    client.segment.return_value = "library-123"
    monkeypatch.setattr(update_library_module, "get_client", Mock(return_value=client))
    updates = {"folders": [{"fullPath": "/media/audiobooks", "id": "folder-123"}]}

    update_library_module.update_library("library-123", updates)

    client.patch.assert_called_once_with("libraries/library-123", body=updates)


@pytest.mark.parametrize(
    "updates",
    [
        None,
        {},
        [],
        {"folders": None},
        {"folders": {}},
        {"folders": [None]},
        {"folders": [{}]},
        {"folders": [{"fullPath": ""}]},
        {"folders": [{"fullPath": "   "}]},
    ],
)
def test_update_library_rejects_invalid_updates(updates):
    with pytest.raises(ValueError):
        update_library_module.update_library("library-123", updates)
