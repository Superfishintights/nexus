"""Google Calendar calendar resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import calendar_request, quote_path_segment


@register_tool(
    namespace="google_calendar",
    description="Get metadata for a Google Calendar calendar resource.",
    examples=['load_tool("google_calendar.get_calendar")("primary")'],
    tool_class="read",
    aliases=[],
)
def get_calendar(calendar_id: str = "primary") -> Dict[str, Any]:
    return calendar_request("GET", f"calendars/{quote_path_segment(calendar_id)}")


@register_tool(
    namespace="google_calendar",
    description="Create a secondary Google Calendar calendar resource.",
    examples=['load_tool("google_calendar.insert_calendar")({"summary": "Team calendar"})'],
    tool_class="write",
    aliases=[],
)
def insert_calendar(body: Dict[str, Any]) -> Dict[str, Any]:
    return calendar_request("POST", "calendars", body=body)


@register_tool(
    namespace="google_calendar",
    description="Patch metadata for a Google Calendar calendar resource.",
    examples=['load_tool("google_calendar.patch_calendar")("primary", {"summary": "New name"})'],
    tool_class="write",
    aliases=[],
)
def patch_calendar(calendar_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return calendar_request("PATCH", f"calendars/{quote_path_segment(calendar_id)}", body=body)


@register_tool(
    namespace="google_calendar",
    description="Replace metadata for a Google Calendar calendar resource.",
    examples=['load_tool("google_calendar.update_calendar")("primary", {"summary": "New name"})'],
    tool_class="write",
    aliases=[],
)
def update_calendar(calendar_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return calendar_request("PUT", f"calendars/{quote_path_segment(calendar_id)}", body=body)


@register_tool(
    namespace="google_calendar",
    description="Clear all events from a primary Google Calendar calendar.",
    examples=['load_tool("google_calendar.clear_calendar")("primary")'],
    tool_class="destructive",
    aliases=[],
)
def clear_calendar(calendar_id: str = "primary") -> Dict[str, Any]:
    return calendar_request("POST", f"calendars/{quote_path_segment(calendar_id)}/clear")


@register_tool(
    namespace="google_calendar",
    description="Delete a secondary Google Calendar calendar resource.",
    examples=['load_tool("google_calendar.delete_calendar")("team@example.com")'],
    tool_class="destructive",
    aliases=[],
)
def delete_calendar(calendar_id: str) -> Dict[str, Any]:
    return calendar_request("DELETE", f"calendars/{quote_path_segment(calendar_id)}")


@register_tool(
    namespace="google_calendar",
    description="Transfer ownership of a Google Calendar calendar to another user.",
    examples=['load_tool("google_calendar.transfer_calendar_ownership")("team@example.com", "new-owner@example.com")'],
    tool_class="admin",
    aliases=[],
)
def transfer_calendar_ownership(
    calendar_id: str,
    new_data_owner: str,
    *,
    use_admin_access: Optional[bool] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/transferOwnership",
        params={"newDataOwner": new_data_owner, "useAdminAccess": use_admin_access},
    )
