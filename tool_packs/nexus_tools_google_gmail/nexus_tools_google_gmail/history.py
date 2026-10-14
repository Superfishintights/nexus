"""Gmail history and watch tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import coerce_list, coerce_optional_str, gmail_request, user_path


@register_tool(namespace="google_gmail", description="List Gmail mailbox history changes.", examples=["load_tool('google_gmail.list_history')('12345')"], aliases=[], tool_class="read")
def list_history(start_history_id: str, user_id: str = "me", *, max_results: Optional[int] = None, page_token: Optional[str] = None, label_id: Optional[str] = None, history_types: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "history"), params={"startHistoryId": start_history_id, "maxResults": max_results, "pageToken": coerce_optional_str(page_token), "labelId": coerce_optional_str(label_id), "historyTypes": coerce_list(history_types)})


@register_tool(namespace="google_gmail", description="Start or renew Gmail push notifications for a mailbox.", examples=["load_tool('google_gmail.watch_mailbox')('projects/my-project/topics/gmail')"], aliases=[], tool_class="admin")
def watch_mailbox(topic_name: str, user_id: str = "me", *, label_ids: Optional[Any] = None, label_filter_action: Optional[str] = None, label_filter_behavior: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"topicName": topic_name}
    labels = coerce_list(label_ids)
    if labels:
        payload["labelIds"] = labels
    if label_filter_action:
        payload["labelFilterAction"] = label_filter_action
    if label_filter_behavior:
        payload["labelFilterBehavior"] = label_filter_behavior
    return gmail_request(user_path(user_id, "watch"), method="POST", payload=payload)


@register_tool(namespace="google_gmail", description="Stop Gmail push notifications for a mailbox.", examples=["load_tool('google_gmail.stop_watch')()"], aliases=[], tool_class="admin")
def stop_watch(user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "stop"), method="POST")
