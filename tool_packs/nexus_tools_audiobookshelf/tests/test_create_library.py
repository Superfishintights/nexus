"""Tests for the registered Audiobookshelf library-creation tool."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import create_library as create_library_module


def test_create_library_has_admin_metadata():
    module_path = Path(create_library_module.__file__)
    module = ast.parse(module_path.read_text())
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_library"
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
    assert "name" in metadata["description"]
    assert "folders" in metadata["description"]
    assert all(option in metadata["description"] for option in ("mediaType", "provider", "settings"))


def test_create_library_posts_exact_library_definition(monkeypatch):
    client = Mock()
    expected = {"id": "library-123", "name": "Audiobooks"}
    client.post.return_value = expected
    monkeypatch.setattr(create_library_module, "get_client", Mock(return_value=client))
    library = {
        "name": "Audiobooks",
        "folders": [{"fullPath": "/media/audiobooks", "id": "folder-123"}],
        "mediaType": "book",
        "provider": "audible",
        "settings": {"coverAspectRatio": 1.6},
    }

    assert create_library_module.create_library(library) == expected
    assert list(inspect.signature(create_library_module.create_library).parameters) == [
        "library"
    ]
    client.post.assert_called_once_with("libraries", body=library)


@pytest.mark.parametrize(
    "library",
    [
        None,
        {},
        [],
        {"name": "", "folders": [{"fullPath": "/media/audiobooks"}]},
        {"name": "   ", "folders": [{"fullPath": "/media/audiobooks"}]},
        {"name": "Audiobooks", "folders": []},
        {"name": "Audiobooks", "folders": {}},
        {"name": "Audiobooks", "folders": [None]},
        {"name": "Audiobooks", "folders": [{}]},
        {"name": "Audiobooks", "folders": [{"fullPath": ""}]},
        {"name": "Audiobooks", "folders": [{"fullPath": "   "}]},
    ],
)
def test_create_library_rejects_invalid_definitions(library):
    with pytest.raises(ValueError):
        create_library_module.create_library(library)
