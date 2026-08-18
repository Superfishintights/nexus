"""Catalog-level acceptance tests for the Audiobookshelf pack."""

from __future__ import annotations

from collections import Counter

from nexus.tool_catalog import get_catalog, get_catalog_problems


EXPECTED_BY_CLASS = {
    "read": {
        "batch_get_items",
        "find_duplicate_items",
        "get_author",
        "get_library",
        "get_library_filter_data",
        "get_library_item",
        "get_library_stats",
        "get_me",
        "get_media_progress",
        "get_series",
        "get_status",
        "list_libraries",
        "list_library_authors",
        "list_library_items",
        "list_library_series",
        "search_authors",
        "search_books",
        "search_covers",
        "search_library",
    },
    "write": {
        "batch_update_items",
        "match_author",
        "match_library_item",
        "start_playback_session",
        "update_author",
        "update_library_item_cover",
        "update_library_item_media",
        "update_media_progress",
        "update_series",
        "upload_library_item_cover",
        "upload_media",
    },
    "admin": {
        "batch_quick_match_items",
        "batch_scan_items",
        "create_backup",
        "create_library",
        "create_notification",
        "create_user",
        "get_logger_data",
        "get_notification_settings",
        "get_server_info",
        "list_backups",
        "list_filesystem_paths",
        "list_sessions",
        "list_tasks",
        "list_users",
        "match_all_library_items",
        "scan_library",
        "scan_library_item",
        "update_library",
        "update_notification_settings",
        "update_user",
        "upload_backup",
    },
    "destructive": {
        "apply_backup",
        "batch_delete_items",
        "delete_backup",
        "delete_library",
        "delete_library_item",
        "delete_media_progress",
        "delete_user",
        "remove_library_item_cover",
        "remove_library_items_with_issues",
    },
}


def test_catalog_exposes_exact_curated_surface(monkeypatch):
    monkeypatch.setenv("NEXUS_TOOL_PACKAGES", "nexus_tools_audiobookshelf")

    catalog = get_catalog(refresh=True)
    audiobookshelf = {
        name: spec for name, spec in catalog.items() if name.startswith("audiobookshelf.")
    }
    expected = {
        f"audiobookshelf.{name}": tool_class
        for tool_class, names in EXPECTED_BY_CLASS.items()
        for name in names
    }

    assert {name: spec.tool_class for name, spec in audiobookshelf.items()} == expected
    assert Counter(spec.tool_class for spec in audiobookshelf.values()) == {
        "read": 19,
        "write": 11,
        "admin": 21,
        "destructive": 9,
    }
    assert all(spec.alias_of is None for spec in audiobookshelf.values())
    assert get_catalog_problems() == ()
