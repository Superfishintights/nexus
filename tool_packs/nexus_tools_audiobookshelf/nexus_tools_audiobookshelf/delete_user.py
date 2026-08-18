"""Delete an Audiobookshelf user."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Permanently delete one exact Audiobookshelf user by ID.",
    examples=['audiobookshelf.delete_user("user-123")'],
    tool_class="destructive",
    aliases=[],
)
def delete_user(user_id: str) -> Any:
    """DELETE /api/users/{user_id} for one exact Audiobookshelf user."""
    client = get_client()
    encoded = client.segment(user_id, name="user_id")
    return client.delete(f"users/{encoded}")
