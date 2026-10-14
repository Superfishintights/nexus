"""Gmail message tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import (
    coerce_list,
    coerce_optional_bool,
    coerce_optional_int,
    coerce_optional_str,
    extract_text_parts,
    gmail_request,
    quote_path_segment,
    user_path,
)
from .mime import build_raw_message


@register_tool(namespace="google_gmail", description="List Gmail messages.", examples=["load_tool('google_gmail.list_messages')(query='from:me')"], aliases=[], tool_class="read")
def list_messages(user_id: str = "me", *, query: Optional[str] = None, max_results: Optional[int] = None, page_token: Optional[str] = None, include_spam_trash: bool = False, label_ids: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "messages"), params={"q": coerce_optional_str(query), "maxResults": max_results, "pageToken": coerce_optional_str(page_token), "includeSpamTrash": coerce_optional_bool(include_spam_trash), "labelIds": coerce_list(label_ids)})


@register_tool(namespace="google_gmail", description="Get a Gmail message by ID.", examples=["load_tool('google_gmail.get_message')('msg_id')"], aliases=[], tool_class="read")
def get_message(message_id: str, user_id: str = "me", *, format: str = "full", metadata_headers: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"messages/{quote_path_segment(message_id)}"), params={"format": coerce_optional_str(format), "metadataHeaders": coerce_list(metadata_headers)})


@register_tool(namespace="google_gmail", description="Get decoded text, headers, and attachment metadata from a Gmail message.", examples=["load_tool('google_gmail.get_message_text')('msg_id')"], aliases=[], tool_class="read")
def get_message_text(message_id: str, user_id: str = "me", *, metadata_headers: Optional[Any] = None) -> Dict[str, Any]:
    message = get_message(message_id, user_id=user_id, format="full", metadata_headers=metadata_headers)
    return extract_text_parts(message)


@register_tool(namespace="google_gmail", description="Get headers from a Gmail message.", examples=["load_tool('google_gmail.get_message_headers')('msg_id')"], aliases=[], tool_class="read")
def get_message_headers(message_id: str, user_id: str = "me", *, metadata_headers: Optional[Any] = None) -> Dict[str, Any]:
    message = get_message(message_id, user_id=user_id, format="metadata", metadata_headers=metadata_headers)
    return {"id": message.get("id"), "threadId": message.get("threadId"), "headers": (message.get("payload") or {}).get("headers") or []}


@register_tool(namespace="google_gmail", description="Get a Gmail message attachment as base64 content.", examples=["load_tool('google_gmail.get_attachment')('msg_id', 'att_id')"], aliases=[], tool_class="read")
def get_attachment(message_id: str, attachment_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"messages/{quote_path_segment(message_id)}/attachments/{quote_path_segment(attachment_id)}"))


@register_tool(namespace="google_gmail", description="Send an email message.", examples=["load_tool('google_gmail.send_message')(to='a@example.com', subject='Hi', body='Hello')"], aliases=[], tool_class="write")
def send_message(to: str, subject: str, body: str, user_id: str = "me", *, from_address: Optional[str] = None, cc: Optional[str] = None, bcc: Optional[str] = None, html: bool = False, thread_id: Optional[str] = None, raw: Optional[str] = None, headers: Optional[Any] = None, attachments: Optional[Any] = None, in_reply_to: Optional[str] = None, references: Optional[str] = None) -> Dict[str, Any]:
    payload = raw or build_raw_message(to=to, subject=subject, body=body, from_address=from_address, cc=cc, bcc=bcc, html=html, headers=headers, attachments=attachments, in_reply_to=in_reply_to, references=references)
    body_payload: Dict[str, Any] = {"raw": payload}
    if thread_id:
        body_payload["threadId"] = thread_id
    return gmail_request(user_path(user_id, "messages/send"), method="POST", payload=body_payload)


@register_tool(namespace="google_gmail", description="Reply to a Gmail thread with a composed email.", examples=["load_tool('google_gmail.reply_to_thread')('thread_id', to='a@example.com', subject='Re: Hi', body='Thanks')"], aliases=[], tool_class="write")
def reply_to_thread(thread_id: str, to: str, subject: str, body: str, user_id: str = "me", **kwargs: Any) -> Dict[str, Any]:
    return send_message(to=to, subject=subject, body=body, user_id=user_id, thread_id=thread_id, **kwargs)


@register_tool(namespace="google_gmail", description="Modify labels on a Gmail message.", examples=["load_tool('google_gmail.modify_message_labels')('msg_id', add_label_ids=['STARRED'])"], tool_class="write", aliases=[])
def modify_message_labels(message_id: str, user_id: str = "me", *, add_label_ids: Optional[Any] = None, remove_label_ids: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"messages/{quote_path_segment(message_id)}/modify"), method="POST", payload={"addLabelIds": coerce_list(add_label_ids) or [], "removeLabelIds": coerce_list(remove_label_ids) or []})


@register_tool(namespace="google_gmail", description="Modify labels on multiple Gmail messages.", examples=["load_tool('google_gmail.batch_modify_messages')(['msg_id'], add_label_ids=['STARRED'])"], tool_class="write", aliases=[])
def batch_modify_messages(message_ids: Any, user_id: str = "me", *, add_label_ids: Optional[Any] = None, remove_label_ids: Optional[Any] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "messages/batchModify"), method="POST", payload={"ids": coerce_list(message_ids) or [], "addLabelIds": coerce_list(add_label_ids) or [], "removeLabelIds": coerce_list(remove_label_ids) or []})


@register_tool(namespace="google_gmail", description="Move a Gmail message to trash.", examples=["load_tool('google_gmail.trash_message')('msg_id')"], aliases=[], tool_class="destructive")
def trash_message(message_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"messages/{quote_path_segment(message_id)}/trash"), method="POST")


@register_tool(namespace="google_gmail", description="Remove a Gmail message from trash.", examples=["load_tool('google_gmail.untrash_message')('msg_id')"], aliases=[], tool_class="write")
def untrash_message(message_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"messages/{quote_path_segment(message_id)}/untrash"), method="POST")


@register_tool(namespace="google_gmail", description="Permanently delete a Gmail message. This cannot be undone.", examples=["load_tool('google_gmail.delete_message_permanently')('msg_id')"], aliases=[], tool_class="destructive")
def delete_message_permanently(message_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"messages/{quote_path_segment(message_id)}"), method="DELETE")


@register_tool(namespace="google_gmail", description="Permanently delete multiple Gmail messages. This cannot be undone.", examples=["load_tool('google_gmail.batch_delete_messages_permanently')(['msg_id'])"], tool_class="destructive", aliases=[])
def batch_delete_messages_permanently(message_ids: Any, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "messages/batchDelete"), method="POST", payload={"ids": coerce_list(message_ids) or []})
