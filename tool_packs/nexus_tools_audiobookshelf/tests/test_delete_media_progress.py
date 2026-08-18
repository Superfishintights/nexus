from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import delete_media_progress as delete_media_progress_module


def test_delete_media_progress_encodes_id_and_deletes_exact_progress(monkeypatch):
    client = Mock()
    expected = {"deleted": True}
    client.segment.return_value = "progress%2Fchapter-1"
    client.delete.return_value = expected
    monkeypatch.setattr(
        delete_media_progress_module,
        "get_client",
        Mock(return_value=client),
    )

    assert delete_media_progress_module.delete_media_progress("progress/chapter-1") == expected
    client.segment.assert_called_once_with("progress/chapter-1", name="progress_id")
    client.delete.assert_called_once_with("me/progress/progress%2Fchapter-1")


@pytest.mark.parametrize("progress_id", ["", "   "])
def test_delete_media_progress_rejects_blank_progress_id(progress_id):
    with pytest.raises(ValueError, match="progress_id must be non-empty"):
        delete_media_progress_module.delete_media_progress(progress_id)
