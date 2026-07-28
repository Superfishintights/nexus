"""Google Calendar event resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import calendar_request, merge_params, quote_path_segment


def _event_collection_params(
    *,
    always_include_email: Optional[bool] = None,
    event_types: Optional[list[str]] = None,
    i_cal_uid: Optional[str] = None,
    max_attendees: Optional[int] = None,
    max_results: Optional[int] = None,
    order_by: Optional[str] = None,
    page_token: Optional[str] = None,
    private_extended_property: Optional[list[str]] = None,
    q: Optional[str] = None,
    shared_extended_property: Optional[list[str]] = None,
    show_deleted: Optional[bool] = None,
    show_hidden_invitations: Optional[bool] = None,
    single_events: Optional[bool] = None,
    sync_token: Optional[str] = None,
    time_max: Optional[str] = None,
    time_min: Optional[str] = None,
    time_zone: Optional[str] = None,
    updated_min: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return merge_params(
        {
            "alwaysIncludeEmail": always_include_email,
            "eventTypes": event_types,
            "iCalUID": i_cal_uid,
            "maxAttendees": max_attendees,
            "maxResults": max_results,
            "orderBy": order_by,
            "pageToken": page_token,
            "privateExtendedProperty": private_extended_property,
            "q": q,
            "sharedExtendedProperty": shared_extended_property,
            "showDeleted": show_deleted,
            "showHiddenInvitations": show_hidden_invitations,
            "singleEvents": single_events,
            "syncToken": sync_token,
            "timeMax": time_max,
            "timeMin": time_min,
            "timeZone": time_zone,
            "updatedMin": updated_min,
        },
        params,
    )


def _event_mutation_params(
    *,
    always_include_email: Optional[bool] = None,
    conference_data_version: Optional[int] = None,
    event_label_version: Optional[int] = None,
    max_attendees: Optional[int] = None,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    supports_attachments: Optional[bool] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return merge_params(
        {
            "alwaysIncludeEmail": always_include_email,
            "conferenceDataVersion": conference_data_version,
            "eventLabelVersion": event_label_version,
            "maxAttendees": max_attendees,
            "sendNotifications": send_notifications,
            "sendUpdates": send_updates,
            "supportsAttachments": supports_attachments,
        },
        params,
    )


@register_tool(
    namespace="google_calendar",
    description="List Google Calendar events with paging, filters, and sync token support.",
    examples=['load_tool("google_calendar.list_events")("primary", max_results=10, single_events=True)'],
    tool_class="read",
    aliases=[],
)
def list_events(
    calendar_id: str = "primary",
    *,
    always_include_email: Optional[bool] = None,
    event_types: Optional[list[str]] = None,
    i_cal_uid: Optional[str] = None,
    max_attendees: Optional[int] = None,
    max_results: Optional[int] = None,
    order_by: Optional[str] = None,
    page_token: Optional[str] = None,
    private_extended_property: Optional[list[str]] = None,
    q: Optional[str] = None,
    shared_extended_property: Optional[list[str]] = None,
    show_deleted: Optional[bool] = None,
    show_hidden_invitations: Optional[bool] = None,
    single_events: Optional[bool] = None,
    sync_token: Optional[str] = None,
    time_max: Optional[str] = None,
    time_min: Optional[str] = None,
    time_zone: Optional[str] = None,
    updated_min: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "GET",
        f"calendars/{quote_path_segment(calendar_id)}/events",
        params=_event_collection_params(
            always_include_email=always_include_email,
            event_types=event_types,
            i_cal_uid=i_cal_uid,
            max_attendees=max_attendees,
            max_results=max_results,
            order_by=order_by,
            page_token=page_token,
            private_extended_property=private_extended_property,
            q=q,
            shared_extended_property=shared_extended_property,
            show_deleted=show_deleted,
            show_hidden_invitations=show_hidden_invitations,
            single_events=single_events,
            sync_token=sync_token,
            time_max=time_max,
            time_min=time_min,
            time_zone=time_zone,
            updated_min=updated_min,
            params=params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Get a single Google Calendar event by ID.",
    examples=['load_tool("google_calendar.get_event")("primary", "event-id")'],
    tool_class="read",
    aliases=[],
)
def get_event(
    calendar_id: str,
    event_id: str,
    *,
    always_include_email: Optional[bool] = None,
    max_attendees: Optional[int] = None,
    time_zone: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "GET",
        f"calendars/{quote_path_segment(calendar_id)}/events/{quote_path_segment(event_id)}",
        params=merge_params(
            {
                "alwaysIncludeEmail": always_include_email,
                "maxAttendees": max_attendees,
                "timeZone": time_zone,
            },
            params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Create a Google Calendar event from a full Event resource body.",
    examples=['load_tool("google_calendar.insert_event")("primary", {"summary": "Standup", "start": {"dateTime": "2026-07-30T09:00:00Z"}, "end": {"dateTime": "2026-07-30T09:30:00Z"}})'],
    tool_class="write",
    aliases=[],
)
def insert_event(
    calendar_id: str,
    body: Dict[str, Any],
    *,
    conference_data_version: Optional[int] = None,
    event_label_version: Optional[int] = None,
    max_attendees: Optional[int] = None,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    supports_attachments: Optional[bool] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/events",
        params=_event_mutation_params(
            conference_data_version=conference_data_version,
            event_label_version=event_label_version,
            max_attendees=max_attendees,
            send_notifications=send_notifications,
            send_updates=send_updates,
            supports_attachments=supports_attachments,
            params=params,
        ),
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Patch a Google Calendar event with partial Event resource fields.",
    examples=['load_tool("google_calendar.patch_event")("primary", "event-id", {"summary": "Updated"})'],
    tool_class="write",
    aliases=[],
)
def patch_event(
    calendar_id: str,
    event_id: str,
    body: Dict[str, Any],
    *,
    always_include_email: Optional[bool] = None,
    conference_data_version: Optional[int] = None,
    event_label_version: Optional[int] = None,
    max_attendees: Optional[int] = None,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    supports_attachments: Optional[bool] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "PATCH",
        f"calendars/{quote_path_segment(calendar_id)}/events/{quote_path_segment(event_id)}",
        params=_event_mutation_params(
            always_include_email=always_include_email,
            conference_data_version=conference_data_version,
            event_label_version=event_label_version,
            max_attendees=max_attendees,
            send_notifications=send_notifications,
            send_updates=send_updates,
            supports_attachments=supports_attachments,
            params=params,
        ),
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Replace a Google Calendar event with a full Event resource body.",
    examples=['load_tool("google_calendar.update_event")("primary", "event-id", {"summary": "Updated"})'],
    tool_class="write",
    aliases=[],
)
def update_event(
    calendar_id: str,
    event_id: str,
    body: Dict[str, Any],
    *,
    always_include_email: Optional[bool] = None,
    conference_data_version: Optional[int] = None,
    event_label_version: Optional[int] = None,
    max_attendees: Optional[int] = None,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    supports_attachments: Optional[bool] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "PUT",
        f"calendars/{quote_path_segment(calendar_id)}/events/{quote_path_segment(event_id)}",
        params=_event_mutation_params(
            always_include_email=always_include_email,
            conference_data_version=conference_data_version,
            event_label_version=event_label_version,
            max_attendees=max_attendees,
            send_notifications=send_notifications,
            send_updates=send_updates,
            supports_attachments=supports_attachments,
            params=params,
        ),
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Delete a Google Calendar event.",
    examples=['load_tool("google_calendar.delete_event")("primary", "event-id", send_updates="none")'],
    tool_class="destructive",
    aliases=[],
)
def delete_event(
    calendar_id: str,
    event_id: str,
    *,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "DELETE",
        f"calendars/{quote_path_segment(calendar_id)}/events/{quote_path_segment(event_id)}",
        params=merge_params(
            {"sendNotifications": send_notifications, "sendUpdates": send_updates},
            params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Create a Google Calendar event from natural language quick-add text.",
    examples=['load_tool("google_calendar.quick_add_event")("primary", "Coffee with Sam tomorrow at 10am")'],
    tool_class="write",
    aliases=[],
)
def quick_add_event(
    calendar_id: str,
    text: str,
    *,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/events/quickAdd",
        params=merge_params(
            {"text": text, "sendNotifications": send_notifications, "sendUpdates": send_updates},
            params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="List instances of a recurring Google Calendar event.",
    examples=['load_tool("google_calendar.list_event_instances")("primary", "event-id", max_results=10)'],
    tool_class="read",
    aliases=[],
)
def list_event_instances(
    calendar_id: str,
    event_id: str,
    *,
    always_include_email: Optional[bool] = None,
    max_attendees: Optional[int] = None,
    max_results: Optional[int] = None,
    original_start: Optional[str] = None,
    page_token: Optional[str] = None,
    show_deleted: Optional[bool] = None,
    time_max: Optional[str] = None,
    time_min: Optional[str] = None,
    time_zone: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "GET",
        f"calendars/{quote_path_segment(calendar_id)}/events/{quote_path_segment(event_id)}/instances",
        params=merge_params(
            {
                "alwaysIncludeEmail": always_include_email,
                "maxAttendees": max_attendees,
                "maxResults": max_results,
                "originalStart": original_start,
                "pageToken": page_token,
                "showDeleted": show_deleted,
                "timeMax": time_max,
                "timeMin": time_min,
                "timeZone": time_zone,
            },
            params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Import an event into Google Calendar without sending notifications.",
    examples=['load_tool("google_calendar.import_event")("primary", {"iCalUID": "uid@example.com", "summary": "Imported"})'],
    tool_class="write",
    aliases=[],
)
def import_event(
    calendar_id: str,
    body: Dict[str, Any],
    *,
    conference_data_version: Optional[int] = None,
    event_label_version: Optional[int] = None,
    supports_attachments: Optional[bool] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/events/import",
        params=merge_params(
            {
                "conferenceDataVersion": conference_data_version,
                "eventLabelVersion": event_label_version,
                "supportsAttachments": supports_attachments,
            },
            params,
        ),
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Move a Google Calendar event to another calendar.",
    examples=['load_tool("google_calendar.move_event")("primary", "event-id", "target@example.com")'],
    tool_class="write",
    aliases=[],
)
def move_event(
    calendar_id: str,
    event_id: str,
    destination: str,
    *,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/events/{quote_path_segment(event_id)}/move",
        params=merge_params(
            {
                "destination": destination,
                "sendNotifications": send_notifications,
                "sendUpdates": send_updates,
            },
            params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Watch changes to Google Calendar events using a Channel resource body.",
    examples=['load_tool("google_calendar.watch_events")("primary", {"id": "channel-id", "type": "web_hook", "address": "https://example.com/hook"})'],
    tool_class="admin",
    aliases=[],
)
def watch_events(
    calendar_id: str,
    body: Dict[str, Any],
    *,
    always_include_email: Optional[bool] = None,
    event_types: Optional[list[str]] = None,
    i_cal_uid: Optional[str] = None,
    max_attendees: Optional[int] = None,
    max_results: Optional[int] = None,
    order_by: Optional[str] = None,
    page_token: Optional[str] = None,
    private_extended_property: Optional[list[str]] = None,
    q: Optional[str] = None,
    shared_extended_property: Optional[list[str]] = None,
    show_deleted: Optional[bool] = None,
    show_hidden_invitations: Optional[bool] = None,
    single_events: Optional[bool] = None,
    sync_token: Optional[str] = None,
    time_max: Optional[str] = None,
    time_min: Optional[str] = None,
    time_zone: Optional[str] = None,
    updated_min: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/events/watch",
        params=_event_collection_params(
            always_include_email=always_include_email,
            event_types=event_types,
            i_cal_uid=i_cal_uid,
            max_attendees=max_attendees,
            max_results=max_results,
            order_by=order_by,
            page_token=page_token,
            private_extended_property=private_extended_property,
            q=q,
            shared_extended_property=shared_extended_property,
            show_deleted=show_deleted,
            show_hidden_invitations=show_hidden_invitations,
            single_events=single_events,
            sync_token=sync_token,
            time_max=time_max,
            time_min=time_min,
            time_zone=time_zone,
            updated_min=updated_min,
            params=params,
        ),
        body=body,
    )
