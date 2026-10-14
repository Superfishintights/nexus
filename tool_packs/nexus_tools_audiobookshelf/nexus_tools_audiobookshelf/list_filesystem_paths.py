"""List configured Audiobookshelf filesystem paths."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="List server-side filesystem paths configured in Audiobookshelf.",
    examples=["audiobookshelf.list_filesystem_paths()"],
    tool_class="admin",
    aliases=[],
)
def list_filesystem_paths() -> Any:
    """Return filesystem paths exposed by the connected Audiobookshelf server."""

    return get_client().get("filesystem")
