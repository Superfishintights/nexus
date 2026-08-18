"""Search external cover providers through Audiobookshelf."""

from __future__ import annotations

from typing import Any, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Search configured cover providers for book or podcast artwork.",
    examples=[
        "audiobookshelf.search_covers(title='The Left Hand of Darkness', author='Ursula K. Le Guin')",
    ],
    tool_class="read",
    aliases=[],
)
def search_covers(
    title: str,
    author: Optional[str] = None,
    provider: Optional[str] = None,
    podcast: bool = False,
) -> Any:
    """Return cover matches from Audiobookshelf's configured providers."""
    if not title or not title.strip():
        raise ValueError("title must be non-empty")

    return get_client().get(
        "search/covers",
        params={
            "title": title,
            "author": author,
            "provider": provider,
            "podcast": podcast,
        },
    )
