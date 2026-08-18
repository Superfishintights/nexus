from __future__ import annotations

from unittest.mock import Mock

from nexus_tools_audiobookshelf import (
    remove_library_items_with_issues as remove_library_items_with_issues_module,
)


def test_remove_library_items_with_issues_encodes_id_and_delegates_delete(monkeypatch):
    client = Mock()
    expected = {"removed": 2}
    client.segment.return_value = "library%2Fid"
    client.delete.return_value = expected
    monkeypatch.setattr(
        remove_library_items_with_issues_module, "get_client", Mock(return_value=client)
    )

    assert (
        remove_library_items_with_issues_module.remove_library_items_with_issues("library/id")
        == expected
    )
    client.segment.assert_called_once_with("library/id", name="library_id")
    client.delete.assert_called_once_with("libraries/library%2Fid/issues")
