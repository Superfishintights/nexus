"""List Audiobookshelf server backups."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="List the Audiobookshelf server backup inventory.",
    examples=["audiobookshelf.list_backups()"],
    tool_class="admin",
    aliases=[],
)
def list_backups() -> Any:
    """Return the backups available on the Audiobookshelf server."""

    return get_client().get("backups")
