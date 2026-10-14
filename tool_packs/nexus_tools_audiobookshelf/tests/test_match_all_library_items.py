from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import match_all_library_items as match_all_library_items_module


def test_match_all_library_items_encodes_id_and_uses_mutating_get(monkeypatch):
    client = Mock()
    client.segment.return_value = "fiction%2Fnew"
    expected = {"success": True}
    client.get.return_value = expected
    monkeypatch.setattr(
        match_all_library_items_module, "get_client", Mock(return_value=client)
    )

    assert match_all_library_items_module.match_all_library_items("fiction/new") == expected
    client.segment.assert_called_once_with("fiction/new", name="library_id")
    client.get.assert_called_once_with("libraries/fiction%2Fnew/matchall")
