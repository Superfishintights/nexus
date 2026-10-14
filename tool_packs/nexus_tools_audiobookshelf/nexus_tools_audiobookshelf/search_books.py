"""Search book metadata providers in Audiobookshelf."""

from __future__ import annotations

from typing import Any, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Search configured Audiobookshelf metadata providers for books.",
    examples=[
        "audiobookshelf.search_books(title='The Sandman', author='Neil Gaiman')",
    ],
    tool_class="read",
    aliases=[],
)
def search_books(
    title: str,
    author: Optional[str] = None,
    provider: Optional[str] = None,
) -> Any:
    """Search books by title, optionally narrowing results by author or provider."""
    if not title or not title.strip():
        raise ValueError("title must be non-empty")

    return get_client().get(
        "search/books",
        params={"title": title, "author": author, "provider": provider},
    )
