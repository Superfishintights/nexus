from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import scan_library as scan_library_module


def test_scan_library_encodes_id_and_posts_without_body(monkeypatch):
    client = Mock()
    client.segment.return_value = "fiction%2Fnew"
    expected = {"success": True}
    client.post.return_value = expected
    monkeypatch.setattr(scan_library_module, "get_client", Mock(return_value=client))

    assert scan_library_module.scan_library("fiction/new") == expected
    client.segment.assert_called_once_with("fiction/new", name="library_id")
    client.post.assert_called_once_with("libraries/fiction%2Fnew/scan")
