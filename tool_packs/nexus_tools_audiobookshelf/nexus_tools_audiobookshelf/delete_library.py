"""Delete an Audiobookshelf library."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Delete an Audiobookshelf library. This permanently removes the library's "
        "items and associated user progress."
    ),
    examples=['audiobookshelf.delete_library("library-123")'],
    tool_class="destructive",
    aliases=[],
)
def delete_library(library_id: str) -> Any:
    """DELETE /api/libraries/{library_id}, including its items and user progress."""
    client = get_client()
    encoded = client.segment(library_id, name="library_id")
    return client.delete(f"libraries/{encoded}")
