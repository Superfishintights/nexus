"""Google Calendar calendarList resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import calendar_request, merge_params, quote_path_segment


@register_tool(
    namespace="google_calendar",
    description="List calendars on the authenticated user's Google Calendar list.",
    examples=['load_tool("google_calendar.list_calendar_entries")(max_results=20)'],
    tool_class="read",
    aliases=[],
)
def list_calendar_entries(
    *,
    max_results: Optional[int] = None,
    min_access_role: Optional[str] = None,
    page_token: Optional[str] = None,
    show_deleted: Optional[bool] = None,
    show_hidden: Optional[bool] = None,
    show_own_organization_only: Optional[bool] = None,
    sync_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "GET",
        "users/me/calendarList",
        params=merge_params(
            {
                "maxResults": max_results,
                "minAccessRole": min_access_role,
                "pageToken": page_token,
                "showDeleted": show_deleted,
                "showHidden": show_hidden,
                "showOwnOrganizationOnly": show_own_organization_only,
                "syncToken": sync_token,
            },
            params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Get one calendar-list entry for the authenticated user.",
    examples=['load_tool("google_calendar.get_calendar_entry")("primary")'],
    tool_class="read",
    aliases=[],
)
def get_calendar_entry(calendar_id: str = "primary") -> Dict[str, Any]:
    return calendar_request("GET", f"users/me/calendarList/{quote_path_segment(calendar_id)}")


@register_tool(
    namespace="google_calendar",
    description="Add an existing calendar to the authenticated user's calendar list.",
    examples=['load_tool("google_calendar.insert_calendar_entry")({"id": "team@example.com"})'],
    tool_class="write",
    aliases=[],
)
def insert_calendar_entry(
    body: Dict[str, Any],
    *,
    color_rgb_format: Optional[bool] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        "users/me/calendarList",
        params={"colorRgbFormat": color_rgb_format},
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Patch one calendar-list entry for the authenticated user.",
    examples=['load_tool("google_calendar.patch_calendar_entry")("primary", {"hidden": false})'],
    tool_class="write",
    aliases=[],
)
def patch_calendar_entry(
    calendar_id: str,
    body: Dict[str, Any],
    *,
    color_rgb_format: Optional[bool] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "PATCH",
        f"users/me/calendarList/{quote_path_segment(calendar_id)}",
        params={"colorRgbFormat": color_rgb_format},
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Replace one calendar-list entry for the authenticated user.",
    examples=['load_tool("google_calendar.update_calendar_entry")("primary", {"selected": true})'],
    tool_class="write",
    aliases=[],
)
def update_calendar_entry(
    calendar_id: str,
    body: Dict[str, Any],
    *,
    color_rgb_format: Optional[bool] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "PUT",
        f"users/me/calendarList/{quote_path_segment(calendar_id)}",
        params={"colorRgbFormat": color_rgb_format},
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Remove a calendar from the authenticated user's calendar list.",
    examples=['load_tool("google_calendar.delete_calendar_entry")("team@example.com")'],
    tool_class="destructive",
    aliases=[],
)
def delete_calendar_entry(calendar_id: str) -> Dict[str, Any]:
    return calendar_request("DELETE", f"users/me/calendarList/{quote_path_segment(calendar_id)}")


@register_tool(
    namespace="google_calendar",
    description="Watch changes to the authenticated user's Google Calendar list.",
    examples=['load_tool("google_calendar.watch_calendar_entries")({"id": "channel-id", "type": "web_hook", "address": "https://example.com/hook"})'],
    tool_class="admin",
    aliases=[],
)
def watch_calendar_entries(
    body: Dict[str, Any],
    *,
    max_results: Optional[int] = None,
    min_access_role: Optional[str] = None,
    page_token: Optional[str] = None,
    show_deleted: Optional[bool] = None,
    show_hidden: Optional[bool] = None,
    show_own_organization_only: Optional[bool] = None,
    sync_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        "users/me/calendarList/watch",
        params=merge_params(
            {
                "maxResults": max_results,
                "minAccessRole": min_access_role,
                "pageToken": page_token,
                "showDeleted": show_deleted,
                "showHidden": show_hidden,
                "showOwnOrganizationOnly": show_own_organization_only,
                "syncToken": sync_token,
            },
            params,
        ),
        body=body,
    )
