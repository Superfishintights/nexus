"""Google Calendar colors and free/busy tools."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import calendar_request


@register_tool(
    namespace="google_calendar",
    description="Get Google Calendar event and calendar color definitions.",
    examples=['load_tool("google_calendar.get_colors")()'],
    tool_class="read",
    aliases=[],
)
def get_colors() -> Dict[str, Any]:
    return calendar_request("GET", "colors")


@register_tool(
    namespace="google_calendar",
    description="Query free/busy information for calendars over a time range.",
    examples=['load_tool("google_calendar.query_freebusy")({"timeMin": "2026-07-30T09:00:00Z", "timeMax": "2026-07-30T17:00:00Z", "items": [{"id": "primary"}]})'],
    tool_class="read",
    aliases=[],
)
def query_freebusy(body: Dict[str, Any]) -> Dict[str, Any]:
    return calendar_request("POST", "freeBusy", body=body)
