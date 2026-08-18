from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import delete_library as delete_library_module


def test_delete_library_encodes_id_and_deletes_library(monkeypatch):
    client = Mock()
    expected = {"deleted": True}
    client.segment.return_value = "fiction%2Fnew"
    client.delete.return_value = expected
    monkeypatch.setattr(delete_library_module, "get_client", Mock(return_value=client))

    assert delete_library_module.delete_library("fiction/new") == expected
    client.segment.assert_called_once_with("fiction/new", name="library_id")
    client.delete.assert_called_once_with("libraries/fiction%2Fnew")
