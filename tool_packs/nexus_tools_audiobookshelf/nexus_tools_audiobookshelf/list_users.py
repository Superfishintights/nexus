"""List Audiobookshelf users."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="List Audiobookshelf users; the shared client redacts returned credential and token fields.",
    examples=["audiobookshelf.list_users()"],
    tool_class="admin",
    aliases=[],
)
def list_users() -> Any:
    """Return Audiobookshelf users with sensitive fields redacted by the shared client."""

    return get_client().get("users")
