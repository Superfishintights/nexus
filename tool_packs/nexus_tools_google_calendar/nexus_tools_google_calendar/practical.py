"""Practical Google Calendar workflow wrappers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .events import insert_event, list_events, patch_event


@register_tool(
    namespace="google_calendar",
    description="Create a timed Google Calendar event from ergonomic fields.",
    examples=['load_tool("google_calendar.create_timed_event")("primary", "Standup", "2026-07-30T09:00:00Z", "2026-07-30T09:30:00Z", attendees=["person@example.com"])'],
    tool_class="write",
    aliases=[],
)
def create_timed_event(
    calendar_id: str,
    summary: str,
    start_datetime: str,
    end_datetime: str,
    *,
    start_time_zone: Optional[str] = None,
    end_time_zone: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[list[str]] = None,
    send_updates: Optional[str] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "summary": summary,
        "start": {"dateTime": start_datetime},
        "end": {"dateTime": end_datetime},
    }
    if start_time_zone:
        body["start"]["timeZone"] = start_time_zone
    if end_time_zone:
        body["end"]["timeZone"] = end_time_zone
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    if attendees:
        body["attendees"] = [{"email": email} for email in attendees]
    return insert_event(calendar_id, body, send_updates=send_updates)


@register_tool(
    namespace="google_calendar",
    description="Create an all-day Google Calendar event from ergonomic fields.",
    examples=['load_tool("google_calendar.create_all_day_event")("primary", "Holiday", "2026-08-01")'],
    tool_class="write",
    aliases=[],
)
def create_all_day_event(
    calendar_id: str,
    summary: str,
    start_date: str,
    *,
    end_date: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    send_updates: Optional[str] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "summary": summary,
        "start": {"date": start_date},
        "end": {"date": end_date or start_date},
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    return insert_event(calendar_id, body, send_updates=send_updates)


@register_tool(
    namespace="google_calendar",
    description="Search Google Calendar events by text and optional time window.",
    examples=['load_tool("google_calendar.search_events")("primary", "budget", time_min="2026-07-01T00:00:00Z")'],
    tool_class="read",
    aliases=[],
)
def search_events(
    calendar_id: str,
    query: str,
    *,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    return list_events(
        calendar_id,
        q=query,
        time_min=time_min,
        time_max=time_max,
        max_results=max_results,
        page_token=page_token,
        single_events=True,
        order_by="startTime",
    )


@register_tool(
    namespace="google_calendar",
    description="Cancel a Google Calendar event by setting its status to cancelled.",
    examples=['load_tool("google_calendar.cancel_event")("primary", "event-id", send_updates="all")'],
    tool_class="destructive",
    aliases=[],
)
def cancel_event(
    calendar_id: str,
    event_id: str,
    *,
    send_updates: Optional[str] = None,
) -> Dict[str, Any]:
    return patch_event(calendar_id, event_id, {"status": "cancelled"}, send_updates=send_updates)
