"""Gmail draft tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import coerce_optional_str, gmail_request, quote_path_segment, user_path
from .mime import build_raw_message


def _draft_payload(to: str, subject: str, body: str, *, thread_id: Optional[str] = None, raw: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
    message: Dict[str, Any] = {"raw": raw or build_raw_message(to=to, subject=subject, body=body, **kwargs)}
    if thread_id:
        message["threadId"] = thread_id
    return {"message": message}


@register_tool(namespace="google_gmail", description="List Gmail drafts.", examples=["load_tool('google_gmail.list_drafts')()"], aliases=[], tool_class="read")
def list_drafts(user_id: str = "me", *, max_results: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "drafts"), params={"maxResults": max_results, "pageToken": coerce_optional_str(page_token)})


@register_tool(namespace="google_gmail", description="Get a Gmail draft.", examples=["load_tool('google_gmail.get_draft')('draft_id')"], aliases=[], tool_class="read")
def get_draft(draft_id: str, user_id: str = "me", *, format: str = "full") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"drafts/{quote_path_segment(draft_id)}"), params={"format": coerce_optional_str(format)})


@register_tool(namespace="google_gmail", description="Create a Gmail draft.", examples=["load_tool('google_gmail.create_draft')(to='a@example.com', subject='Hi', body='Hello')"], aliases=[], tool_class="write")
def create_draft(to: str, subject: str, body: str, user_id: str = "me", *, from_address: Optional[str] = None, cc: Optional[str] = None, bcc: Optional[str] = None, html: bool = False, thread_id: Optional[str] = None, raw: Optional[str] = None, headers: Optional[Any] = None, attachments: Optional[Any] = None, in_reply_to: Optional[str] = None, references: Optional[str] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "drafts"), method="POST", payload=_draft_payload(to, subject, body, thread_id=thread_id, raw=raw, from_address=from_address, cc=cc, bcc=bcc, html=html, headers=headers, attachments=attachments, in_reply_to=in_reply_to, references=references))


@register_tool(namespace="google_gmail", description="Replace a Gmail draft's message content.", examples=["load_tool('google_gmail.update_draft')('draft_id', to='a@example.com', subject='Hi', body='Updated')"], aliases=[], tool_class="write")
def update_draft(draft_id: str, to: str, subject: str, body: str, user_id: str = "me", *, from_address: Optional[str] = None, cc: Optional[str] = None, bcc: Optional[str] = None, html: bool = False, thread_id: Optional[str] = None, raw: Optional[str] = None, headers: Optional[Any] = None, attachments: Optional[Any] = None, in_reply_to: Optional[str] = None, references: Optional[str] = None) -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"drafts/{quote_path_segment(draft_id)}"), method="PUT", payload=_draft_payload(to, subject, body, thread_id=thread_id, raw=raw, from_address=from_address, cc=cc, bcc=bcc, html=html, headers=headers, attachments=attachments, in_reply_to=in_reply_to, references=references))


@register_tool(namespace="google_gmail", description="Send an existing Gmail draft.", examples=["load_tool('google_gmail.send_draft')('draft_id')"], aliases=[], tool_class="write")
def send_draft(draft_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "drafts/send"), method="POST", payload={"id": draft_id})


@register_tool(namespace="google_gmail", description="Permanently delete a Gmail draft.", examples=["load_tool('google_gmail.delete_draft')('draft_id')"], aliases=[], tool_class="destructive")
def delete_draft(draft_id: str, user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, f"drafts/{quote_path_segment(draft_id)}"), method="DELETE")
