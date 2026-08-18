"""Create an on-server Audiobookshelf backup."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Create an on-server Audiobookshelf backup.",
    examples=["audiobookshelf.create_backup()"],
    tool_class="admin",
    aliases=[],
)
def create_backup() -> Any:
    """Create and return an Audiobookshelf server backup."""

    return get_client().post("backups")
