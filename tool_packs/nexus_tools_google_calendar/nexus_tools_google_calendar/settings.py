"""Google Calendar settings resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import calendar_request, merge_params, quote_path_segment


@register_tool(
    namespace="google_calendar",
    description="List Google Calendar user settings with paging and sync token support.",
    examples=['load_tool("google_calendar.list_settings")()'],
    tool_class="read",
    aliases=[],
)
def list_settings(
    *,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    sync_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "GET",
        "users/me/settings",
        params=merge_params(
            {"maxResults": max_results, "pageToken": page_token, "syncToken": sync_token},
            params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Get one Google Calendar user setting.",
    examples=['load_tool("google_calendar.get_setting")("timezone")'],
    tool_class="read",
    aliases=[],
)
def get_setting(setting: str) -> Dict[str, Any]:
    return calendar_request("GET", f"users/me/settings/{quote_path_segment(setting)}")


@register_tool(
    namespace="google_calendar",
    description="Watch Google Calendar user setting changes.",
    examples=['load_tool("google_calendar.watch_settings")({"id": "channel-id", "type": "web_hook", "address": "https://example.com/hook"})'],
    tool_class="admin",
    aliases=[],
)
def watch_settings(
    body: Dict[str, Any],
    *,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    sync_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        "users/me/settings/watch",
        params=merge_params(
            {"maxResults": max_results, "pageToken": page_token, "syncToken": sync_token},
            params,
        ),
        body=body,
    )
