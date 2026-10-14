from __future__ import annotations

from unittest.mock import Mock

import pytest

from nexus_tools_audiobookshelf import update_user as update_user_module


def test_update_user_encodes_id_and_patches_exact_updates(monkeypatch):
    client = Mock()
    updates = {
        "isActive": False,
        "permissions": {"download": True},
        "librariesAccessible": ["library-1"],
        "tagsAccessible": ["tag-1"],
    }
    expected = {"id": "user/id", **updates}
    client.segment.return_value = "user%2Fid"
    client.patch.return_value = expected
    monkeypatch.setattr(update_user_module, "get_client", Mock(return_value=client))

    assert update_user_module.update_user("user/id", updates) == expected
    client.segment.assert_called_once_with("user/id", name="user_id")
    client.patch.assert_called_once_with("users/user%2Fid", body=updates)


@pytest.mark.parametrize("updates", [{}, [], None])
def test_update_user_rejects_empty_or_non_dict_updates(updates):
    with pytest.raises(ValueError, match="updates must be a non-empty dictionary"):
        update_user_module.update_user("user-123", updates)


@pytest.mark.parametrize("permissions", [None, [], "admin"])
def test_update_user_rejects_non_dict_permissions(permissions):
    with pytest.raises(ValueError, match="updates.permissions must be a dictionary"):
        update_user_module.update_user("user-123", {"permissions": permissions})
