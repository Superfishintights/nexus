"""Google Calendar ACL resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import calendar_request, merge_params, quote_path_segment


def _acl_list_params(
    *,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    show_deleted: Optional[bool] = None,
    sync_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return merge_params(
        {
            "maxResults": max_results,
            "pageToken": page_token,
            "showDeleted": show_deleted,
            "syncToken": sync_token,
        },
        params,
    )


@register_tool(
    namespace="google_calendar",
    description="List access control rules for a Google Calendar calendar.",
    examples=['load_tool("google_calendar.list_acl_rules")("primary")'],
    tool_class="read",
    aliases=[],
)
def list_acl_rules(
    calendar_id: str = "primary",
    *,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    show_deleted: Optional[bool] = None,
    sync_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "GET",
        f"calendars/{quote_path_segment(calendar_id)}/acl",
        params=_acl_list_params(
            max_results=max_results,
            page_token=page_token,
            show_deleted=show_deleted,
            sync_token=sync_token,
            params=params,
        ),
    )


@register_tool(
    namespace="google_calendar",
    description="Get one access control rule from a Google Calendar calendar.",
    examples=['load_tool("google_calendar.get_acl_rule")("primary", "user:person@example.com")'],
    tool_class="read",
    aliases=[],
)
def get_acl_rule(calendar_id: str, rule_id: str) -> Dict[str, Any]:
    return calendar_request(
        "GET",
        f"calendars/{quote_path_segment(calendar_id)}/acl/{quote_path_segment(rule_id)}",
    )


@register_tool(
    namespace="google_calendar",
    description="Create an access control rule for a Google Calendar calendar.",
    examples=['load_tool("google_calendar.insert_acl_rule")("primary", {"role": "reader", "scope": {"type": "user", "value": "person@example.com"}})'],
    tool_class="admin",
    aliases=[],
)
def insert_acl_rule(
    calendar_id: str,
    body: Dict[str, Any],
    *,
    send_notifications: Optional[bool] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/acl",
        params={"sendNotifications": send_notifications},
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Patch an access control rule for a Google Calendar calendar.",
    examples=['load_tool("google_calendar.patch_acl_rule")("primary", "user:person@example.com", {"role": "writer"})'],
    tool_class="admin",
    aliases=[],
)
def patch_acl_rule(
    calendar_id: str,
    rule_id: str,
    body: Dict[str, Any],
    *,
    send_notifications: Optional[bool] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "PATCH",
        f"calendars/{quote_path_segment(calendar_id)}/acl/{quote_path_segment(rule_id)}",
        params={"sendNotifications": send_notifications},
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Replace an access control rule for a Google Calendar calendar.",
    examples=['load_tool("google_calendar.update_acl_rule")("primary", "user:person@example.com", {"role": "reader"})'],
    tool_class="admin",
    aliases=[],
)
def update_acl_rule(
    calendar_id: str,
    rule_id: str,
    body: Dict[str, Any],
    *,
    send_notifications: Optional[bool] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "PUT",
        f"calendars/{quote_path_segment(calendar_id)}/acl/{quote_path_segment(rule_id)}",
        params={"sendNotifications": send_notifications},
        body=body,
    )


@register_tool(
    namespace="google_calendar",
    description="Delete an access control rule from a Google Calendar calendar.",
    examples=['load_tool("google_calendar.delete_acl_rule")("primary", "user:person@example.com")'],
    tool_class="destructive",
    aliases=[],
)
def delete_acl_rule(calendar_id: str, rule_id: str) -> Dict[str, Any]:
    return calendar_request(
        "DELETE",
        f"calendars/{quote_path_segment(calendar_id)}/acl/{quote_path_segment(rule_id)}",
    )


@register_tool(
    namespace="google_calendar",
    description="Watch access control rule changes for a Google Calendar calendar.",
    examples=['load_tool("google_calendar.watch_acl_rules")("primary", {"id": "channel-id", "type": "web_hook", "address": "https://example.com/hook"})'],
    tool_class="admin",
    aliases=[],
)
def watch_acl_rules(
    calendar_id: str,
    body: Dict[str, Any],
    *,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    show_deleted: Optional[bool] = None,
    sync_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return calendar_request(
        "POST",
        f"calendars/{quote_path_segment(calendar_id)}/acl/watch",
        params=_acl_list_params(
            max_results=max_results,
            page_token=page_token,
            show_deleted=show_deleted,
            sync_token=sync_token,
            params=params,
        ),
        body=body,
    )
