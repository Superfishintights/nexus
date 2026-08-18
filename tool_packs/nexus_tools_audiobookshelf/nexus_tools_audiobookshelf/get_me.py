"""Retrieve the authenticated Audiobookshelf user profile."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Retrieve the profile for the authenticated Audiobookshelf user.",
    examples=["audiobookshelf.get_me()"],
    tool_class="read",
    aliases=[],
)
def get_me() -> Any:
    """Retrieve the profile for the authenticated Audiobookshelf user."""
    return get_client().get("me")
