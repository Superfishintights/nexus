"""Google Calendar push notification channel tools."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import calendar_request


@register_tool(
    namespace="google_calendar",
    description="Stop a Google Calendar push notification channel.",
    examples=['load_tool("google_calendar.stop_channel")({"id": "channel-id", "resourceId": "resource-id"})'],
    tool_class="admin",
    aliases=[],
)
def stop_channel(body: Dict[str, Any]) -> Dict[str, Any]:
    return calendar_request("POST", "channels/stop", body=body)
