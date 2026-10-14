from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2].parent
PACK_ROOT = Path(__file__).resolve().parents[1]
for path in (str(REPO_ROOT), str(PACK_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


MODULES = (
    "nexus_tools_google_calendar.acl",
    "nexus_tools_google_calendar.calendar_list",
    "nexus_tools_google_calendar.calendars",
    "nexus_tools_google_calendar.channels",
    "nexus_tools_google_calendar.colors_freebusy",
    "nexus_tools_google_calendar.events",
    "nexus_tools_google_calendar.practical",
    "nexus_tools_google_calendar.settings",
)


class FakeGoogleClient:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, str, Dict[str, Any]]] = []

    def request(self, service: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append((service, path, kwargs))
        return {"service": service, "path": path, **kwargs}


def import_tool_modules() -> None:
    from nexus.tool_registry import clear_registry

    clear_registry()
    for module_name in MODULES:
        if module_name in sys.modules:
            del sys.modules[module_name]
        importlib.import_module(module_name)


def test_registers_expected_google_calendar_tools_with_explicit_classes() -> None:
    import_tool_modules()

    from nexus.tool_registry import iter_tools

    tools = {tool.name: tool for tool in iter_tools() if tool.alias_of is None}
    expected_classes = {
        "google_calendar.cancel_event": "destructive",
        "google_calendar.clear_calendar": "destructive",
        "google_calendar.create_all_day_event": "write",
        "google_calendar.create_timed_event": "write",
        "google_calendar.delete_acl_rule": "destructive",
        "google_calendar.delete_calendar": "destructive",
        "google_calendar.delete_calendar_entry": "destructive",
        "google_calendar.delete_event": "destructive",
        "google_calendar.get_acl_rule": "read",
        "google_calendar.get_calendar": "read",
        "google_calendar.get_calendar_entry": "read",
        "google_calendar.get_colors": "read",
        "google_calendar.get_event": "read",
        "google_calendar.get_setting": "read",
        "google_calendar.import_event": "write",
        "google_calendar.insert_acl_rule": "admin",
        "google_calendar.insert_calendar": "write",
        "google_calendar.insert_calendar_entry": "write",
        "google_calendar.insert_event": "write",
        "google_calendar.list_acl_rules": "read",
        "google_calendar.list_calendar_entries": "read",
        "google_calendar.list_event_instances": "read",
        "google_calendar.list_events": "read",
        "google_calendar.list_settings": "read",
        "google_calendar.move_event": "write",
        "google_calendar.patch_acl_rule": "admin",
        "google_calendar.patch_calendar": "write",
        "google_calendar.patch_calendar_entry": "write",
        "google_calendar.patch_event": "write",
        "google_calendar.query_freebusy": "read",
        "google_calendar.quick_add_event": "write",
        "google_calendar.search_events": "read",
        "google_calendar.stop_channel": "admin",
        "google_calendar.transfer_calendar_ownership": "admin",
        "google_calendar.update_acl_rule": "admin",
        "google_calendar.update_calendar": "write",
        "google_calendar.update_calendar_entry": "write",
        "google_calendar.update_event": "write",
        "google_calendar.watch_acl_rules": "admin",
        "google_calendar.watch_calendar_entries": "admin",
        "google_calendar.watch_events": "admin",
        "google_calendar.watch_settings": "admin",
    }
    assert len(tools) == 42
    assert set(tools) == set(expected_classes)
    assert {name: tool.tool_class for name, tool in tools.items()} == expected_classes


def test_list_events_passes_calendar_path_and_sync_parameters(monkeypatch: Any) -> None:
    import_tool_modules()

    import nexus_tools_google_calendar.client as client_module
    from nexus_tools_google_calendar.events import list_events

    fake = FakeGoogleClient()
    monkeypatch.setattr(client_module, "get_client", lambda: fake)

    result = list_events(
        "team/calendar@example.com",
        sync_token="sync-1",
        max_results=50,
        single_events=True,
        show_deleted=False,
        params={"custom": "kept"},
    )

    assert result["service"] == "calendar"
    assert result["path"] == "calendars/team%2Fcalendar%40example.com/events"
    assert result["method"] == "GET"
    assert result["params"]["syncToken"] == "sync-1"
    assert result["params"]["maxResults"] == 50
    assert result["params"]["singleEvents"] is True
    assert result["params"]["showDeleted"] is False
    assert result["params"]["custom"] == "kept"


def test_insert_event_uses_body_and_send_updates(monkeypatch: Any) -> None:
    import_tool_modules()

    import nexus_tools_google_calendar.client as client_module
    from nexus_tools_google_calendar.events import insert_event

    fake = FakeGoogleClient()
    monkeypatch.setattr(client_module, "get_client", lambda: fake)
    body = {"summary": "Standup"}

    result = insert_event("primary", body, send_updates="all", supports_attachments=True)

    assert result["path"] == "calendars/primary/events"
    assert result["method"] == "POST"
    assert result["payload"] is body
    assert result["params"] == {"sendUpdates": "all", "supportsAttachments": True}


def test_practical_create_timed_event_builds_google_event(monkeypatch: Any) -> None:
    import_tool_modules()

    import nexus_tools_google_calendar.client as client_module
    from nexus_tools_google_calendar.practical import create_timed_event

    fake = FakeGoogleClient()
    monkeypatch.setattr(client_module, "get_client", lambda: fake)

    result = create_timed_event(
        "primary",
        "Planning",
        "2026-07-30T09:00:00Z",
        "2026-07-30T10:00:00Z",
        attendees=["a@example.com", "b@example.com"],
        send_updates="all",
    )

    assert result["method"] == "POST"
    assert result["params"] == {"sendUpdates": "all"}
    assert result["payload"]["summary"] == "Planning"
    assert result["payload"]["attendees"] == [
        {"email": "a@example.com"},
        {"email": "b@example.com"},
    ]


def test_acl_and_settings_watch_paths(monkeypatch: Any) -> None:
    import_tool_modules()

    import nexus_tools_google_calendar.client as client_module
    from nexus_tools_google_calendar.acl import watch_acl_rules
    from nexus_tools_google_calendar.settings import watch_settings

    fake = FakeGoogleClient()
    monkeypatch.setattr(client_module, "get_client", lambda: fake)

    acl_result = watch_acl_rules("primary", {"id": "c1"}, sync_token="s1")
    settings_result = watch_settings({"id": "c2"}, page_token="p1")

    assert acl_result["path"] == "calendars/primary/acl/watch"
    assert acl_result["method"] == "POST"
    assert acl_result["params"] == {"syncToken": "s1"}
    assert settings_result["path"] == "users/me/settings/watch"
    assert settings_result["params"] == {"pageToken": "p1"}
