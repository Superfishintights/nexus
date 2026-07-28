"""Gmail thread tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import coerce_list, coerce_optional_bool, coerce_optional_str, extract_text_parts, gmail_request, quote_path_segment, user_path


@register_tool(namespace="google_gmail", description="List Gmail threads.", examples=["load_tool('google_gmail.list_threads')(query='is:unread')"], aliases=[], tool_class="read")
def list_threads(user_id: str = "me", *, query: Optional[str] = None, max_results: Optional[int] = None, page_token: Optional[str] = None, include_spam_trash: bool = False, label_ids: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "threads"), params={"q": coerce_optional_str(query), "maxResults": max_results, "pageToken": coerce_optional_str(page_token), "includeSpamTrash": coerce_optional_bool(include_spam_trash), "labelIds": coerce_list(label_ids)})


@register_tool(namespace="google_gmail", description="Get a Gmail thread by ID.", examples=["load_tool('google_gmail.get_thread')('thread_id')"], aliases=[], tool_class="read")
def get_thread(thread_id: str, user_id: str = "me", *, format: str = "full", metadata_headers: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"threads/{quote_path_segment(thread_id)}"), params={"format": coerce_optional_str(format), "metadataHeaders": coerce_list(metadata_headers)})


@register_tool(namespace="google_gmail", description="Get decoded text summaries for every message in a Gmail thread.", examples=["load_tool('google_gmail.get_thread_text')('thread_id')"], aliases=[], tool_class="read")
def get_thread_text(thread_id: str, user_id: str = "me", *, metadata_headers: Optional[Any] = None) -> Dict[str, Any]:
    thread = get_thread(thread_id, user_id=user_id, format="full", metadata_headers=metadata_headers)
    return {"id": thread.get("id"), "historyId": thread.get("historyId"), "snippet": thread.get("snippet"), "messages": [extract_text_parts(message) for message in thread.get("messages") or []]}


@register_tool(namespace="google_gmail", description="Modify labels on a Gmail thread.", examples=["load_tool('google_gmail.modify_thread_labels')('thread_id', add_label_ids=['STARRED'])"], tool_class="write", aliases=[])
def modify_thread_labels(thread_id: str, user_id: str = "me", *, add_label_ids: Optional[Any] = None, remove_label_ids: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"threads/{quote_path_segment(thread_id)}/modify"), method="POST", payload={"addLabelIds": coerce_list(add_label_ids) or [], "removeLabelIds": coerce_list(remove_label_ids) or []})


@register_tool(namespace="google_gmail", description="Move a Gmail thread to trash.", examples=["load_tool('google_gmail.trash_thread')('thread_id')"], aliases=[], tool_class="destructive")
def trash_thread(thread_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"threads/{quote_path_segment(thread_id)}/trash"), method="POST")


@register_tool(namespace="google_gmail", description="Remove a Gmail thread from trash.", examples=["load_tool('google_gmail.untrash_thread')('thread_id')"], aliases=[], tool_class="write")
def untrash_thread(thread_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"threads/{quote_path_segment(thread_id)}/untrash"), method="POST")


@register_tool(namespace="google_gmail", description="Permanently delete a Gmail thread. This cannot be undone.", examples=["load_tool('google_gmail.delete_thread_permanently')('thread_id')"], aliases=[], tool_class="destructive")
def delete_thread_permanently(thread_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"threads/{quote_path_segment(thread_id)}"), method="DELETE")
