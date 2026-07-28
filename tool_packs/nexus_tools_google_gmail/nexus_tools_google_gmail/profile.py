"""Gmail profile tools."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import gmail_request, user_path


@register_tool(
    namespace="google_gmail",
    description="Get the Gmail profile for a mailbox.",
    examples=["load_tool('google_gmail.get_profile')()"],
    aliases=[],
    tool_class="read",
)
def get_profile(user_id: str = "me") -> Dict[str, Any]:
    return gmail_request(user_path(user_id, "profile"))
