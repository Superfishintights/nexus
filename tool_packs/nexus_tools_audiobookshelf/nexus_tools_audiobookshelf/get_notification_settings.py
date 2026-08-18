"""Audiobookshelf tool: get_notification_settings."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Get Audiobookshelf notification settings and configured notification events. "
        "Sensitive notification endpoint URLs are sanitized."
    ),
    examples=["audiobookshelf.get_notification_settings()"],
    tool_class="admin",
    aliases=[],
)
def get_notification_settings() -> Any:
    """Return notification settings and event configuration with sensitive values redacted."""

    return get_client().get("notifications")
