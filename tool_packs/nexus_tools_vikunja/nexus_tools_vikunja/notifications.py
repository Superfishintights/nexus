"""Approved Vikunja API v2 ordinary operations, derived from deployed v2.7.0."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text
from ._ordinary import safe_response, safe_request, fields_object, time_entry_fields, subscription_entity, session_uuid


@register_tool(
    namespace="vikunja",
    description="List notifications. Returns the authenticated user's own notifications, newest first. Notifications about a project the caller can no longer read are omitted; the filtering happens in the query, so pages come back full and total and total_pages count the visible notifications only. Link shares have no notifications and are refused. Query parameters: [{\"name\":\"page\",\"description\":\"1-based page number.\",\"schema\":{\"default\":1,\"description\":\"1-based page number.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"per_page\",\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"schema\":{\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"q\",\"description\":\"Search query; filters the list to items matching this string.\",\"schema\":{\"description\":\"Search query; filters the list to items matching this string.\",\"type\":\"string\"}}]",
    examples=['load_tool("vikunja.list_notifications")()'],
    tool_class='read',
    aliases=[],
)
def list_notifications(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    "GET /api/v2/notifications. Returns the authenticated user's own notifications, newest first. Notifications about a project the caller can no longer read are omitted; the filtering happens in the query, so pages come back full and total and total_pages count the visible notifications only. Link shares have no notifications and are refused."
    client = get_client()
    return safe_response(client.page('notifications', page=page, per_page=per_page, params={**(params or {}), **({'q': query} if query is not None else {})}))


@register_tool(
    namespace="vikunja",
    description="Mark all notifications as read. Marks every notification of the authenticated user as read. Link shares have no notifications and are refused.",
    examples=['load_tool("vikunja.mark_all_notifications_read")()'],
    tool_class='write',
    aliases=[],
)
def mark_all_notifications_read(params: dict[str, Any] | None = None) -> Any:
    'POST /api/v2/notifications. Marks every notification of the authenticated user as read. Link shares have no notifications and are refused.'
    client = get_client()
    return safe_response(safe_request(client, 'POST', 'notifications', params=params))


@register_tool(
    namespace="vikunja",
    description="Delete all notifications. Deletes every notification of the authenticated user. Only the caller's own notifications are affected; link shares have no notifications and are refused.",
    examples=['load_tool("vikunja.delete_all_notifications")()'],
    tool_class='destructive',
    aliases=[],
)
def delete_all_notifications(params: dict[str, Any] | None = None) -> Any:
    "DELETE /api/v2/notifications. Deletes every notification of the authenticated user. Only the caller's own notifications are affected; link shares have no notifications and are refused."
    client = get_client()
    return safe_response(safe_request(client, 'DELETE', 'notifications', params=params))


@register_tool(
    namespace="vikunja",
    description="Mark a notification as (un-)read. Marks one of the authenticated user's notifications as read or unread. A user can only mark their own notifications. read=True marks it read; read=False marks it unread. Request body schema: {\"content\":{\"application/json\":{\"schema\":{\"$ref\":\"#/components/schemas/DatabaseNotifications\"}}},\"required\":true}",
    examples=['load_tool("vikunja.set_notification_read")(notification_id=1, read=True)'],
    tool_class='write',
    aliases=[],
)
def set_notification_read(notification_id: int, read: bool = True, params: dict[str, Any] | None = None) -> Any:
    "PUT /api/v2/notifications/{notificationid}. Marks one of the authenticated user's notifications as read or unread. A user can only mark their own notifications."
    if not isinstance(read, bool):
        raise ValueError("read must be a boolean")
    client = get_client()
    return safe_response(safe_request(client, 'PUT', f'notifications/{positive_id(notification_id)}', params=params, body={'read':read}))

