"""Create an Audiobookshelf notification."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Create an Audiobookshelf notification for an event, delivery URLs, and "
        "title and body templates."
    ),
    examples=[
        'audiobookshelf.create_notification({"eventName": "onItemAdded", "urls": ["https://notify.example.com/audiobookshelf"], "titleTemplate": "New audiobook added", "bodyTemplate": "{{title}} is now available."})',
    ],
    tool_class="admin",
    aliases=[],
)
def create_notification(notification: Dict[str, Any]) -> Any:
    """Validate and POST an Audiobookshelf notification definition unchanged."""
    if not isinstance(notification, dict) or not notification:
        raise ValueError("notification must be a non-empty dictionary")

    event_name = notification.get("eventName")
    if not isinstance(event_name, str) or not event_name.strip():
        raise ValueError("notification must include a non-blank eventName")

    urls = notification.get("urls")
    if not isinstance(urls, list) or not urls:
        raise ValueError("notification must include a non-empty urls list")
    if any(not isinstance(url, str) or not url.strip() for url in urls):
        raise ValueError("each url must be a non-blank string")

    for field in ("titleTemplate", "bodyTemplate"):
        value = notification.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"notification must include a non-blank {field}")

    return get_client().post("notifications", body=notification)
