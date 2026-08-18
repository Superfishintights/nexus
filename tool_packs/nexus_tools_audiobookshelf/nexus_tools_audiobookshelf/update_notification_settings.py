"""Update Audiobookshelf server-wide notification settings."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Replace or update Audiobookshelf's admin-wide notification settings; supported "
        "notification endpoints and fields depend on the configured connector URL and server version."
    ),
    examples=[
        'audiobookshelf.update_notification_settings({"apprise": {"enabled": true}})',
    ],
    tool_class="admin",
    aliases=[],
)
def update_notification_settings(settings: Dict[str, Any]) -> Any:
    """Validate and PATCH the complete notification-settings payload unchanged."""
    if not isinstance(settings, dict) or not settings:
        raise ValueError("settings must be a non-empty dictionary")

    return get_client().patch("notifications", body=settings)
