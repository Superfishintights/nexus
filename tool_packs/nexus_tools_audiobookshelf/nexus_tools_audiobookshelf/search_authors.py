"""Search author metadata providers in Audiobookshelf."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Search configured Audiobookshelf metadata providers for authors.",
    examples=[
        "audiobookshelf.search_authors(query='Octavia E. Butler')",
    ],
    tool_class="read",
    aliases=[],
)
def search_authors(query: str) -> Any:
    """Search author metadata providers by query."""
    if not query or not query.strip():
        raise ValueError("query must be non-empty")

    return get_client().get("search/authors", params={"q": query})
