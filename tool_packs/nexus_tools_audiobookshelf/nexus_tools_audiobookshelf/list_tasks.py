"""List Audiobookshelf background tasks."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="List Audiobookshelf background server tasks.",
    examples=["audiobookshelf.list_tasks()"],
    tool_class="admin",
    aliases=[],
)
def list_tasks() -> Any:
    """Return background tasks currently known to the Audiobookshelf server."""

    return get_client().get("tasks")
