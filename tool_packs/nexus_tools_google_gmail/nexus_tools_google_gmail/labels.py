"""Gmail label tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import coerce_json, gmail_request, quote_path_segment, user_path


@register_tool(namespace="google_gmail", description="List Gmail labels.", examples=["load_tool('google_gmail.list_labels')()"], aliases=[], tool_class="read")
def list_labels(user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "labels"))


@register_tool(namespace="google_gmail", description="Get a Gmail label.", examples=["load_tool('google_gmail.get_label')('Label_123')"], aliases=[], tool_class="read")
def get_label(label_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"labels/{quote_path_segment(label_id)}"))


@register_tool(namespace="google_gmail", description="Create a Gmail label.", examples=["load_tool('google_gmail.create_label')('Clients')"], aliases=[], tool_class="write")
def create_label(name: str, user_id: str = "me", *, message_list_visibility: Optional[str] = None, label_list_visibility: Optional[str] = None, color: Optional[Any] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"name": name}
    if message_list_visibility:
        payload["messageListVisibility"] = message_list_visibility
    if label_list_visibility:
        payload["labelListVisibility"] = label_list_visibility
    parsed_color = coerce_json(color)
    if parsed_color:
        payload["color"] = parsed_color
    return gmail_request(user_path(user_id, "labels"), method="POST", payload=payload)


@register_tool(namespace="google_gmail", description="Patch selected fields on a Gmail label.", examples=["load_tool('google_gmail.patch_label')('Label_123', payload={'name':'Clients'})"], aliases=[], tool_class="write")
def patch_label(label_id: str, payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"labels/{quote_path_segment(label_id)}"), method="PATCH", payload=coerce_json(payload) or {})


@register_tool(namespace="google_gmail", description="Replace a Gmail label.", examples=["load_tool('google_gmail.update_label')('Label_123', payload={'name':'Clients'})"], aliases=[], tool_class="write")
def update_label(label_id: str, payload: Any, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"labels/{quote_path_segment(label_id)}"), method="PUT", payload=coerce_json(payload) or {})


@register_tool(namespace="google_gmail", description="Permanently delete a Gmail label and remove it from messages.", examples=["load_tool('google_gmail.delete_label')('Label_123')"], aliases=[], tool_class="destructive")
def delete_label(label_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"labels/{quote_path_segment(label_id)}"), method="DELETE")
