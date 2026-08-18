"""Tests for the registered Audiobookshelf media-upload tool."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import upload_media as upload_media_module


def test_upload_media_delegates_all_arguments_to_client(monkeypatch):
    client = Mock()
    expected = {"id": "upload-123"}
    client.upload_media.return_value = expected
    monkeypatch.setattr(upload_media_module, "get_client", Mock(return_value=client))
    file_paths = ("/uploads/example.m4b", "/uploads/chapter.mp3")

    assert (
        upload_media_module.upload_media(
            "Example Book",
            "library-123",
            "folder-456",
            file_paths,
            author="Example Author",
            series="Example Series",
        )
        == expected
    )
    client.upload_media.assert_called_once_with(
        title="Example Book",
        library_id="library-123",
        folder_id="folder-456",
        file_paths=file_paths,
        author="Example Author",
        series="Example Series",
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"title": "   "}, "title must be non-empty"),
        ({"library_id": "   "}, "library_id must be non-empty"),
        ({"folder_id": "   "}, "folder_id must be non-empty"),
        ({"file_paths": []}, "file_paths must contain at least one path"),
    ],
)
def test_upload_media_rejects_required_empty_values(kwargs, message):
    arguments = {
        "title": "Example Book",
        "library_id": "library-123",
        "folder_id": "folder-456",
        "file_paths": ["/uploads/example.m4b"],
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=message):
        upload_media_module.upload_media(**arguments)
