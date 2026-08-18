"""Search items within an Audiobookshelf library."""

from __future__ import annotations

from typing import Any, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Search books and podcasts within an Audiobookshelf library.",
    examples=[
        "audiobookshelf.search_library(library_id='library-123', query='Neil Gaiman')",
    ],
    tool_class="read",
    aliases=[],
)
def search_library(library_id: str, query: str, limit: Optional[int] = None) -> Any:
    """Search a library by title, author, narrator, or other indexed text."""
    if not query or not query.strip():
        raise ValueError("query must be non-empty")

    client = get_client()
    encoded_library_id = client.segment(library_id, name="library_id")
    return client.get(
        f"libraries/{encoded_library_id}/search",
        params={"q": query, "limit": limit},
    )
